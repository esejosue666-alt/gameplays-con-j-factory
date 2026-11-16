#!/usr/bin/env python3
"""Discover scene-specific gameplay candidates without downloading videos.

Search results are unverified candidates. Ranking uses title and public metadata
heuristics only; it does not inspect footage, measure retention, or verify reuse permissions.
"""
import argparse
import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from yt_dlp import YoutubeDL

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "gameplay_candidates.json"

# Each scene gets independent searches. Keep game names in the query only when
# the footage should come from that game (scene 3 is specifically The Witcher 3).
SCENE_SEARCHES = {
    1: [
        "Cyberpunk 2077 Corpo Plaza FF06B5 statue location gameplay",
        "Cyberpunk 2077 magenta statue Corpo Plaza close up gameplay",
        "Cyberpunk 2077 FF06B5 statue Night City exploration",
    ],
    2: [
        "Cyberpunk 2077 FF06B5 statue monks meditation gameplay",
        "Cyberpunk 2077 Corpo Plaza monk statue FF06B5 gameplay",
        "Cyberpunk 2077 FF06B5 statue details close up",
    ],
    3: [
        "The Witcher 3 next gen FF06B5 secret area ouroboros gameplay",
        "The Witcher 3 FF06B5 easter egg secret cave gameplay",
        "The Witcher 3 magenta ouroboros symbol secret location",
    ],
    4: [
        "Cyberpunk 2077 Biotechnica protein farm church interior gameplay",
        "Cyberpunk 2077 FF06B5 church servers computer terminal gameplay",
        "Cyberpunk 2077 church server room laptop Biotechnica gameplay",
    ],
    5: [
        "Cyberpunk 2077 Arasaka Tower 3D arcade full gameplay secret rooms",
        "Cyberpunk 2077 Arasaka Tower 3D hidden wall secret room gameplay",
        "Cyberpunk 2077 Johnny Silverhand arcade Arasaka Tower 3D gameplay",
    ],
    6: [
        "Cyberpunk 2077 Arasaka Tower 3D secret level floor minus 10 maze gameplay",
        "Cyberpunk 2077 Arasaka Tower 3D hidden maze QR code gameplay",
        "Cyberpunk 2077 FF06B5 arcade maze level 10 walkthrough",
    ],
    7: [
        "Cyberpunk 2077 landfill dump laptop FF06B5 location gameplay",
        "Cyberpunk 2077 Badlands junkyard laptop ouroboros gameplay",
        "Cyberpunk 2077 Biotechnica church server codes terminal gameplay",
    ],
    8: [
        "Cyberpunk 2077 Badlands mattress FF06B5 secret event gameplay",
        "Cyberpunk 2077 Polyhistor mattress wait secret cutscene gameplay",
        "Cyberpunk 2077 Mackinaw Demiurge monster truck Badlands gameplay",
    ],
    9: [
        "Cyberpunk 2077 Polyhistor FF06B5 cutscene golden cube gameplay",
        "Cyberpunk 2077 FF06B5 Polyhistor laptop cube scene",
        "Cyberpunk 2077 Badlands Polyhistor secret event aftermath gameplay",
    ],
    10: [
        "Cyberpunk 2077 Night City Corpo Plaza FF06B5 statue exploration gameplay",
        "Cyberpunk 2077 Badlands free roam landscape driving gameplay",
        "Cyberpunk 2077 FF06B5 mystery statue final scene gameplay",
    ],
}

SCENE_TERMS = {
    1: ["corpo plaza", "statue", "ff06b5", "magenta"],
    2: ["statue", "monk", "monks", "ff06b5", "corpo plaza"],
    3: ["witcher", "witcher 3", "ouroboros", "ff06b5", "secret"],
    4: ["biotechnica", "church", "server", "laptop", "terminal"],
    5: ["arasaka tower 3d", "arasaka", "arcade", "secret", "johnny"],
    6: ["arasaka tower 3d", "maze", "labyrinth", "qr", "secret level"],
    7: ["landfill", "dump", "laptop", "badlands", "server", "ouroboros"],
    8: ["badlands", "mattress", "polyhistor", "demiurge", "monster truck"],
    9: ["polyhistor", "cube", "ff06b5", "cutscene", "badlands"],
    10: ["night city", "statue", "badlands", "exploration", "ff06b5"],
}

STOP_WORDS = {
    "cyberpunk", "2077", "gameplay", "the", "and", "with", "how", "to",
    "in", "of", "a", "an", "for", "secret", "location", "full",
}

def clean(value, limit=500):
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    return value[:limit]

def build_queries(scene, scene_number):
    planned = SCENE_SEARCHES.get(scene_number, [])
    if planned:
        return planned
    tags = [str(t).replace("_", " ") for t in scene.get("visual_tags", [])]
    return [clean("Cyberpunk 2077 " + " ".join(tags[:3]) + " gameplay", 220)]

ATTENTION_TERMS = [
    "combat", "boss fight", "chase", "pursuit", "explosion", "explosive",
    "intense", "cinematic", "rare", "hidden", "secret", "mystery",
    "discovered", "discovery", "easter egg", "cutscene", "reveal",
    "surprise", "surprising", "scary", "creepy", "glitch", "all secrets",
    "full run", "no damage", "legendary", "underground",
]

