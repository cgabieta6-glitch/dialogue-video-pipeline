import re
import json
import os
import sys
import urllib.request
import urllib.parse
from collections import Counter

# ============================================================
# MODE 1 (DEFAULT): RAKE + YAKE-Style Smart Keyword Extraction
# ============================================================

# Try to import RAKE and YAKE — graceful fallback if missing
try:
    from rake_nltk import Rake
    HAS_RAKE = True
except ImportError:
    HAS_RAKE = False

try:
    import yake
    HAS_YAKE = True
except ImportError:
    HAS_YAKE = False

# Try to import spacy for enhanced Smart Mode
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

NLP = None
if HAS_SPACY:
    try:
        # Load small english model
        NLP = spacy.load("en_core_web_sm")
    except OSError:
        print("  [Setup] Downloading spaCy en_core_web_sm model. This happens once...")
        import subprocess
        try:
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
            NLP = spacy.load("en_core_web_sm")
        except Exception as e:
            print(f"  [Setup] Failed to setup spaCy model: {e}")
            HAS_SPACY = False
            NLP = None

# Try to import sentence-transformers for Semantic Similarity boost
try:
    from sentence_transformers import SentenceTransformer, util as st_util
    HAS_SBERT = True
except ImportError:
    HAS_SBERT = False

SBERT_MODEL = None
if HAS_SBERT:
    try:
        SBERT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        print("  [Setup] Sentence Transformer model loaded.")
    except Exception as e:
        print(f"  [Setup] Failed to load Sentence Transformer: {e}")
        HAS_SBERT = False
        SBERT_MODEL = None

# Predefined visual categories for semantic matching
VISUAL_CATEGORIES = [
    "Business Meeting Office", "Financial Chart Graph", "Stock Market Trading",
    "Nature Landscape Mountains", "Ocean Beach Coastline", "Forest Trees Wilderness",
    "Technology Computer Code", "Artificial Intelligence Robot", "Server Data Center",
    "Science Laboratory Experiment", "Microscope Biology Cells", "Chemical Reaction",
    "Medical Hospital Doctor", "Human Brain Neuroscience", "DNA Genetics",
    "City Skyline Architecture", "Construction Building Site", "House Interior Design",
    "People Crowd Community", "Family Children Playing", "Student Classroom Education",
    "Food Cooking Kitchen", "Restaurant Dining Table", "Fresh Fruits Vegetables",
    "Sports Athletics Competition", "Fitness Gym Workout", "Running Marathon",
    "Music Concert Performance", "Art Painting Gallery", "Cinema Film Production",
    "Space Astronomy Stars", "Planet Earth Globe", "Rocket Launch Space Shuttle",
    "Car Driving Highway", "Airplane Airport Travel", "Ship Sailing Ocean",
    "Farm Agriculture Crops", "Animal Wildlife Safari", "Pet Dog Cat",
    "War Military Conflict", "Peace Dove Freedom", "Justice Law Courtroom",
    "Money Currency Wallet", "Shopping Retail Store", "E-commerce Online Shopping",
    "Rain Storm Weather", "Sunrise Sunset Sky", "Snow Winter Cold",
    "Abstract Geometric Patterns", "Colorful Gradient Background", "Texture Surface Material",
]
VISUAL_CATEGORY_EMBEDDINGS = None

# Try to import KeyBERT for BERT-based keyword extraction
try:
    from keybert import KeyBERT
    HAS_KEYBERT = True
except ImportError:
    HAS_KEYBERT = False

KBERT_MODEL = None
if HAS_KEYBERT:
    try:
        KBERT_MODEL = KeyBERT(model="all-MiniLM-L6-v2")
        print("  [Setup] KeyBERT model loaded.")
    except Exception as e:
        print(f"  [Setup] Failed to load KeyBERT: {e}")
        HAS_KEYBERT = False
        KBERT_MODEL = None

