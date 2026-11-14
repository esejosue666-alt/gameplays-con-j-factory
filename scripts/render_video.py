#!/usr/bin/env python3
"""Render narrated scenes with relevant local gameplay/images, subtitles and fallback cards."""
import asyncio, json, subprocess, sys, textwrap, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT = Path(__file__).resolve().parents[1]
W, H = 1920, 1080
VOICE = "es-MX-JorgeNeural"

def run(cmd):
    subprocess.run(cmd, check=True)

def probe_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True)
    return float(result.stdout.strip())

def font(size, bold=False):
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
    ]
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()

def make_card(scene, index, total, out, visual_override=None):
    src = visual_override or scene.get("visual")
    if src and (ROOT / src).is_file() and Path(src).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
        base = Image.open(ROOT / src).convert("RGB").resize((W, H)).convert("RGBA")
        base = Image.alpha_composite(base, Image.new("RGBA", (W, H), (0, 0, 0, 135)))
    else:
        base = Image.new("RGBA", (W, H), (12, 18, 32, 255))
        d = ImageDraw.Draw(base)
        for y in range(H):
            shade = int(22 + 35 * y / H)
            d.line((0, y, W, y), fill=(8, shade, shade + 25, 255))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((80, 75, W-80, H-75), radius=28, outline=(90, 180, 220, 190), width=4)
    d.text((135, 125), "GAMEPLAYS CON J  •  MISTERIOS Y SECRETOS", font=font(30, True), fill=(120, 220, 240, 255))
    d.text((135, 215), str(scene.get("heading") or f"Parte {index+1}")[:90], font=font(62, True), fill="white")
    d.text((135, H-145), f"{index+1:02d} / {total:02d}", font=font(28, True), fill=(170, 210, 225, 255))
    base.convert("RGB").save(out, quality=94)

def select_visual(scene, used_assets):
    """Choose a relevant local asset only when its reuse rights and attribution are documented."""
    catalog_path = ROOT / "assets/gameplay/catalog.json"
    if not catalog_path.is_file():
        return None, None, None
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None, None, None
    wanted = {str(tag).strip().lower() for tag in scene.get("visual_tags", [])}
    if not wanted:
        return None, None, None
    ranked = []
    for item in catalog.get("assets", []):
        if item.get("approved_for_use") is not True:
            continue
        basis = item.get("rights_basis")
        if basis not in {"own_recording", "written_permission", "license"}:
            continue
        if basis == "written_permission":
            if not item.get("permission_evidence") or not item.get("creator_name") or not item.get("source_url"):
                continue
        if basis == "license":
            if not item.get("license_url") or not item.get("creator_name") or not item.get("source_url"):
                continue
        if basis == "own_recording" and not item.get("source_note"):
            continue
        path = ROOT / str(item.get("path", ""))
        if not path.is_file() or path.resolve().as_posix() in used_assets:
            continue
        tags = {str(tag).strip().lower() for tag in item.get("tags", [])}
        score = len(wanted.intersection(tags))
        if score:
            ranked.append((score, path, item))
    if not ranked:
        return None, None, None
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    chosen = ranked[0][1]
    return chosen, chosen.resolve().as_posix(), ranked[0][2]

async def speak(text, path):
    await edge_tts.Communicate(text, VOICE).save(str(path))

