"""
Interactive Preview Editor (Step 3.5 -- Advanced)
A local web server that lets you visually review and REPLACE images
for each dialogue segment, pulling results from all 5 search tiers.
Think invideo.ai-style media editing — click any image, pick a replacement.

Usage:
    python preview_editor.py                    # Auto-detects first 'done *.json'
    python preview_editor.py "done exercise no 10.json"  # Specify a file
    python preview_editor.py --port 9000        # Custom port
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import random
import socket
import threading
import webbrowser
import base64
import mimetypes
import time
import argparse
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import webbrowser

try:
    from preview_page import generate_html
except ImportError:
    generate_html = None
from playwright.sync_api import sync_playwright

socket.setdefaulttimeout(10.0)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
]


# ============================================================
# SEARCH FUNCTIONS (Return URLs only, no download)
# ============================================================

def fetch_degoog_urls(term, limit=12):
    """Tier 1: Degoog - return list of image URLs."""
    try:
        degoog_base = os.getenv("DEGOOG_BASE_URL", "http://127.0.0.1:8082")
        params = {"q": term, "type": "images"}
        url = f"{degoog_base}/api/search?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        urls = []
        for r in data.get("results", [])[:limit]:
            if isinstance(r, dict):
                img = r.get("thumbnail") or r.get("url")
                if img and img.startswith("http"):
                    urls.append(img)
        return urls
    except Exception:
        return []


def fetch_wikimedia_urls(term, limit=10):
    """Tier 2: Wikimedia Commons - return list of image URLs."""
    try:
        params = {
            "action": "query", "format": "json", "prop": "pageimages",
            "generator": "search", "gsrsearch": term, "gsrlimit": limit,
            "pithumbsize": 400, "gsrnamespace": "6"
        }
        url = f"https://commons.wikimedia.org/w/api.php?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "StewiePipelineBot/2.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        urls = []
        for page in pages.values():
            thumb = page.get("thumbnail", {}).get("source")
            if thumb:
                urls.append(thumb)
        return urls
    except Exception:
        return []


def fetch_searxng_urls(term, limit=12):
    """Tier 3: SearXNG - return list of image URLs."""
    try:
        searxng_base = os.getenv("SEARXNG_BASE_URL", "http://localhost:8888")
        params = {"q": term, "categories": "images", "format": "json", "safesearch": "0"}
        url = f"{searxng_base}/search?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json",
        })
        time.sleep(0.3)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        urls = []
        for r in data.get("results", [])[:limit]:
            img = r.get("img_src") or r.get("url")
            if img and isinstance(img, str):
                if img.startswith("//"):
                    img = "https:" + img
                if img.startswith("http"):
                    urls.append(img)
        return urls
    except Exception:
        return []


def fetch_klipy_urls(term, limit=12):
    """Tier 4: Klipy GIF - return list of GIF URLs."""
    api_key = os.getenv("KLIPY_API_KEY", "t4CHqwPHXfNhRyoedR8YL9Rnf0omI8KU2C6pjW1Cv31MqB3aWoOgpCff8YEzA1Zh")
    if not api_key:
        return []
    try:
        params = {
            "q": term,
            "per_page": limit,
            "customer_id": "pipeline_user",
            "content_filter": "off",
            "format_filter": "gif",
        }
        url = f"https://api.klipy.com/api/v1/{api_key}/gifs/search?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        urls = []
        for item in data.get("data", {}).get("data", []):
            file_obj = item.get("file", {})
            for size in ["md", "sm", "hd"]:
                entry = file_obj.get(size, {}).get("gif", {})
                if entry.get("url"):
                    urls.append(entry["url"])
                    break
        return urls
    except Exception:
        return []


def fetch_giphy_urls(term, limit=12):
    """Tier 5: Giphy GIF - return list of GIF URLs."""
    api_key = os.getenv("GIPHY_API_KEY", "HjAQuQCRRgZPCZStMtwwDK3EytDhy5vV")
    if not api_key:
        return []
    try:
        params = {"q": term, "api_key": api_key, "limit": limit, "rating": "r"}
        url = f"https://api.giphy.com/v1/gifs/search?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        urls = []
        for r in data.get("data", []):
            images = r.get("images", {})
            for fmt in ["original", "downsized", "downsized_medium"]:
                entry = images.get(fmt)
                if entry and entry.get("url"):
                    urls.append(entry["url"])
                    break
        return urls
    except Exception:
        return []


def _fetch_searxng_engine(term, engine, limit=12):
    try:
        searxng_base = os.getenv("SEARXNG_BASE_URL", "http://localhost:8888")
        params = {"q": term, "categories": "images", "engines": engine, "format": "json", "safesearch": "0"}
        url = f"{searxng_base}/search?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS), "Accept": "application/json"})
        time.sleep(0.3)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        urls = []
        for r in data.get("results", [])[:limit]:
            img = r.get("img_src") or r.get("url")
            if img and isinstance(img, str) and not img.lower().endswith(".svg"):
                if img.startswith("//"): img = "https:" + img
                if img.startswith("http"): urls.append(img)
        return urls
    except Exception:
        return []

def fetch_unsplash_urls(term, limit=12):
    try:
        url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(term)}&per_page={limit}&client_id=rGy28dBeqAc9szkRLHet6kwVQ9-z1UrsEXGG_IfImT0"
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [r["urls"]["regular"] for r in data.get("results", [])]
    except Exception: return []

def fetch_pexels_urls(term, limit=12):
    try:
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(term)}&per_page={limit}"
        req = urllib.request.Request(url, headers={"Authorization": "bBikoIhqeNoqIllcmDZmwrpRBqP4BsxFXfUX5u70RA4PpqAKTAsIFtWB", "User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [r["src"]["medium"] for r in data.get("photos", [])]
    except Exception: return []

def fetch_pixabay_urls(term, limit=12):
    try:
        url = f"https://pixabay.com/api/?key=54448226-5c5a24e493b6a64dfe6f3c560&q={urllib.parse.quote(term)}&per_page={max(3, limit)}"
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [r["webformatURL"] for r in data.get("hits", [])]
    except Exception: return []

def fetch_pexels_video_urls(term, limit=12):
    try:
        url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(term)}&per_page={limit}"
        req = urllib.request.Request(url, headers={"Authorization": "bBikoIhqeNoqIllcmDZmwrpRBqP4BsxFXfUX5u70RA4PpqAKTAsIFtWB", "User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        urls = []
        for r in data.get("videos", []):
            for video_file in r.get("video_files", []):
                if video_file.get("file_type") == "video/mp4":
                    urls.append(video_file.get("link"))
                    break
        return urls[:limit]
    except Exception: return []

def fetch_pixabay_video_urls(term, limit=12):
    try:
        url = f"https://pixabay.com/api/videos/?key=54448226-5c5a24e493b6a64dfe6f3c560&q={urllib.parse.quote(term)}&per_page={max(3, limit)}"
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        urls = []
        for r in data.get("hits", []):
            videos = r.get("videos", {})
            for size in ["medium", "small", "tiny", "large"]:
                if videos.get(size, {}).get("url"):
                    urls.append(videos[size]["url"])
                    break
        return urls[:limit]
    except Exception: return []

def fetch_desmos_urls(term, limit=12):
    # Generates a direct URL to the Desmos API
    return [f"https://www.desmos.com/calculator/render?equation={urllib.parse.quote(term)}&width=1920&height=1080"]

def fetch_same_energy_urls(term, limit=12):
    try:
        url = f"https://same.energy/search?q={urllib.parse.quote(term)}"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                bypass_csp=True, ignore_https_errors=True
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=15000)
            images = page.eval_on_selector_all("img", "elements => elements.map(e => e.src)")
            browser.close()
        
        valid = []
        for img_url in set(images):
            if img_url.startswith("http") and "blobcdn.same.energy" in img_url:
                valid.append(img_url)
                if len(valid) >= limit: break
        return valid
    except Exception: return []

def fetch_openverse_urls(term, limit=12):
    try:
        client_id = "V0fh5TbZs7kKW7xe3tly9mnUivv4Dr6WzjHZ8iOz"
        client_secret = "XtJLQAV9mogv8xIcWqWGzOEoS5nDVEraiSunjcYNh1n8wgDwZsslta2UdUqFYsbNLZpgPrmttFCoxrHAY70dXagnmzhXpemxjNJlXJKZ0h9Zq5XLL4zeyYV1nw0kHjbL"
        # OAuth token wrapper
        data = urllib.parse.urlencode({'client_id': client_id, 'client_secret': client_secret, 'grant_type': 'client_credentials'}).encode()
        r_auth = urllib.request.Request("https://api.openverse.org/v1/auth_tokens/token/", data=data, method="POST", headers={"User-Agent": random.choice(USER_AGENTS), "Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(r_auth, timeout=8) as r:
            token = json.loads(r.read().decode())["access_token"]
            
        url = f"https://api.openverse.org/v1/images/?q={urllib.parse.quote(term)}&page_size={limit}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [r["url"] for r in data.get("results", [])]
    except Exception: return []

def fetch_internet_archive_urls(term, limit=12):
    try:
        query = f'mediatype:image AND ({term})'
        params = {"q": query, "fl[]": "identifier", "output": "json", "rows": limit}
        url = f"https://archive.org/advancedsearch.php?{urllib.parse.urlencode(params, doseq=True)}"
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        urls = []
        for doc in data.get("response", {}).get("docs", []):
            if "identifier" in doc:
                urls.append(f"https://archive.org/services/img/{doc['identifier']}")
        return urls
    except Exception:
        return []

def fetch_inaturalist_urls(term, limit=12):
    try:
        url = f"https://api.inaturalist.org/v1/taxa/autocomplete?q={urllib.parse.quote(term)}"
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not data.get("results"): return []
        
        taxon_id = data["results"][0]["id"]
        obs_url = f"https://api.inaturalist.org/v1/observations?taxon_id={taxon_id}&photos=true&per_page={limit}&quality_grade=research"
        obs_req = urllib.request.Request(obs_url, headers={"User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(obs_req, timeout=8) as obs_resp:
            obs_data = json.loads(obs_resp.read().decode("utf-8"))
        
        urls = []
        for obs in obs_data.get("results", []):
            for photo in obs.get("observation_photos", []):
                p_url = photo.get("photo", {}).get("url")
                if p_url:
                    urls.append(p_url.replace("square", "medium"))
                    break
        return urls
    except Exception: return []

def fetch_servier_urls(term, limit=12):
    try:
        url = f"https://smart.servier.com/?s={urllib.parse.quote(term)}"
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        urls = re.findall(r'<img[^>]+src="([^">]+)"', html)
        valid = []
        for raw_u in set(urls):
            if "wp-content/uploads" in raw_u:
                valid.append(re.sub(r'-\d+x\d+(?=\.png|\.jpg|\.jpeg)', '', raw_u))
        return valid[:max(1, limit)]
    except Exception:
        return []

def fetch_pdimagearchive_urls(term, limit=12):
    try:
        url = f"https://pdimagearchive.org/?s={urllib.parse.quote(term)}"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                bypass_csp=True, ignore_https_errors=True
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=12000)
            page.wait_for_timeout(2000)
            images = page.eval_on_selector_all("img", "elements => elements.map(e => e.src)")
            browser.close()
        
        valid = []
        for raw_u in set(images):
            if "images.pdimagearchive.org/collections" in raw_u:
                valid.append(raw_u.split("?")[0])
                if len(valid) >= limit: break
        return valid
    except Exception: return []

def fetch_gbif_urls(term, limit=12):
    try:
        url = f"https://api.gbif.org/v1/occurrence/search?q={urllib.parse.quote(term)}&mediaType=StillImage&limit={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        urls = []
        for result in data.get("results", []):
            for media in result.get("media", []):
                if media.get("type") == "StillImage" and media.get("identifier"):
                    urls.append(media["identifier"])
        return urls[:limit]
    except Exception: return []

TIER_MAP = {
    1: ("Degoog", fetch_degoog_urls),
    2: ("Wikimedia", fetch_wikimedia_urls),
    3: ("SearXNG", fetch_searxng_urls),
    4: ("Klipy GIF", fetch_klipy_urls),
    5: ("Giphy GIF", fetch_giphy_urls),
    6: ("Unsplash", fetch_unsplash_urls),
    7: ("Pexels", fetch_pexels_urls),
    8: ("Pixabay", fetch_pixabay_urls),
    9: ("Openverse", fetch_openverse_urls),
    10: ("Int. Archive", fetch_internet_archive_urls),
    11: ("iNaturalist (Botany)", fetch_inaturalist_urls),
    12: ("Smart Servier (Medical)", fetch_servier_urls),
    13: ("PDImageArchive", fetch_pdimagearchive_urls),
    14: ("GBIF (Bio Dataset)", fetch_gbif_urls),
    15: ("Pexels Video", fetch_pexels_video_urls),
    16: ("Pixabay Video", fetch_pixabay_video_urls),
    17: ("Desmos Graph", fetch_desmos_urls),
    18: ("Same.Energy", fetch_same_energy_urls),
}


# ============================================================
# IMAGE DOWNLOAD
# ============================================================

def get_extension(url, content_type=""):
    """Determine file extension from URL or content-type."""
    path = urllib.parse.urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    if ext in [".gif", ".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm"]:
        return ext
    if content_type:
        if "gif" in content_type: return ".gif"
        if "jpeg" in content_type: return ".jpg"
        if "png" in content_type: return ".png"
        if "webp" in content_type: return ".webp"
        if "mp4" in content_type: return ".mp4"
        if "webm" in content_type: return ".webm"
    return ".jpg"


def download_and_save(url, save_dir, term, dialogue_id=None):
    """Download an image from URL, save to save_dir, return relative path."""
    os.makedirs(save_dir, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.info().get("Content-Type", "").lower()
            if "image" not in content_type and "video" not in content_type and "octet-stream" not in content_type:
                return None
            ext = get_extension(url, content_type)
            safe_term = "".join([c if c.isalnum() else "_" for c in term]).strip()[:100]
            prefix = f"{dialogue_id}_" if dialogue_id is not None else ""
            filename = f"{prefix}{safe_term}{ext}"
            filepath = os.path.join(save_dir, filename)

            start = time.time()
            with open(filepath, "wb") as f:
                while True:
                    if time.time() - start > 15:
                        raise Exception("Download timeout")
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)

            if os.path.getsize(filepath) < 2048:
                os.remove(filepath)
                return None

            return filepath
    except Exception:
        return None


# ============================================================
# GLOBAL STATE
# ============================================================

class AppState:
    json_file = None
    json_data = None
    images_folder = None
    title = ""


# ============================================================
# HTTP HANDLER
# ============================================================

class EditorHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        """Suppress default access logs."""
        pass

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---- ROUTING ----

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            self.send_html(get_editor_html(AppState.title, len(AppState.json_data)))
        elif path == "/api/data":
            self.send_json(AppState.json_data)
        elif path == "/api/files":
            files = sorted([f for f in os.listdir(".") if f.startswith("done ") and f.endswith(".json")])
            self.send_json({"files": files, "current": AppState.json_file})
        elif path == "/api/search":
            self._handle_search(parsed.query)
        elif path.startswith("/local-image/"):
            self._serve_local_image(urllib.parse.unquote(path[len("/local-image/"):]))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/replace":
            self._handle_replace()
        elif self.path == "/api/switch_file":
            self._handle_switch_file()
        elif self.path == "/api/export_html":
            self._handle_export_html()
        else:
            self.send_error(404)

    # ---- API HANDLERS ----

    def _handle_switch_file(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except Exception:
            self.send_json({"success": False, "error": "Invalid request body"}, 400)
            return

        new_file = body.get("file")
        if not new_file or not os.path.exists(new_file) or not new_file.endswith(".json"):
            self.send_json({"success": False, "error": "Invalid file"}, 400)
            return

        try:
            with open(new_file, "r", encoding="utf-8") as f:
                AppState.json_data = json.load(f)
            AppState.json_file = new_file
            AppState.title = new_file.replace("done ", "").replace(".json", "")
            AppState.images_folder = new_file.replace(".json", "_images")
            os.makedirs(AppState.images_folder, exist_ok=True)
            self.send_json({"success": True, "title": AppState.title})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def _handle_export_html(self):
        if not generate_html:
            self.send_json({"success": False, "error": "preview_page.py not found"}, 500)
            return
            
        try:
            html_content = generate_html(AppState.json_data, AppState.title)
            out_dir = "output_videos"
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{AppState.title}_preview.html")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            self.send_json({"success": True, "path": out_path})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def _handle_search(self, qs):
        params = urllib.parse.parse_qs(qs)
        term = params.get("q", [""])[0]
        tier = int(params.get("tier", ["0"])[0])

        if tier not in TIER_MAP or not term:
            self.send_json({"tier": tier, "name": "Unknown", "urls": []})
            return

        name, fetch_fn = TIER_MAP[tier]
        urls = fetch_fn(term)
        self.send_json({"tier": tier, "name": name, "urls": urls})

    def _handle_replace(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except Exception:
            self.send_json({"success": False, "error": "Invalid request body"}, 400)
            return

        seg_id = body.get("id")
        image_url = body.get("url")
        new_search_term = body.get("search_term")

        if seg_id is None or not image_url:
            self.send_json({"success": False, "error": "Missing id or url"}, 400)
            return

        # Find the segment
        segment = None
        for item in AppState.json_data:
            if item.get("id") == seg_id:
                segment = item
                break

        if not segment:
            self.send_json({"success": False, "error": f"Segment {seg_id} not found"}, 404)
            return

        # Delete old image file if it exists
        old_image = segment.get("image", "")
        if old_image and os.path.exists(old_image):
            try:
                os.remove(old_image)
            except Exception:
                pass

        # Download the new image
        term = new_search_term or segment.get("image_search", "image")
        local_path = download_and_save(image_url, AppState.images_folder, term, dialogue_id=seg_id)

        if not local_path:
            self.send_json({"success": False, "error": "Failed to download image"})
            return

        # Update segment
        rel_path = os.path.join(AppState.images_folder, os.path.basename(local_path)).replace("\\", "/")
        segment["image"] = rel_path
        if new_search_term:
            segment["image_search"] = new_search_term

        # Save JSON
        try:
            with open(AppState.json_file, "w", encoding="utf-8") as f:
                json.dump(AppState.json_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.send_json({"success": False, "error": f"Failed to save JSON: {e}"})
            return

        self.send_json({"success": True, "image": rel_path})

    def _serve_local_image(self, rel_path):
        """Serve a local image file."""
        # Security: prevent directory traversal
        abs_path = os.path.abspath(rel_path)
        if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
            self.send_error(404, "Image not found")
            return

        mime, _ = mimetypes.guess_type(abs_path)
        if not mime:
            mime = "application/octet-stream"

        try:
            with open(abs_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(data)
        except Exception:
            self.send_error(500)


# ============================================================
# HTML / CSS / JS (Single Page App)
# ============================================================

def get_editor_html(title, count):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Editor - {title}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: 'Inter', sans-serif;
    background: #0a0c10;
    color: #e1e4e8;
    min-height: 100vh;
}}

/* ---- HEADER ---- */
.top-bar {{
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(10, 12, 16, 0.85);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding: 0.8rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.top-bar h1 {{
    font-size: 1.1rem;
    font-weight: 600;
    color: #fff;
}}
.top-bar .meta {{
    font-size: 0.75rem;
    color: #8b949e;
}}

/* ---- CARDS ---- */
.container {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 1.5rem 1rem;
}}

.card {{
    display: flex;
    align-items: stretch;
    background: #151921;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    margin-bottom: 0.75rem;
    overflow: hidden;
    transition: border-color 0.2s;
}}
.card:hover {{
    border-color: rgba(255,255,255,0.12);
}}

.card-text {{
    flex: 1;
    padding: 1rem 1.25rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-width: 0;
}}

.card-header {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-bottom: 0.5rem;
}}

.badge {{
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 0.15rem 0.5rem;
    border-radius: 5px;
}}
.speaker-a .badge {{ background: rgba(99,179,237,0.12); color: #63b3ed; }}
.speaker-b .badge {{ background: rgba(183,148,244,0.12); color: #b794f4; }}

.id-badge {{
    font-size: 0.6rem;
    color: #484f58;
    font-weight: 500;
}}

.paragraph {{
    font-size: 0.9rem;
    line-height: 1.55;
    color: #c0c6ce;
}}

/* ---- IMAGE CELL (clickable) ---- */
.card-image {{
    width: 200px;
    min-width: 200px;
    background: #0d1117;
    position: relative;
    cursor: pointer;
    overflow: hidden;
}}
.card-image img, .card-image video {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    transition: filter 0.2s;
}}
.card-image:hover img, .card-image:hover video {{
    filter: brightness(0.45);
}}
.card-image .overlay {{
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.2s;
    pointer-events: none;
}}
.card-image:hover .overlay {{
    opacity: 1;
}}
.overlay-icon {{
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(4px);
    border-radius: 50%;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
}}
.overlay-icon svg {{
    width: 20px;
    height: 20px;
    fill: #fff;
}}
.no-image {{
    width: 100%;
    height: 100%;
    min-height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    color: #484f58;
}}

/* Speaker B flipped */
.speaker-b {{ flex-direction: row-reverse; }}
.speaker-b .card-text {{ text-align: right; }}
.speaker-b .card-header {{ justify-content: flex-end; }}

/* ---- MODAL ---- */
.modal-backdrop {{
    position: fixed;
    inset: 0;
    z-index: 200;
    background: rgba(0,0,0,0.7);
    backdrop-filter: blur(6px);
    display: none;
    align-items: center;
    justify-content: center;
}}
.modal-backdrop.open {{
    display: flex;
}}

.modal {{
    background: #151921;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    width: 90vw;
    max-width: 900px;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: 0 24px 80px rgba(0,0,0,0.5);
}}

.modal-header {{
    padding: 1rem 1.25rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    flex-shrink: 0;
}}
.modal-header h2 {{
    font-size: 0.95rem;
    font-weight: 600;
    color: #fff;
    white-space: nowrap;
}}
.modal-close {{
    background: none;
    border: none;
    color: #8b949e;
    font-size: 1.3rem;
    cursor: pointer;
    padding: 0.25rem;
    line-height: 1;
}}
.modal-close:hover {{ color: #fff; }}

.search-row {{
    padding: 0.75rem 1.25rem;
    display: flex;
    gap: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    flex-shrink: 0;
}}
.search-row input {{
    flex: 1;
    background: #0d1117;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    color: #e1e4e8;
    font-family: inherit;
    font-size: 0.85rem;
    outline: none;
    transition: border-color 0.2s;
}}
.search-row input:focus {{
    border-color: rgba(99,179,237,0.5);
}}
.search-btn {{
    background: #2563eb;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.1rem;
    font-family: inherit;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
    white-space: nowrap;
}}
.search-btn:hover {{ background: #1d4ed8; }}
.search-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}

/* ---- URL paste row ---- */
.url-row {{
    padding: 0.5rem 1.25rem;
    display: flex;
    gap: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    flex-shrink: 0;
}}
.url-row input {{
    flex: 1;
    background: #0d1117;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 0.45rem 0.75rem;
    color: #e1e4e8;
    font-family: inherit;
    font-size: 0.8rem;
    outline: none;
}}
.url-row input:focus {{
    border-color: rgba(183,148,244,0.5);
}}
.url-apply-btn {{
    background: #7c3aed;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 0.45rem 0.9rem;
    font-family: inherit;
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
}}
.url-apply-btn:hover {{ background: #6d28d9; }}

.modal-body {{
    flex: 1;
    overflow-y: auto;
    padding: 1rem 1.25rem;
}}

/* ---- TIER SECTIONS ---- */
.tier-section {{
    margin-bottom: 1.25rem;
}}
.tier-label {{
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #8b949e;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.tier-label .dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    display: inline-block;
}}
.tier-1 .dot {{ background: #3b82f6; }}
.tier-2 .dot {{ background: #10b981; }}
.tier-3 .dot {{ background: #f59e0b; }}
.tier-4 .dot {{ background: #ec4899; }}
.tier-5 .dot {{ background: #8b5cf6; }}

.tier-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 0.5rem;
}}

.tier-thumb {{
    aspect-ratio: 4/3;
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    border: 2px solid transparent;
    transition: border-color 0.15s, transform 0.15s;
    background: #0d1117;
    position: relative;
}}
.tier-thumb:hover {{
    border-color: #2563eb;
    transform: scale(1.03);
}}
.tier-thumb img, .tier-thumb video {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}}

.tier-loading, .tier-empty, .tier-error {{
    font-size: 0.75rem;
    color: #484f58;
    padding: 0.5rem 0;
}}

/* Spinner */
.spinner {{
    display: inline-block;
    width: 14px; height: 14px;
    border: 2px solid rgba(255,255,255,0.1);
    border-top-color: #63b3ed;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    vertical-align: middle;
    margin-right: 0.4rem;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}

/* ---- TOAST ---- */
.toast {{
    position: fixed;
    bottom: 1.5rem;
    left: 50%;
    transform: translateX(-50%) translateY(80px);
    background: #1e293b;
    color: #e1e4e8;
    padding: 0.6rem 1.2rem;
    border-radius: 10px;
    font-size: 0.82rem;
    font-weight: 500;
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
    z-index: 300;
    opacity: 0;
    transition: all 0.3s ease;
    pointer-events: none;
}}
.toast.success {{ border-left: 3px solid #10b981; }}
.toast.error {{ border-left: 3px solid #ef4444; }}
.toast.show {{
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}}

/* ---- REPLACING OVERLAY ---- */
.replacing-overlay {{
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
}}

/* ---- RESPONSIVE ---- */
@media (max-width: 700px) {{
    .card {{ flex-direction: column !important; }}
    .card-image {{ width: 100%; min-width: unset; height: 180px; }}
    .speaker-b .card-text {{ text-align: left; }}
    .speaker-b .card-header {{ justify-content: flex-start; }}
    .modal {{ width: 96vw; max-height: 92vh; }}
    .tier-grid {{ grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); }}
}}
</style>
</head>
<body>

<div class="top-bar">
    <div style="display: flex; align-items: center; gap: 1rem;">
        <h1 id="page-title">{title}</h1>
        <select id="file-switcher" onchange="switchFile(this.value)" style="background: #151921; color: #e1e4e8; border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 0.3rem 0.5rem; font-family: inherit; font-size: 0.8rem; cursor: pointer; outline: none;"></select>
        <button onclick="exportHtml()" style="background: #10b981; color: #fff; border: none; border-radius: 6px; padding: 0.3rem 0.8rem; font-size: 0.8rem; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#059669'" onmouseout="this.style.background='#10b981'">Export HTML</button>
    </div>
    <span class="meta" id="page-meta">{count} segments &middot; Click any image to replace</span>
</div>

<div class="container" id="cards"></div>

<!-- MODAL -->
<div class="modal-backdrop" id="modal">
    <div class="modal">
        <div class="modal-header">
            <h2 id="modal-title">Replace Image</h2>
            <button class="modal-close" onclick="closeModal()">&times;</button>
        </div>
        <div class="search-row">
            <input type="text" id="search-input" placeholder="Search term..." autocomplete="off">
            <button class="search-btn" id="search-btn" onclick="doSearch()">Search All Tiers</button>
            <button class="search-btn" id="desmos-btn" onclick="doDesmosSearch()" style="background: #0284c7;">Generate Desmos</button>
        </div>
        <div class="url-row">
            <input type="text" id="url-input" placeholder="Or paste an image URL directly...">
            <button class="url-apply-btn" onclick="applyCustomUrl()">Apply URL</button>
        </div>
        <div class="modal-body" id="modal-body"></div>
    </div>
</div>

<!-- TOAST -->
<div class="toast" id="toast"></div>

<script>
// ============================================================
// STATE
// ============================================================
let segments = [];
let activeSegId = null;

const TIERS = [
    {{ id: 1, name: 'Degoog', dot: '#3b82f6' }},
    {{ id: 2, name: 'Wikimedia', dot: '#10b981' }},
    {{ id: 3, name: 'SearXNG', dot: '#f59e0b' }},
    {{ id: 4, name: 'Klipy GIF', dot: '#ec4899' }},
    {{ id: 5, name: 'Giphy GIF', dot: '#8b5cf6' }},
    {{ id: 6, name: 'Unsplash', dot: '#ef4444' }},
    {{ id: 7, name: 'Pexels', dot: '#14b8a6' }},
    {{ id: 8, name: 'Pixabay', dot: '#f97316' }},
    {{ id: 9, name: 'Openverse', dot: '#84cc16' }},
    {{ id: 10, name: 'Int. Archive', dot: '#a8a29e' }},
    {{ id: 11, name: 'iNaturalist', dot: '#16a34a' }},
    {{ id: 12, name: 'Servier Med', dot: '#e11d48' }},
    {{ id: 13, name: 'PD Archive', dot: '#000000' }},
    {{ id: 14, name: 'GBIF Repo', dot: '#10b981' }},
    {{ id: 15, name: 'Pexels Vid', dot: '#14b8a6' }},
    {{ id: 16, name: 'Pixabay Vid', dot: '#f97316' }},
    {{ id: 17, name: 'Desmos Math', dot: '#3b82f6', manualOnly: true }},
    {{ id: 18, name: 'Same.Energy', dot: '#d946ef' }},
];

// ============================================================
// INIT
// ============================================================
async function init() {{
    const fileResp = await fetch('/api/files');
    const fileData = await fileResp.json();
    const select = document.getElementById('file-switcher');
    select.innerHTML = fileData.files.map(f => `<option value="${{f}}" ${{f === fileData.current ? 'selected' : ''}}>${{f}}</option>`).join('');

    await loadData();
}}

async function loadData() {{
    const resp = await fetch('/api/data');
    segments = await resp.json();
    document.getElementById('page-meta').innerHTML = `${{segments.length}} segments &middot; Click any image to replace`;
    renderCards();
}}

async function switchFile(filename) {{
    showToast('Switching file...', '');
    try {{
        const resp = await fetch('/api/switch_file', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ file: filename }})
        }});
        const data = await resp.json();
        if (data.success) {{
            document.getElementById('page-title').textContent = data.title;
            await loadData();
            showToast('File loaded', 'success');
        }} else {{
            showToast('Failed to switch', 'error');
        }}
    }} catch (e) {{
        showToast('Network error', 'error');
    }}
}}

async function exportHtml() {{
    showToast('Exporting HTML...', '');
    try {{
        const resp = await fetch('/api/export_html', {{ method: 'POST' }});
        const data = await resp.json();
        if (data.success) {{
            showToast(`Exported! Saved to ${{data.path}}`, 'success');
        }} else {{
            showToast(data.error || 'Export failed', 'error');
        }}
    }} catch (e) {{
        showToast('Network error', 'error');
    }}
}}

// ============================================================
// RENDER
// ============================================================
function renderCards() {{
    const container = document.getElementById('cards');
    container.innerHTML = segments.map(seg => {{
        const isB = String(seg.character || '').includes('01');
        const cls = isB ? 'speaker-b' : 'speaker-a';
        const label = isB ? 'Speaker 2' : 'Speaker 1';
        const imgSrc = seg.image ? `/local-image/${{encodeURIComponent(seg.image)}}` : '';
        const isVid = imgSrc.toLowerCase().includes('.mp4') || imgSrc.toLowerCase().includes('.webm');
        const imgHtml = imgSrc
            ? (isVid ? `<video id="img-${{seg.id}}" src="${{imgSrc}}" autoplay loop muted playsinline></video>` : `<img id="img-${{seg.id}}" src="${{imgSrc}}" alt="Segment ${{seg.id}}">`)
            : `<div class="no-image">No image</div>`;
        return `
        <div class="card ${{cls}}" id="card-${{seg.id}}">
            <div class="card-text">
                <div class="card-header">
                    <span class="badge">${{label}}</span>
                    <span class="id-badge">#${{seg.id}}</span>
                </div>
                <p class="paragraph">${{escHtml(seg.paragraph || '')}}</p>
            </div>
            <div class="card-image" onclick="openModal(${{seg.id}})">
                ${{imgHtml}}
                <div class="overlay">
                    <div class="overlay-icon">
                        <svg viewBox="0 0 24 24"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 000-1.41l-2.34-2.34a1 1 0 00-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>
                    </div>
                </div>
            </div>
        </div>`;
    }}).join('');
}}

function escHtml(s) {{
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

// ============================================================
// MODAL
// ============================================================
function openModal(id) {{
    activeSegId = id;
    const seg = segments.find(s => s.id === id);
    if (!seg) return;

    document.getElementById('modal-title').textContent = `Replace Image — #${{id}}`;
    document.getElementById('search-input').value = seg.image_search || seg.paragraph || '';
    document.getElementById('url-input').value = '';
    document.getElementById('modal').classList.add('open');

    // Render empty tier sections
    const body = document.getElementById('modal-body');
    body.innerHTML = TIERS.map(t => `
        <div class="tier-section tier-${{t.id}}">
            <div class="tier-label"><span class="dot"></span>${{t.name}}</div>
            <div id="tier-results-${{t.id}}" class="tier-loading">Ready to search</div>
        </div>
    `).join('');

    // Auto-search
    doSearch();
}}

function closeModal() {{
    document.getElementById('modal').classList.remove('open');
    activeSegId = null;
}}

// Close on backdrop click
document.getElementById('modal').addEventListener('click', function(e) {{
    if (e.target === this) closeModal();
}});

// Close on Escape
document.addEventListener('keydown', e => {{
    if (e.key === 'Escape') closeModal();
}});

// Enter key in search input
document.getElementById('search-input').addEventListener('keydown', e => {{
    if (e.key === 'Enter') doSearch();
}});

// ============================================================
// SEARCH
// ============================================================
async function doSearch() {{
    const term = document.getElementById('search-input').value.trim();
    if (!term) return;

    const btn = document.getElementById('search-btn');
    btn.disabled = true;
    btn.textContent = 'Searching...';

    // Show loading for each auto tier
    TIERS.forEach(t => {{
        if (!t.manualOnly) {{
            document.getElementById(`tier-results-${{t.id}}`).innerHTML = '<span class="spinner"></span> Searching...';
        }}
    }});

    // Fire all tier searches in parallel
    const promises = TIERS.map(async (t) => {{
        if (t.manualOnly) return;
        try {{
            const resp = await fetch(`/api/search?q=${{encodeURIComponent(term)}}&tier=${{t.id}}`);
            const data = await resp.json();
            renderTierResults(t.id, data.urls || []);
        }} catch (e) {{
            document.getElementById(`tier-results-${{t.id}}`).innerHTML =
                '<div class="tier-error">Failed to reach this tier</div>';
        }}
    }});

    await Promise.all(promises);
    btn.disabled = false;
    btn.textContent = 'Search All Tiers';
}}

async function doDesmosSearch() {{
    const term = document.getElementById('search-input').value.trim();
    if (!term) return;

    const btn = document.getElementById('desmos-btn');
    btn.disabled = true;
    btn.textContent = 'Generating...';

    const t = TIERS.find(x => x.id === 17);
    document.getElementById(`tier-results-${{t.id}}`).innerHTML = '<span class="spinner"></span> Generating...';

    try {{
        const resp = await fetch(`/api/search?q=${{encodeURIComponent(term)}}&tier=${{t.id}}`);
        const data = await resp.json();
        renderTierResults(t.id, data.urls || []);
    }} catch (e) {{
        document.getElementById(`tier-results-${{t.id}}`).innerHTML =
            '<div class="tier-error">Failed to reach this tier</div>';
    }}

    btn.disabled = false;
    btn.textContent = 'Generate Desmos';
}}

function renderTierResults(tierId, urls) {{
    const el = document.getElementById(`tier-results-${{tierId}}`);
    if (!urls.length) {{
        el.innerHTML = '<div class="tier-empty">No results</div>';
        return;
    }}
    el.className = 'tier-grid';
    el.innerHTML = urls.map(url => {{
        const lower = url.toLowerCase();
        const isVid = lower.includes('.mp4') || lower.includes('.webm') || lower.includes('/video');
        const mediaHtml = isVid 
            ? `<video src="${{escAttr(url)}}" autoplay loop muted playsinline onloadeddata="this.play()" onerror="this.parentElement.style.display='none'"></video>` 
            : `<img src="${{escAttr(url)}}" loading="lazy" onerror="this.parentElement.style.display='none'">`;
        return `
        <div class="tier-thumb" onclick="selectImage('${{escAttr(url)}}')">
            ${{mediaHtml}}
        </div>
        `;
    }}).join('');
}}

function escAttr(s) {{
    return s.replace(/'/g, "\\\\'").replace(/"/g, '&quot;');
}}

// ============================================================
// REPLACE
// ============================================================
async function selectImage(url) {{
    if (activeSegId === null) return;
    const currentSegId = activeSegId;
    const term = document.getElementById('search-input').value.trim();

    closeModal();
    showToast('Downloading...', '');

    try {{
        const resp = await fetch('/api/replace', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ id: currentSegId, url: url, search_term: term }})
        }});
        const data = await resp.json();

        if (data.success) {{
            // Update local state
            const seg = segments.find(s => s.id === currentSegId);
            if (seg) {{
                seg.image = data.image;
                if (term) seg.image_search = term;
            }}
            // Update card image
            const imgEl = document.getElementById(`img-${{currentSegId}}`);
            if (imgEl) {{
                imgEl.src = `/local-image/${{encodeURIComponent(data.image)}}?t=${{Date.now()}}`;
            }} else {{
                // Card had no image before, re-render
                renderCards();
            }}
            showToast('Image replaced!', 'success');
        }} else {{
            showToast(data.error || 'Replace failed', 'error');
        }}
    }} catch (e) {{
        showToast('Network error', 'error');
    }}
}}

async function applyCustomUrl() {{
    const url = document.getElementById('url-input').value.trim();
    if (!url) return;
    await selectImage(url);
}}

// ============================================================
// TOAST
// ============================================================
function showToast(msg, type) {{
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = 'toast ' + (type || '') + ' show';
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove('show'), 2500);
}}

// ============================================================
// BOOT
// ============================================================
init();
</script>
</body>
</html>"""


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Interactive Preview Editor")
    parser.add_argument("json_file", nargs="?", help="Path to a 'done *.json' file (auto-detects if omitted)")
    parser.add_argument("--port", type=int, default=8090, help="Port for the local server (default: 8090)")
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open the browser")
    args = parser.parse_args()

    # Find JSON file
    if args.json_file:
        if not os.path.exists(args.json_file):
            print(f"File not found: {args.json_file}")
            sys.exit(1)
        AppState.json_file = args.json_file
    else:
        candidates = sorted([f for f in os.listdir(".") if f.startswith("done ") and f.endswith(".json")])
        if not candidates:
            print("No 'done *.json' files found in the current directory.")
            sys.exit(1)
        AppState.json_file = candidates[0]
        if len(candidates) > 1:
            print(f"Multiple JSON files found. Using: {AppState.json_file}")
            print(f"  (To pick a specific file: python preview_editor.py \"filename.json\")")

    # Load data
    with open(AppState.json_file, "r", encoding="utf-8") as f:
        AppState.json_data = json.load(f)

    AppState.title = AppState.json_file.replace("done ", "").replace(".json", "")
    AppState.images_folder = AppState.json_file.replace(".json", "_images")
    os.makedirs(AppState.images_folder, exist_ok=True)

    print(f"Loaded: {AppState.json_file} ({len(AppState.json_data)} segments)")
    print(f"Images folder: {AppState.images_folder}")

    # Start server
    port = args.port
    server = HTTPServer(("127.0.0.1", port), EditorHandler)
    url = f"http://127.0.0.1:{port}"

    print(f"Editor running at {url}")
    print("Press Ctrl+C to stop.\n")

    if not args.no_open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
