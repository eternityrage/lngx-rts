"""
Lingexa Roots - Unlock English Word Roots
One root unlocks dozens of words
"""

import os, sys, json, random, asyncio, subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
AI_MODEL = os.getenv("AI_MODEL")
if not AI_MODEL:
    raise ValueError("AI_MODEL not set!")

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
for d in [OUTPUT_DIR, VIDEO_DIR, HISTORY_DIR]:
    d.mkdir(exist_ok=True)

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
TTS_VOICE = "en-US-GuyNeural"
CHANNEL_NAME = "Lingexa Roots"
WORDS_PER_VIDEO = 3
WORD_HISTORY_FILE = HISTORY_DIR / "all_generated_words.json"
FONTS_DIR = Path(__file__).parent / "fonts"

def load_word_history():
    if WORD_HISTORY_FILE.exists():
        with open(WORD_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"words": [], "last_updated": None}

def save_word_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(WORD_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def is_word_used(word):
    history = load_word_history()
    return word.lower().strip() in [w.lower().strip() for w in history.get("words", [])]

def add_words_to_history(words):
    history = load_word_history()
    existing = [w.lower().strip() for w in history.get("words", [])]
    for w in words:
        wl = w.lower().strip()
        if wl not in existing:
            history["words"].append(wl)
            existing.append(wl)
    save_word_history(history)

def generate_word_data(num_words=WORDS_PER_VIDEO):
    max_attempts = 20
    categories = [
        "Latin roots (bene, mal, dict, duct, struct)",
        "Greek roots (bio, geo, hydro, photo, graph)",
        "Latin roots (port, form, tract, vent, press)",
        "Greek roots (logos, pathos, ethos, chronos)",
        "Latin roots (cede, ceed, gress, spect, scrib)",
        "Greek roots (phone, scope, techno, mega)",
        "Latin roots (fac, fact, fect, flict, flex)",
        "Latin roots (aud, voc, spir, aqua, cent)",
    ]
    collected = []
    for attempt in range(max_attempts):
        try:
            import requests
            url = "https://gen.pollinations.ai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}", "Content-Type": "application/json"}
            cat = categories[attempt % len(categories)]
            remaining = num_words - len(collected)
            print(f"[api] Attempt {attempt + 1}: {cat} (need {remaining} more)")
            history = load_word_history()
            all_used = history.get("words", [])
            used_set = set()
            for w in all_used:
                used_set.add(w.lower().strip())
            used_set.update([w["word"].lower().strip() for w in collected])
            context = list(used_set)[-50:] if len(used_set) > 50 else list(used_set)
            used_str = ", ".join(context) if context else "(none)"
            prompt = f"""Generate exactly 15 English words from {cat}.

STRICT RULES:
- NEVER repeat: {used_str}
- All words must share the SAME root
- Return ONLY a valid JSON array
- KEEP SHORT: definition max 8 words, example max 8 words

CRITICAL for 'explanation': Write a SHORT natural sentence explaining BOTH the root AND the rest of the word. NO symbols, NO arrows, NO equals signs. Plain English only.
Good example: "Bene means good and volence means wishing, so benevolence is wishing good upon others."
Good example: "Mal means bad and volent means wishing, so malevolent describes someone who wishes bad things."
Bad example: "bene=good so benevolence means good"
Bad example: "Mal means bad, so a malady is a bad condition." (only explains root, not the whole word)

Format:
[{{"word":"benevolence","root":"bene","root_meaning":"good","part_of_speech":"noun","definition":"kindness and charity","example":"She showed benevolence.","explanation":"Bene means good and volence means wishing, so benevolence is wishing good upon others."}}]

Return ONLY the JSON array.""" 
            payload = {"model": AI_MODEL, "messages": [{"role": "system", "content": "Return ONLY valid JSON arrays."}, {"role": "user", "content": prompt}], "temperature": 1.2}
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            words = json.loads(content)
            if not isinstance(words, list):
                raise ValueError("Not a list")
            fresh = []
            for w in words:
                word = w.get("word", "").strip()
                if not word:
                    continue
                if len(word.split()) > 1:
                    continue
                if word.lower().strip() in used_set:
                    continue
                fresh.append(w)
                used_set.add(word.lower().strip())
                if len(collected) + len(fresh) >= num_words:
                    break
            collected.extend(fresh)
            if len(collected) >= num_words:
                add_words_to_history([w["word"] for w in collected[:num_words]])
                return collected[:num_words]
        except Exception as e:
            print(f"[api] Attempt {attempt + 1} FAILED: {e}")
    if collected:
        add_words_to_history([w["word"] for w in collected])
        return collected
    raise RuntimeError("API failed all attempts")

