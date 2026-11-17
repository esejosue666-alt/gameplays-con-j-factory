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


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm"}

def rights_are_documented(item):
    if item.get("approved_for_use") is not True:
        return False
    basis = item.get("rights_basis")
    if basis == "own_recording":
        return bool(item.get("source_note"))
    if basis == "written_permission":
        return bool(item.get("permission_evidence") and item.get("creator_name") and item.get("source_url"))
    if basis == "license":
        return bool(item.get("license_url") and item.get("creator_name") and item.get("source_url"))
    return False

def read_catalog():
    path = ROOT / "assets/gameplay/catalog.json"
    if not path.is_file():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("assets", [])
    except (json.JSONDecodeError, OSError):
        return []

def select_fallback_video(scene, used_assets):
    """Find an approved same-game combat recording for scenes without an exact shot."""
    required = {str(tag).strip().lower() for tag in scene.get("fallback_background_tags", [])}
    if not required:
        return None, None, None
    ranked = []
    for item in read_catalog():
        if not rights_are_documented(item):
            continue
        path = ROOT / str(item.get("path", ""))
        if not path.is_file() or path.suffix.lower() not in VIDEO_EXTS:
            continue
        key = path.resolve().as_posix()
        if key in used_assets and not scene.get("fallback_allow_background_reuse", False):
            continue
        tags = {str(tag).strip().lower() for tag in item.get("tags", [])}
        # Require every configured tag, e.g. both cyberpunk_2077 and combat.
        if not required.issubset(tags):
            continue
        ranked.append((len(tags.intersection(required)), path, item))
    if not ranked:
        return None, None, None
    ranked.sort(key=lambda entry: entry[0], reverse=True)
    path, item = ranked[0][1], ranked[0][2]
    return path, path.resolve().as_posix(), item

def select_fallback_images(scene, used_assets, limit=3):
    wanted = {str(tag).strip().lower() for tag in scene.get("fallback_image_tags", [])}
    if not wanted:
        return []
    ranked = []
    for item in read_catalog():
        if not rights_are_documented(item):
            continue
        path = ROOT / str(item.get("path", ""))
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue
        key = path.resolve().as_posix()
        if key in used_assets:
            continue
        tags = {str(tag).strip().lower() for tag in item.get("tags", [])}
        score = len(wanted.intersection(tags))
        if score:
            ranked.append((score, path, key, item))
    ranked.sort(key=lambda entry: entry[0], reverse=True)
    return [(path, key, item) for _, path, key, item in ranked[:limit]]

def make_asset_panel(image_path, caption, out):
    """Place a real, rights-cleared still inside a transparent panel over moving gameplay."""
    panel = Image.new("RGBA", (1480, 800), (0, 0, 0, 0))
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle((5, 5, 1475, 795), radius=34, fill=(5, 12, 25, 222), outline=(90, 205, 230, 245), width=4)
    draw.text((58, 38), caption[:70], font=font(40, True), fill=(245, 250, 255, 255))
    with Image.open(image_path) as source:
        image = source.convert("RGB")
        image.thumbnail((1350, 610), Image.Resampling.LANCZOS)
        x = (1480 - image.width) // 2
        y = 115 + (610 - image.height) // 2
        panel.alpha_composite(image.convert("RGBA"), (x, y))
    draw = ImageDraw.Draw(panel)
    draw.text((58, 748), "IMAGEN DE APOYO", font=font(20, True), fill=(135, 220, 235, 255))
    panel.save(out)

def make_story_panel(panel_data, out):
    """Create an explanatory graphic, clearly labelled as a recreation, not game footage."""
    width, height = 1480, 800
    panel = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle((5, 5, width-5, height-5), radius=34, fill=(5, 12, 25, 222), outline=(90, 205, 230, 245), width=4)
    title = str(panel_data.get("title", "Pista del misterio"))[:70]
    subtitle = str(panel_data.get("subtitle", ""))[:150]
    kind = str(panel_data.get("kind", "servers")).lower()
    draw.text((58, 38), title, font=font(42, True), fill=(245, 250, 255, 255))
    wrapped = textwrap.wrap(subtitle, width=78)
    for line_no, line in enumerate(wrapped[:2]):
        draw.text((62, 100 + line_no * 36), line, font=font(25), fill=(185, 213, 230, 255))

    cyan = (85, 220, 240, 255)
    pale = (200, 235, 245, 255)
    if kind == "church":
        draw.polygon([(505, 610), (740, 270), (975, 610)], outline=cyan, fill=(16, 45, 65, 225))
        draw.rectangle((555, 600, 925, 690), outline=cyan, width=6)
        draw.rectangle((690, 485, 790, 690), outline=pale, width=5)
        for x in (600, 835):
            draw.rectangle((x, 525, x+65, 585), outline=pale, width=4)
        draw.line((740, 270, 740, 210), fill=cyan, width=7)
        draw.ellipse((720, 190, 760, 230), outline=cyan, width=5)
    elif kind == "laptop":
        draw.rounded_rectangle((425, 260, 1055, 625), radius=22, outline=cyan, width=8, fill=(10, 30, 48, 230))
        draw.rectangle((470, 305, 1010, 570), outline=pale, width=4)
        for n in range(5):
            y = 345 + n * 42
            draw.line((515, y, 700 + (n % 3) * 70, y), fill=cyan if n % 2 == 0 else pale, width=7)
        draw.polygon([(350, 640), (1130, 640), (1055, 700), (425, 700)], outline=cyan, fill=(20, 55, 75, 245))
    else:
        for rack_x in (390, 620, 850):
            draw.rounded_rectangle((rack_x, 245, rack_x+190, 690), radius=15, outline=cyan, width=7, fill=(10, 30, 48, 235))
            for row in range(4):
                y = 280 + row * 94
                draw.rounded_rectangle((rack_x+20, y, rack_x+170, y+68), radius=8, outline=pale, width=3)
                draw.ellipse((rack_x+35, y+24, rack_x+51, y+40), fill=cyan)
                draw.line((rack_x+72, y+33, rack_x+145, y+33), fill=pale, width=4)
    draw.text((58, 748), "RECREACIÓN VISUAL · NO ES CAPTURA DEL JUEGO", font=font(20, True), fill=(135, 220, 235, 255))
    panel.save(out)

