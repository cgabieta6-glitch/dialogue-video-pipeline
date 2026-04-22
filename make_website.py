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
    
    segments_html = ""
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

        segments_html += f"""
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
            display: block;
            margin: 0 auto 40px auto;
            background: white;
            box-shadow: 0 15px 45px rgba(0,0,0,0.4);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            width: 95%; 
            max-width: 900px;
            overflow: visible; /* Allow canvas to push height */
            border-radius: 4px;
        }}
        .pdf-page-container:hover {{
            box-shadow: 0 20px 60px rgba(0,0,0,0.6);
            transform: translateY(-5px);
        }}
        .pdf-page-container canvas {{
            display: block;
            max-width: 100%;
            height: auto;
            z-index: 1;
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
            z-index: 2;
            pointer-events: auto; /* Allow selection */
        }}
        .textLayer > span {{
            color: transparent;
            position: absolute;
            white-space: pre;
            cursor: text;
            transform-origin: 0% 0%;
        }}

        .text-match-highlight, .pdf-match-highlight {{
            background: #facc15 !important;
            color: #000 !important;
            border-radius: 2px;
            box-shadow: 0 0 4px rgba(250, 204, 21, 0.8);
            cursor: pointer; /* Click to remove */
            transition: box-shadow 0.3s;
        }}
        .pulse-highlight {{
            box-shadow: 0 0 15px #fff, 0 0 25px #facc15 !important;
            transform: scale(1.1);
        }}

        /* Playback specific highlight */
        .pdf-playback-highlight {{
            background: #ef4444 !important; /* Red for playback */
            opacity: 0.6;
            border-radius: 3px;
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
        }}
        .card-match-highlight {{
            border-left: 4px solid #facc15 !important; /* Subtle side indicator only */
            background: transparent !important;
        }}

        /* New Scroll Sidebar Architecture */
        .panel-outer {{
            position: relative;
            flex: 1;
            display: flex;
            overflow: hidden; /* Prevent outer scroll */
            background: rgba(0,0,0,0.2);
        }}
        .pdf-controls {{
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border-bottom: 1px solid var(--header-border);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .pdf-tools-row {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .editable-active {{
            outline: 1px dashed #facc15 !important;
            background: white !important; /* Mask the original PDF text underneath */
            color: black !important;      /* Make your new text visible */
            z-index: 100 !important;
            box-shadow: 0 0 5px rgba(0,0,0,0.2);
            mix-blend-mode: normal !important;
        }}
        .editable-active:focus {{
            outline: 2px solid #facc15 !important;
            background: white !important;
            color: black !important;
            z-index: 101 !important;
        }}
        /* Dim the canvas slightly when editing to focus on text layer */
        .split-screen:has(.editable-active) .pdf-page-container canvas {{
            opacity: 0.4;
            filter: grayscale(1);
        }}
        .panel-content {{
            flex: 1;
            overflow-y: auto;
            scrollbar-width: thin; /* Firefox */
            scrollbar-color: rgba(128,128,128,0.3) transparent;
        }}
        /* Webkit scrollbar cleanup */
        .panel-content::-webkit-scrollbar {{
            width: 8px;
        }}
        .panel-content::-webkit-scrollbar-track {{
            background: transparent;
        }}
        .panel-content::-webkit-scrollbar-thumb {{
            background: rgba(128,128,128,0.3);
            border-radius: 4px;
        }}

        .scroll-sidebar {{
            width: 14px;
            height: 100%;
            background: rgba(0, 0, 0, 0.4); /* Dark strip like browser search */
            position: relative;
            border-left: 1px solid rgba(255,255,255,0.05);
            pointer-events: auto; 
            cursor: crosshair;
        }}
        .scroll-marker {{
            position: absolute;
            left: 0;
            width: 100%;
            height: 3px;
            background: #facc15;
            box-shadow: 0 0 8px rgba(250, 204, 21, 0.6);
            border-radius: 0;
            z-index: 10;
            cursor: pointer;
            transition: transform 0.1s;
        }}
        .scroll-marker:hover {{
            transform: scaleY(2);
            background: #fff;
            z-index: 20;
        }}
        
        .split-screen {{
            display: flex;
            flex-direction: row;
            height: 100vh;
            gap: 0;
            background: #1a1a2e;
            overflow: hidden;
            position: relative;
        }}

        /* Orientation and Swapping */
        .split-screen.layout-vertical {{ flex-direction: column; }}
        .split-screen.layout-swapped {{ flex-direction: row-reverse; }}
        .split-screen.layout-vertical.layout-swapped {{ flex-direction: column-reverse; }}

        /* Resizer styles */
        .resizer {{
            background: rgba(255,255,255,0.05);
            position: relative;
            z-index: 1000;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .split-screen:not(.layout-vertical) .resizer {{
            width: 6px;
            cursor: col-resize;
            height: 100%;
        }}
        .split-screen.layout-vertical .resizer {{
            width: 100%;
            cursor: row-resize;
            height: 6px;
        }}

        .resizer:hover, .resizer.dragging {{
            background: #facc15;
            box-shadow: 0 0 15px rgba(250, 204, 21, 0.5);
        }}
        .resizer-handle {{
            background: rgba(255,255,255,0.2);
            border-radius: 1px;
        }}
        .split-screen:not(.layout-vertical) .resizer-handle {{
            width: 2px;
            height: 30px;
        }}
        .split-screen.layout-vertical .resizer-handle {{
            width: 30px;
            height: 2px;
        }}

        .pdf-hidden #drag-bar {{
            display: none !important;
        }}
        
        .panel-outer {{
            position: relative;
            flex: 1;
            display: flex;
            overflow: hidden;
            background: rgba(0,0,0,0.2);
        }}
        .panel-outer:nth-of-type(1) {{
            flex: 0 0 50%;
            min-width: 200px;
            min-height: 200px;
        }}
        .panel-outer:nth-of-type(2) {{
            flex: 1;
            min-width: 200px;
            min-height: 200px;
        }}

        /* --- LEED-STYLE FLOATING TOOLBAR --- */
        .floating-toolbar {{
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(15, 17, 23, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 8px 15px;
            display: flex;
            align-items: center;
            gap: 8px;
            z-index: 9999;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .floating-toolbar:hover {{
            background: rgba(15, 17, 23, 0.95);
            bottom: 35px;
        }}
        .tool-group {{
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 0 8px;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .tool-group:last-child {{ border-right: none; }}
        
        .leed-btn {{
            background: transparent;
            border: none;
            color: #94a3b8;
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 1.2rem;
            position: relative;
        }}
        .leed-btn:hover {{
            background: rgba(255, 255, 255, 0.05);
            color: #fff;
        }}
        .leed-btn.active {{
            background: #facc15;
            color: #0f1117;
            box-shadow: 0 0 15px rgba(250, 204, 21, 0.4);
        }}
        .leed-btn[title]:hover::after {{
            content: attr(title);
            position: absolute;
            bottom: 130%;
            left: 50%;
            transform: translateX(-50%);
            background: #1e293b;
            color: #fff;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.75rem;
            white-space: nowrap;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            pointer-events: none;
        }}

        /* --- OVERLAY ANNOTATIONS --- */
        .pdf-annotation-text {{
            position: absolute;
            background: transparent;
            border: 1px dashed transparent;
            color: #facc15;
            font-family: 'Outfit', sans-serif;
            font-size: 14px;
            padding: 2px 4px;
            cursor: move;
            z-index: 1000;
            white-space: nowrap;
            min-width: 20px;
        }}
        .pdf-annotation-text:hover {{
            border-color: rgba(250, 204, 21, 0.5);
            background: rgba(250, 204, 21, 0.05);
        }}
        .pdf-annotation-text.editing {{
            border-color: #facc15;
            background: rgba(0,0,0,0.8);
            outline: none;
        }}

        /* --- PANEL CLEANUP --- */
        .header-content, .pdf-controls {{
            display: none !important; /* Hide old UI */
        }}
        .panel-content {{
            padding-top: 10px; /* More room without header */
        }}
        .split-screen {{
            height: 100vh;
        }}

        /* PDF Panel Hiding */
        .pdf-hidden .panel-outer:nth-of-type(2) {{
            display: none !important;
        }}
        .pdf-hidden .panel-outer:nth-of-type(1) {{
            flex: 1;
            max-width: 100%;
        }}
        
        #pdf-panel-toggle.active {{
            background: #facc15 !important;
            color: #1a1a2e !important;
            box-shadow: 0 0 10px rgba(250, 204, 21, 0.4);
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 0;
            overflow: hidden;
        }}

        .left-panel {{
            flex: 1;
            height: 100vh;
            overflow-y: auto;
            position: relative;
        }}

        .right-panel {{
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #121212;
            height: 100vh;
            overflow-y: auto;
            position: relative;
        }}

        #pdf-viewer-container {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
            background: #1a1a1a;
            min-height: 100%;
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
        <!-- Floating LEED-Style Toolbar -->
        <div class="floating-toolbar">
            <div class="tool-group">
                <button class="leed-btn active" data-tool="select" title="Selection Tool">🏹</button>
                <button class="leed-btn" data-tool="highlight" title="Text Highlighter">🖍️</button>
                <button class="leed-btn" data-tool="text" title="Type Annotation">⌨️</button>
                <button class="leed-btn" data-tool="draw" title="Sketch/Draw">🖌️</button>
                <button class="leed-btn" id="leed-eraser" title="Clear All Annotations">🗑️</button>
            </div>
            <div class="tool-group">
                <button class="leed-btn" id="leed-swap" title="Swap Panels">⇄</button>
                <button class="leed-btn" id="leed-flip" title="Vertical/Horizontal Flip">⊟</button>
                <button class="leed-btn active" id="leed-pdf" title="Show/Hide PDF">📄</button>
            </div>
            <div class="tool-group">
                <button class="leed-btn" id="leed-focus" title="Cinematic Focus Mode">🎯</button>
                <button class="leed-btn" id="leed-play" title="Play All Dialogue">▶</button>
                <button class="leed-btn" id="leed-theme" title="Cycle Themes">🌓</button>
            </div>
        </div>
        <!-- Left Panel: Dialogue Cards -->
        <div class="panel-outer">
            <div class="panel-content left-panel">
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
                                <button class="tool-toggle" id="layout-flip-toggle" title="Switch between Side-by-Side and Top-Bottom Layout">⊟ Flip</button>
                                <button class="tool-toggle" id="layout-swap-toggle" title="Swap Panel Positions">⇄ Swap</button>
                                <button class="tool-toggle" id="pdf-panel-toggle" title="Toggle PDF Panel (Side-by-Side)">📄 PDF</button>
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

                    <div id="segments-container">
                        {segments_html}
                    </div>
                </div>
            </div>
            <div class="scroll-sidebar" id="left-scroll-markers"></div>
        </div>

        <!-- Draggable Resizer -->
        <div class="resizer" id="drag-bar">
            <div class="resizer-handle"></div>
        </div>

        <!-- Right Panel: PDF Viewer -->
        <div class="panel-outer">
            <div class="panel-content right-panel">
                <div class="pdf-controls">
                    <div class="pdf-header">
                        <span>📄 Script Viewer (Interactive)</span>
                    </div>
                    <div class="pdf-tools-row">
                        <button id="pdf-edit-toggle" class="tool-btn" title="Toggle Correction Mode (Edit PDF Text)">✏️</button>
                        <button class="clear-highlights-btn" onclick="clearAllHighlights()" title="Clear all saved highlights">Clear Highlights</button>
                    </div>
                </div>
                <div id="pdf-viewer-container">
                    <div id="pdf-fallback" class="pdf-placeholder" style="display: {'none' if has_pdf else 'flex'}; flex-direction: column; justify-content: center; align-items: center; height: 100%; padding: 2rem;">
                        <p>To view your script, place a PDF named <strong>script.pdf</strong> into the <strong>assets</strong> folder.</p>
                    </div>
                    <!-- PDF pages will be rendered here -->
                </div>
            </div>
            <div class="scroll-sidebar" id="right-scroll-markers"></div>
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
    let pdfEdits = JSON.parse(localStorage.getItem(storageKey + '_pdf_edits') || '{{}}');
    let editMode = false;

    function applyEditability() {{
        document.querySelectorAll('.textLayer span').forEach(span => {{
            span.contentEditable = editMode;
            if (editMode) {{
                span.classList.add('editable-active');
                if (!span.dataset.editHandled) {{
                    span.dataset.editHandled = "true";
                    span.onblur = () => saveSpanEdit(span);
                    span.onkeydown = (e) => {{
                        if (e.key === 'Enter') {{
                            e.preventDefault();
                            span.blur();
                        }}
                    }};
                }}
            }} else {{
                span.classList.remove('editable-active');
            }}
        }});
    }}

    function saveSpanEdit(span) {{
        const pageContainer = span.closest('.pdf-page-container');
        if (!pageContainer) return;
        const pageNum = pageContainer.id.replace('pdf-page-', '');
        const spanIndex = Array.from(span.parentNode.children).indexOf(span);
        
        if (!pdfEdits[pageNum]) pdfEdits[pageNum] = {{}};
        pdfEdits[pageNum][spanIndex] = span.innerText;
        
        localStorage.setItem(storageKey + '_pdf_edits', JSON.stringify(pdfEdits));
    }}

    function applyPersistedEdits(pageNum, container) {{
        const edits = pdfEdits[pageNum];
        if (!edits) return;
        
        const spans = container.querySelectorAll('.textLayer span');
        Object.keys(edits).forEach(index => {{
            if (spans[index]) {{
                spans[index].innerText = edits[index];
            }}
        }});
    }}

    // Global logic initialization
    // Load persisted data
        const savedNotes = localStorage.getItem(storageKey + '_notes');
        if (savedNotes) document.querySelector('#sticky-note textarea').value = savedNotes;

        const savedTheme = localStorage.getItem(storageKey + '_theme');
        if (savedTheme) {{
            document.documentElement.setAttribute('data-theme', savedTheme);
            document.querySelectorAll('.theme-dot').forEach(d => {{
                d.classList.toggle('active', d.getAttribute('data-theme') === savedTheme);
            }});
        }}

        // Setup PDF Edit Toggle
        const editToggle = document.getElementById('pdf-edit-toggle');
        if (editToggle) {{
            editToggle.onclick = () => {{
                editMode = !editMode;
                editToggle.classList.toggle('active', editMode);
                applyEditability();
            }};
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

        // PDF Panel Toggle Logic
        const pdfToggleBtn = document.getElementById('pdf-panel-toggle');
        const splitScreen = document.querySelector('.split-screen');
        const isPdfHidden = localStorage.getItem(storageKey + '_pdf_hidden') === 'true';
        
        if (isPdfHidden) {{
            splitScreen.classList.add('pdf-hidden');
            pdfToggleBtn.classList.remove('active');
        }} else {{
            pdfToggleBtn.classList.add('active');
        }}

        pdfToggleBtn.onclick = () => {{
            const hidden = splitScreen.classList.toggle('pdf-hidden');
            pdfToggleBtn.classList.toggle('active', !hidden);
            localStorage.setItem(storageKey + '_pdf_hidden', hidden);
            updateScrollMarkers();
        }};

    // LEED-Style Toolbar Wiring
    const toolButtons = document.querySelectorAll('.leed-btn[data-tool]');
    let currentTool = 'select';

    toolButtons.forEach(btn => {{
        btn.onclick = () => {{
            toolButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentTool = btn.dataset.tool;
            
            // Toggle drawing canvas visibility/activity
            const canvas = document.getElementById('drawing-canvas');
            if (currentTool === 'draw') {{
                canvas.classList.add('active');
            }} else {{
                canvas.classList.remove('active');
            }}
        }};
    }});

    // Layout Buttons
    document.getElementById('leed-swap').onclick = () => document.getElementById('layout-swap-toggle').click();
    document.getElementById('leed-flip').onclick = () => document.getElementById('layout-flip-toggle').click();
    document.getElementById('leed-pdf').onclick = (e) => {{
        document.getElementById('pdf-panel-toggle').click();
        e.currentTarget.classList.toggle('active');
    }};
    document.getElementById('leed-focus').onclick = (e) => {{
        document.getElementById('focus-toggle').click();
        e.currentTarget.classList.toggle('active');
    }};
    document.getElementById('leed-play').onclick = () => document.getElementById('play-btn').click();
    document.getElementById('leed-eraser').onclick = () => {{
        if (confirm('Clear all drawings, highlights, and text annotations?')) {{
            clearAllHighlights(); // This also reloads
        }}
    }};
    document.getElementById('leed-theme').onclick = () => {{
        const themes = ['midnight', 'ocean', 'sunset', 'forest', 'lavender', 'light'];
        const current = document.documentElement.getAttribute('data-theme') || 'midnight';
        const next = themes[(themes.indexOf(current) + 1) % themes.length];
        document.querySelector(`.theme-dot[data-theme="${{next}}"]`).click();
    }};

    // New Text Annotation Logic
    const pdfAnnoTextKey = storageKey + '_pdf_text_annos';
    let pdfTextAnnos = JSON.parse(localStorage.getItem(pdfAnnoTextKey) || '[]');

    function createTextAnno(x, y, pageNum, text = "", isNew = true) {{
        const container = document.getElementById('pdf-page-' + pageNum);
        if (!container) return;

        const anno = document.createElement('div');
        anno.className = 'pdf-annotation-text';
        anno.style.left = x + 'px';
        anno.style.top = y + 'px';
        anno.contentEditable = true;
        anno.innerText = text;

        if (isNew) {{
            setTimeout(() => anno.focus(), 10);
            anno.classList.add('editing');
        }}

        anno.onblur = () => {{
            anno.classList.remove('editing');
            if (anno.innerText.trim() === "") {{
                anno.remove();
                saveTextAnnos();
            }} else {{
                saveTextAnnos();
            }}
        }};

        container.appendChild(anno);
    }}

    function saveTextAnnos() {{
        const annos = [];
        document.querySelectorAll('.pdf-annotation-text').forEach(el => {{
            const container = el.closest('.pdf-page-container');
            if (!container) return;
            annos.push({{
                x: parseFloat(el.style.left),
                y: parseFloat(el.style.top),
                pageNum: container.dataset.pageNumber,
                text: el.innerText
            }});
        }});
        localStorage.setItem(pdfAnnoTextKey, JSON.stringify(annos));
    }}

    function loadTextAnnos(pageNum, container) {{
        pdfTextAnnos.forEach(a => {{
            if (a.pageNum == pageNum) {{
                createTextAnno(a.x, a.y, a.pageNum, a.text, false);
            }}
        }});
    }}

    // Global listener for adding new text annotations
    document.addEventListener('mousedown', (e) => {{
        if (currentTool !== 'text') return;
        const pageContainer = e.target.closest('.pdf-page-container');
        if (!pageContainer) return;
        
        // Don't spawn if clicking existing anno
        if (e.target.classList.contains('pdf-annotation-text')) return;

        const rect = pageContainer.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const pageNum = pageContainer.dataset.pageNumber;

        createTextAnno(x, y, pageNum, "Type here...", true);
    }});

        console.log("Script initializing...");
        const dragBar = document.getElementById('drag-bar');
        const leftPanelOuter = document.querySelector('.panel-outer:nth-of-type(1)');
        let isDragging = false;

        const savedWidth = localStorage.getItem(storageKey + '_left_width');
        const savedHeight = localStorage.getItem(storageKey + '_left_height');
        
        if (!isPdfHidden) {{
            if (isVertical && savedHeight) leftPanelOuter.style.flex = `0 0 ${{savedHeight}}px`;
            else if (!isVertical && savedWidth) leftPanelOuter.style.flex = `0 0 ${{savedWidth}}px`;
        }}

        dragBar.addEventListener('mousedown', (e) => {{
            isDragging = true;
            dragBar.classList.add('dragging');
            document.body.style.cursor = splitScreen.classList.contains('layout-vertical') ? 'row-resize' : 'col-resize';
            document.body.style.userSelect = 'none';
        }});

        document.addEventListener('mousemove', (e) => {{
            if (!isDragging) return;
            
            const isVert = splitScreen.classList.contains('layout-vertical');
            const isSwp = splitScreen.classList.contains('layout-swapped');
            
            if (isVert) {{
                let newHeight = isSwp ? window.innerHeight - e.clientY : e.clientY;
                if (newHeight > 150 && newHeight < window.innerHeight - 150) {{
                    leftPanelOuter.style.flex = `0 0 ${{newHeight}}px`;
                    localStorage.setItem(storageKey + '_left_height', newHeight);
                }}
            }} else {{
                let newWidth = isSwp ? window.innerWidth - e.clientX : e.clientX;
                if (newWidth > 200 && newWidth < window.innerWidth - 200) {{
                    leftPanelOuter.style.flex = `0 0 ${{newWidth}}px`;
                    localStorage.setItem(storageKey + '_left_width', newWidth);
                }}
            }}
            updateScrollMarkers();
        }});

        document.addEventListener('mouseup', () => {{
            if (isDragging) {{
                isDragging = false;
                dragBar.classList.remove('dragging');
                document.body.style.cursor = 'default';
                document.body.style.userSelect = 'auto';
                updateScrollMarkers();
            }}
        }});

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
        const pdfjsLib = window['pdfjsLib'] || window['pdfjs-dist/build/pdf'];
        const pdfViewerContainer = document.getElementById('pdf-viewer-container');
        const rightPanel = document.querySelector('.right-panel');
        if (pdfjsLib) {{
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        }}

        let pdfDoc = null;
        let pageRendering = new Set();
        let renderedPages = new Set();
        let persistentHighlights = JSON.parse(localStorage.getItem(storageKey + '_text_highlights') || '[]');

        function normalizeText(text) {{
            if (!text) return "";
            return text.toLowerCase().replace(/[^\\w\\s]/g, '').replace(/\\s+/g, ' ').trim();
        }}

        async function initPDFViewer(base64Data) {{
            console.log("PDF Engine: Starting initialization...");
            if (!base64Data) {{
                console.error("PDF Engine: No base64 data provided!");
                return;
            }}
            try {{
                console.log("PDF Engine: Decoding base64 data (" + base64Data.length + " chars)...");
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
                    root: rightPanel, 
                    rootMargin: '800px 0px', // More proactive loading
                    threshold: 0.01 
                }});

                for (let i = 1; i <= pdfDoc.numPages; i++) {{
                    const pageContainer = document.createElement('div');
                    pageContainer.className = 'pdf-page-container';
                    pageContainer.id = 'pdf-page-' + i;
                    pageContainer.dataset.pageNumber = i;
                    
                    // Loading skeleton with typical aspect ratio (A4 is approx 1/1.41)
                    pageContainer.style.aspectRatio = "1 / 1.41";
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
        console.log("PDF Engine: Checking for data...");
        
        if (typeof pdfData !== 'undefined' && pdfData && pdfData.length > 0) {{
            console.log("PDF Engine: Data found, launching viewer...");
            pdfFallback.style.display = 'none';
            initPDFViewer(pdfData);
            
            // Apply persistent highlights to cards on load
            setTimeout(() => {{
                persistentHighlights.forEach(text => syncToCard(text));
            }}, 1000); // Small delay to ensure cards are in DOM
        }} else {{
            console.warn("No PDF Data found in HTML.");
            pdfFallback.style.display = 'flex';
        }}

        async function renderPage(pageNum) {{
            if (renderedPages.has(pageNum) || pageRendering.has(pageNum)) return;
            pageRendering.add(pageNum);

            try {{
                const page = await pdfDoc.getPage(pageNum);
                const baseScale = 1.4; // Optimized for the split-screen panel
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
                canvas.style.width = "100%";
                canvas.style.height = "auto";
                container.style.width = "95%";
                container.style.maxWidth = Math.floor(viewport.width) + "px";
                container.style.height = "auto";
                
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

                // Text Layer - Dynamically scaled to match responsive canvas
                const textLayerDiv = document.createElement('div');
                textLayerDiv.className = 'textLayer';
                
                // Calculate effective scale (Actual Width / Unscaled Width)
                const actualWidth = container.clientWidth;
                const unscaledWidth = viewport.width / viewport.scale;
                const effectiveScale = actualWidth / unscaledWidth;
                
                textLayerDiv.style.setProperty('--scale-factor', effectiveScale);
                container.appendChild(textLayerDiv);

                const textContent = await page.getTextContent();
                await pdfjsLib.renderTextLayer({{
                    textContentSource: textContent,
                    container: textLayerDiv,
                    viewport: page.getViewport({{ scale: effectiveScale }}),
                    textDivs: []
                }}).promise;

                renderedPages.add(pageNum);
                
                // Apply persisted text edits (Old correction mode)
                applyPersistedEdits(pageNum, container);
                
                // Apply new Leed-Style Text Annotations
                loadTextAnnos(pageNum, container);
                
                // Re-apply edit mode if active
                if (editMode) applyEditability();

                updateScrollMarkers();

                // Apply persistent highlights to this newly rendered page
                persistentHighlights.forEach(text => syncToPDF(text, false, false));
            }} catch (e) {{
                console.error("Error rendering page " + pageNum, e);
            }} finally {{
                pageRendering.delete(pageNum);
            }}
        }}

        // Persistence for Highlights helpers
        function saveHighlight(text) {{
            if (!text || text.length < 5) return;
            if (!persistentHighlights.includes(text)) {{
                persistentHighlights.push(text);
                localStorage.setItem(storageKey + '_text_highlights', JSON.stringify(persistentHighlights));
            }}
        }}

        window.clearAllHighlights = function() {{
            persistentHighlights = [];
            localStorage.setItem(storageKey + '_text_highlights', JSON.stringify([]));
            location.reload();
        }};

        function removeHighlight(text) {{
            const normalized = normalizeText(text);
            persistentHighlights = persistentHighlights.filter(h => normalizeText(h) !== normalized);
            localStorage.setItem(storageKey + '_text_highlights', JSON.stringify(persistentHighlights));
            
            // Seamlessly remove from DOM without reload
            const highlights = document.querySelectorAll('.pdf-match-highlight, .text-match-highlight');
            highlights.forEach(el => {{
                if (normalizeText(el.textContent) === normalized) {{
                    const parent = el.parentNode;
                    while (el.firstChild) parent.insertBefore(el.firstChild, el);
                    parent.removeChild(el);
                    
                    // If it's a card, check if we should remove the card-level highlight
                    const card = parent.closest('.card');
                    if (card && !card.querySelector('.text-match-highlight')) {{
                        card.classList.remove('card-match-highlight');
                    }}
                }}
            }});
            updateScrollMarkers();
        }}

        function updateScrollMarkers() {{
            // Use requestAnimationFrame to avoid layout thrashing
            requestAnimationFrame(() => {{
                updateMarkersForPanel('.left-panel', '#left-scroll-markers', '.text-match-highlight');
                updateMarkersForPanel('.right-panel', '#right-scroll-markers', '.pdf-match-highlight');
            }});
        }}

        function updateMarkersForPanel(panelSelector, markerContainerId, highlightSelector) {{
            const panel = document.querySelector(panelSelector);
            const markerContainer = document.querySelector(markerContainerId);
            if (!panel || !markerContainer) return;

            markerContainer.innerHTML = '';
            const scrollHeight = panel.scrollHeight;
            const clientHeight = panel.clientHeight;
            if (scrollHeight <= clientHeight) return; // No scrollbar, no markers needed

            const highlights = panel.querySelectorAll(highlightSelector);
            const seenPositions = new Set();

            highlights.forEach(h => {{
                // Calculate absolute top position relative to panel's content
                let top = 0;
                let curr = h;
                while (curr && curr !== panel) {{
                    top += curr.offsetTop;
                    curr = curr.offsetParent;
                }}

                const percent = (top / scrollHeight) * 100;
                
                // Prevent overcrowding markers too close to each other
                const roundedPercent = Math.round(percent);
                if (seenPositions.has(roundedPercent)) return;
                seenPositions.add(roundedPercent);

                const marker = document.createElement('div');
                marker.className = 'scroll-marker';
                marker.style.top = percent + '%';
                marker.title = 'Jump to highlight';
                
                // Make marker clickable to jump to highlight
                marker.onclick = (e) => {{
                    e.stopPropagation();
                    h.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    
                    // Pulse the highlight
                    h.classList.add('pulse-highlight');
                    setTimeout(() => h.classList.remove('pulse-highlight'), 1000);
                }};

                markerContainer.appendChild(marker);
            }});
        }}

        // Observer to update markers when PDF pages are rendered
        const resizeObserver = new ResizeObserver(() => updateScrollMarkers());
        resizeObserver.observe(document.querySelector('.left-panel'));
        resizeObserver.observe(document.querySelector('.right-panel'));

        // Global listener for highlight removal
        document.addEventListener('click', (e) => {{
            if (e.target.classList.contains('pdf-match-highlight') || e.target.classList.contains('text-match-highlight')) {{
                removeHighlight(e.target.textContent);
            }}
        }});

        // Bidirectional Highlighting Logic
        let selectionTimeout;
        document.addEventListener('selectionchange', () => {{
            clearTimeout(selectionTimeout);
            selectionTimeout = setTimeout(() => {{
                const selection = window.getSelection();
                if (!selection.rangeCount) return;
                
                const selectedText = selection.toString().trim();
                if (selectedText.length < 3) return;

                const range = selection.getRangeAt(0);
                const container = range.commonAncestorContainer.nodeType === 3 ? range.commonAncestorContainer.parentElement : range.commonAncestorContainer;
                const isLeft = container.closest('.left-panel') || (selection.anchorNode && selection.anchorNode.parentElement.closest('.left-panel'));
                const isRight = container.closest('.right-panel') || (selection.anchorNode && selection.anchorNode.parentElement.closest('.right-panel'));

                const normalizedSelected = normalizeText(selectedText);

                // Left to Right (Card -> PDF)
                if (isLeft) {{
                    saveHighlight(normalizedSelected);
                    syncToPDF(normalizedSelected, false, true);
                }} 
                // Right to Left (PDF -> Card)
                else if (isRight) {{
                    saveHighlight(normalizedSelected);
                    syncToCard(normalizedSelected);
                    // Also trigger the PDF highlight injection so it stays after click-away
                    syncToPDF(normalizedSelected, false, false); 
                }}
            }}, 500); // Debounce to prevent lag
        }});

        function syncToPDF(normalizedText, isPlayback = false, isManualSelection = false) {{
            const highlightClass = isPlayback ? 'pdf-playback-highlight' : 'pdf-match-highlight';
            
            // Only clear playback highlights (which should be transient)
            if (isPlayback) {{
                document.querySelectorAll('.pdf-playback-highlight').forEach(el => {{
                    const parent = el.parentNode;
                    while (el.firstChild) parent.insertBefore(el.firstChild, el);
                    parent.removeChild(el);
                }});
            }}

            const spans = document.querySelectorAll('.textLayer span');
            let foundInRendered = false;
            const regex = new RegExp(`(${{normalizedText.split('').join('[\\\\s\\\\W]*')}})`, 'gi');

            for (let span of spans) {{
                // Skip if already highlighted by this specific class to prevent nesting
                if (span.querySelector('.' + highlightClass)) continue;
                if (span.classList.contains(highlightClass)) continue;

                const spanText = normalizeText(span.textContent);
                if (spanText.includes(normalizedText) || normalizedText.includes(spanText)) {{
                    if (span.textContent.match(regex)) {{
                        // Optimization: Only replace if not already wrapped
                        if (!span.innerHTML.includes(highlightClass)) {{
                            span.innerHTML = span.textContent.replace(regex, `<span class="${{highlightClass}}">$1</span>`);
                        }}
                        
                        if (!foundInRendered && (isPlayback || isManualSelection)) {{
                            span.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                            foundInRendered = true;
                        }}
                    }}
                }}
            }}
            updateScrollMarkers();
            
            if (isManualSelection) {{
                searchAllPages(normalizedText, !foundInRendered);
            }}
        }}

        async function searchAllPages(normalizedText, shouldScroll = true) {{
            if (!pdfDoc) return;
            let scrolled = false;
            for (let i = 1; i <= pdfDoc.numPages; i++) {{
                const page = await pdfDoc.getPage(i);
                const textContent = await page.getTextContent();
                const pageText = normalizeText(textContent.items.map(item => item.str).join(' '));
                
                if (pageText.includes(normalizedText)) {{
                    const container = document.getElementById('pdf-page-' + i);
                    if (shouldScroll && !scrolled) {{
                        container.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                        scrolled = true;
                    }}
                    // Note: We don't break here so we can find all matching pages
                    // In a more advanced version, we'd trigger renderPage(i) here
                }}
            }}
        }}

        function syncToCard(normalizedText) {{
            const cards = document.querySelectorAll('.card');
            const regex = new RegExp(`(${{normalizedText.split('').join('[\\\\s\\\\W]*')}})`, 'gi');
            let found = false;

            for (let card of cards) {{
                const paragraph = card.querySelector('.paragraph');
                const paraText = normalizeText(paragraph.textContent);
                
                if (paraText.includes(normalizedText) || normalizedText.includes(paraText)) {{
                    card.classList.add('card-match-highlight');
                    
                    // Highlight the text if not already highlighted
                    if (!paragraph.innerHTML.includes('text-match-highlight')) {{
                        if (paragraph.textContent.match(regex)) {{
                            paragraph.innerHTML = paragraph.textContent.replace(regex, `<span class="text-match-highlight">$1</span>`);
                        }}
                    }}

                    // Scroll to the first match
                    if (!found) {{
                         card.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                         found = true;
                    }}
                }}
            }}
            updateScrollMarkers();
        }}

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
            
            // Sync PDF to this card's text
            const paragraph = card.querySelector('.paragraph');
            if (paragraph) {{
                syncToPDF(normalizeText(paragraph.textContent), true);
            }}
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

    // Click-to-Play & Selection Logic
    document.querySelectorAll('.card-text').forEach(el => {{
        el.style.cursor = 'text'; // Make it clear text is selectable
        el.title = 'Double-click a word to sync, or click card to play';
        
        el.addEventListener('dblclick', (e) => {{
            const selection = window.getSelection();
            const selectedText = selection.toString().trim();
            if (selectedText.length >= 3) {{
                const normalized = normalizeText(selectedText);
                syncToPDF(normalized, false, true);
                saveHighlight(normalized);
            }}
        }});

        el.addEventListener('click', (e) => {{
            // Don't trigger if they clicked exactly on a text highlight
            if (e.target.classList.contains('text-match-highlight')) return;
            
            // Only trigger segment skip if NOT selecting text
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