def stamp(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def make_srt(text, duration, path):
    # Approximate phrase timing from character count; captions remain readable.
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks = []
    for sentence in sentences:
        words = sentence.split()
        current = ""
        for word in words:
            candidate = (current + " " + word).strip()
            if len(candidate) > 88 and current:
                chunks.append(current)
                current = word
            else:
                current = candidate
        if current:
            chunks.append(current)
    if not chunks:
        chunks = [text.strip()]
    weights = [max(1, len(x)) for x in chunks]
    total = sum(weights)
    cursor = 0.0
    lines = []
    for i, (chunk, weight) in enumerate(zip(chunks, weights), 1):
        end = duration if i == len(chunks) else cursor + duration * weight / total
        lines.extend([str(i), f"{stamp(cursor)} --> {stamp(end)}", chunk, ""])
        cursor = end
    path.write_text("\n".join(lines), encoding="utf-8")

def escape_filter_path(path):
    return str(path).replace("\\", "/").replace(":", r"\:")

def render_scene(scene, index, total, work, used_assets, used_asset_items):
    narration = str(scene.get("narration", "")).strip()
    if not narration:
        raise SystemExit(f"Escena {index+1}: falta narration.")
    audio = work / f"voice_{index:03d}.mp3"
    srt = work / f"captions_{index:03d}.srt"
    clip = work / f"clip_{index:03d}.mp4"
    asyncio.run(speak(narration, audio))
    duration = probe_duration(audio)
    make_srt(narration, duration, srt)

    selected = select_visual(scene, used_assets)
    visual_path, visual_key, asset_item = selected if selected else (None, None, None)
    valid_visual = visual_path and visual_path.is_file()
    if valid_visual and visual_key:
        used_assets.add(visual_key)
        used_asset_items[visual_key] = asset_item
    is_video = bool(valid_visual and visual_path.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"})
    if not valid_visual or not is_video:
        card = work / f"card_{index:03d}.jpg"
        make_card(scene, index, total, card, str(visual_path) if valid_visual else None)
        visual_path = card

    subtitles = escape_filter_path(srt)
    filters = (
        "scale=1920:1080:force_original_aspect_ratio=increase,"
        "crop=1920:1080,setsar=1,eq=brightness=-0.16,"
        f"subtitles='{subtitles}':force_style='FontName=DejaVu Sans,FontSize=21,"
        "Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=58'"
    )
    cmd = ["ffmpeg", "-y"]
    if is_video:
        cmd += ["-stream_loop", "-1", "-i", str(visual_path)]
    else:
        cmd += ["-loop", "1", "-i", str(visual_path)]
    cmd += ["-i", str(audio), "-vf", filters, "-map", "0:v:0", "-map", "1:a:0",
            "-t", f"{duration:.3f}", "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart", str(clip)]
    run(cmd)
    return clip

def main():
    episode = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("episodes/demo.json")
    if not episode.is_absolute():
        episode = ROOT / episode
    data = json.loads(episode.read_text(encoding="utf-8"))
    scenes = data.get("scenes", [])
    if not scenes:
        raise SystemExit("El episodio necesita al menos una escena.")
    work = ROOT / "work/scenes"
    work.mkdir(parents=True, exist_ok=True)
    used_assets = set()
    used_asset_items = {}
    clips = [render_scene(scene, i, len(scenes), work, used_assets, used_asset_items) for i, scene in enumerate(scenes)]
    concat = ROOT / "work/concat.txt"
    concat.write_text("".join("file '" + p.as_posix() + "'\n" for p in clips), encoding="utf-8")
    out = ROOT / "output/final.mp4"
    out.parent.mkdir(exist_ok=True)
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-c", "copy", "-movflags", "+faststart", str(out)])
    description = str(data.get("description", "")).strip()
    credits = []
    for item in used_asset_items.values():
        basis = item.get("rights_basis")
        if basis == "own_recording":
            continue
        creator = str(item.get("creator_name", "Creador no especificado")).strip()
        channel = str(item.get("creator_channel_url", "")).strip()
        source = str(item.get("source_url", "")).strip()
        license_url = str(item.get("license_url", "")).strip()
        label = str(item.get("attribution_text", "")).strip() or f"Gameplay: {creator}"
        line = f"- {label}"
        if channel:
            line += f" | Canal: {channel}"
        if source:
            line += f" | Clip original: {source}"
        if license_url:
            line += f" | Licencia: {license_url}"
        credits.append(line)
    if credits:
        description += "\n\nGAMEPLAY DE TERCEROS — CRÉDITOS Y FUENTES\n" + "\n".join(dict.fromkeys(credits))
    meta = {
        "title": str(data.get("title", "Video de Gameplays con J"))[:100],
        "description": description[:5000],
        "tags": data.get("tags", ["videojuegos", "misterios"]),
        "categoryId": "20", "privacyStatus": "private"
    }
    (ROOT / "output/metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("VIDEO_READY=" + str(out))
    print(f"Borrador generado. Assets aprobados usados: {len(used_asset_items)}. Sus créditos se añadieron a metadata.json. Las escenas sin coincidencia usan tarjetas de respaldo.")

if __name__ == "__main__":
    main()