# Ensure NLTK stopwords are available for rake_nltk
if HAS_RAKE:
    try:
        import nltk
        nltk.data.find('corpora/stopwords')
    except LookupError:
        import nltk
        nltk.download('stopwords', quiet=True)
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab', quiet=True)

# Words that are visually meaningless (filler/conversational) but NOT in standard stop lists
EXTRA_STOP_WORDS = set([
    "actually", "basically", "completely", "definitely", "essentially", "extremely",
    "fundamentally", "honestly", "incredibly", "inherently", "instantly", "literally",
    "obviously", "perfectly", "precisely", "specifically", "absolutely", "aggressively",
    "constantly", "drastically", "endlessly", "entirely", "exactly", "exclusively",
    "explicitly", "heavily", "highly", "identically", "immediately", "infinitely",
    "massively", "mathematically", "meaningfully", "necessarily", "overwhelmingly",
    "practically", "profoundly", "seamlessly", "sequentially", "simultaneously",
    "statistically", "strategically", "successfully", "theoretically", "thoroughly",
    "tremendously", "ultimately", "universally", "violently", "viscerally", "visually",
    # Conversational fillers
    "yeah", "okay", "right", "sure", "guess", "mean", "like", "know", "think",
    "really", "well", "thing", "stuff", "kind", "sort", "gonna", "wanna", "gotta",
    "kinda", "sorta", "alright", "anyway", "anyways", "hmm", "huh", "ugh",
    # Podcast/dialogue meta-words  
    "listener", "listeners", "episode", "podcast", "today", "deep", "dive",
    "recap", "overview", "takeaway", "takeaways", "wrap", "joining",
])
def extract_visual_query_spacy(paragraph, used_queries):
    """
    MODE 1 (Enhanced): Extract visually meaningful search queries using spaCy.
    
    Strategy:
    1. Find Noun Chunks (e.g., 'red car')
    2. Find Visual Entities (LOC, GPE, FAC, PRODUCT, EVENT)
    3. Filter out filler/conversational words
    4. Build a visually concrete search query
    """
    if not paragraph or len(paragraph.strip()) < 5 or NLP is None:
        return extract_visual_query_rake_yake(paragraph, used_queries)
        
    doc = NLP(paragraph)
    candidates = []
    
    # 1. Visual Entities
    visual_ent_labels = {"LOC", "GPE", "FAC", "PRODUCT", "EVENT", "ORG", "PERSON"}
    for ent in doc.ents:
        if ent.label_ in visual_ent_labels:
            clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', ent.text).strip()
            if clean_text and clean_text.lower() not in EXTRA_STOP_WORDS:
                candidates.append(("ent", 2.0, clean_text.title()))
                
    # 2. Noun Chunks (especially those with adjectives)
    for chunk in doc.noun_chunks:
        # Check if the chunk has an adjective modifier
        has_adj = any(token.pos_ == "ADJ" for token in chunk)
        # Clean text
        clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', chunk.text).strip()
        words = clean_text.lower().split()
        
        # Skip if all filler
        if not clean_text or all(w in EXTRA_STOP_WORDS for w in words):
            continue
            
        # Ignore pronouns
        if chunk.root.pos_ == "PRON":
            continue
            
        score = 1.5 if has_adj else 1.0
        
        # Expanded Visual Indicators
        visual_categories = [
            "chart", "graph", "diagram", "table", "plot", "histogram", "map", "dashboard",
            "data", "formula", "equation", "model", "system", "machine", "robot", "server",
            "market", "price", "cost", "money", "dollar", "income", "currency", "coin",
            "building", "house", "city", "car", "road", "bridge", "office", "street", "factory",
            "animal", "plant", "tree", "flower", "mountain", "ocean", "river", "forest", "beach",
            "experiment", "laboratory", "chemical", "reaction", "energy", "microscope", "telescope",
            "computer", "software", "code", "algorithm", "network", "screen", "laptop", "phone",
            "brain", "cell", "body", "organ", "muscle", "bone", "blood", "heart", "eye",
            "people", "person", "crowd", "team", "group", "family", "child", "man", "woman",
            "food", "drink", "coffee", "meal", "kitchen", "restaurant", "fruit", "vegetable"
        ]
        
        for vi in visual_categories:
            if vi in clean_text.lower():
                score *= 2.0
                break
                
        candidates.append(("chunk", score, clean_text.title()))
        
    if not candidates:
        return extract_visual_query_rake_yake(paragraph, used_queries)
        
    # Sort by score descending
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    query_parts = []
    seen_words = set()
    
    for _, _, phrase in candidates:
        if not phrase:
            continue
        phrase_words = set(w.lower() for w in phrase.split())
        if phrase_words.issubset(seen_words):
            continue
            
        query_parts.append(phrase)
        seen_words.update(phrase_words)
        
        current_len = len(" ".join(query_parts))
        if current_len >= 40 or len(query_parts) >= 3:
            break
            
    if not query_parts:
        return extract_visual_query_rake_yake(paragraph, used_queries)
        
    query = " ".join(query_parts).strip()
    
    if len(query) > 80:
        query = query[:80].rsplit(" ", 1)[0]
        
    if query in used_queries:
        base = query
        counter = 1
        while query in used_queries:
            query = f"{base} {counter}"
            counter += 1
            
    used_queries.add(query)
    return query


