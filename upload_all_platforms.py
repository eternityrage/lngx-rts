import os, sys, json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

upload_dir = Path(__file__).parent / "upload"
if upload_dir.exists() and str(upload_dir) not in sys.path:
    sys.path.insert(0, str(upload_dir))

upload_to_facebook = None
upload_to_instagram = None
upload_to_youtube = None

try:
    from upload_facebook import upload_to_facebook as fb_upload
    upload_to_facebook = fb_upload
except ImportError:
    pass
try:
    from upload_instagram import upload_to_instagram as ig_upload
    upload_to_instagram = ig_upload
except ImportError:
    pass
try:
    from upload_to_youtube import upload_to_youtube as yt_upload
    upload_to_youtube = yt_upload
except ImportError:
    pass

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

def upload_to_all_platforms(video_path, caption, word, reel_data=None):
    results = {"timestamp": datetime.now().isoformat(), "word": word, "video": video_path, "uploads": {}, "platforms_attempted": [], "platforms_successful": [], "platforms_skipped": [], "platforms_failed": []}
    print(f"\n{'='*80}\n{CHANNEL_NAME.upper()} - MULTI-PLATFORM UPLOAD\n{'='*80}")
    if not Path(video_path).exists():
        return results
    platforms = [("facebook", upload_to_facebook, "Facebook"), ("instagram", upload_to_instagram, "Instagram"), ("youtube", upload_to_youtube, "YouTube")]
    for platform_name, upload_func, display_name in platforms:
        print(f"\n{display_name} UPLOAD...")
        results["platforms_attempted"].append(platform_name)
        if upload_func:
            try:
                if platform_name == "facebook":
                    upload_result = upload_func(video_path=video_path, description=caption, title=f"Word Root: {word}")
                elif platform_name == "instagram":
                    upload_result = upload_func(video_path=video_path, caption=caption, is_story=False)
                elif platform_name == "youtube":
                    from upload_to_youtube import generate_video_metadata
                    yt_title, yt_description, yt_tags = generate_video_metadata(reel_data.get("words", []), reel_data)
                    upload_result = upload_func(video_path=video_path, title=yt_title, description=yt_description, tags=yt_tags, category_id='27')
                if upload_result:
                    results["uploads"][platform_name] = upload_result
                    results["platforms_successful"].append(platform_name)
                else:
                    results["platforms_failed"].append(platform_name)
            except Exception as e:
                results["uploads"][platform_name] = {"status": "failed", "error": str(e)}
                results["platforms_failed"].append(platform_name)
        else:
            results["platforms_skipped"].append(platform_name)
    print(f"\nSuccessful: {len(results['platforms_successful'])}, Failed: {len(results['platforms_failed'])}, Skipped: {len(results['platforms_skipped'])}")
    return results

def main():
    reel = get_latest_reel()
    if not reel:
        print("No reel found! Run lingexa_roots_bot.py first.")
        sys.exit(1)
    caption = generate_caption(reel, platform="facebook")
    print(f"Caption ({len(caption)} chars)")
    print(caption[:500])
    upload_to_all_platforms(reel['video_path'], caption, reel['word'], reel)

if __name__ == "__main__":
    main()