def render_combat_background(background, panels, audio, duration, srt, out):
    """Keep combat gameplay moving while support images change during the narration."""
    cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(background)]
    for panel in panels:
        cmd += ["-loop", "1", "-framerate", "30", "-i", str(panel)]
    cmd += ["-i", str(audio)]
    filters = [
        "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps=30,eq=brightness=-0.12[bg]"
    ]
    previous = "bg"
    count = len(panels)
    for panel_index in range(count):
        input_index = panel_index + 1
        start = duration * panel_index / count
        end = duration * (panel_index + 1) / count
        panel_label = f"panel{panel_index}"
        output_label = f"scene{panel_index}"
        filters.append(f"[{input_index}:v]scale=1480:800:force_original_aspect_ratio=decrease,pad=1480:800:(ow-iw)/2:(oh-ih)/2:color=0x00000000,format=rgba[{panel_label}]")
        filters.append(f"[{previous}][{panel_label}]overlay=(W-w)/2:(H-h)/2:enable='between(t,{start:.3f},{end:.3f})':eof_action=pass[{output_label}]")
        previous = output_label
    subtitles = escape_filter_path(srt)
    style = "FontName=DejaVu Sans,FontSize=21,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=58"
    filters.append(f"[{previous}]subtitles='{subtitles}':force_style='{style}'[vout]")
    audio_index = len(panels) + 1
    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", f"{audio_index}:a:0",
        "-t", f"{duration:.3f}", "-r", "30", "-c:v", "libx264",
        "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", str(out)
    ]
    run(cmd)


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
    valid_visual = bool(visual_path and visual_path.is_file())
    is_video = bool(valid_visual and visual_path.suffix.lower() in VIDEO_EXTS)

    # Exact scene footage always wins. The combat fallback is only for a missing exact video.
    if not is_video:
        fallback = select_fallback_video(scene, used_assets)
        background_path, background_key, background_item = fallback if fallback else (None, None, None)
        if background_path and background_path.is_file():
            image_assets = []
            image_keys = set(used_assets)
            if valid_visual and visual_path.suffix.lower() in IMAGE_EXTS:
                image_assets.append((visual_path, visual_key, asset_item))
                if visual_key:
                    image_keys.add(visual_key)
            image_assets.extend(select_fallback_images(scene, image_keys, limit=3))
            panels = []
            for panel_number, (image_path, image_key, image_item) in enumerate(image_assets[:3]):
                panel_path = work / f"support_{index:03d}_{panel_number:02d}.png"
                caption = str(image_item.get("caption") or image_item.get("attribution_text") or "Imagen de apoyo")
                make_asset_panel(image_path, caption, panel_path)
                panels.append(panel_path)
                if image_key:
                    used_assets.add(image_key)
                    used_asset_items[image_key] = image_item

            # When no cleared church/server stills exist, show three labelled explanatory visuals.
            fallback_specs = scene.get("fallback_panels", [])
            panel_number = len(panels)
            while len(panels) < 3 and panel_number < len(fallback_specs):
                panel_path = work / f"support_{index:03d}_{panel_number:02d}.png"
                make_story_panel(fallback_specs[panel_number], panel_path)
                panels.append(panel_path)
                panel_number += 1
            if not panels:
                make_story_panel(
                    {"title": scene.get("heading", "Pista del misterio"),
                     "subtitle": "Gameplay de combate como fondo y visual de contexto",
                     "kind": "servers"},
                    work / f"support_{index:03d}_00.png"
                )
                panels = [work / f"support_{index:03d}_00.png"]

            used_assets.add(background_key)
            used_asset_items[background_key] = background_item
            render_combat_background(background_path, panels, audio, duration, srt, clip)
            print(f"Escena {index+1}: fondo de combate aprobado + {len(panels)} imagen(es) de apoyo.")
            return clip
        elif scene.get("fallback_background_tags"):
            print(f"Escena {index+1}: no hay gameplay de combate aprobado en catalog.json; no se usará material público sin permiso.")

    # Preserve the existing renderer for exact video, approved stills, and the ordinary card fallback.
    if valid_visual and visual_key:
        used_assets.add(visual_key)
        used_asset_items[visual_key] = asset_item
    is_video = bool(valid_visual and visual_path.suffix.lower() in VIDEO_EXTS)
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