def _semantic_boost(paragraph, base_query):
    """
    Optionally enrich a search query by appending the best-matching visual category
    using Sentence Transformer cosine similarity.
    Returns the boosted query, or the original if SBERT is unavailable.
    """
    global VISUAL_CATEGORY_EMBEDDINGS
    
    if not HAS_SBERT or SBERT_MODEL is None:
        return base_query
    
    try:
        # Pre-compute category embeddings once (lazy init)
        if VISUAL_CATEGORY_EMBEDDINGS is None:
            VISUAL_CATEGORY_EMBEDDINGS = SBERT_MODEL.encode(VISUAL_CATEGORIES, convert_to_tensor=True)
        
        # Encode the paragraph
        para_embedding = SBERT_MODEL.encode(paragraph[:500], convert_to_tensor=True)
        
        # Compute cosine similarity against all categories
        scores = st_util.cos_sim(para_embedding, VISUAL_CATEGORY_EMBEDDINGS)[0]
        best_idx = scores.argmax().item()
        best_score = scores[best_idx].item()
        
        # Only append if similarity is reasonably high (> 0.25)
        if best_score > 0.25:
            category = VISUAL_CATEGORIES[best_idx]
            # Avoid appending if the category words are already in the query
            cat_words = set(w.lower() for w in category.split())
            query_words = set(w.lower() for w in base_query.split())
            new_words = cat_words - query_words
            if new_words:
                # Take at most 2 new words from the category
                suffix = " ".join(list(new_words)[:2]).title()
                boosted = f"{base_query} {suffix}"
                if len(boosted) <= 80:
                    return boosted
        
        return base_query
    except Exception:
        return base_query


