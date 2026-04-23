import os
import json
import urllib.request
import urllib.parse
import urllib.error
from abc import ABC, abstractmethod
from typing import Optional
import re
import random
import time
import socket
import argparse
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Prevent any socket operation from hanging forever
socket.setdefaulttimeout(10.0)

class ImageSearchProvider(ABC):
    """
    Abstract Base Class for Image Search Providers.
    Any new search backend must implement the `search_image` method.
    """
    
    @abstractmethod
    def search_image(self, term: str) -> Optional[str]:
        """
        Searches for an image based on the term, downloads it to `downloaded_images/`, 
        and returns the absolute local path to the image.
        Uses dialogue_id as a filename prefix if provided.
        Return None if not found or if term is empty.
        """
        pass


class TripleTierProvider(ImageSearchProvider):
    """
    Advanced Multi-Tier Fallback System for Image Search.
    Tier 1: Degoog (Local Docker at port 8082, highly reliable aggregator)
    Tier 2: Wikimedia Commons (Official rate-limit-free API)
    Tier 3: Improved SearXNG (Evasive scraper for safety)
    Tier 4: Klipy GIF Search (requires KLIPY_API_KEY)
    Tier 5: Giphy GIF Search (Giphy API, requires GIPHY_API_KEY)
    """


    def __init__(self, tier_order=None, include_meme=True):
        self.download_dir = "downloaded_images"
        os.makedirs(self.download_dir, exist_ok=True)
        self.searxng_base = os.getenv("SEARXNG_BASE_URL", "http://localhost:8888")
        self.klipy_api_key = os.getenv("KLIPY_API_KEY")
        self.giphy_api_key = os.getenv("GIPHY_API_KEY")
        
        # Default order if none provided: 1 (Degoog), 2 (Wikimedia), 3 (SearXNG), 4 (Klipy), 5 (Giphy)
        self.tier_order = tier_order or [1, 2, 3, 4, 5]
        self.include_meme = include_meme
        
        # User Agents for rotating to avoid 403s on SearXNG
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        ]

    def get_extension(self, url, content_type):
        path = urllib.parse.urlparse(url).path
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.gif', '.jpg', '.jpeg', '.png', '.webp', '.mp4', '.webm']: return ext
        if content_type:
            if 'image/gif' in content_type: return '.gif'
            if 'image/jpeg' in content_type: return '.jpg'
            if 'image/png' in content_type: return '.png'
            if 'image/webp' in content_type: return '.webp'
            if 'video/mp4' in content_type: return '.mp4'
            if 'video/webm' in content_type: return '.webm'
        return '.jpg'

    def _download_image(self, img_url, term, source_name="Unknown", dialogue_id=None):
        try:
            req = urllib.request.Request(img_url, headers={"User-Agent": random.choice(self.user_agents)})
            with urllib.request.urlopen(req, timeout=10) as response:
                content_type = response.info().get('Content-Type', '').lower()
                # Strict image/video validation
                if 'image' not in content_type and 'video' not in content_type and 'application/octet-stream' not in content_type:
                    raise Exception(f"URL returned non-media content: {content_type}")
                
                ext = self.get_extension(img_url, content_type)
                
                safe_term = "".join([c if c.isalnum() else "_" for c in term]).strip()[:100]
                prefix = f"{dialogue_id}_" if dialogue_id is not None else ""
                img_name = os.path.join(self.download_dir, f"{prefix}{safe_term}{ext}")
                
                # Download in chunks with an absolute maximum time allowed (10 seconds)
                start_time = time.time()
                with open(img_name, 'wb') as f:
                    while True:
                        if time.time() - start_time > 10.0:
                            raise Exception("Download took too long. Cancelling request.")
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
            
            # File size verification (reject 1x1 tracking pixels or broken downloads)
            if os.path.exists(img_name) and os.path.getsize(img_name) < 2048:
                os.remove(img_name)
                raise Exception(f"Downloaded image is too small (<2KB). Likely invalid/broken.")
                
            return os.path.abspath(img_name)
        except Exception as e:
            print(f"[{source_name}] Download failed for {img_url[:50]}...: {e}")
            return None

    def _search_searxng_improved(self, term: str, **kwargs) -> Optional[str]:
        """Tier 3: Evasive SearXNG Implementation"""
        dialogue_id = kwargs.get("dialogue_id")
        try:
            params = {"q": term, "categories": "images", "format": "json", "safesearch": "0"}
            url = f"{self.searxng_base}/search?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={
                "User-Agent": random.choice(self.user_agents),
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://google.com"
            })
            
            time.sleep(0.5)  # Anti-403 micro-delay
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            results = data.get("results", [])
            if not results:
                print(f"[SearXNG] No results for '{term}'.")
                return None

            # Try up to 5 results, skip SVGs and icon engines
            skip_engines = {"lucide", "devicons", "fontawesome"}
            for r in results[:8]:
                engine = r.get("engine", "").lower()
                if engine in skip_engines:
                    continue

                raw_url = r.get("img_src") or r.get("url")
                if not raw_url or not isinstance(raw_url, str):
                    continue

                img_url = str(raw_url)
                if img_url.startswith("//"):
                    img_url = "https:" + img_url

                # Skip SVG files (not useful for video rendering)
                if img_url.lower().endswith(".svg"):
                    continue

                if not img_url.startswith("http"):
                    continue

                print(f"[SearXNG] Found image: {img_url[:60]}...")
                downloaded = self._download_image(img_url, term, source_name="SearXNG", dialogue_id=dialogue_id)
                if downloaded:
                    return downloaded
                print(f"[SearXNG] Download failed, trying next result...")

            print(f"[SearXNG] All results failed for '{term}'.")
        except Exception as e:
            print(f"[SearXNG] Search failed/timed out: {e}")
        return None

    def _search_wikimedia(self, term: str, **kwargs) -> Optional[str]:
        """Tier 1: Wikimedia Commons API"""
        dialogue_id = kwargs.get("dialogue_id")
        try:
            print(f"[Wikimedia] Trying fallback for '{term}'...")
            params = {
                "action": "query", "format": "json", "prop": "pageimages",
                "generator": "search", "gsrsearch": term, "gsrlimit": 5,
                "pithumbsize": 800, "gsrnamespace": "6"
            }
            url = f"https://commons.wikimedia.org/w/api.php?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": "StewiePipelineBot/2.0"})
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            pages = data.get("query", {}).get("pages", {})
            if pages:
                page = list(pages.values())[0]
                img_url = page.get("thumbnail", {}).get("source")
                if img_url:
                    print(f"[Wikimedia] Found image: {img_url[:50]}...")
                    return self._download_image(img_url, term, source_name="Wikimedia", dialogue_id=kwargs.get("dialogue_id"))
        except Exception as e:
            print(f"[Wikimedia] Search failed: {e}")
        return None

    def _search_degoog(self, term: str, **kwargs) -> Optional[str]:
        """Tier 3: Degoog Image Search API (Self-hosted)"""
        dialogue_id = kwargs.get("dialogue_id")
        
        # Add 'meme funny' suffix if enabled
        search_term = f"{term} meme funny" if self.include_meme else term
        
        try:
            print(f"[Degoog] Trying search for '{search_term}'...")
            degoog_base = os.getenv("DEGOOG_BASE_URL", "http://127.0.0.1:8082")
            # Degoog uses 'type=images' and returns JSON via /api/search
            params = {"q": search_term, "type": "images"}
            url = f"{degoog_base}/api/search?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": random.choice(self.user_agents)})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            results = data.get("results", [])
            if not results:
                print(f"[Degoog] No results found for '{search_term}'.")
                return None

            # Attempt to find a direct image link in the results
            for result in results:
                if not isinstance(result, dict): continue
                # PREFER 'thumbnail' (Direct Bing CDN) over 'url' (Original Page)
                img_url = result.get("thumbnail") or result.get("url")
                if img_url and img_url.startswith('http'):
                    print(f"[Degoog] Found direct image link: {img_url[:50]}...")
                    downloaded = self._download_image(img_url, term, source_name="Degoog", dialogue_id=kwargs.get("dialogue_id"))
                    if downloaded:
                        return downloaded
                    else:
                        print(f"[Degoog] Failed to download {img_url[:30]}..., trying next result.")
        except Exception as e:
            print(f"[Degoog] Search failed: {e}")
        return None

    def _search_klipy(self, term: str, **kwargs) -> Optional[str]:
        """Tier 4: Klipy GIF Search"""
        dialogue_id = kwargs.get("dialogue_id")
        if not self.klipy_api_key:
            print("[Klipy] Skipped: KLIPY_API_KEY not set.")
            return None
        try:
            print(f"[Klipy] Searching for '{term}'...")
            params = {
                "q": term,
                "per_page": 1,
                "customer_id": "pipeline_user",
                "content_filter": "off",
                "format_filter": "gif",
            }
            url = f"https://api.klipy.com/api/v1/{self.klipy_api_key}/gifs/search?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": random.choice(self.user_agents)})

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            items = data.get("data", {}).get("data", [])
            if items:
                # Prefer hd > md > sm, gif format
                file_obj = items[0].get("file", {})
                gif_url = None
                for size in ["hd", "md", "sm"]:
                    entry = file_obj.get(size, {}).get("gif", {})
                    if entry.get("url"):
                        gif_url = entry["url"]
                        break

                if gif_url:
                    print(f"[Klipy] Found GIF: {gif_url[:50]}...")
                    return self._download_image(gif_url, term, source_name="Klipy", dialogue_id=dialogue_id)
            print(f"[Klipy] No results for '{term}'.")
        except Exception as e:
            print(f"[Klipy] Search failed: {e}")
        return None

    def _search_giphy(self, term: str, **kwargs) -> Optional[str]:
        """Tier 5: Giphy GIF Search"""
        dialogue_id = kwargs.get("dialogue_id")
        if not self.giphy_api_key:
            print("[Giphy] Skipped: GIPHY_API_KEY not set.")
            return None
        try:
            print(f"[Giphy] Searching for '{term}'...")
            params = {
                "q": term,
                "api_key": self.giphy_api_key,
                "limit": 1,
                "rating": "r"
            }
            url = f"https://api.giphy.com/v1/gifs/search?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": random.choice(self.user_agents)})

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            results = data.get("data", [])
            if results:
                # Prefer 'original' size, fall back to 'downsized'
                images = results[0].get("images", {})
                gif_url = None
                for fmt in ["original", "downsized", "downsized_medium"]:
                    entry = images.get(fmt)
                    if entry and entry.get("url"):
                        gif_url = entry["url"]
                        break

                if gif_url:
                    print(f"[Giphy] Found GIF: {gif_url[:50]}...")
                    return self._download_image(gif_url, term, source_name="Giphy", dialogue_id=dialogue_id)
            print(f"[Giphy] No results for '{term}'.")
        except Exception as e:
            print(f"[Giphy] Search failed: {e}")
        return None


    def _search_unsplash(self, term: str, dialogue_id=None) -> Optional[str]:
        client_id = os.getenv("UNSPLASH_ACCESS_KEY")
        if not client_id:
            print("[Unsplash] Skipped: UNSPLASH_ACCESS_KEY not set.")
            return None
        try:
            url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(term)}&per_page=1&client_id={client_id}"
            req = urllib.request.Request(url, headers={"User-Agent": random.choice(self.user_agents)})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
            for r in data.get("results", []):
                img_url = r["urls"]["regular"]
                print(f"[Unsplash] Found image: {img_url[:60]}...")
                downloaded = self._download_image(img_url, term, source_name="Unsplash", dialogue_id=dialogue_id)
                if downloaded: return downloaded
        except Exception as e:
            print(f"[Unsplash] Search failed: {e}")
        return None

    def _search_pexels(self, term: str, dialogue_id=None) -> Optional[str]:
        try:
            url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(term)}&per_page=1"
            api_key = os.getenv("PEXELS_API_KEY")
            if not api_key:
                print("[Pexels] Skipped: PEXELS_API_KEY not set.")
                return None
            req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": random.choice(self.user_agents)})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
            for r in data.get("photos", []):
                img_url = r["src"]["medium"]
                print(f"[Pexels] Found image: {img_url[:60]}...")
                downloaded = self._download_image(img_url, term, source_name="Pexels", dialogue_id=dialogue_id)
                if downloaded: return downloaded
        except Exception as e:
            print(f"[Pexels] Search failed: {e}")
        return None

    def _search_pixabay(self, term: str, dialogue_id=None) -> Optional[str]:
        api_key = os.getenv("PIXABAY_API_KEY")
        if not api_key:
            print("[Pixabay] Skipped: PIXABAY_API_KEY not set.")
            return None
        try:
            url = f"https://pixabay.com/api/?key={api_key}&q={urllib.parse.quote(term)}&per_page=3"
            req = urllib.request.Request(url, headers={"User-Agent": random.choice(self.user_agents)})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
            for r in data.get("hits", []):
                img_url = r["webformatURL"]
                print(f"[Pixabay] Found image: {img_url[:60]}...")
                downloaded = self._download_image(img_url, term, source_name="Pixabay", dialogue_id=dialogue_id)
                if downloaded: return downloaded
        except Exception as e:
            print(f"[Pixabay] Search failed: {e}")
        return None

    def _search_pexels_video(self, term: str, dialogue_id=None) -> Optional[str]:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            print("[Pexels Video] Skipped: PEXELS_API_KEY not set.")
            return None
        try:
            url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(term)}&per_page=1"
            req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": random.choice(self.user_agents)})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
            for r in data.get("videos", []):
                video_url = None
                for video_file in r.get("video_files", []):
                    if video_file.get("file_type") == "video/mp4":
                        video_url = video_file.get("link")
                        break
                if video_url:
                    print(f"[Pexels Video] Found video: {video_url[:60]}...")
                    downloaded = self._download_image(video_url, term, source_name="Pexels Video", dialogue_id=dialogue_id)
                    if downloaded: return downloaded
        except Exception as e:
            print(f"[Pexels Video] Search failed: {e}")
        return None

    def _search_pixabay_video(self, term: str, dialogue_id=None) -> Optional[str]:
        api_key = os.getenv("PIXABAY_API_KEY")
        if not api_key:
            print("[Pixabay Video] Skipped: PIXABAY_API_KEY not set.")
            return None
        try:
            url = f"https://pixabay.com/api/videos/?key={api_key}&q={urllib.parse.quote(term)}&per_page=3"
            req = urllib.request.Request(url, headers={"User-Agent": random.choice(self.user_agents)})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
            for r in data.get("hits", []):
                videos = r.get("videos", {})
                video_url = None
                for size in ["medium", "small", "tiny", "large"]:
                    if videos.get(size, {}).get("url"):
                        video_url = videos[size]["url"]
                        break
                if video_url:
                    print(f"[Pixabay Video] Found video: {video_url[:60]}...")
                    downloaded = self._download_image(video_url, term, source_name="Pixabay Video", dialogue_id=dialogue_id)
                    if downloaded: return downloaded
        except Exception as e:
            print(f"[Pixabay Video] Search failed: {e}")
        return None

    def _search_desmos(self, term: str, dialogue_id=None) -> Optional[str]:
        try:
            # Desmos Generative Graph API
            img_url = f"https://www.desmos.com/calculator/render?equation={urllib.parse.quote(term)}&width=1920&height=1080"
            print(f"[Desmos] Generated graph for: {term}")
            # The URL is a direct endpoint that returns a PNG, so we download it directly
            downloaded = self._download_image(img_url, term, source_name="Desmos", dialogue_id=dialogue_id)
            if downloaded: return downloaded
        except Exception as e:
            print(f"[Desmos] Graph generation failed: {e}")
        return None

    def _search_same_energy(self, term: str, dialogue_id=None) -> Optional[str]:
        try:
            url = f"https://same.energy/search?q={urllib.parse.quote(term)}"
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    bypass_csp=True, ignore_https_errors=True
                )
                page = context.new_page()
                page.goto(url, wait_until="networkidle", timeout=15000)
                images = page.eval_on_selector_all("img", "elements => elements.map(e => e.src)")
                browser.close()
            
            for img_url in set(images):
                if img_url.startswith("http") and "blobcdn.same.energy" in img_url:
                    print(f"[Same.Energy] Found image: {img_url[:60]}...")
                    downloaded = self._download_image(img_url, term, source_name="Same.Energy", dialogue_id=dialogue_id)
                    if downloaded: return downloaded
        except Exception as e:
            print(f"[Same.Energy] Search failed: {e}")
        return None

    def _search_openverse(self, term: str, dialogue_id=None) -> Optional[str]:
        client_id = os.getenv("OPENVERSE_CLIENT_ID")
        client_secret = os.getenv("OPENVERSE_CLIENT_SECRET")
        if not client_id or not client_secret:
            print("[Openverse] Skipped: OPENVERSE credentials not set.")
            return None
        try:
            data = urllib.parse.urlencode({'client_id': client_id, 'client_secret': client_secret, 'grant_type': 'client_credentials'}).encode()
            r_auth = urllib.request.Request("https://api.openverse.org/v1/auth_tokens/token/", data=data, method="POST", headers={"User-Agent": random.choice(self.user_agents), "Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(r_auth, timeout=8) as r:
                token = json.loads(r.read().decode())["access_token"]
                
            url = f"https://api.openverse.org/v1/images/?q={urllib.parse.quote(term)}&page_size=1"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": random.choice(self.user_agents)})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
            for r in data.get("results", []):
                img_url = r["url"]
                print(f"[Openverse] Found image: {img_url[:60]}...")
                downloaded = self._download_image(img_url, term, source_name="Openverse", dialogue_id=dialogue_id)
                if downloaded: return downloaded
        except Exception as e:
            print(f"[Openverse] Search failed: {e}")
        return None

    def _search_internet_archive(self, term: str, dialogue_id=None) -> Optional[str]:
        try:
            query = f'mediatype:image AND ({term})'
            params = {"q": query, "fl[]": "identifier", "output": "json", "rows": 5}
            url = f"https://archive.org/advancedsearch.php?{urllib.parse.urlencode(params, doseq=True)}"
            req = urllib.request.Request(url, headers={"User-Agent": random.choice(self.user_agents)})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            for doc in data.get("response", {}).get("docs", []):
                if "identifier" in doc:
                    img_url = f"https://archive.org/services/img/{doc['identifier']}"
                    print(f"[Int. Archive] Found image: {img_url[:60]}...")
                    downloaded = self._download_image(img_url, term, source_name="Int. Archive", dialogue_id=dialogue_id)
                    if downloaded: return downloaded
        except Exception as e:
            print(f"[Int. Archive] Search failed: {e}")
        return None
    def _search_servier(self, term: str, dialogue_id=None) -> Optional[str]:
        try:
            url = f"https://smart.servier.com/?s={urllib.parse.quote(term)}"
            req = urllib.request.Request(url, headers={"User-Agent": random.choice(self.user_agents)})
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
            urls = re.findall(r'<img[^>]+src="([^">]+)"', html)
            for raw_u in set(urls):
                if "wp-content/uploads" in raw_u:
                    img_url = re.sub(r'-\d+x\d+(?=\.png|\.jpg|\.jpeg)', '', raw_u)
                    print(f"[Smart Servier] Found image: {img_url[:60]}...")
                    downloaded = self._download_image(img_url, term, source_name="Smart Servier", dialogue_id=dialogue_id)
                    if downloaded: return downloaded
        except Exception as e:
            print(f"[Smart Servier] Search failed: {e}")
        return None

    def _search_inaturalist(self, term: str, dialogue_id=None) -> Optional[str]:
        try:
            url = f"https://api.inaturalist.org/v1/taxa/autocomplete?q={urllib.parse.quote(term)}"
            req = urllib.request.Request(url, headers={"User-Agent": random.choice(self.user_agents)})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if not data.get("results"): return None
            
            taxon_id = data["results"][0]["id"]
            obs_url = f"https://api.inaturalist.org/v1/observations?taxon_id={taxon_id}&photos=true&per_page=5&quality_grade=research"
            obs_req = urllib.request.Request(obs_url, headers={"User-Agent": random.choice(self.user_agents)})
            with urllib.request.urlopen(obs_req, timeout=8) as obs_resp:
                obs_data = json.loads(obs_resp.read().decode("utf-8"))
            
            for obs in obs_data.get("results", []):
                for photo in obs.get("observation_photos", []):
                    p_url = photo.get("photo", {}).get("url")
                    if p_url:
                        img_url = p_url.replace("square", "medium")
                        print(f"[iNaturalist] Found image: {img_url[:60]}...")
                        downloaded = self._download_image(img_url, term, source_name="iNaturalist", dialogue_id=dialogue_id)
                        if downloaded: return downloaded
        except Exception as e:
            print(f"[iNaturalist] Search failed: {e}")
        return None

    def _search_pdimagearchive(self, term: str, dialogue_id=None) -> Optional[str]:
        try:
            url = f"https://pdimagearchive.org/?s={urllib.parse.quote(term)}"
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    bypass_csp=True, ignore_https_errors=True
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=12000)
                page.wait_for_timeout(2000)
                images = page.eval_on_selector_all("img", "elements => elements.map(e => e.src)")
                browser.close()
            
            for raw_u in set(images):
                if "images.pdimagearchive.org/collections" in raw_u:
                    img_url = raw_u.split("?")[0] # Strip the ?width= downscale arguments
                    print(f"[PDImageArchive] Found image: {img_url[:60]}...")
                    downloaded = self._download_image(img_url, term, source_name="PDImageArchive", dialogue_id=dialogue_id)
                    if downloaded: return downloaded
        except Exception as e:
            print(f"[PDImageArchive] Search failed: {e}")
        return None

    def _search_gbif(self, term: str, dialogue_id=None) -> Optional[str]:
        try:
            url = f"https://api.gbif.org/v1/occurrence/search?q={urllib.parse.quote(term)}&mediaType=StillImage&limit=5"
            req = urllib.request.Request(url, headers={"User-Agent": random.choice(self.user_agents)})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            for result in data.get("results", []):
                for media in result.get("media", []):
                    if media.get("type") == "StillImage" and media.get("identifier"):
                        img_url = media["identifier"]
                        print(f"[GBIF] Found image: {img_url[:60]}...")
                        downloaded = self._download_image(img_url, term, source_name="GBIF", dialogue_id=dialogue_id)
                        if downloaded: return downloaded
        except Exception as e:
            print(f"[GBIF] Search failed: {e}")
        return None

    def search_image(self, term: str, dialogue_id: Optional[int] = None) -> Optional[str]:
        if not term: return None
        
        # 1. Local Cache Check
        safe_term = "".join([c if c.isalnum() else "_" for c in term]).strip()[:100]
        prefix = f"{dialogue_id}_" if dialogue_id is not None else ""
        
        # Check both prefixed and non-prefixed as cache fallback
        patterns = [
            os.path.abspath(os.path.join(self.download_dir, f"{prefix}{safe_term}")),
            os.path.abspath(os.path.join(self.download_dir, f"{safe_term}"))
        ]
        
        for p in patterns:
            for ext in ['.gif', '.jpg', '.jpeg', '.png', '.webp', '.mp4', '.webm']:
                existing = f"{p}{ext}"
                if os.path.exists(existing):
                    print(f"[Cache] Found local image for '{term}' (Pattern: {os.path.basename(existing)}).")
                    return existing

        params = {"dialogue_id": dialogue_id}
        result = None

        # 2. Iterate through configured tiers
        for tier in self.tier_order:
            if result: break

            if tier == 1:
                # Degoog Fallback (Includes 'meme funny')
                result = self._search_degoog(term, **params)
            elif tier == 2:
                # Wikimedia Fallback
                result = self._search_wikimedia(term, **params)
            elif tier == 3:
                # SearXNG Fallback (Improved evasion)
                result = self._search_searxng_improved(term, dialogue_id=dialogue_id)
            elif tier == 4:
                # Klipy GIF Search
                result = self._search_klipy(term, **params)
            elif tier == 5:
                # Giphy GIF Search
                result = self._search_giphy(term, **params)
            elif tier == 6:
                result = self._search_unsplash(term, dialogue_id)
            elif tier == 7:
                result = self._search_pexels(term, dialogue_id)
            elif tier == 8:
                result = self._search_pixabay(term, dialogue_id)
            elif tier == 9:
                result = self._search_openverse(term, dialogue_id)
            elif tier == 10:
                result = self._search_internet_archive(term, dialogue_id)
            elif tier == 11:
                result = self._search_inaturalist(term, dialogue_id)
            elif tier == 12:
                result = self._search_servier(term, dialogue_id)
            elif tier == 13:
                result = self._search_pdimagearchive(term, dialogue_id)
            elif tier == 14:
                result = self._search_gbif(term, dialogue_id)
            elif tier == 15:
                result = self._search_pexels_video(term, dialogue_id)
            elif tier == 16:
                result = self._search_pixabay_video(term, dialogue_id)
            elif tier == 17:
                result = self._search_desmos(term, dialogue_id)
            elif tier == 18:
                result = self._search_same_energy(term, dialogue_id)
            
        if not result:
            print(f"[Error] ALL media providers ({self.tier_order}) failed for '{term}'.")
            
        return result

# Expose classic name for old integrations
SearXNGProvider = TripleTierProvider


def process_json_files(tier_order=None, include_meme=True, use_paragraph=False):
    provider = TripleTierProvider(tier_order=tier_order, include_meme=include_meme)
    
    # We will look for all JSON files that DO NOT start with "done "
    for filename in os.listdir('.'):
        if not filename.startswith('done ') and filename.endswith('.json'):
            print(f"\n--- Processing {filename} ---")
            print(f"--- Using Tiers: {provider.tier_order} ---")
            
            # Create a dedicated download folder named to avoid conflicts with existing .m4a files
            folder_name = f"done {filename.replace('.json', '_images')}"  # e.g., "done chem_ch4_images"
            provider.download_dir = folder_name
            os.makedirs(provider.download_dir, exist_ok=True)
            
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            updated = False
            for item in data:
                term = item.get("paragraph", "") if use_paragraph else item.get("image_search", "")
                dialogue_id = item.get("id")
                
                # If we haven't already downloaded an image for this item
                if "image" not in item and term:
                    print(f"Item {dialogue_id} - Searching for: '{term}'")
                    image_path = provider.search_image(term, dialogue_id=dialogue_id)
                    if image_path:
                        # Add relative path including the folder name
                        item["image"] = os.path.join(folder_name, os.path.basename(image_path)).replace("\\", "/")
                        updated = True
                    else:
                        print(f"Item {dialogue_id} - No image found.")
            
            if updated:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"Successfully updated {filename} with downloaded images.")
            else:
                print(f"No updates necessary for {filename}.")
                
            # Rename the file to have a "done " prefix when fully processed
            done_filename = f"done {filename}"
            try:
                if os.path.exists(done_filename):
                    os.remove(done_filename) # Prevent FileExistsError on Windows
                os.rename(filename, done_filename)
                print(f"Renamed {filename} to {done_filename}")
            except Exception as e:
                print(f"Error renaming {filename} to {done_filename}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Triple-Tier Image Search Pipeline")
    parser.add_argument(
        "--tiers", 
        type=str, 
        default="1,2,3,4,5", 
        help="Comma-separated tier order (e.g., '1,2,3,4,5' for Degoog->Wiki->SearXNG->Klipy->Giphy)"
    )
    parser.add_argument(
        "--no-meme", 
        action="store_true", 
        help="Disable adding 'meme funny' suffix to Degoog searches"
    )
    parser.add_argument(
        "--use-paragraph", 
        action="store_true", 
        help="Use the full paragraph text for image search instead of the 'image_search' field"
    )
    args = parser.parse_args()
    
    # Parse the tier string into a list of integers
    try:
        requested_tiers = [int(t.strip()) for t in args.tiers.split(",")]
        # Filter to only valid tiers 1, 2, 3, 4, 5
        final_tiers = [t for t in requested_tiers if t in [1, 2, 3, 4, 5]]
        if not final_tiers:
            print("No valid tiers specified. Defaulting to 1,2,3,4,5.")
            final_tiers = [1, 2, 3, 4, 5]
    except Exception as e:
        print(f"Error parsing tiers: {e}. Defaulting to 1,2,3.")
        final_tiers = [1, 2, 3, 4, 5]

    process_json_files(tier_order=final_tiers, include_meme=not args.no_meme, use_paragraph=args.use_paragraph)
