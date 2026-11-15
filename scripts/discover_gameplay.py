#!/usr/bin/env python3
"""Discover relevant third-party gameplay videos without downloading them.

Every result is an unverified candidate. Public availability, search ranking, and
credit do not establish permission to reuse a creator's recording.
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from yt_dlp import YoutubeDL

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "gameplay_candidates.json"

TAG_LABELS = {
    "corpo_plaza": "Corpo Plaza statue location",
    "statue": "FF06B5 statue",
    "ff06b5": "FF06B5 mystery",
    "night_city": "Night City exploration",
    "monks": "monks statue",
    "hex_color": "magenta hexadecimal code",
    "the_witcher_3": "The Witcher 3 FF06B5 easter egg",
    "ouroboros": "ouroboros symbol laptop",
    "magenta_symbol": "magenta symbol",
    "secret_area": "secret area",
    "church": "Biotechnica church",
    "biotechnica": "Biotechnica protein farm church",
    "servers": "church servers",
    "arcade": "Arasaka Tower 3D arcade",
    "arasaka_tower_3d": "Arasaka Tower 3D gameplay",
    "secret_rooms": "Arasaka Tower 3D secret rooms",
    "johnny_silverhand": "Johnny Silverhand arcade gameplay",
    "maze": "Arasaka Tower 3D floor minus 10 maze",
    "qr_code": "FF06B5 QR code",
    "secret_level": "Arasaka Tower 3D secret level",
    "dump": "Cyberpunk 2077 landfill laptop",
    "badlands": "Cyberpunk 2077 Badlands gameplay",
    "laptop": "FF06B5 laptop",
    "church_servers": "Biotechnica church server keypad",
    "mattress": "FF06B5 mattress secret cutscene",
    "polyhistor": "Polyhistor FF06B5 cutscene",
    "monster_truck": "Mackinaw Demiurge monster truck",
    "cube": "FF06B5 golden cube cutscene",
    "exploration": "Cyberpunk 2077 free roam exploration",
}

def clean(value, limit=500):
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    return value[:limit]

def build_query(episode_title, scene):
    tags = [TAG_LABELS.get(str(t).lower(), str(t).replace("_", " ")) for t in scene.get("visual_tags", [])]
    # Prioritize the scene heading and the most distinctive tags; avoid query overload.
    distinct = []
    for term in [scene.get("heading", "")] + tags[:3]:
        term = clean(term, 90)
        if term and term.lower() not in [x.lower() for x in distinct]:
            distinct.append(term)
    return clean("Cyberpunk 2077 " + " ".join(distinct) + " gameplay", 240)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_path")
    parser.add_argument("--results-per-scene", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.results_per_scene <= 10:
        raise SystemExit("--results-per-scene must be between 1 and 10")
    episode_path = Path(args.episode_path)
    if not episode_path.is_absolute():
        episode_path = ROOT / episode_path
    data = json.loads(episode_path.read_text(encoding="utf-8"))
    scenes = data.get("scenes", [])
    if not scenes:
        raise SystemExit("Episode has no scenes.")

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "episode": str(data.get("title", episode_path.name)),
        "notice": "Candidates only. No video was downloaded. YouTube attribution does not grant reuse permission. Obtain and retain permission or verify a compatible license before use.",
        "scenes": [],
    }
    opts = {
        "quiet": True,
        "no_warnings": False,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "ignoreerrors": False,
        "socket_timeout": 30,
        "extractor_retries": 3,
        "playlistend": args.results_per_scene,
    }
    with YoutubeDL(opts) as ydl:
        for index, scene in enumerate(scenes, 1):
            query = build_query(data.get("title", ""), scene)
            # Retry with a shorter query if the detailed scene query returns no entries.
            tags = [TAG_LABELS.get(str(t).lower(), str(t).replace("_", " ")) for t in scene.get("visual_tags", [])]
            short_query = clean("Cyberpunk 2077 " + " ".join(tags[:2]) + " gameplay", 160)
            queries = [query]
            if short_query.lower() != query.lower():
                queries.append(short_query)
            entry = {
                "scene_number": index,
                "scene_heading": clean(scene.get("heading", f"Scene {index}"), 180),
                "visual_tags": scene.get("visual_tags", []),
                "search_query": query,
                "search_attempts": [],
                "candidates": [],
                "search_error": None,
                "empty_reason": None,
            }
            for attempt_query in queries:
                entry["search_attempts"].append(attempt_query)
                try:
                    info = ydl.extract_info(
                        f"ytsearch{args.results_per_scene}:{attempt_query}",
                        download=False,
                    )
                    videos = (info or {}).get("entries", []) or []
                    for video in videos:
                        if not video:
                            continue
                        video_id = clean(video.get("id", ""), 80)
                        url = clean(video.get("webpage_url") or (f"https://www.youtube.com/watch?v={video_id}" if video_id else ""), 500)
                        if not url:
                            continue
                        if any(item["source_url"] == url for item in entry["candidates"]):
                            continue
                        entry["candidates"].append({
                            "title": clean(video.get("title"), 240),
                            "creator_name": clean(video.get("uploader") or video.get("channel"), 180),
                            "creator_channel_url": clean(video.get("uploader_url") or video.get("channel_url"), 500),
                            "source_url": url,
                            "duration_seconds": video.get("duration"),
                            "view_count_at_search": video.get("view_count"),
                            "upload_date": clean(video.get("upload_date"), 16),
                            "license_metadata": clean(video.get("license"), 160),
                            "permission_status": "not_verified",
                            "approved_for_use": False,
                            "review_note": "Contact the recording's rights holder or independently verify a compatible license. Credit alone is insufficient.",
                        })
                    if entry["candidates"]:
                        break
                    entry["empty_reason"] = "YouTube search returned no entries for this query."
                except Exception as exc:
                    entry["search_error"] = clean(f"{type(exc).__name__}: {exc}", 500)
                    print(f"Search failed for scene {index}: {entry['search_error']}")
                    # Try the shorter fallback query after an extractor/search failure.
                    continue
            if entry["candidates"]:
                entry["empty_reason"] = None
            report["scenes"].append(entry)
            print(f"Scene {index}/{len(scenes)}: {len(entry['candidates'])} candidate(s)")
            time.sleep(1)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(s["candidates"]) for s in report["scenes"])
    print(f"Candidate report: {OUTPUT}")
    print(f"Total candidates: {total}. None are approved or downloaded.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