def relevance(title, scene_number):
    """Scene-specific title score; does not verify the actual footage."""
    title_l = clean(title, 300).lower()
    terms = SCENE_TERMS.get(scene_number, [])
    matched = [term for term in terms if term in title_l]
    score = len(matched)
    score += sum(1 for term in matched if " " in term)
    return score, matched

def attention_signals(title):
    title_l = clean(title, 300).lower()
    return [term for term in ATTENTION_TERMS if term in title_l]

def score_candidate(relevance_score, attention_matches, view_count):
    # Scene relevance dominates; hook wording and views are secondary signals.
    relevance_part = min(relevance_score / 7.0, 1.0)
    hook_part = min(len(attention_matches) / 3.0, 1.0)
    try:
        popularity_part = min(math.log10(max(int(view_count or 0), 0) + 1) / 7.0, 1.0)
    except (TypeError, ValueError):
        popularity_part = 0.0
    return round(100 * (0.70 * relevance_part + 0.20 * hook_part + 0.10 * popularity_part), 1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_path")
    parser.add_argument("--results-per-scene", type=int, default=6)
    parser.add_argument("--queries-per-scene", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.results_per_scene <= 10:
        raise SystemExit("--results-per-scene must be between 1 and 10")
    if not 1 <= args.queries_per_scene <= 5:
        raise SystemExit("--queries-per-scene must be between 1 and 5")

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
        "notice": "Candidates only. No video was downloaded. Title relevance is heuristic and does not verify footage. YouTube attribution does not grant reuse permission. Obtain and retain permission or verify a compatible license before use.",
        "ranking_method": "Heuristic: 70% scene-title relevance, 20% attention-hook words, 10% log-scaled view count. Metadata only; it does not inspect footage, measure real retention, or verify reuse rights.",
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
            queries = build_queries(scene, index)[:args.queries_per_scene]
            entry = {
                "scene_number": index,
                "scene_heading": clean(scene.get("heading", f"Scene {index}"), 180),
                "visual_tags": scene.get("visual_tags", []),
                "search_query": queries[0] if queries else "",
                "search_attempts": [],
                "candidates": [],
                "search_error": None,
                "empty_reason": None,
            }
            candidates_by_url = {}
            errors = []

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
                        url = clean(
                            video.get("webpage_url") or
                            (f"https://www.youtube.com/watch?v={video_id}" if video_id else ""),
                            500,
                        )
                        if not url:
                            continue
                        score, matched = relevance(video.get("title"), index)
                        candidate = {
                            "title": clean(video.get("title"), 240),
                            "creator_name": clean(video.get("uploader") or video.get("channel"), 180),
                            "creator_channel_url": clean(video.get("uploader_url") or video.get("channel_url"), 500),
                            "source_url": url,
                            "duration_seconds": video.get("duration"),
                            "view_count_at_search": video.get("view_count"),
                            "upload_date": clean(video.get("upload_date"), 16),
                            "license_metadata": clean(video.get("license"), 160),
                            "relevance_score": score,
                            "matched_title_terms": matched,
                            "attention_signals": attention_signals(video.get("title")),
                            "attention_score": score_candidate(score, attention_signals(video.get("title")), video.get("view_count")),
                            "ranking_note": "Heuristic based on title keywords and public view count only; it does not assess the actual visuals or audience retention.",
                            "relevance_note": "Title-based estimate only; open and inspect the actual footage.",
                            "permission_status": "not_verified",
                            "approved_for_use": False,
                            "review_note": "Contact the recording's rights holder or independently verify a compatible license. Credit alone is insufficient.",
                        }
                        previous = candidates_by_url.get(url)
                        if previous is None or candidate["relevance_score"] > previous["relevance_score"]:
                            candidates_by_url[url] = candidate
                except Exception as exc:
                    message = clean(f"{type(exc).__name__}: {exc}", 500)
                    errors.append(message)
                    print(f"Search failed for scene {index}: {message}")
                time.sleep(0.5)

            ranked = sorted(
                candidates_by_url.values(),
                key=lambda item: (item["attention_score"], item["relevance_score"], item.get("view_count_at_search") or 0),
                reverse=True,
            )
            entry["candidates"] = ranked[:args.results_per_scene]
            if not entry["candidates"]:
                entry["empty_reason"] = "All scene-specific YouTube searches returned no candidates."
                if errors:
                    entry["search_error"] = " | ".join(errors[:3])
            elif errors:
                entry["search_error"] = "Some query attempts failed: " + " | ".join(errors[:2])

            report["scenes"].append(entry)
            print(f"Scene {index}/{len(scenes)}: {len(entry['candidates'])} candidate(s) from {len(entry['search_attempts'])} targeted search(es)")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(s["candidates"]) for s in report["scenes"])
    empty = [str(s["scene_number"]) for s in report["scenes"] if not s["candidates"]]
    print(f"Candidate report: {OUTPUT}")
    print(f"Total candidates: {total}. Empty scenes: {', '.join(empty) if empty else 'none'}.")
    print("None are approved or downloaded.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
