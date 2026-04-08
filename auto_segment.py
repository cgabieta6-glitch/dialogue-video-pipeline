import re
import json
import os
import sys
from collections import Counter

# Very simple stop words to filter out for image search keywords
STOP_WORDS = set([
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
    "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", 
    "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", 
    "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", 
    "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", 
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", 
    "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", 
    "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", 
    "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", 
    "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", 
    "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", "like", "really", "want",
    "think", "know", "look", "see", "mean", "right", "exactly", "yeah", "ok", "okay", "well", "got", "let", "s",
    "kind", "bit", "actually", "going", "goes", "getting", "looking", "looked", "take", "looked", "looked", "seen",
    "everything", "everywhere", "anywhere", "anything", "nothing", "day", "night", "time", "year", "years", "people",
    "man", "woman", "child", "children", "life", "death", "world", "earth", "planet", "universe", "space", "star", "stars",
    "sun", "moon", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "hundred", "thousand"
])

def extract_image_keywords(paragraph, used_queries):
    words = re.findall(r'\b[a-zA-Z]{4,}\b', paragraph.lower())
    filtered_words = [w for w in words if w not in STOP_WORDS]
    counts = Counter(filtered_words)
    top_words = [word for word, count in counts.most_common(6)]
    
    # Try different combinations if already used
    base_query = " ".join(top_words).title()
    if not base_query:
        return "" # Let the caller handle conversational fillers
        
    query = base_query
    counter = 1
    while query in used_queries:
        query = f"{base_query} {counter}"
        counter += 1
        
    used_queries.add(query)
    return query

def process_file(filename, use_paragraph=False):
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return

    print(f"Processing {filename}...")
    if use_paragraph:
        print("  [Mode] Using full paragraph text as image_search")
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = []
    current_id = 0
    used_queries = set()

    # Regex to match [0.03s - 17.36s] [SPEAKER_00]:  paragraph.... or just [SPEAKER_00]:
    pattern = re.compile(r'(?:\[.*?\]\s*)?\[(SPEAKER_\d+)\]:\s*(.*)')

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        line_clean = re.sub(r'^\d+:\s*', '', line)
        match = pattern.search(line_clean)
        if match:
            character = match.group(1)
            paragraph = match.group(2).strip()
            
            if use_paragraph:
                # Use the full paragraph text as the search query
                image_search = paragraph
            else:
                image_search = extract_image_keywords(paragraph, used_queries)
            
            # If the paragraph is just filler (e.g. "Yeah", "Right"), use the visual context of the previous line!
            if not image_search and entries:
                image_search = entries[-1]["image_search"]
            # Failsafe if the very first line of the transcript is mysteriously empty of useful words
            if not image_search:
                image_search = "Background Visual Textures"
            
            entries.append({
                "id": current_id,
                "character": character,
                "paragraph": paragraph,
                "image_search": image_search
            })
            current_id += 1

    out_name = os.path.basename(filename).replace('.txt', '.json')
    base_dir = os.path.dirname(filename)
    out_path = os.path.join(base_dir, out_name)
    
    with open(out_path, 'w', encoding='utf-8') as outfile:
        json.dump(entries, outfile, indent=2, ensure_ascii=False)
        
    print(f'Done! Created {out_name} with {len(entries)} items.')

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Auto-segment transcripts into JSON for the video pipeline.")
    parser.add_argument(
        "files", nargs="*",
        help="Specific .txt files to process. If none given, processes all 'done *.txt' files in the current directory."
    )
    parser.add_argument(
        "--use-paragraph",
        action="store_true",
        help="Use the full paragraph text as the 'image_search' field instead of extracted keywords"
    )
    args = parser.parse_args()

    if args.files:
        files_to_process = args.files
    else:
        # Auto-discover all .txt files that have NOT been processed yet (no "done" prefix)
        files_to_process = [f for f in os.listdir('.') if f.endswith('.txt') and not f.startswith('done ')]
        if not files_to_process:
            print("No unprocessed .txt files found in the current directory. Pass filenames as arguments.")
            sys.exit(1)

    for f in files_to_process:
        process_file(f, use_paragraph=args.use_paragraph)