def extract_visual_query_rake_yake(paragraph, used_queries):
    """
    MODE 1 (Default): Extract visually meaningful search queries using RAKE + YAKE.
    
    Strategy:
    1. Use RAKE to find multi-word keyword phrases (ranked by score)
    2. Use YAKE to find single/bi-gram keywords (ranked by relevance)
    3. Merge results, prioritize proper nouns and concrete visual terms
    4. Build a coherent 3-6 word search query
    """
    if not paragraph or len(paragraph.strip()) < 5:
        return ""
    
    candidates = []
    
    # --- RAKE Extraction ---
    if HAS_RAKE:
        try:
            rake = Rake(
                min_length=1,
                max_length=3,  # Max 3-word phrases
                include_repeated_phrases=False
            )
            rake.extract_keywords_from_text(paragraph)
            # get_ranked_phrases_with_scores returns [(score, phrase), ...]
            rake_results = rake.get_ranked_phrases_with_scores()
            for score, phrase in rake_results[:10]:
                # Filter out phrases that are all filler
                words = phrase.lower().split()
                if not all(w in EXTRA_STOP_WORDS for w in words):
                    candidates.append(("rake", score, phrase))
        except Exception:
            pass
    
    # --- YAKE Extraction ---
    if HAS_YAKE:
        try:
            # YAKE: lower score = more relevant
            kw_extractor = yake.KeywordExtractor(
                lan="en",
                n=2,          # Up to bigrams
                top=10,
                dedupLim=0.5  # Deduplication threshold
            )
            yake_results = kw_extractor.extract_keywords(paragraph)
            for phrase, score in yake_results:
                words = phrase.lower().split()
                if not all(w in EXTRA_STOP_WORDS for w in words):
                    # Invert YAKE score so higher = better (like RAKE)
                    candidates.append(("yake", 1.0 / (score + 0.001), phrase))
        except Exception:
            pass
    
    # --- Proper Noun Boost ---
    # Find capitalized words that aren't at sentence starts
    proper_nouns = []
    sentences = re.split(r'[.!?]\s+', paragraph)
    for sentence in sentences:
        words = sentence.split()
        for i, word in enumerate(words):
            clean = re.sub(r'[^a-zA-Z]', '', word)
            if (clean and clean[0].isupper() and len(clean) >= 3 
                and i > 0  # Not sentence-start
                and clean.lower() not in EXTRA_STOP_WORDS):
                proper_nouns.append(clean)
    
    # --- Build Final Query ---
    if not candidates and not proper_nouns:
        # Absolute fallback: use simple frequency method
        return _fallback_frequency_extract(paragraph, used_queries)
    
    # Score and rank all candidates
    ranked = []
    for source, score, phrase in candidates:
        # Boost phrases containing proper nouns
        boost = 1.0
        for pn in proper_nouns:
            if pn.lower() in phrase.lower():
                boost = 2.5
                break
        
        # Boost phrases with concrete/visual words
        visual_indicators = [
            "chart", "graph", "diagram", "table", "plot", "histogram",
            "data", "formula", "equation", "model", "system", "machine",
            "market", "price", "cost", "money", "dollar", "income",
            "building", "house", "city", "car", "road", "bridge",
            "animal", "plant", "tree", "flower", "mountain", "ocean",
            "experiment", "laboratory", "chemical", "reaction", "energy",
            "computer", "software", "code", "algorithm", "network",
            "brain", "cell", "body", "organ", "muscle", "bone",
        ]
        for vi in visual_indicators:
            if vi in phrase.lower():
                boost *= 1.5
                break
        
        # Penalize very short phrases (1-2 chars after cleaning)
        clean_phrase = re.sub(r'[^a-zA-Z\s]', '', phrase).strip()
        if len(clean_phrase) < 4:
            boost *= 0.1
        
        ranked.append((score * boost, clean_phrase))
    
    # Sort by boosted score (highest first)
    ranked.sort(key=lambda x: x[0], reverse=True)
    
    # Take top phrases, combine with proper nouns
    query_parts = []
    seen_words = set()
    
    # Add top proper nouns first (up to 2)
    unique_proper = []
    for pn in proper_nouns:
        if pn.lower() not in seen_words:
            unique_proper.append(pn)
            seen_words.add(pn.lower())
    for pn in unique_proper[:2]:
        query_parts.append(pn)
    
    # Add top-ranked keyword phrases (up to fill ~50 chars)
    for score, phrase in ranked:
        if not phrase:
            continue
        # Skip if all words already in query
        phrase_words = set(w.lower() for w in phrase.split())
        if phrase_words.issubset(seen_words):
            continue
        
        query_parts.append(phrase.title())
        seen_words.update(phrase_words)
        
        current_len = len(" ".join(query_parts))
        if current_len >= 40 or len(query_parts) >= 4:
            break
    
    if not query_parts:
        return _fallback_frequency_extract(paragraph, used_queries)
    
    query = " ".join(query_parts).strip()
    
    # Truncate to reasonable length
    if len(query) > 80:
        query = query[:80].rsplit(" ", 1)[0]
    
    # Deduplication
    if query in used_queries:
        base = query
        counter = 1
        while query in used_queries:
            query = f"{base} {counter}"
            counter += 1
    
    used_queries.add(query)
    return query


