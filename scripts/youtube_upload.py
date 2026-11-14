#!/usr/bin/env python3
"""Upload a reviewed MP4. OAuth credentials come from YOUTUBE_TOKEN_B64."""
import base64
import json
import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main() -> int:
    video_path = Path(os.getenv("VIDEO_PATH", "output/final.mp4"))
    metadata_path = Path(os.getenv("METADATA_PATH", "output/metadata.json"))
    encoded = os.getenv("YOUTUBE_TOKEN_B64", "").strip()
    if not encoded:
        raise SystemExit("Missing YOUTUBE_TOKEN_B64 repository secret.")
    if not video_path.is_file():
        raise SystemExit(f"Video file not found: {video_path}")
    if not metadata_path.is_file():
        raise SystemExit(f"Metadata file not found: {metadata_path}")

    try:
        info = json.loads(base64.b64decode(encoded, validate=True).decode("utf-8"))
    except Exception:
        raise SystemExit("YOUTUBE_TOKEN_B64 is not valid Base64-encoded OAuth JSON.")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    title = str(metadata.get("title", "")).strip()
    description = str(metadata.get("description", "")).strip()
    tags = metadata.get("tags", [])
    category_id = str(metadata.get("categoryId", "20"))
    privacy = str(metadata.get("privacyStatus", "private"))
    if not title:
        raise SystemExit("metadata.json must contain a non-empty title.")
    if privacy not in {"private", "unlisted", "public"}:
        raise SystemExit("privacyStatus must be private, unlisted, or public.")
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise SystemExit("tags must be a JSON array of strings.")

    credentials = Credentials.from_authorized_user_info(info, SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    youtube = build("youtube", "v3", credentials=credentials)
    body = {
        "snippet": {
            "title": title[:100], "description": description[:5000],
            "tags": tags[:500], "categoryId": category_id,
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    print("Upload completed:", "https://www.youtube.com/watch?v=" + response["id"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
