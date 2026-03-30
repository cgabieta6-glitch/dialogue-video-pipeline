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
    Advanced Triple-Tier Fallback System for Image Search.
    Tier 1: Degoog (Local Docker at port 8082, highly reliable aggregator)
    Tier 2: Wikimedia Commons (Official rate-limit-free API)
    Tier 3: Improved SearXNG (Evasive scraper for safety)
    """


    def __init__(self, tier_order=None):
        self.download_dir = "downloaded_images"
        os.makedirs(self.download_dir, exist_ok=True)
        self.searxng_base = os.getenv("SEARXNG_BASE_URL", "http://localhost:8080")
        
        # Default order if none provided: 1 (Degoog), 2 (Wikimedia), 3 (SearXNG)
        self.tier_order = tier_order or [1, 2, 3]
        
        # User Agents for rotating to avoid 403s on SearXNG
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        ]

    def get_extension(self, url, content_type):
        path = urllib.parse.urlparse(url).path
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.gif', '.jpg', '.jpeg', '.png', '.webp']: return ext
        if content_type:
            if 'image/gif' in content_type: return '.gif'
            if 'image/jpeg' in content_type: return '.jpg'
            if 'image/png' in content_type: return '.png'
            if 'image/webp' in content_type: return '.webp'
        return '.jpg'

    def _download_image(self, img_url, term, source_name="Unknown", dialogue_id=None):
        try:
            req = urllib.request.Request(img_url, headers={"User-Agent": random.choice(self.user_agents)})
            with urllib.request.urlopen(req, timeout=10) as response:
                content_type = response.info().get('Content-Type', '').lower()
                # Strict image validation
                if 'image' not in content_type and 'application/octet-stream' not in content_type:
                    raise Exception(f"URL returned non-image content: {content_type}")
                
                ext = self.get_extension(img_url, content_type)
                
                safe_term = "".join([c if c.isalnum() else "_" for c in term]).strip()
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
        """Tier 2: Evasive SearXNG Implementation"""
        dialogue_id = kwargs.get("dialogue_id")
        try:
            params = {"q": term, "categories": "images", "format": "json", "safesearch": "0"}
            url = f"{self.searxng_base}/search?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={
                "User-Agent": random.choice(self.user_agents), # Rotate agent
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://google.com" # Spoof referer
            })
            
            time.sleep(0.5) # Anti-403 micro-delay
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            results = data.get("results", [])
            if results:
                raw_url = results[0].get("img_src") or results[0].get("url")
                if raw_url and isinstance(raw_url, str):
                    img_url = str(raw_url)
                    if img_url.startswith("//"): img_url = "https:" + img_url
                    print(f"[SearXNG] Found image: {img_url[:50]}...")
                    return self._download_image(img_url, term, source_name="SearXNG", dialogue_id=dialogue_id)
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
                "generator": "search", "gsrsearch": term, "gsrlimit": 1,
                "pithumbsize": 800
            }
            url = f"https://en.wikipedia.org/w/api.php?{urllib.parse.urlencode(params)}"
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
        search_term = f"{term} meme funny" # Automatically append explicit internet culture tags
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


    def search_image(self, term: str, dialogue_id: Optional[int] = None) -> Optional[str]:
        if not term: return None
        
        # 1. Local Cache Check
        safe_term = "".join([c if c.isalnum() else "_" for c in term]).strip()
        prefix = f"{dialogue_id}_" if dialogue_id is not None else ""
        
        # Check both prefixed and non-prefixed as cache fallback
        patterns = [
            os.path.abspath(os.path.join(self.download_dir, f"{prefix}{safe_term}")),
            os.path.abspath(os.path.join(self.download_dir, f"{safe_term}"))
        ]
        
        for p in patterns:
            for ext in ['.gif', '.jpg', '.jpeg', '.png', '.webp']:
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
            
        if not result:
            print(f"[Error] ALL image providers ({self.tier_order}) failed for '{term}'.")
            
        return result

# Expose classic name for old integrations
SearXNGProvider = TripleTierProvider


def process_json_files(tier_order=None):
    provider = TripleTierProvider(tier_order=tier_order)
    
    # We will look for all JSON files that start with "done "
    for filename in os.listdir('.'):
        if filename.startswith('done ') and filename.endswith('.json'):
            print(f"\n--- Processing {filename} ---")
            print(f"--- Using Tiers: {provider.tier_order} ---")
            
            # Create a dedicated download folder named to avoid conflicts with existing .m4a files
            folder_name = filename.replace('.json', '_images')  # e.g., "done chem_ch4_images"
            provider.download_dir = folder_name
            os.makedirs(provider.download_dir, exist_ok=True)
            
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            updated = False
            for item in data:
                term = item.get("image_search", "")
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Triple-Tier Image Search Pipeline")
    parser.add_argument(
        "--tiers", 
        type=str, 
        default="1,2,3", 
        help="Comma-separated tier order (e.g., '1,2,3' for Degoog->Wiki->SearXNG)"
    )
    args = parser.parse_args()
    
    # Parse the tier string into a list of integers
    try:
        requested_tiers = [int(t.strip()) for t in args.tiers.split(",")]
        # Filter to only valid tiers 1, 2, 3
        final_tiers = [t for t in requested_tiers if t in [1, 2, 3]]
        if not final_tiers:
            print("No valid tiers specified. Defaulting to 1,2,3.")
            final_tiers = [1, 2, 3]
    except Exception as e:
        print(f"Error parsing tiers: {e}. Defaulting to 1,2,3.")
        final_tiers = [1, 2, 3]

    process_json_files(tier_order=final_tiers)
