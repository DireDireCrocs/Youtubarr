import json
import os
import re
from ytmusicapi import YTMusic, OAuthCredentials
from django.conf import settings

def guess_artist_from_title(title: str, channel_title: str) -> str:
    """
    Heuristics:
    - 'Artist - Song' => take left half
    - Channel like 'Foo - Topic' => use 'Foo'
    - Otherwise: empty string (we'll skip for MB search)
    """
    if " - " in title:
        left = title.split(" - ", 1)[0].strip()
        # avoid generic prefixes like "Official Video"
        if len(left) >= 2:
            return left
    if " - Topic" in channel_title:
        return channel_title.replace(" - Topic", "").strip()
    return ""

def get_ytmusic():
    """
    Return a YTMusic instance. Requires oauth.json.
    """
    data_dir = "/data"
    json_path = os.path.join(data_dir, "oauth.json")

    if not os.path.exists(json_path):
        raise RuntimeError("No oauth.json found in /data")

    return YTMusic(json_path, oauth_credentials=OAuthCredentials(client_id=settings.YOUTUBE_OAUTH_CLIENT_ID, client_secret=settings.YOUTUBE_OAUTH_CLIENT_SECRET))

def fetch_liked_music():
    ytmusic = get_ytmusic()
    playlist = ytmusic.get_playlist("LM")
    items = []
    for track in playlist["tracks"]:
        vid = track.get("videoId")
        if not vid:
            continue
        items.append({
            "video_id": vid,
            "title": track.get("title", ""),
            "artist": (track.get("artists") or [{}])[0].get("name", ""),
        })
    return items
