"""
YouTube Upload - Lingexa Roots
"""

import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv()
CHANNEL_NAME = "Lingexa Roots"

def get_auth():
    cid = (os.getenv('YOUTUBE_CLIENT_ID') or os.getenv('YT_CLIENT_ID', '')).strip()
    csec = (os.getenv('YOUTUBE_CLIENT_SECRET') or os.getenv('YT_CLIENT_SECRET', '')).strip()
    rt = (os.getenv('YOUTUBE_REFRESH_TOKEN') or os.getenv('YT_REFRESH_TOKEN', '')).strip()
    if not all([cid, csec, rt]):
        raise ValueError("Missing YouTube credentials!")
    creds = Credentials(None, refresh_token=rt, token_uri="https://oauth2.googleapis.com/token", client_id=cid, client_secret=csec, scopes=["https://www.googleapis.com/auth/youtube"])
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)

def generate_video_metadata(words_data, reel_data=None):
    if not words_data:
        return f"Word Roots - {CHANNEL_NAME}", f"Learn word roots with {CHANNEL_NAME}!", ["word roots", "vocabulary", CHANNEL_NAME.replace(' ', '')]
    root = words_data[0].get("root", "")
    root_m = words_data[0].get("root_meaning", "")
    first_words = [w.get("word", "") for w in words_data[:3]]
    title = f"3 Words from ONE Root: {root.upper()} = {root_m.upper()} - {', '.join(first_words)}"
    lines = [f"🌱 Learn 3 words from the root {root.upper()} ({root_m.upper()}) with {CHANNEL_NAME}!", f""]
    for i, w in enumerate(words_data, 1):
        word = w.get("word", "")
        pos = w.get("part_of_speech", "")
        definition = w.get("definition", "")
        example = w.get("example", "")
        expl = w.get("explanation", "")
        lines.append(f"{i}. {word.upper()} ({pos})")
        lines.append(f"   Definition: {definition}")
        lines.append(f"   Example: {example}")
        if expl:
            lines.append(f"   💡 {expl}")
        lines.append(f"")
    lines.extend([f"=== ABOUT {CHANNEL_NAME.upper()} ===", f"", f"Learn one root, unlock dozens of words!", f"🔔 Subscribe for daily root word lessons!", f"", f"=== HASHTAGS ===", f"#LingexaRoots #WordRoots #Vocabulary #LearnEnglish #Etymology #RootWords #ESL #Shorts"])
    return title, "\n".join(lines), ["word roots", "vocabulary", "learn english", "etymology", "root words", "english vocabulary", "esl", CHANNEL_NAME.replace(' ', '').lower(), root] + [w.get("word", "").lower() for w in words_data[:5]]

def upload_to_youtube(video_path, title, description, tags=None, category_id='27'):
    if tags is None:
        tags = ['word roots', 'vocabulary', CHANNEL_NAME.replace(' ', '').lower()]
    yt = get_auth()
    body = {'snippet': {'title': title, 'description': description, 'tags': tags, 'categoryId': category_id}, 'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}}
    media = MediaFileUpload(video_path, chunksize=1024*1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
    print(f"[youtube] Uploaded! Video ID: {resp.get('id')}")
    return {"status": "success", "video_id": resp.get('id'), "title": title}