def _fallback_frequency_extract(paragraph, used_queries):
    """Minimal fallback if RAKE/YAKE both unavailable and no proper nouns found."""
    # Basic stop words for fallback only
    basic_stops = set([
        "i", "me", "my", "we", "our", "you", "your", "he", "him", "his", "she", "her",
        "it", "its", "they", "them", "their", "what", "which", "who", "this", "that",
        "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "a", "an", "the", "and", "but",
        "if", "or", "because", "as", "until", "while", "of", "at", "by", "for",
        "with", "about", "into", "through", "during", "before", "after", "to", "from",
        "up", "down", "in", "out", "on", "off", "over", "under", "again", "then",
        "once", "here", "there", "when", "where", "why", "how", "all", "any", "both",
        "each", "more", "most", "other", "some", "such", "no", "not", "only", "own",
        "same", "so", "than", "too", "very", "can", "will", "just", "don", "should",
        "now", "s", "t",
    ])
    all_stops = basic_stops | EXTRA_STOP_WORDS
    
    words = re.findall(r'\b[a-zA-Z]{4,}\b', paragraph.lower())
    filtered = [w for w in words if w not in all_stops]
    counts = Counter(filtered)
    top = [word for word, _ in counts.most_common(4)]
    
    query = " ".join(top).title()
    if not query:
        return ""
    
    if query in used_queries:
        base = query
        counter = 1
        while query in used_queries:
            query = f"{base} {counter}"
            counter += 1
    
    used_queries.add(query)
    return query


# ============================================================
# MODE 2: LLM-Powered Query Generation (Ollama)
# ============================================================

def extract_visual_query_llm(paragraph, used_queries, model="gemma2:2b", ollama_url="http://localhost:11434"):
    """
    MODE 2 (--use-llm): Use a local Ollama LLM to generate image search queries.
    Falls back to RAKE/YAKE mode if Ollama is unreachable.
    """
    if not paragraph or len(paragraph.strip()) < 5:
        return ""
    
    prompt = (
        "Generate a concise 3-5 word image search query that would find a relevant, "
        "visual stock photo for this dialogue line. The query should describe a concrete, "
        "searchable visual scene or object. Return ONLY the search query, nothing else.\n\n"
        f"Dialogue: \"{paragraph[:500]}\"\n\n"
        "Search query:"
    )
    
    try:
        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 20,  # Keep responses very short
            }
        }).encode("utf-8")
        
        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            query = result.get("response", "").strip()
        
        # Clean up the LLM response
        # Remove quotes, asterisks, newlines, and any "Search query:" prefix the model might echo
        query = query.replace('"', '').replace("'", "").replace("*", "").strip()
        query = query.split("\n")[0].strip()  # Take only first line
        query = re.sub(r'^(search\s+query\s*:\s*)', '', query, flags=re.IGNORECASE).strip()
        
        # Validate: reject if too short, too long, or contains garbage
        if len(query) < 3 or len(query) > 100:
            print(f"  [LLM] Bad response length ({len(query)} chars), falling back to RAKE/YAKE")
            return extract_visual_query_rake_yake(paragraph, used_queries)
        
        # Truncate to reasonable length
        if len(query) > 80:
            query = query[:80].rsplit(" ", 1)[0]
        
        # Deduplication
        if query in used_queries:
            base = query
            counter = 1
            while query in used_queries:
                query = f"{base} {counter}"
                counter += 1
        
        used_queries.add(query)
        return query
        
    except Exception as e:
        print(f"  [LLM] Ollama request failed: {e}")
        print(f"  [LLM] Falling back to RAKE/YAKE extraction...")
        return extract_visual_query_rake_yake(paragraph, used_queries)

# ============================================================
# MODE 3: Gemini Cloud LLM Generation
# ============================================================

