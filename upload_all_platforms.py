"""
Lingexa Roots - Upload Script
"""

import os, sys, json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
upload_dir = Path(__file__).parent / "upload"
if upload_dir.exists() and str(upload_dir) not in sys.path:
    sys.path.insert(0, str(upload_dir))

CHANNEL_NAME = "Lingexa Roots"

def get_latest_reel():
    video_dir = Path("output/video")
    if not video_dir.exists():
        return None
    reels = list(video_dir.glob("*/final_reel.mp4"))
    if not reels:
        return None
    latest = max(reels, key=lambda p: p.stat().st_mtime)
    metadata_file = latest.parent / "metadata.json"
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    words_data = metadata.get("words", [])
    all_words = [w.get("word", "") for w in words_data]
    return {"video_path": str(latest), "metadata": metadata, "words": words_data, "all_words": all_words, "word": all_words[0] if all_words else "Roots"}

def generate_caption(reel_data, platform="facebook"):
    words = reel_data.get("words", [])
    if not words:
        return f"Learn word roots with {CHANNEL_NAME}! #LingexaRoots"
    if platform == "facebook":
        lines = [f"🌱 Unlock 3 Words from ONE Root with {CHANNEL_NAME}!", f""]
        root = words[0].get("root", "")
        root_m = words[0].get("root_meaning", "")
        if root:
            lines.append(f"Root: {root.upper()} = {root_m.upper()}")
            lines.append(f"")
        for i, w in enumerate(words, 1):
            word = w.get("word", "")
            pos = w.get("part_of_speech", "")
            definition = w.get("definition", "")
            example = w.get("example", "")
            expl = w.get("explanation", "")
            lines.append(f"{i}. {word.upper()} ({pos})")
            lines.append(f"   → {definition}")
            lines.append(f"   Example: {example}")
            if expl:
                lines.append(f"   💡 {expl}")
            lines.append(f"")
        lines.extend([f"💡 Learn one root, unlock dozens of words!", f"🔔 Follow {CHANNEL_NAME} for daily word roots!", f"", f"#LingexaRoots #WordRoots #Vocabulary #LearnEnglish #Etymology #EnglishVocabulary #RootWords #ESL #LanguageLearning"])
    else:
        lines = [f"🌱 3 words from one root!", f""]
        for i, w in enumerate(words[:3], 1):
            lines.append(f"{i}. {w['word']}")
        lines.extend([f"", f"#LingexaRoots #WordRoots #Vocabulary"])
    return "\n".join(lines)

def main():
    reel = get_latest_reel()
    if not reel:
        print("No reel found!")
        sys.exit(1)
    caption = generate_caption(reel, platform="facebook")
    print(f"Caption ({len(caption)} chars)")
    print(caption[:500])

if __name__ == "__main__":
    main()
