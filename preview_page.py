"""
Preview Page Generator (Step 3.5 — Optional)
Generates a simple HTML preview page from processed JSON files.
Shows each dialogue paragraph alongside its downloaded image.
Run this AFTER search_provider.py and BEFORE make_video.py.

Usage:
    python preview_page.py
"""

import os
import json
import base64
import mimetypes
import argparse
import webbrowser

OUTPUT_DIR = "output_videos"


def image_to_data_uri(image_path):
    """Convert a local image file to a base64 data URI for embedding in HTML."""
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        mime, _ = mimetypes.guess_type(image_path)
        if not mime:
            ext = os.path.splitext(image_path)[1].lower()
            if ext in ['.mp4']: mime = "video/mp4"
            elif ext in ['.webm']: mime = "video/webm"
            else: mime = "image/jpeg"
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return None


def generate_html(data, title):
    """Generate a self-contained HTML string from JSON dialogue data."""

    cards_html = ""
    for item in data:
        dialogue_id = item.get("id", "?")
        character = item.get("character", "UNKNOWN")
        paragraph = item.get("paragraph", "")
        image_path = item.get("image", "")

        # Determine speaker styling
        if "01" in str(character):
            speaker_label = "Speaker 2"
            speaker_class = "speaker-b"
        else:
            speaker_label = "Speaker 1"
            speaker_class = "speaker-a"

        # Build image/video element
        data_uri = image_to_data_uri(image_path)
        if data_uri:
            if data_uri.startswith("data:video"):
                img_html = f'<video src="{data_uri}" autoplay loop muted playsinline style="width: 100%; height: 100%; object-fit: cover;"></video>'
            else:
                img_html = f'<img src="{data_uri}" alt="Image for segment {dialogue_id}" loading="lazy">'
        else:
            img_html = '<div class="no-image">No image</div>'

        # Escape HTML in paragraph
        safe_paragraph = (
            paragraph.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

        cards_html += f"""
        <div class="card {speaker_class}">
            <div class="card-text">
                <div class="card-header">
                    <span class="badge">{speaker_label}</span>
                    <span class="id-badge">#{dialogue_id}</span>
                </div>
                <p class="paragraph">{safe_paragraph}</p>
            </div>
            <div class="card-image">
                {img_html}
            </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Preview — {title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0f1117;
            color: #e1e4e8;
            min-height: 100vh;
            padding: 2rem 1rem;
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 2.5rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}

        header h1 {{
            font-size: 1.6rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 0.4rem;
        }}

        header p {{
            font-size: 0.85rem;
            color: #8b949e;
        }}

        .card {{
            display: flex;
            align-items: stretch;
            background: #161b22;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            margin-bottom: 1rem;
            overflow: hidden;
            transition: border-color 0.2s;
        }}

        .card:hover {{
            border-color: rgba(255,255,255,0.15);
        }}

        .card-text {{
            flex: 1;
            padding: 1.2rem 1.5rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-width: 0;
        }}

        .card-header {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.6rem;
        }}

        .badge {{
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
        }}

        .speaker-a .badge {{
            background: rgba(99, 179, 237, 0.15);
            color: #63b3ed;
        }}

        .speaker-b .badge {{
            background: rgba(183, 148, 244, 0.15);
            color: #b794f4;
        }}

        .id-badge {{
            font-size: 0.65rem;
            color: #484f58;
            font-weight: 500;
        }}

        .paragraph {{
            font-size: 0.95rem;
            line-height: 1.6;
            color: #c9d1d9;
            word-wrap: break-word;
        }}

        .card-image {{
            width: 220px;
            min-width: 220px;
            background: #0d1117;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .card-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}

        .no-image {{
            font-size: 0.75rem;
            color: #484f58;
            text-align: center;
            padding: 1rem;
        }}

        /* Alternate card direction for speaker B */
        .speaker-b {{
            flex-direction: row-reverse;
        }}

        .speaker-b .card-text {{
            text-align: right;
        }}

        .speaker-b .card-header {{
            justify-content: flex-end;
        }}

        /* Responsive */
        @media (max-width: 700px) {{
            .card {{
                flex-direction: column !important;
            }}
            .card-image {{
                width: 100%;
                min-width: unset;
                height: 200px;
            }}
            .speaker-b .card-text {{
                text-align: left;
            }}
            .speaker-b .card-header {{
                justify-content: flex-start;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p>{len(data)} dialogue segments</p>
        </header>
        {cards_html}
    </div>
</body>
</html>"""


def process_json_files(no_open=False):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    json_files = sorted([f for f in os.listdir('.') if f.startswith('done ') and f.endswith('.json')])

    if not json_files:
        print("No 'done *.json' files found.")
        return

    for jf in json_files:
        print(f"Generating preview for: {jf}")

        with open(jf, 'r', encoding='utf-8') as f:
            data = json.load(f)

        title = jf.replace('done ', '').replace('.json', '')
        html_content = generate_html(data, title)

        output_path = os.path.join(OUTPUT_DIR, f"{title}_preview.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"  [OK] Saved: {output_path}")

        if not no_open:
            webbrowser.open(os.path.abspath(output_path))
            print(f"  [OK] Opened in browser.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate HTML preview pages from processed dialogue JSON files.")
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't auto-open the preview in your browser"
    )
    args = parser.parse_args()
    process_json_files(no_open=args.no_open)