def extract_visual_query_gemini(paragraph, used_queries, api_key):
    """
    MODE 3 (--use-gemini): Use Google Gemini API to generate image search queries.
    Falls back to spaCy/Smart mode if the request fails.
    """
    if not paragraph or len(paragraph.strip()) < 5:
        return ""
        
    prompt = (
        "Generate a concise 3-5 word image search query that would find a relevant, "
        "visual stock photo for this dialogue line. The query should describe a concrete, "
        "searchable visual scene or object. Return ONLY the search query, nothing else.\n\n"
        f"Dialogue: \"{paragraph[:500]}\"\n\n"
        "Search query:"
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = json.dumps({
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 20
        }
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            
            # Navigate Gemini JSON structure
            candidates = result.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned from Gemini")
                
            query = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
            
        # Clean up the LLM response
        query = query.replace('"', '').replace("'", "").replace("*", "").strip()
        query = query.split("\n")[0].strip()
        query = re.sub(r'^(search\s+query\s*:\s*)', '', query, flags=re.IGNORECASE).strip()
        
        if len(query) < 3 or len(query) > 100:
            print(f"  [Gemini] Bad response length ({len(query)} chars), falling back to Smart mode")
            return extract_visual_query_spacy(paragraph, used_queries) if HAS_SPACY else extract_visual_query_rake_yake(paragraph, used_queries)
            
        if len(query) > 80:
            query = query[:80].rsplit(" ", 1)[0]
            
        if query in used_queries:
            base = query
            counter = 1
            while query in used_queries:
                query = f"{base} {counter}"
                counter += 1
                
        used_queries.add(query)
        return query
        
    except Exception as e:
        print(f"  [Gemini] API request failed: {e}")
        print(f"  [Gemini] Falling back to Smart mode...")
        return extract_visual_query_spacy(paragraph, used_queries) if HAS_SPACY else extract_visual_query_rake_yake(paragraph, used_queries)



# ============================================================
# MODE 4: KeyBERT-Powered Query Generation
# ============================================================

def extract_visual_query_keybert(paragraph, used_queries):
    """
    MODE 4 (--use-keybert): Use KeyBERT BERT-embedding keyword extraction.
    Extracts the most semantically relevant keywords from the paragraph.
    Falls back to spaCy/RAKE if KeyBERT is unavailable.
    """
    if not paragraph or len(paragraph.strip()) < 5 or KBERT_MODEL is None:
        return extract_visual_query_spacy(paragraph, used_queries) if HAS_SPACY else extract_visual_query_rake_yake(paragraph, used_queries)
    
    try:
        # Extract keywords: mix of unigrams, bigrams, and trigrams
        keywords = KBERT_MODEL.extract_keywords(
            paragraph,
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            top_n=8,
            use_mmr=True,        # Maximal Marginal Relevance for diversity
            diversity=0.5
        )
        
        if not keywords:
            return extract_visual_query_spacy(paragraph, used_queries) if HAS_SPACY else extract_visual_query_rake_yake(paragraph, used_queries)
        
        # keywords is [(keyword, score), ...]
        query_parts = []
        seen_words = set()
        
        for kw, score in keywords:
            # Skip filler words
            words = kw.lower().split()
            if all(w in EXTRA_STOP_WORDS for w in words):
                continue
            
            # Skip if all words already in query
            kw_words = set(w.lower() for w in kw.split())
            if kw_words.issubset(seen_words):
                continue
            
            query_parts.append(kw.title())
            seen_words.update(kw_words)
            
            current_len = len(" ".join(query_parts))
            if current_len >= 40 or len(query_parts) >= 3:
                break
        
        if not query_parts:
            return extract_visual_query_spacy(paragraph, used_queries) if HAS_SPACY else extract_visual_query_rake_yake(paragraph, used_queries)
        
        query = " ".join(query_parts).strip()
        
        if len(query) > 80:
            query = query[:80].rsplit(" ", 1)[0]
        
        # Deduplication
        if query in used_queries:
            base = query
            counter = 1
            while query in used_queries:
                query = f"{base} {counter}"
                counter += 1
        
        used_queries.add(query)
        return query
        
    except Exception as e:
        print(f"  [KeyBERT] Extraction failed: {e}")
        return extract_visual_query_spacy(paragraph, used_queries) if HAS_SPACY else extract_visual_query_rake_yake(paragraph, used_queries)


# ============================================================
# FILE PROCESSING
# ============================================================

def process_file(filename, mode="smart", llm_model="gemma2:2b", ollama_url="http://localhost:11434", gemini_api_key=None, use_semantic=False):
    """
    Process a transcript .txt file into a JSON file with image_search fields.
    
    Modes:
        "smart"     - RAKE/YAKE noun-phrase extraction (default)
        "keybert"   - KeyBERT BERT-embedding extraction
        "llm"       - Ollama LLM-powered generation
        "gemini"    - Gemini Cloud LLM generation
        "paragraph" - Use full paragraph text as-is
    """
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return

    print(f"Processing {filename}...")
    
    mode_labels = {
        "smart": "Smart Extraction (spaCy/RAKE/YAKE)",
        "keybert": "KeyBERT Extraction",
        "llm": f"Ollama LLM ({llm_model})",
        "gemini": "Gemini Cloud LLM",
        "paragraph": "Full Paragraph Text",
    }
    print(f"  [Mode] {mode_labels.get(mode, mode)}")
    
    if mode == "gemini":
        if not gemini_api_key:
            print("  [Gemini] Error: API key is required for Gemini mode.")
            print("  [Gemini] Pass --gemini-api-key or set GEMINI_API_KEY env var.")
            print("  [Gemini] Falling back to Smart mode.")
            mode = "smart"
    
    if mode == "keybert":
        if not HAS_KEYBERT:
            print("  [KeyBERT] Warning: keybert not installed. Falling back to Smart mode.")
            print("  [KeyBERT] Install with: pip install keybert")
            mode = "smart"
    
    # If using LLM mode, test Ollama connectivity first
    if mode == "llm":
        try:
            req = urllib.request.Request(f"{ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                models_data = json.loads(resp.read().decode("utf-8"))
                available_models = [m.get("name", "") for m in models_data.get("models", [])]
             
                # Check if requested model is available
                model_found = any(llm_model in m for m in available_models)
                if not model_found:
                    print(f"  [LLM] Warning: Model '{llm_model}' not found in Ollama.")
                    print(f"  [LLM] Available models: {available_models}")
                    print(f"  [LLM] Falling back to RAKE/YAKE mode.")
                    mode = "smart"
                else:
                    print(f"  [LLM] Connected to Ollama. Model '{llm_model}' is available.")
        except Exception as e:
            print(f"  [LLM] Cannot connect to Ollama at {ollama_url}: {e}")
            print(f"  [LLM] Is Ollama running? Try: ollama serve")
            print(f"  [LLM] Falling back to RAKE/YAKE mode.")
            mode = "smart"
    
    # Print library status for smart mode
    if mode == "smart":
        libs = []
        if HAS_SPACY: libs.append("spaCy")
        if HAS_RAKE: libs.append("RAKE")
        if HAS_YAKE: libs.append("YAKE")
        if use_semantic and HAS_SBERT: libs.append("Semantic Boost")
        if libs:
            print(f"  [Smart] Using: {' + '.join(libs)}")
        else:
            print(f"  [Smart] Warning: No advanced extractors installed. Using basic fallback.")
            print(f"  [Smart] Install with: pip install spacy rake-nltk yake")
        if use_semantic and not HAS_SBERT:
            print(f"  [Semantic] Warning: sentence-transformers not installed. Semantic boost disabled.")
            print(f"  [Semantic] Install with: pip install sentence-transformers")
    
    # Try multiple encodings
    lines = None
    for enc in ['utf-8-sig', 'utf-16', 'utf-8']:
        try:
            with open(filename, 'r', encoding=enc) as f:
                lines = f.readlines()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if lines is None:
        print(f"  [Error] Could not decode {filename} with any known encoding. Skipping.")
        return

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
            
            # Generate image_search based on mode
            if mode == "paragraph":
                image_search = paragraph
            elif mode == "llm":
                image_search = extract_visual_query_llm(
                    paragraph, used_queries, 
                    model=llm_model, ollama_url=ollama_url
                )
            elif mode == "gemini":
                image_search = extract_visual_query_gemini(
                    paragraph, used_queries, api_key=gemini_api_key
                )
            elif mode == "keybert":
                image_search = extract_visual_query_keybert(paragraph, used_queries)
            else:  # "smart" (default)
                if HAS_SPACY:
                    image_search = extract_visual_query_spacy(paragraph, used_queries)
                else:
                    image_search = extract_visual_query_rake_yake(paragraph, used_queries)
                
                # Apply semantic similarity boost if enabled
                if use_semantic and image_search:
                    image_search = _semantic_boost(paragraph, image_search)
            
            # If the paragraph is just filler, reuse previous entry's search
            if not image_search and entries:
                image_search = entries[-1]["image_search"]
            # Failsafe for first line
            if not image_search:
                image_search = "Abstract Background Texture"
            
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
    parser = argparse.ArgumentParser(
        description="Auto-segment transcripts into JSON for the video pipeline.",
        epilog="""
Modes:
  (default)        spaCy (or RAKE/YAKE) smart noun-chunk extraction (best quality, no network needed)
  --use-keybert    Use KeyBERT BERT-embedding keyword extraction (high quality, no network needed)
  --use-semantic   Add semantic similarity boost to Smart mode (appends best visual category)
  --use-gemini     Use Google Gemini Cloud LLM for intelligent query generation (requires API key)
  --use-llm        Use local Ollama LLM for intelligent query generation
  --use-paragraph  Use the raw paragraph text as-is (simple, no processing)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "files", nargs="*",
        help="Specific .txt files to process. If none given, processes all unprocessed .txt files."
    )
    parser.add_argument(
        "--use-paragraph",
        action="store_true",
        help="Use the full paragraph text as the 'image_search' field"
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use local Ollama LLM to generate image search queries (requires Ollama running)"
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default="gemma2:2b",
        help="Ollama model to use for LLM mode (default: gemma2:2b)"
    )
    parser.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama API URL (default: http://localhost:11434)"
    )
    parser.add_argument(
        "--use-gemini",
        action="store_true",
        help="Use Google Gemini API to generate image search queries"
    )
    parser.add_argument(
        "--gemini-api-key",
        type=str,
        default=os.environ.get("GEMINI_API_KEY", ""),
        help="Gemini API Key (can also be set via GEMINI_API_KEY environment variable)"
    )
    parser.add_argument(
        "--use-semantic",
        action="store_true",
        help="Enable semantic similarity boost for Smart mode (appends best visual category match)"
    )
    parser.add_argument(
        "--use-keybert",
        action="store_true",
        help="Use KeyBERT BERT-embedding keyword extraction instead of RAKE/YAKE"
    )
    args = parser.parse_args()

    # Determine mode
    if args.use_gemini:
        mode = "gemini"
    elif args.use_keybert:
        mode = "keybert"
    elif args.use_llm:
        mode = "llm"
    elif args.use_paragraph:
        mode = "paragraph"
    else:
        mode = "smart"

    if args.files:
        files_to_process = args.files
    else:
        # Auto-discover unprocessed .txt files
        files_to_process = [f for f in os.listdir('.') if f.endswith('.txt') and not f.startswith('done ')]
        if not files_to_process:
            print("No unprocessed .txt files found in the current directory. Pass filenames as arguments.")
            sys.exit(1)

    for f in files_to_process:
        process_file(f, mode=mode, llm_model=args.llm_model, ollama_url=args.ollama_url, gemini_api_key=args.gemini_api_key, use_semantic=args.use_semantic)