def create_background():
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 245, 250, 245
        else:
            r = int(245 + (238 - 245) * ((ratio - 0.5) * 2))
            g = int(250 + (245 - 250) * ((ratio - 0.5) * 2))
            b = int(245 + (240 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img

async def gen_audio(text, voice, path):
    try:
        import edge_tts
        await edge_tts.Communicate(text, voice).save(path)
        return True
    except:
        return False

async def gen_audio_retry(text, voice, path, retries=3):
    for a in range(1, retries + 1):
        ok = await gen_audio(text, voice, path)
        if ok and Path(path).exists() and Path(path).stat().st_size > 100:
            return True
        await asyncio.sleep(2 * a)
    return False

def get_audio_duration(file):
    if not Path(file).exists():
        return 2.0
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except:
        return 2.0

def generate_all_audio(words, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []
    total = 0.0
    for i, w in enumerate(words):
        word = w["word"]
        pos = w.get("part_of_speech", "")
        definition = w.get("definition", "")
        example = w.get("example", "")
        root_m = w.get("root", "")
        root_mean = w.get("root_meaning", "")
        expl = w.get("explanation", "")
        text = f"{word}. {pos}. {definition}. Example: {example}."
        if root_m and root_mean:
            text += f" The root {root_m} means {root_mean}."
        if expl:
            clean_expl = expl.replace("→", "which means").replace("=", "means").replace("+", "plus")
            text += f" {clean_expl}."
        fp = out_dir / f"w_{i}.mp3"
        ok = asyncio.run(gen_audio_retry(text, TTS_VOICE, str(fp)))
        if not ok:
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "5", str(fp)], capture_output=True)
        dur = get_audio_duration(str(fp))
        audio_files.append({"file": str(fp), "duration": dur})
        total += dur + 0.3
    print(f"[audio] {len(audio_files)} words, {total:.1f}s")
    return audio_files, total

def create_final_audio(audio_files, out_file):
    od = Path(out_file).parent
    parts = []
    for i, af in enumerate(audio_files):
        p = od / f"pd_{i}.mp3"
        subprocess.run(["ffmpeg", "-y", "-i", str(af["file"]), "-af", "apad=pad_dur=0.3", "-ar", "24000", "-ac", "1", "-c:a", "libmp3lame", str(p)], capture_output=True)
        parts.append(p)
    cl = od / "cl.txt"
    with open(cl, "w") as f:
        for part in parts:
            f.write(f"file '{str(part.resolve()).replace(chr(92), chr(47))}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(cl), "-c:a", "libmp3lame", str(out_file)], capture_output=True)
    for p in parts:
        if p.exists(): p.unlink()
    if cl.exists(): cl.unlink()
    return Path(out_file).exists() and Path(out_file).stat().st_size > 100

def wrap_text(draw, text, font, max_w):
    words = text.split()
    lines = []
    cur = []
    for w in words:
        t = ' '.join(cur + [w])
        if draw.textbbox((0, 0), t, font=font)[2] <= max_w or not cur:
            cur.append(w)
        else:
            lines.append(' '.join(cur))
            cur = [w]
    if cur:
        lines.append(' '.join(cur))
    return lines

def generate_word_image(word_data, bg_image, out_path):
    from PIL import Image, ImageDraw, ImageFont

    img = bg_image.copy().convert('RGBA')
    draw = ImageDraw.Draw(img)

    MX = 90
    CX = VIDEO_WIDTH // 2
    CW = VIDEO_WIDTH - MX * 2

    FONT_BOLD = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf","/usr/share/fonts/noto/NotoSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf","C:/Windows/Fonts/segoeuib.ttf",
    ]
    FONT_REG = [
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf","/usr/share/fonts/noto/NotoSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf","C:/Windows/Fonts/segoeui.ttf",
    ]

    def lf(paths, sz):
        for p in paths:
            try:
                f = ImageFont.truetype(p, sz)
                if draw.textbbox((0, 0), "AW", font=f)[2] > sz * 0.5:
                    return f
            except:
                continue
        return ImageFont.load_default()

    f_head = lf(FONT_BOLD, 65)
    f_root_badge = lf(FONT_BOLD, 44)
    f_root_mean = lf(FONT_REG, 36)
    f_word = lf(FONT_BOLD, 150)
    f_pos = lf(FONT_BOLD, 50)
    f_dlab = lf(FONT_BOLD, 42)
    f_def = lf(FONT_REG, 62)
    f_exlab = lf(FONT_BOLD, 42)
    f_ex = lf(FONT_REG, 50)
    f_explab = lf(FONT_BOLD, 38)
    f_exp = lf(FONT_REG, 44)
    f_foot = lf(FONT_BOLD, 40)

    word = word_data["word"].upper()
    pos = word_data.get("part_of_speech", "")
    definition = word_data.get("definition", "")
    example = word_data.get("example", "")
    root = word_data.get("root", "")
    root_meaning = word_data.get("root_meaning", "")
    explanation = word_data.get("explanation", "")

    H = (30, 70, 40)
    W = (20, 55, 30)
    DB = (35, 80, 50)
    EB = (180, 215, 190)
    L = (50, 90, 60)

    draw.rectangle([(0, 0), (VIDEO_WIDTH, 90)], fill=H)
    draw.text((CX, 45), CHANNEL_NAME.upper(), fill=(255, 255, 255), font=f_head, anchor="mm")

    y = 260

    MAX_WW = CW
    fs = 150
    wf = lf(FONT_BOLD, fs)
    ww = draw.textbbox((0, 0), word, font=wf)[2]
    while ww > MAX_WW and fs > 40:
        fs -= 5
        wf = lf(FONT_BOLD, fs)
        ww = draw.textbbox((0, 0), word, font=wf)[2]
    wh = draw.textbbox((0, 0), "Ay", font=wf)[3] - draw.textbbox((0, 0), "Ay", font=wf)[1]
    draw.text((CX, y + wh // 2), word, fill=W, font=wf, anchor="mm", stroke_width=max(1, fs // 40), stroke_fill=(210, 225, 210))
    y += wh + 40

    if root and root_meaning:
        root_text = f"{root.upper()} = {root_meaning.upper()}"
        rb = draw.textbbox((0, 0), root_text, font=f_root_badge)
        rw = rb[2] - rb[0]
        rh = rb[3] - rb[1]
        draw.rounded_rectangle([(CX - rw // 2 - 14, y), (CX + rw // 2 + 14, y + rh + 18)], radius=10, fill=(50, 110, 70))
        draw.text((CX, y + rh // 2 + 9), root_text, fill=(255, 255, 255), font=f_root_badge, anchor="mm")
        y += rh + 55

    if pos:
        pb = draw.textbbox((0, 0), pos.upper(), font=f_pos)
        pw = pb[2] - pb[0]
        ph = pb[3] - pb[1]
        draw.rounded_rectangle([(CX - pw // 2 - 18, y), (CX + pw // 2 + 18, y + ph + 18)], radius=10, fill=(60, 100, 75))
        draw.text((CX, y + ph // 2 + 9), pos.upper(), fill=(220, 255, 220), font=f_pos, anchor="mm")
        y += ph + 60

    draw.text((MX, y), "MEANING", fill=L, font=f_dlab, anchor="lm")
    y += 55

    dl = wrap_text(draw, definition, f_def, CW - 60)
    while len(dl) > 2 and f_def.size > 36:
        f_def = lf(FONT_REG, f_def.size - 4)
        dl = wrap_text(draw, definition, f_def, CW - 60)
    lh = draw.textbbox((0, 0), "A", font=f_def)[3] - draw.textbbox((0, 0), "A", font=f_def)[1]
    ls = int(lh * 1.5)
    th = (len(dl) - 1) * ls + lh
    pd = 40
    bh = th + pd * 2
    box = Image.new('RGBA', (CW, bh), DB + (255,))
    bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([(0, 0), (CW, bh)], radius=16, fill=DB + (255,))
    for i, line in enumerate(dl):
        ly = pd + (i * ls) + (lh // 2)
        bd.text((CW // 2, ly), line, fill=(255, 255, 255), font=f_def, anchor="mm")
    img.paste(box, (MX, y), box)
    y += bh + 55

    draw.text((MX, y), "EXAMPLE", fill=L, font=f_exlab, anchor="lm")
    y += 55

    el = wrap_text(draw, example, f_ex, CW - 60)
    while len(el) > 2 and f_ex.size > 30:
        f_ex = lf(FONT_REG, f_ex.size - 4)
        el = wrap_text(draw, example, f_ex, CW - 60)
    elh = draw.textbbox((0, 0), "A", font=f_ex)[3] - draw.textbbox((0, 0), "A", font=f_ex)[1]
    els = int(elh * 1.5)
    eth = (len(el) - 1) * els + elh
    epd = 35
    ebh = eth + epd * 2
    ebox = Image.new('RGBA', (CW, ebh), (180, 215, 190, 220))
    ed = ImageDraw.Draw(ebox)
    ed.rounded_rectangle([(0, 0), (CW, ebh)], radius=14, fill=(180, 215, 190, 220))
    for i, line in enumerate(el):
        ly = epd + (i * els) + (elh // 2)
        ed.text((CW // 2, ly), line, fill=(20, 55, 30), font=f_ex, anchor="mm")
    img.paste(ebox, (MX, y), ebox)
    y += ebh + 50

    if explanation and y < VIDEO_HEIGHT - 200:
        draw.text((MX, y), "HOW IT WORKS", fill=L, font=f_explab, anchor="lm")
        y += 50
        expl = wrap_text(draw, explanation, f_exp, CW - 60)
        while len(expl) > 2 and f_exp.size > 28:
            f_exp = lf(FONT_REG, f_exp.size - 4)
            expl = wrap_text(draw, explanation, f_exp, CW - 60)
        xlh = draw.textbbox((0, 0), "A", font=f_exp)[3] - draw.textbbox((0, 0), "A", font=f_exp)[1]
        xls = int(xlh * 1.5)
        xth = (len(expl) - 1) * xls + xlh
        xpd = 30
        xbh = xth + xpd * 2
        xbox = Image.new('RGBA', (CW, xbh), (220, 235, 220, 200))
        xd = ImageDraw.Draw(xbox)
        xd.rounded_rectangle([(0, 0), (CW, xbh)], radius=12, fill=(220, 235, 220, 200))
        for i, line in enumerate(expl):
            ly = xpd + (i * xls) + (xlh // 2)
            xd.text((CW // 2, ly), line, fill=(30, 70, 40), font=f_exp, anchor="mm")
        img.paste(xbox, (MX, y), xbox)

    draw.rectangle([(0, VIDEO_HEIGHT - 65), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=H)
    draw.text((CX, VIDEO_HEIGHT - 32), f"Unlock word roots daily  |  {CHANNEL_NAME}", fill=(200, 230, 210), font=f_foot, anchor="mm")

    img = img.convert('RGB')
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=96, optimize=True)
    print(f"[image] {Path(out_path).name}")
    return out_path

def create_video(image_files, audio_files, out_file):
    print(f"[video] {len(image_files)} images...")
    clips = []
    for i, (ip, ai) in enumerate(zip(image_files, audio_files)):
        tc = Path(out_file).parent / f"c_{i}.mp4"
        d = ai["duration"]
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(ip), "-i", str(ai["file"]),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
            "-t", f"{d}", "-shortest", str(tc)], capture_output=True)
        ad = get_audio_duration(str(tc))
        print(f"  Clip {i+1}: {ad:.1f}s")
        clips.append(tc)
    if not clips:
        return False
    cf = Path(out_file).parent / "cl.txt"
    with open(cf, "w") as f:
        for c in clips:
            f.write(f"file '{str(c.resolve()).replace(chr(92), chr(47))}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(cf), "-c", "copy", str(out_file)], capture_output=True)
    for c in clips:
        if c.exists(): c.unlink()
    if cf.exists(): cf.unlink()
    print(f"[video] {Path(out_file).name}")
    return True

def generate_reel():
    print(f"\n{'='*80}\n  {CHANNEL_NAME.upper()}\n{'='*80}\n")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rd = VIDEO_DIR / f"roots_{ts}"
    rd.mkdir()
    print("[1/3] Generating words from a common root...")
    words = generate_word_data(WORDS_PER_VIDEO)
    for i, w in enumerate(words, 1):
        r = w.get("root", "?")
        rm = w.get("root_meaning", "")
        print(f"  {i}. {w['word']}  ({r} = {rm})")
    print("\n[2/3] Generating images...")
    bg = create_background()
    imgs = []
    for i, w in enumerate(words):
        ip = rd / f"w_{i}.jpg"
        generate_word_image(w, bg, str(ip))
        imgs.append(str(ip))
    print("\n[3/3] Generating audio & video...")
    af, td = generate_all_audio(words, str(rd))
    fa = rd / "narration.mp3"
    create_final_audio(af, str(fa))
    ov = rd / "final_reel.mp4"
    create_video(imgs, af, str(ov))
    meta = {"channel": CHANNEL_NAME, "words": words, "timestamp": ts, "video": str(ov), "duration": td}
    with open(rd / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\n{'='*80}\n  COMPLETE! {td:.1f}s\n{'='*80}\n")
    return meta

if __name__ == "__main__":
    print(f"\n{'='*80}\n  {CHANNEL_NAME.upper()}\n{'='*80}\n")
    generate_reel()
