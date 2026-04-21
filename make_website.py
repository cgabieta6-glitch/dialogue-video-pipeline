import os
import shutil
import json
import argparse
import webbrowser
import sys
import base64
import time

# Cache buster for assets
CACHE_BUSTER = int(time.time())

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def build_html_content(title, segments, has_pdf=False, pdf_base64=None):
    """Generate the static HTML string using the card layout with embedded JS player."""
    
    cards_html = ""
    for seg in segments:
        dialogue_id = seg["id"]
        character = seg.get("character", "UNKNOWN")
        paragraph = seg.get("paragraph", "")
        media_path = seg.get("media_path", "")
        
        # Determine speaker styling
        if "01" in str(character):
            speaker_label = "Speaker 2"
            speaker_class = "speaker-b"
        else:
            speaker_label = "Speaker 1"
            speaker_class = "speaker-a"

        # Build image/video element
        if media_path:
            ext = media_path.split('.')[-1].lower()
            if ext in ['mp4', 'webm']:
                img_html = f'<video src="{media_path}" autoplay loop muted playsinline style="width: 100%; height: 100%; object-fit: cover;"></video>'
            else:
                img_html = f'<img src="{media_path}" alt="Image for segment {dialogue_id}" loading="lazy">'
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
        <div class="card {speaker_class}" id="card-{dialogue_id}">
            <div class="card-text">
                <div class="card-header">
                    <span class="badge">{speaker_label}</span>
                    <span class="id-badge">#{dialogue_id}</span>
                    <button class="anno-btn" onclick="toggleAnno({dialogue_id})" title="Annotate this segment">💬</button>
                </div>
                <p class="paragraph">{safe_paragraph}</p>
                <div class="anno-area" id="anno-area-{dialogue_id}">
                    <textarea class="anno-input" data-id="{dialogue_id}" placeholder="Add a note for this segment..."></textarea>
                </div>
            </div>
            <div class="card-image">
                {img_html}
            </div>
        </div>"""

    # Create JS payload for playback
    js_segments = []
    for s in segments:
        js_segments.append({
            "id": s["id"],
            "audio_path": s.get("audio_path")
        })
    segments_json = json.dumps(js_segments, indent=4)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Playable Web Video — {title}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf_viewer.min.css">
    <script>
        {f'const pdfData = "{pdf_base64}";' if pdf_base64 else ''}
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Theme Variables */
        :root, [data-theme="midnight"] {{
            --bg: #0f1117;
            --text: #e1e4e8;
            --card-bg: #161b22;
            --card-border: rgba(255,255,255,0.06);
            --card-hover-border: rgba(255,255,255,0.15);
            --header-border: rgba(255,255,255,0.08);
            --subtext: #8b949e;
            --badge-a-bg: rgba(99, 179, 237, 0.15);
            --badge-a-text: #63b3ed;
            --badge-b-bg: rgba(183, 148, 244, 0.15);
            --badge-b-text: #b794f4;
            --id-badge: #484f58;
            --paragraph: #c9d1d9;
            --image-bg: #0d1117;
            --accent: #10b981;
            --accent-hover: #059669;
            --accent-shadow: rgba(16, 185, 129, 0.5);
            --active-shadow: rgba(16, 185, 129, 0.2);
        }}

        [data-theme="ocean"] {{
            --bg: #0a192f;
            --text: #ccd6f6;
            --card-bg: #112240;
            --card-border: rgba(100, 255, 218, 0.08);
            --card-hover-border: rgba(100, 255, 218, 0.2);
            --header-border: rgba(100, 255, 218, 0.1);
            --subtext: #8892b0;
            --badge-a-bg: rgba(100, 255, 218, 0.12);
            --badge-a-text: #64ffda;
            --badge-b-bg: rgba(99, 179, 237, 0.12);
            --badge-b-text: #63b3ed;
            --id-badge: #495670;
            --paragraph: #a8b2d1;
            --image-bg: #0a192f;
            --accent: #64ffda;
            --accent-hover: #45e0be;
            --accent-shadow: rgba(100, 255, 218, 0.4);
            --active-shadow: rgba(100, 255, 218, 0.2);
        }}

        [data-theme="sunset"] {{
            --bg: #1a1020;
            --text: #f0e6d3;
            --card-bg: #261830;
            --card-border: rgba(255, 150, 100, 0.1);
            --card-hover-border: rgba(255, 150, 100, 0.25);
            --header-border: rgba(255, 150, 100, 0.1);
            --subtext: #a08b9b;
            --badge-a-bg: rgba(255, 154, 108, 0.15);
            --badge-a-text: #ff9a6c;
            --badge-b-bg: rgba(255, 107, 161, 0.15);
            --badge-b-text: #ff6ba1;
            --id-badge: #6b5570;
            --paragraph: #dcc8b8;
            --image-bg: #1a1020;
            --accent: #ff6b6b;
            --accent-hover: #e05555;
            --accent-shadow: rgba(255, 107, 107, 0.4);
            --active-shadow: rgba(255, 107, 107, 0.2);
        }}

        [data-theme="forest"] {{
            --bg: #0d1b0f;
            --text: #d4e7d0;
            --card-bg: #162419;
            --card-border: rgba(100, 200, 120, 0.08);
            --card-hover-border: rgba(100, 200, 120, 0.2);
            --header-border: rgba(100, 200, 120, 0.1);
            --subtext: #7fa882;
            --badge-a-bg: rgba(120, 220, 140, 0.12);
            --badge-a-text: #78dc8c;
            --badge-b-bg: rgba(180, 220, 100, 0.12);
            --badge-b-text: #b4dc64;
            --id-badge: #4b6b4f;
            --paragraph: #b8d4b2;
            --image-bg: #0d1b0f;
            --accent: #4ade80;
            --accent-hover: #22c55e;
            --accent-shadow: rgba(74, 222, 128, 0.4);
            --active-shadow: rgba(74, 222, 128, 0.2);
        }}

        [data-theme="lavender"] {{
            --bg: #15121f;
            --text: #ddd6f3;
            --card-bg: #1e1a2e;
            --card-border: rgba(180, 150, 255, 0.08);
            --card-hover-border: rgba(180, 150, 255, 0.2);
            --header-border: rgba(180, 150, 255, 0.1);
            --subtext: #8e82a8;
            --badge-a-bg: rgba(165, 130, 255, 0.15);
            --badge-a-text: #a582ff;
            --badge-b-bg: rgba(255, 130, 200, 0.15);
            --badge-b-text: #ff82c8;
            --id-badge: #5a5070;
            --paragraph: #c5b8e0;
            --image-bg: #15121f;
            --accent: #a78bfa;
            --accent-hover: #8b5cf6;
            --accent-shadow: rgba(167, 139, 250, 0.4);
            --active-shadow: rgba(167, 139, 250, 0.2);
        }}

        [data-theme="light"] {{
            --bg: #f5f5f5;
            --text: #1a1a2e;
            --card-bg: #ffffff;
            --card-border: rgba(0,0,0,0.08);
            --card-hover-border: rgba(0,0,0,0.18);
            --header-border: rgba(0,0,0,0.08);
            --subtext: #6b7280;
            --badge-a-bg: rgba(37, 99, 235, 0.1);
            --badge-a-text: #2563eb;
            --badge-b-bg: rgba(147, 51, 234, 0.1);
            --badge-b-text: #9333ea;
            --id-badge: #9ca3af;
            --paragraph: #374151;
            --image-bg: #e5e7eb;
            --accent: #2563eb;
            --accent-hover: #1d4ed8;
            --accent-shadow: rgba(37, 99, 235, 0.4);
            --active-shadow: rgba(37, 99, 235, 0.2);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        /* PDF.js Rendering Styles */
        .pdf-page-container {{
            position: relative;
            margin-bottom: 20px;
            background: white;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            display: inline-block;
        }}
        .pdf-page-container canvas {{
            display: block;
        }}
        .textLayer {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            overflow: hidden;
            opacity: 1.0;
            line-height: 1.0;
            mix-blend-mode: multiply;
        }}
        .textLayer > span {{
            color: transparent;
            position: absolute;
            white-space: pre;
            cursor: text;
            transform-origin: 0% 0%;
        }}

        /* Match Highlights */
        .pdf-match-highlight {{
            background-color: rgba(255, 255, 0, 0.4);
            border-radius: 2px;
            box-shadow: 0 0 4px rgba(255, 255, 0, 0.6);
            padding: 1px 0;
            margin: -1px 0;
        }}
        .card-match-highlight {{
            border: 2px solid var(--accent) !important;
            background: var(--active-shadow) !important;
            box-shadow: 0 0 20px var(--active-shadow);
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            margin: 0;
            padding: 0;
            transition: background 0.4s ease, color 0.4s ease;
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            overflow: hidden;
        }}

        .split-screen {{
            display: flex;
            height: 100vh;
            width: 100vw;
            overflow: hidden;
        }}

        .left-panel {{
            flex: 1;
            height: 100vh;
            overflow-y: auto;
            padding: 2rem 1rem;
            position: relative;
            scrollbar-width: thin;
            scrollbar-color: var(--accent) transparent;
        }}

        .right-panel {{
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--card-bg);
            border-left: 1px solid var(--card-border);
            height: 100vh;
            overflow: hidden;
            position: relative;
        }}

        .pdf-controls {{
            padding: 0.8rem;
            border-bottom: 1px solid var(--header-border);
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--card-bg);
            z-index: 10;
        }}

        .pdf-upload-label {{
            background: var(--accent);
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 600;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}

        .pdf-upload-label:hover {{
            background: var(--accent-hover);
            transform: translateY(-1px);
        }}

        #pdf-viewer-container {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #1a1a1a;
            position: relative;
        }}

        #pdf-viewer-container iframe, #pdf-viewer-container object {{
            width: 100%;
            height: 100%;
            border: none;
        }}

        .pdf-placeholder {{
            color: var(--subtext);
            font-size: 1rem;
            text-align: center;
            max-width: 300px;
            line-height: 1.5;
        }}

        .container {{
            max-width: 100%;
            margin: 0 auto;
            position: relative;
        }}

        /* Progress Tracker */
        #progress-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: rgba(255,255,255,0.05);
            z-index: 6000;
        }}
        #progress-bar {{
            height: 100%;
            width: 0%;
            background: var(--accent);
            box-shadow: 0 0 10px var(--accent-shadow);
            transition: width 0.3s ease;
        }}

        header {{
            text-align: center;
            margin-bottom: 2.5rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--header-border);
            position: relative;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}

        header h1 {{
            font-size: 1.6rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 0.4rem;
        }}

        header p {{
            font-size: 0.85rem;
            color: var(--subtext);
            margin-bottom: 1rem;
        }}

        .controls-row {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
        }}

        /* Search & Filter */
        .search-wrapper {{
            position: relative;
            max-width: 300px;
            width: 100%;
        }}
        .search-input {{
            width: 100%;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            padding: 8px 12px 8px 35px;
            border-radius: 20px;
            color: var(--text);
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }}
        .search-input:focus {{
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--active-shadow);
        }}
        .search-icon {{
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            opacity: 0.5;
            font-size: 0.9rem;
        }}

        /* Speed & Focus Controls */
        .study-tools {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--card-bg);
            padding: 4px;
            border-radius: 10px;
            border: 1px solid var(--card-border);
        }}
        .tool-toggle {{
            padding: 6px 12px;
            border-radius: 6px;
            border: none;
            background: transparent;
            color: var(--subtext);
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .tool-toggle.active {{
            background: var(--accent);
            color: white;
        }}
        .tool-toggle:hover:not(.active) {{
            background: var(--header-border);
            color: var(--text);
        }}

        /* Focus Mode Styles */
        body.focus-mode .card:not(.active) {{
            opacity: 0.2;
            filter: blur(2px) grayscale(0.5);
            pointer-events: none;
        }}
        body.focus-mode .card.active {{
            transform: scale(1.05);
            box-shadow: 0 0 50px rgba(0,0,0,0.8);
            z-index: 100;
        }}
        body.focus-mode header, body.focus-mode .drawing-toolbox, body.focus-mode #note-toggle {{
            opacity: 0.3;
            transition: opacity 0.3s;
        }}
        body.focus-mode header:hover {{ opacity: 1; }}

        .play-btn {{
            background: var(--accent);
            color: white;
            border: none;
            padding: 0.6rem 1.5rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s, transform 0.1s;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .play-btn:hover {{ background: var(--accent-hover); transform: scale(1.05); }}
        .play-btn:active {{ transform: scale(0.95); }}

        /* Theme Picker */
        .theme-picker {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-left: 10px;
            vertical-align: middle;
        }}

        .theme-dot {{
            width: 22px;
            height: 22px;
            border-radius: 50%;
            border: 2px solid transparent;
            cursor: pointer;
            transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
        }}
        .theme-dot:hover {{ transform: scale(1.25); }}
        .theme-dot.active {{ border-color: var(--text); box-shadow: 0 0 8px var(--accent-shadow); }}

        .bg-controls {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            margin-left: 15px;
            padding-left: 15px;
            border-left: 1px solid var(--header-border);
        }}

        .bg-btn {{
            background: var(--card-bg);
            color: var(--text);
            border: 1px solid var(--card-border);
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .bg-btn:hover {{ background: var(--header-border); border-color: var(--accent); }}

        #bg-color-picker {{
            width: 30px;
            height: 30px;
            padding: 0;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            background: none;
        }}
        #bg-color-picker::-webkit-color-swatch-wrapper {{ padding: 0; }}
        #bg-color-picker::-webkit-color-swatch {{ border-radius: 50%; border: 2px solid var(--card-border); }}

        .play-btn.floating {{
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            right: auto;
            box-shadow: 0 10px 25px var(--accent-shadow);
            z-index: 2000;
            padding: 1rem 2rem;
            font-size: 1.1rem;
            border-radius: 50px;
            animation: popIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        }}

        @keyframes popIn {{
            from {{ transform: translateX(-50%) scale(0); opacity: 0; }}
            to {{ transform: translateX(-50%) scale(1); opacity: 1; }}
        }}

        .card {{
            display: flex;
            align-items: stretch;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            margin-bottom: 1rem;
            transition: border-color 0.3s, transform 0.3s, box-shadow 0.3s, z-index 0s;
            position: relative;
            z-index: 1;
        }}

        /* Active highlight for playing card */
        .card.active {{
            border-color: var(--accent);
            transform: scale(1.02);
            box-shadow: 0 0 20px var(--active-shadow);
            z-index: 50;
        }}

        .card:hover {{
            border-color: var(--card-hover-border);
            z-index: 50;
        }}

        .card-text {{
            flex: 1;
            padding: 1.2rem 1.5rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-width: 0;
            position: relative;
            z-index: 200; /* Ensure text sits above popping images */
        }}

        /* Right Panel: PDF */
        .right-panel {{
            flex: 1; background: #1a1a1a; overflow-y: scroll;
            position: relative; scroll-behavior: smooth;
        }}

        .pdf-viewer-container {{
            display: flex; flex-direction: column; align-items: center; 
            padding: 40px 20px; min-height: 100%;
        }}

        .pdf-page-container {{
            position: relative;
            display: inline-block; /* Hugs the canvas to keep text aligned */
            margin: 0 auto 30px auto; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            background: white;
            line-height: 0;
        }}

        /* PDF.js Text Layer - CRITICAL for alignment */
        .textLayer {{
            position: absolute; left: 0; top: 0; right: 0; bottom: 0;
            overflow: hidden; line-height: 1.0;
            mix-blend-mode: multiply;
        }}
        .textLayer span {{
            color: transparent; position: absolute; white-space: pre;
            cursor: text; transform-origin: 0% 0%;
        }}

        .pdf-match-highlight {{ 
            background-color: rgba(255, 255, 0, 0.4); 
            border-bottom: 2px solid orange;
            border-radius: 2px;
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

        .speaker-a .badge {{ background: var(--badge-a-bg); color: var(--badge-a-text); }}
        .speaker-b .badge {{ background: var(--badge-b-bg); color: var(--badge-b-text); }}

        .id-badge {{
            font-size: 0.65rem;
            color: var(--id-badge);
            font-weight: 500;
            flex: 1;
        }}

        .anno-btn {{
            background: none;
            border: none;
            font-size: 0.9rem;
            cursor: pointer;
            opacity: 0.4;
            transition: opacity 0.2s, transform 0.2s;
            padding: 2px 6px;
        }}
        .anno-btn:hover {{ opacity: 1; transform: scale(1.2); }}

        .anno-area {{
            display: none;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px dashed var(--card-border);
        }}
        .anno-area.visible {{ display: block; }}

        .anno-input {{
            width: 100%;
            background: rgba(250, 204, 21, 0.05);
            border: 1px solid rgba(250, 204, 21, 0.1);
            border-radius: 6px;
            padding: 8px;
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-size: 0.8rem;
            min-height: 40px;
            resize: vertical;
            outline: none;
            transition: border-color 0.2s;
        }}
        .anno-input:focus {{ border-color: rgba(250, 204, 21, 0.4); }}

        .paragraph {{
            font-size: 0.95rem;
            line-height: 1.6;
            color: var(--paragraph);
            word-wrap: break-word;
        }}

        /* Highlight styles */
        .highlight {{
            background-color: rgba(250, 204, 21, 0.4);
            color: #fff;
            padding: 0.1rem 0.2rem;
            border-radius: 3px;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        .highlight:hover {{
            background-color: rgba(239, 68, 68, 0.4); /* red-ish tint on hover to indicate erase */
        }}

        #highlighter-btn {{
            display: none;
            position: absolute;
            background: #10b981;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            z-index: 1000;
        }}
        #highlighter-btn:hover {{ background: var(--accent-hover); }}

        .card-image {{
            width: 220px;
            min-width: 220px;
            background: var(--image-bg);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
            position: relative;
            z-index: 1;
            border-radius: 0 12px 12px 0;
        }}

        .card-image:hover, .card.active .card-image {{
            transform: scale(1.6);
            box-shadow: 0 20px 40px rgba(0,0,0,0.9);
            z-index: 100;
            border-radius: 8px;
        }}

        .card-image img, .card-image video {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
            border-radius: inherit;
        }}

        .no-image {{
            font-size: 0.75rem;
            color: var(--id-badge);
            text-align: center;
            padding: 1rem;
        }}

        .speaker-b {{ flex-direction: row-reverse; }}
        .speaker-b .card-text {{ text-align: right; }}
        .speaker-b .card-header {{ justify-content: flex-end; }}
        .speaker-b .card-image {{ border-radius: 12px 0 0 12px; }}

        @media (max-width: 1000px) {{
            .split-screen {{
                flex-direction: column;
                height: auto;
                overflow: visible;
            }}
            .left-panel, .right-panel {{
                height: auto;
                flex: none;
                width: 100%;
                overflow: visible;
            }}
            .right-panel {{
                height: 80vh;
                border-left: none;
                border-top: 1px solid var(--card-border);
            }}
            body {{
                overflow: auto;
            }}
        }}

        @media (max-width: 700px) {{
            .card {{ flex-direction: column !important; }}
            .card-image {{ width: 100%; min-width: unset; height: 200px; border-radius: 0 0 12px 12px !important; }}
            .speaker-b .card-image {{ border-radius: 0 0 12px 12px !important; }}
            .speaker-b .card-text {{ text-align: left; }}
            .speaker-b .card-header {{ justify-content: flex-start; }}
        }}

        /* Sticky Note */
        #note-toggle {{
            position: fixed;
            bottom: 30px;
            left: 30px;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: #facc15;
            color: #1a1a2e;
            border: none;
            font-size: 1.3rem;
            cursor: pointer;
            z-index: 3000;
            box-shadow: 0 4px 15px rgba(250, 204, 21, 0.4);
            transition: transform 0.2s, background 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        #note-toggle:hover {{ transform: scale(1.15); }}

        #sticky-note {{
            display: none;
            position: fixed;
            bottom: 85px;
            left: 30px;
            width: 300px;
            background: #facc15;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            z-index: 3000;
            overflow: hidden;
            animation: popIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        }}
        #sticky-note.visible {{ display: block; }}

        #sticky-note .note-header {{
            background: #eab308;
            padding: 8px 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: grab;
            user-select: none;
        }}
        #sticky-note .note-header:active {{ cursor: grabbing; }}

        #sticky-note .note-header span {{
            font-weight: 700;
            font-size: 0.85rem;
            color: #1a1a2e;
        }}

        #sticky-note .note-header button {{
            background: none;
            border: none;
            font-size: 1rem;
            cursor: pointer;
            color: #1a1a2e;
            opacity: 0.6;
        }}
        #sticky-note .note-header button:hover {{ opacity: 1; }}

        #sticky-note textarea {{
            width: 100%;
            height: 200px;
            border: none;
            padding: 12px;
            font-family: 'Inter', sans-serif;
            font-size: 0.85rem;
            resize: vertical;
            background: #fef9c3;
            color: #1a1a2e;
            outline: none;
        }}
        #sticky-note textarea::placeholder {{
            color: #92700c;
        }}

        #sticky-note.wobbling {{
            animation: wobble 0.15s infinite alternate ease-in-out;
        }}

        @keyframes wobble {{
            from {{ transform: rotate(-1.5deg); }}
            to {{ transform: rotate(1.5deg); }}
        }}

        /* Drawing Mode */
        #drawing-canvas {{
            position: absolute;
            top: 0;
            left: 0;
            pointer-events: none;
            z-index: 4000;
        }}
        #drawing-canvas.active {{
            pointer-events: all;
            cursor: crosshair;
        }}

        .drawing-toolbox {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #1a1a2e;
            padding: 10px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            display: flex;
            flex-direction: column;
            gap: 10px;
            z-index: 5001;
            border: 1px solid rgba(255,255,255,0.1);
            transform: translateX(120%);
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }}
        .drawing-toolbox.visible {{ transform: translateX(0); }}

        .tool-btn {{
            width: 36px;
            height: 36px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            transition: transform 0.2s;
        }}
        .tool-btn:hover {{ transform: scale(1.1); }}
        .tool-btn.active {{ outline: 2px solid white; outline-offset: 2px; }}

        #draw-toggle-btn {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #facc15;
            color: #1a1a2e;
            z-index: 5002;
            box-shadow: 0 4px 15px rgba(250, 204, 21, 0.4);
        }}
    </style>
</head>
<body>
    <div id="progress-container"><div id="progress-bar"></div></div>
    
    <div class="split-screen">
        <div class="left-panel">
            <div class="container">
                <header>
                    <div class="title-section">
                        <h1>{title}</h1>
                        <p>{len(segments)} dialogue segments</p>
                    </div>

                    <div class="controls-row">
                        <div class="search-wrapper">
                            <span class="search-icon">🔍</span>
                            <input type="text" class="search-input" id="search-input" placeholder="Search script...">
                        </div>

                        <div class="study-tools">
                            <button class="tool-toggle" id="focus-toggle" title="Cinematic Focus Mode">🎯 Focus</button>
                            <select class="tool-toggle" id="speed-select" title="Playback Speed" style="padding: 5px 8px;">
                                <option value="0.75">0.75x</option>
                                <option value="1" selected>1.0x</option>
                                <option value="1.25">1.25x</option>
                                <option value="1.5">1.5x</option>
                                <option value="2">2.0x</option>
                            </select>
                        </div>

                        <button class="play-btn" id="play-btn">▶ Play All</button>

                        <div class="theme-picker" id="theme-picker">
                            <span class="theme-dot active" data-theme="midnight" style="background:#0f1117;border:2px solid #444;" title="Midnight"></span>
                            <span class="theme-dot" data-theme="ocean" style="background:#0a192f;" title="Ocean"></span>
                            <span class="theme-dot" data-theme="sunset" style="background:linear-gradient(135deg,#ff9a6c,#ff6ba1);" title="Sunset"></span>
                            <span class="theme-dot" data-theme="forest" style="background:#0d1b0f;" title="Forest"></span>
                            <span class="theme-dot" data-theme="lavender" style="background:linear-gradient(135deg,#a582ff,#ff82c8);" title="Lavender"></span>
                            <span class="theme-dot" data-theme="light" style="background:#f5f5f5;" title="Light"></span>
                        </div>

                        <div class="bg-controls">
                            <button class="bg-btn" id="bg-img-btn" title="Upload Background Image">🖼️ Image</button>
                            <input type="color" id="bg-color-picker" title="Pick Background Color" value="#0f1117">
                            <input type="file" id="bg-upload" accept="image/*" style="display:none">
                        </div>
                    </div>
                </header>

                <!-- Hidden audio element -->
                <audio id="audio-player" src=""></audio>
                
                <!-- Floating Highlighter Button -->
                <button id="highlighter-btn">Highlight</button>

                <!-- Sticky Note Toggle -->
                <button id="note-toggle" title="Toggle Sticky Note">📝</button>
                <div id="sticky-note">
                    <div class="note-header">
                        <span>📌 Notes</span>
                        <button id="note-close">✕</button>
                    </div>
                    <textarea placeholder="Jot down your notes here..."></textarea>
                </div>

                <!-- Drawing Mode -->
                <canvas id="drawing-canvas"></canvas>
                <button id="draw-toggle-btn" class="tool-btn" title="Toggle Drawing Mode">🖌️</button>
                <div class="drawing-toolbox" id="draw-toolbox">
                    <button class="tool-btn active" style="background:#ff4444" data-color="#ff4444"></button>
                    <button class="tool-btn" style="background:#44ff44" data-color="#44ff44"></button>
                    <button class="tool-btn" style="background:#facc15" data-color="#facc15"></button>
                    <button class="tool-btn" style="background:#ffffff" data-color="#ffffff"></button>
                    <hr style="border:0; border-top:1px solid rgba(255,255,255,0.1)">
                    <button class="tool-btn" id="draw-clear" title="Clear Drawing" style="background:#333; color:white">🗑️</button>
                </div>

                {cards_html}
            </div>
        </div>

        <div class="right-panel">
            <div class="pdf-controls">
                <div class="pdf-header">
                    <span>📄 Script Viewer (Interactive)</span>
                </div>
            </div>
            <div id="pdf-viewer-container">
                <div id="pdf-fallback" class="pdf-placeholder" style="display: {'none' if has_pdf else 'flex'}; flex-direction: column; justify-content: center; align-items: center; height: 100%; padding: 2rem;">
                    <p>To view your script, place a PDF named <strong>script.pdf</strong> into the <strong>assets</strong> folder.</p>
                </div>
                <!-- PDF pages will be rendered here -->
            </div>
        </div>
    </div>

<script>
    const segments = {segments_json};
    
    let currentIndex = 0;
    let isPlaying = false;

    function toggleAnno(id) {{
        const area = document.getElementById('anno-area-' + id);
        area.classList.toggle('visible');
    }}

    const storageKey = 'dialogue_video_pipeline_' + '{title}'.replace(/\\s+/g, '_');

    // Load persisted data
    window.addEventListener('DOMContentLoaded', () => {{
        const savedNotes = localStorage.getItem(storageKey + '_notes');
        if (savedNotes) document.querySelector('#sticky-note textarea').value = savedNotes;

        const savedTheme = localStorage.getItem(storageKey + '_theme');
        if (savedTheme) {{
            document.documentElement.setAttribute('data-theme', savedTheme);
            document.querySelectorAll('.theme-dot').forEach(d => {{
                d.classList.toggle('active', d.getAttribute('data-theme') === savedTheme);
            }});
        }}

        const savedBgColor = localStorage.getItem(storageKey + '_bg_color');
        if (savedBgColor) {{
            document.body.style.backgroundColor = savedBgColor;
            document.documentElement.style.setProperty('--bg', savedBgColor);
            document.getElementById('bg-color-picker').value = savedBgColor;
        }}

        const savedBgImg = localStorage.getItem(storageKey + '_bg_img');
        if (savedBgImg) {{
            document.body.style.backgroundImage = `url('${{savedBgImg}}')`;
        }}

        // Load Study Tool Preferences
        const savedSpeed = localStorage.getItem(storageKey + '_speed');
        if (savedSpeed) {{
            document.getElementById('speed-select').value = savedSpeed;
            audio.playbackRate = parseFloat(savedSpeed);
        }}

        const savedFocus = localStorage.getItem(storageKey + '_focus') === 'true';
        if (savedFocus) {{
            document.body.classList.add('focus-mode');
            document.getElementById('focus-toggle').classList.add('active');
        }}

        // Load card annotations
        document.querySelectorAll('.anno-input').forEach(input => {{
            const id = input.getAttribute('data-id');
            const saved = localStorage.getItem(storageKey + '_anno_' + id);
            if (saved) {{
                input.value = saved;
                document.getElementById('anno-area-' + id).classList.add('visible');
            }}
            input.addEventListener('input', (e) => {{
                localStorage.setItem(storageKey + '_anno_' + id, e.target.value);
            }});
        }});

        // PDF.js Integration Logic
        const pdfjsLib = window['pdfjs-dist/build/pdf'];
        const pdfViewerContainer = document.getElementById('pdf-viewer-container');
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

        let pdfDoc = null;
        let pageRendering = new Set();
        let renderedPages = new Set();

        async function initPDFViewer(base64Data) {{
            console.log("Initializing Optimized PDF Viewer...");
            try {{
                const binaryString = atob(base64Data);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {{
                    bytes[i] = binaryString.charCodeAt(i);
                }}
                
                pdfDoc = await pdfjsLib.getDocument({{ 
                    data: bytes,
                    disableWorker: true,
                    verbosity: 0
                }}).promise;
                
                const observer = new IntersectionObserver((entries) => {{
                    entries.forEach(entry => {{
                        if (entry.isIntersecting) {{
                            const num = parseInt(entry.target.dataset.pageNumber);
                            renderPage(num);
                        }}
                    }});
                }}, {{ 
                    root: pdfViewerContainer, 
                    rootMargin: '500px 0px', // Proactive loading
                    threshold: 0.01 
                }});

                for (let i = 1; i <= pdfDoc.numPages; i++) {{
                    const pageContainer = document.createElement('div');
                    pageContainer.className = 'pdf-page-container';
                    pageContainer.id = 'pdf-page-' + i;
                    pageContainer.dataset.pageNumber = i;
                    
                    // Loading skeleton
                    pageContainer.innerHTML = '<div style="display:flex; height:100%; align-items:center; justify-content:center; color:#555; font-size:0.8rem;">Loading Page...</div>';
                    
                    pdfViewerContainer.appendChild(pageContainer);
                    observer.observe(pageContainer);
                }}
            }} catch (e) {{
                console.error("PDF.js Error:", e);
                pdfFallback.innerHTML = `<h2>PDF Load Error</h2><p>${{e.message}}</p>`;
                pdfFallback.style.display = 'flex';
            }}
        }}

        // PDF Initialization
        const pdfFallback = document.getElementById('pdf-fallback');
        
        if (typeof pdfData !== 'undefined' && pdfData) {{
            pdfFallback.style.display = 'none';
            initPDFViewer(pdfData);
        }} else {{
            console.warn("No PDF Data found in HTML.");
            pdfFallback.style.display = 'flex';
        }}

        async function renderPage(pageNum) {{
            if (renderedPages.has(pageNum) || pageRendering.has(pageNum)) return;
            pageRendering.add(pageNum);

            try {{
                const page = await pdfDoc.getPage(pageNum);
                const baseScale = 1.5;
                const viewport = page.getViewport({{ scale: baseScale }});
                const container = document.getElementById('pdf-page-' + pageNum);
                
                // Clear loading skeleton
                container.innerHTML = '';

                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');

                // CRITICAL: High-DPI Display Scaling
                const outputScale = window.devicePixelRatio || 1;
                canvas.width = Math.floor(viewport.width * outputScale);
                canvas.height = Math.floor(viewport.height * outputScale);
                canvas.style.width = Math.floor(viewport.width) + "px";
                canvas.style.height = Math.floor(viewport.height) + "px";
                container.style.width = Math.floor(viewport.width) + "px";
                container.style.height = Math.floor(viewport.height) + "px";
                
                container.appendChild(canvas);

                const transform = outputScale !== 1 
                    ? [outputScale, 0, 0, outputScale, 0, 0] 
                    : null;

                const renderContext = {{
                    canvasContext: context,
                    transform: transform,
                    viewport: viewport
                }};
                
                await page.render(renderContext).promise;

                // Text Layer with Scale Factor and Explicit Dimensions
                const textLayerDiv = document.createElement('div');
                textLayerDiv.className = 'textLayer';
                textLayerDiv.style.width = viewport.width + 'px';
                textLayerDiv.style.height = viewport.height + 'px';
                textLayerDiv.style.setProperty('--scale-factor', viewport.scale);
                container.appendChild(textLayerDiv);

                const textContent = await page.getTextContent();
                await pdfjsLib.renderTextLayer({{
                    textContentSource: textContent,
                    container: textLayerDiv,
                    viewport: viewport,
                    textDivs: []
                }}).promise;

                renderedPages.add(pageNum);
            }} catch (e) {{
                console.error("Error rendering page " + pageNum, e);
            }} finally {{
                pageRendering.delete(pageNum);
            }}
        }}

        // Normalization Utility for Fuzzy Matching
        function normalizeText(text) {{
            return text.toLowerCase().replace(/[^\\w\\s]/g, '').replace(/\\s+/g, ' ').trim();
        }}

        // Bidirectional Highlighting Logic
        document.addEventListener('selectionchange', () => {{
            const selection = window.getSelection();
            const selectedText = selection.toString().trim();
            if (selectedText.length < 3) return;

            const range = selection.getRangeAt(0);
            const container = range.commonAncestorContainer.parentElement;

            // Clear previous highlights
            document.querySelectorAll('.pdf-match-highlight').forEach(el => {{
                const parent = el.parentNode;
                while (el.firstChild) parent.insertBefore(el.firstChild, el);
                parent.removeChild(el);
            }});
            document.querySelectorAll('.card-match-highlight').forEach(el => el.classList.remove('card-match-highlight'));

            const normalizedSelected = normalizeText(selectedText);

            // Left to Right (Card -> PDF)
            if (container.closest('.left-panel')) {{
                syncToPDF(normalizedSelected);
            }} 
            // Right to Left (PDF -> Card)
            else if (container.closest('.right-panel')) {{
                syncToCard(normalizedSelected);
            }}
        }});

        function syncToPDF(normalizedText) {{
            const spans = document.querySelectorAll('.textLayer span');
            let found = false;
            for (let span of spans) {{
                if (normalizeText(span.textContent).includes(normalizedText)) {{
                    const regex = new RegExp(`(${{normalizedText.split('').join('[\\\\s\\\\W]*')}})`, 'gi');
                    span.innerHTML = span.textContent.replace(regex, '<span class="pdf-match-highlight">$1</span>');
                    
                    if (!found) {{
                        span.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        found = true;
                    }}
                }}
            }}
            
            if (!found) {{
                console.log("No match found in currently rendered pages. Searching document...");
                searchAllPages(normalizedText);
            }}
        }}

        async function searchAllPages(normalizedText) {{
            if (!pdfDoc) return;
            for (let i = 1; i <= pdfDoc.numPages; i++) {{
                const page = await pdfDoc.getPage(i);
                const textContent = await page.getTextContent();
                const pageText = normalizeText(textContent.items.map(item => item.str).join(' '));
                
                if (pageText.includes(normalizedText)) {{
                    const container = document.getElementById('pdf-page-' + i);
                    container.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    // Rendering will be triggered by IntersectionObserver
                    break;
                }}
            }}
        }}

        function syncToCard(normalizedText) {{
            const cards = document.querySelectorAll('.card');
            for (let card of cards) {{
                const paragraph = card.querySelector('.paragraph');
                if (normalizeText(paragraph.textContent).includes(normalizedText)) {{
                    card.classList.add('card-match-highlight');
                    card.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    break;
                }}
            }}
        }}
    }});
    
    const audio = document.getElementById('audio-player');
    const playBtn = document.getElementById('play-btn');

    function highlightCard(id) {{
        // Remove active class from all
        document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
        // Add to current
        const card = document.getElementById('card-' + id);
        if (card) {{
            card.classList.add('active');
            card.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
    }}

    function playSegment(index) {{
        if (index >= segments.length) {{
            // Finished
            isPlaying = false;
            playBtn.innerHTML = '▶ Play All';
            document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
            currentIndex = 0;
            return;
        }}

        const seg = segments[index];
        highlightCard(seg.id);

        // Update Progress Bar
        const progress = ((index + 1) / segments.length) * 100;
        document.getElementById('progress-bar').style.width = progress + '%';

        if (seg.audio_path) {{
            audio.src = encodeURI(seg.audio_path);
            audio.load();
            if (isPlaying) {{
                audio.play().catch(e => alert("Audio error: " + e.message));
            }}
        }} else {{
            // No audio? Auto-advance after 2 seconds
            if (isPlaying) {{
                setTimeout(() => loadNext(), 2000);
            }}
        }}
    }}

    function loadNext() {{
        currentIndex++;
        playSegment(currentIndex);
    }}

    audio.onended = () => {{
        if (isPlaying) loadNext();
    }};

    playBtn.addEventListener('click', () => {{
        if (isPlaying) {{
            audio.pause();
            isPlaying = false;
            playBtn.innerHTML = '▶ Resume';
            document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
        }} else {{
            isPlaying = true;
            playBtn.innerHTML = '⏸ Pause';
            
            if (!audio.getAttribute('src')) {{
                playSegment(currentIndex);
            }} else {{
                audio.play().catch(e => alert("Playback failed: " + e.message));
                highlightCard(segments[currentIndex].id);
            }}
        }}
    }});

    // Floating Button Logic (Listen to left-panel scroll)
    document.querySelector('.left-panel').addEventListener('scroll', (e) => {{
        if (e.target.scrollTop > 200) {{
            playBtn.classList.add('floating');
        }} else {{
            playBtn.classList.remove('floating');
        }}
    }});

    // Theme Switcher
    document.querySelectorAll('.theme-dot').forEach(dot => {{
        dot.addEventListener('click', () => {{
            const theme = dot.getAttribute('data-theme');
            document.documentElement.setAttribute('data-theme', theme);
            document.querySelectorAll('.theme-dot').forEach(d => d.classList.remove('active'));
            dot.classList.add('active');
            localStorage.setItem(storageKey + '_theme', theme);
        }});
    }});

    // Background Customization
    const bgImgBtn = document.getElementById('bg-img-btn');
    const bgUpload = document.getElementById('bg-upload');
    const bgColorPicker = document.getElementById('bg-color-picker');

    bgImgBtn.addEventListener('click', () => bgUpload.click());

    bgUpload.addEventListener('change', (e) => {{
        if (e.target.files && e.target.files[0]) {{
            const reader = new FileReader();
            reader.onload = (event) => {{
                const imgData = event.target.result;
                document.body.style.backgroundImage = `url('${{imgData}}')`;
                try {{
                    localStorage.setItem(storageKey + '_bg_img', imgData);
                }} catch (e) {{
                    console.warn("Background image too large to save locally.");
                }}
            }};
            reader.readAsDataURL(e.target.files[0]);
        }}
    }});

    bgColorPicker.addEventListener('input', (e) => {{
        const color = e.target.value;
        document.body.style.backgroundImage = 'none';
        document.body.style.backgroundColor = color;
        document.documentElement.style.setProperty('--bg', color);
        localStorage.setItem(storageKey + '_bg_color', color);
        localStorage.removeItem(storageKey + '_bg_img');
    }});

    // Study Tools Logic
    const focusToggle = document.getElementById('focus-toggle');
    const speedSelect = document.getElementById('speed-select');
    const searchInput = document.getElementById('search-input');

    focusToggle.addEventListener('click', () => {{
        const isFocus = document.body.classList.toggle('focus-mode');
        focusToggle.classList.toggle('active', isFocus);
        localStorage.setItem(storageKey + '_focus', isFocus);
    }});

    speedSelect.addEventListener('change', (e) => {{
        const speed = e.target.value;
        audio.playbackRate = parseFloat(speed);
        localStorage.setItem(storageKey + '_speed', speed);
    }});

    // Search Logic
    searchInput.addEventListener('input', (e) => {{
        const term = e.target.value.toLowerCase();
        document.querySelectorAll('.card').forEach(card => {{
            const text = card.querySelector('.paragraph').textContent.toLowerCase();
            const character = card.querySelector('.badge').textContent.toLowerCase();
            if (text.includes(term) || character.includes(term)) {{
                card.style.display = 'flex';
            }} else {{
                card.style.display = 'none';
            }}
        }});
    }});

    // Highlighter Feature
    const highlightBtn = document.getElementById('highlighter-btn');
    
    document.addEventListener('selectionchange', () => {{
        const selection = window.getSelection();
        if (selection.toString().trim() !== '' && selection.rangeCount > 0) {{
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            
            let node = selection.anchorNode;
            let isParagraph = false;
            while(node && node !== document.body) {{
                if(node.classList && node.classList.contains('paragraph')) {{
                    isParagraph = true; break;
                }}
                node = node.parentNode;
            }}
            
            if (isParagraph) {{
                highlightBtn.style.display = 'block';
                const leftPanel = document.querySelector('.left-panel');
                highlightBtn.style.top = (leftPanel.scrollTop + rect.top - 30) + 'px';
                highlightBtn.style.left = (leftPanel.scrollLeft + rect.left + (rect.width/2) - 35) + 'px';
            }} else {{
                highlightBtn.style.display = 'none';
            }}
        }} else {{
            setTimeout(() => {{
                if (window.getSelection().toString().trim() === '') {{
                    highlightBtn.style.display = 'none';
                }}
            }}, 100);
        }}
    }});

    highlightBtn.addEventListener('click', () => {{
        const selection = window.getSelection();
        if (!selection.rangeCount) return;
        const range = selection.getRangeAt(0);
        
        const span = document.createElement('span');
        span.className = 'highlight';
        span.title = 'Click to erase highlight';
        range.surroundContents(span);
        
        selection.removeAllRanges();
        highlightBtn.style.display = 'none';
    }});

    // Eraser Feature: Click on a highlight to remove it
    document.addEventListener('click', (e) => {{
        if (e.target.classList && e.target.classList.contains('highlight')) {{
            const parent = e.target.parentNode;
            while (e.target.firstChild) {{
                parent.insertBefore(e.target.firstChild, e.target);
            }}
            parent.removeChild(e.target);
            parent.normalize();
        }}
    }});

    // Manual Media Changer
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*,video/*';
    fileInput.style.display = 'none';
    document.body.appendChild(fileInput);

    let currentTargetCard = null;

    document.querySelectorAll('.card-image').forEach(el => {{
        el.style.cursor = 'pointer';
        el.title = 'Click to manually swap image/video';
        
        el.addEventListener('click', (e) => {{
            const card = e.target.closest('.card');
            if (card) {{
                currentTargetCard = card;
                fileInput.click();
            }}
        }});
    }});

    fileInput.addEventListener('change', (e) => {{
        if (!e.target.files.length || !currentTargetCard) return;
        const file = e.target.files[0];
        const fileUrl = URL.createObjectURL(file);
        
        const imgContainer = currentTargetCard.querySelector('.card-image');
        imgContainer.innerHTML = '';
        
        if (file.type.startsWith('video/')) {{
            const video = document.createElement('video');
            video.src = fileUrl;
            video.autoplay = true;
            video.loop = true;
            video.muted = true;
            video.playsInline = true;
            imgContainer.appendChild(video);
        }} else {{
            const img = document.createElement('img');
            img.src = fileUrl;
            imgContainer.appendChild(img);
        }}
        
        fileInput.value = '';
    }});

    // Click-to-Play Feature
    document.querySelectorAll('.card-text').forEach(el => {{
        el.style.cursor = 'pointer';
        el.title = 'Click to skip to this dialogue';
        
        el.addEventListener('click', (e) => {{
            // Don't trigger if they clicked a highlight to erase it
            if (e.target.classList && e.target.classList.contains('highlight')) return;

            // Don't trigger if the user has highlighted text
            const selection = window.getSelection();
            if (selection && selection.toString().trim() !== '') return;

            const card = e.target.closest('.card');
            if (!card) return;
            
            const cardIdStr = card.id.replace('card-', '');
            const targetId = parseInt(cardIdStr);
            
            const targetIndex = segments.findIndex(s => s.id === targetId);
            if (targetIndex !== -1) {{
                currentIndex = targetIndex;
                isPlaying = true;
                playBtn.innerHTML = '⏸ Pause';
                
                // Always show the floating button if they started playing from somewhere deep
                if (document.querySelector('.left-panel').scrollTop > 200) {{
                    playBtn.classList.add('floating');
                }}
                
                playSegment(currentIndex);
            }}
        }});
    }});

    // Sticky Note
    const noteToggle = document.getElementById('note-toggle');
    const stickyNote = document.getElementById('sticky-note');
    const noteClose = document.getElementById('note-close');

    noteToggle.addEventListener('click', () => {{
        stickyNote.classList.toggle('visible');
    }});

    noteClose.addEventListener('click', () => {{
        stickyNote.classList.remove('visible');
    }});

    const noteTextarea = stickyNote.querySelector('textarea');
    noteTextarea.addEventListener('input', (e) => {{
        localStorage.setItem(storageKey + '_notes', e.target.value);
    }});

    // Drag the sticky note
    let isDragging = false, dragOffsetX = 0, dragOffsetY = 0;
    const noteHeader = stickyNote.querySelector('.note-header');

    noteHeader.addEventListener('mousedown', (e) => {{
        isDragging = true;
        stickyNote.classList.add('wobbling');
        const rect = stickyNote.getBoundingClientRect();
        dragOffsetX = e.clientX - rect.left;
        dragOffsetY = e.clientY - rect.top;
        // Switch from bottom/left positioning to top/left for free dragging
        stickyNote.style.top = rect.top + 'px';
        stickyNote.style.left = rect.left + 'px';
        stickyNote.style.bottom = 'auto';
    }});

    document.addEventListener('mousemove', (e) => {{
        if (!isDragging) return;
        stickyNote.style.top = (e.clientY - dragOffsetY) + 'px';
        stickyNote.style.left = (e.clientX - dragOffsetX) + 'px';
    }});

    document.addEventListener('mouseup', () => {{
        isDragging = false;
        stickyNote.classList.remove('wobbling');
    }});

    // Drawing Logic
    const canvas = document.getElementById('drawing-canvas');
    const ctx = canvas.getContext('2d');
    const drawToggle = document.getElementById('draw-toggle-btn');
    const drawToolbox = document.getElementById('draw-toolbox');
    const drawClear = document.getElementById('draw-clear');

    let isDrawingMode = false;
    let isPainting = false;
    let currentColor = '#ff4444';
    let saveTimeout;

    function resizeCanvas() {{
        const temp = canvas.toDataURL();
        canvas.width = Math.max(document.documentElement.scrollWidth, window.innerWidth);
        canvas.height = Math.max(document.documentElement.scrollHeight, window.innerHeight);
        const img = new Image();
        img.onload = () => ctx.drawImage(img, 0, 0);
        img.src = temp;
    }}

    function saveDrawing() {{
        try {{
            localStorage.setItem(storageKey + '_drawing', canvas.toDataURL('image/webp', 0.3));
        }} catch(e) {{
            console.warn("Drawing too large to save.");
        }}
    }}


    // Initial load of drawing
    window.addEventListener('load', () => {{
        canvas.width = Math.max(document.documentElement.scrollWidth, window.innerWidth);
        canvas.height = Math.max(document.documentElement.scrollHeight, window.innerHeight);
        const saved = localStorage.getItem(storageKey + '_drawing');
        if (saved) {{
            const img = new Image();
            img.onload = () => ctx.drawImage(img, 0, 0);
            img.src = saved;
        }}
    }});

    window.addEventListener('resize', resizeCanvas);

    drawToggle.addEventListener('click', () => {{
        isDrawingMode = !isDrawingMode;
        canvas.classList.toggle('active', isDrawingMode);
        drawToolbox.classList.toggle('visible', isDrawingMode);
        drawToggle.style.right = isDrawingMode ? '80px' : '20px';
        drawToggle.innerHTML = isDrawingMode ? '✕' : '🖌️';
    }});

    document.querySelectorAll('.drawing-toolbox [data-color]').forEach(btn => {{
        btn.addEventListener('click', () => {{
            document.querySelectorAll('.drawing-toolbox [data-color]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentColor = btn.getAttribute('data-color');
        }});
    }});

    drawClear.addEventListener('click', () => {{
        if (confirm('Clear all drawings?')) {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            localStorage.removeItem(storageKey + '_drawing');
        }}
    }});

    canvas.addEventListener('mousedown', (e) => {{
        if (!isDrawingMode) return;
        isPainting = true;
        ctx.beginPath();
        ctx.moveTo(e.pageX, e.pageY);
        ctx.strokeStyle = currentColor;
        ctx.lineWidth = 4;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
    }});

    canvas.addEventListener('mousemove', (e) => {{
        if (!isPainting) return;
        
        // Use requestAnimationFrame for smooth drawing
        requestAnimationFrame(() => {{
            if (!isPainting) return;
            ctx.lineTo(e.pageX, e.pageY);
            ctx.stroke();
        }});
    }});

    canvas.addEventListener('mouseup', () => {{
        if (!isPainting) return;
        isPainting = false;
        
        // Debounce saving to prevent lag
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(saveDrawing, 1000);
    }});
</script>
</body>
</html>
"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Web Video Maker - Exports playable HTML websites")
    parser.add_argument("--no-open", action="store_true", help="Don't open the output in a browser")
    args = parser.parse_args()

    OUTPUT_DIR = "output_websites"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    json_files = sorted([f for f in os.listdir('.') if f.startswith('done ') and f.endswith('.json')])

    if not json_files:
        print("❌ No JSON files found starting with 'done '")
        return

    print(f"📋 Found {len(json_files)} JSON files to export as websites\n")

    for jf in json_files:
        raw_name = jf.replace('done ', '').replace('.json', '')
        if raw_name.endswith('.m4a'):
            raw_name = raw_name[:-4]

        print(f"🎬 Creating Website for: {raw_name}")

        audio_folder = raw_name.replace('_', ' ')
        if not os.path.isdir(audio_folder) and os.path.isdir(raw_name):
            audio_folder = raw_name

        images_folder = jf.replace('.json', '_images')

        project_dir = os.path.join(OUTPUT_DIR, raw_name)
        assets_dir = os.path.join(project_dir, "assets")
        
        # SAFETY UPDATE: Do not delete the project directory. 
        # This preserves manually placed files like PDFs in the assets folder.
        os.makedirs(assets_dir, exist_ok=True)

        has_pdf = False
        
        # 1. Check for ANY existing PDF in the assets folder and AUTO-RENAME to script.pdf
        existing_assets = os.listdir(assets_dir)
        pdfs_in_assets = [f for f in existing_assets if f.lower().endswith('.pdf')]
        
        if pdfs_in_assets:
            if "script.pdf" not in pdfs_in_assets:
                # Rename the first PDF found to script.pdf so the website can load it
                shutil.move(os.path.join(assets_dir, pdfs_in_assets[0]), os.path.join(assets_dir, "script.pdf"))
                print(f"  [INFO] Auto-renamed '{pdfs_in_assets[0]}' to 'script.pdf' in assets.")
            has_pdf = True
            print(f"  [INFO] Script PDF is ready in assets folder.")

        # 2. Robust PDF Search for NEW files in root to copy over
        search_dirs = [os.getcwd(), os.path.dirname(os.path.abspath(__file__))]
        found_pdf_path = None
        
        for s_dir in search_dirs:
            pdf_files = [f for f in os.listdir(s_dir) if f.lower().endswith('.pdf')]
            if pdf_files:
                found_pdf_path = os.path.join(s_dir, pdf_files[0])
                break
        
        if found_pdf_path:
            print(f"  [INFO] New PDF found in root: '{os.path.basename(found_pdf_path)}'. Updating assets/script.pdf...")
            shutil.copy2(found_pdf_path, os.path.join(assets_dir, "script.pdf"))
            has_pdf = True

        # 3. Base64 encode for file:// protocol support
        pdf_encoded_string = None
        if has_pdf:
            import base64
            final_pdf = os.path.join(assets_dir, "script.pdf")
            try:
                with open(final_pdf, "rb") as pdf_file:
                    pdf_encoded_string = base64.b64encode(pdf_file.read()).decode('utf-8')
                print(f"  [SUCCESS] Inlining PDF data for {raw_name} ({len(pdf_encoded_string)//1024} KB)")
            except Exception as e:
                print(f"  [ERROR] Failed to read PDF: {e}")
                has_pdf = False
        elif not has_pdf:
            print(f"  [WARNING] No PDF found in search dirs or assets folder. Fallback message will be shown.")

        with open(jf, 'r', encoding='utf-8') as f:
            data = json.load(f)

        web_segments = []

        for item in data:
            seg_id = item.get("id")
            if seg_id is None:
                continue

            char_str = item.get("character", "00")
            speaker_id = char_str.split("_")[1] if "_" in char_str else "00"
            counter = seg_id + 1
            audio_file = os.path.join(audio_folder, f"speaker{int(speaker_id)}_audio_{counter}.mp3")

            out_audio_rel = None
            out_image_rel = None

            if os.path.exists(audio_file):
                out_audio_name = f"seg_{seg_id}.mp3"
                shutil.copy2(audio_file, os.path.join(assets_dir, out_audio_name))
                out_audio_rel = f"assets/{out_audio_name}"

            image_file = item.get("image")
            if image_file and os.path.exists(image_file):
                ext = os.path.splitext(image_file)[1].lower()
                out_image_name = f"img_{seg_id}{ext}"
                shutil.copy2(image_file, os.path.join(assets_dir, out_image_name))
                out_image_rel = f"assets/{out_image_name}"

            web_segments.append({
                "id": seg_id,
                "character": item.get("character", ""),
                "paragraph": item.get("paragraph", ""),
                "audio_path": out_audio_rel,
                "media_path": out_image_rel
            })

        html_content = build_html_content(raw_name, web_segments, has_pdf=has_pdf, pdf_base64=pdf_encoded_string)
        html_path = os.path.join(project_dir, "index.html")
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"  ✅ Exported to {project_dir}/")
        
        if not args.no_open:
            webbrowser.open(os.path.abspath(html_path))

if __name__ == "__main__":
    main()
