import os, time, requests
from dateutil import parser as dateparser
from django.conf import settings
from django.db import transaction
from celery import shared_task
from .models import AppSettings, Playlist, TrackItem, Artist, Snapshot
from .utils import guess_artist_from_title, fetch_liked_music
import json
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
YT_API_ITEMS = "https://www.googleapis.com/youtube/v3/playlistItems"
YT_API_PLAYLISTS = "https://www.googleapis.com/youtube/v3/playlists"
MB_API = "https://musicbrainz.org/ws/2/artist/"
MB_HEADERS = {"User-Agent": settings.MB_USER_AGENT}

def _get_api_key():
    s = AppSettings.load()
    return s.youtube_api_key or settings.YOUTUBE_API_KEY

def fetch_playlist_items(playlist: Playlist):
    if playlist.playlist_id == "LM":
        items = fetch_liked_music()
        count = 0
        for it in items:
            with transaction.atomic():
                ti, created = TrackItem.objects.get_or_create(
                    playlist=playlist,
                    video_id=it["video_id"],
                    defaults=dict(
                        title=it["title"],
                        artist_name_guess=it["artist"],
                        channel_title="YouTube Music",
                        position=0,  # LM doesn’t have stable positions
                        published_at=None,
                    ),
                )
                if not created:
                    ti.title = it["title"]
                    ti.artist_name_guess = it["artist"]
                    ti.save(update_fields=["title", "artist_name_guess"])
            count += 1
        playlist.title = "Liked Music"
        playlist.channel_title = "YouTube Music"
        playlist.last_synced = timezone.now()
        playlist.save(update_fields=["title", "channel_title", "last_synced"])
        return count
    api_key = _get_api_key()
    if not api_key:
        return 0

    # --- Fetch playlist metadata ---
    meta_params = {
        "part": "snippet",
        "id": playlist.playlist_id,
        "key": api_key,
    }
    rmeta = requests.get(YT_API_PLAYLISTS, params=meta_params, timeout=30)
    if rmeta.status_code == 200:
        meta = rmeta.json()
        items = meta.get("items", [])
        if items:
            sn = items[0].get("snippet", {})
            playlist.title = sn.get("title", playlist.title)
            playlist.channel_title = sn.get("channelTitle", playlist.channel_title)
            playlist.last_synced = timezone.now()
            playlist.save(update_fields=["title", "channel_title", "last_synced"])

    # --- Fetch playlist items ---
    params = {
        "part": "snippet,contentDetails",
        "playlistId": playlist.playlist_id,
        "maxResults": settings.YOUTUBE_QUOTA_SAFE_PAGE_SIZE,
        "key": api_key,
    }
    count = 0
    url = YT_API_ITEMS
    while True:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            break
        data = r.json()

        for it in data.get("items", []):
            sn = it.get("snippet", {})
            vd = sn.get("resourceId", {}).get("videoId")
            title = sn.get("title", "")
            ch = sn.get("channelTitle", "")
            published = sn.get("publishedAt")
            artist_guess = guess_artist_from_title(title, ch)

            with transaction.atomic():
                ti, created = TrackItem.objects.get_or_create(
                    playlist=playlist,
                    video_id=vd,
                    defaults=dict(
                        title=title,
                        channel_title=ch,
                        position=sn.get("position", 0),
                        published_at=dateparser.parse(published) if published else None,
                        artist_name_guess=artist_guess,
                    )
                )

                if created:
                    # filled on creation, nothing more to do
                    pass
                else:
                    # only update "machine" fields that should always be current
                    ti.position = sn.get("position", ti.position)
                    ti.save(update_fields=["position"])

            count += 1

        token = data.get("nextPageToken")
        if not token:
            break
        params["pageToken"] = token
    return count


def search_mb_artist_mbid(name: str) -> str | None:
    if not name:
        return None
    params = {"query": f'artist:"{name}"', "fmt": "json"}
    r = requests.get(MB_API, params=params, headers=MB_HEADERS, timeout=30)
    if r.status_code == 200:
        js = r.json()
        arts = js.get("artists") or []
        if arts:
            return arts[0]["id"]
    return None

@shared_task
def refresh_playlists():
    updated = 0
    for pl in Playlist.objects.filter(enabled=True):
        print(f"Fetching items for playlist {pl.playlist_id} ({pl.title})")
        updated += fetch_playlist_items(pl)
    return updated

@shared_task
def resolve_missing_mbids():
    # Respect MB 1 rps
    names = (TrackItem.objects
             .filter(blacklisted=False, artist__isnull=True)
             .exclude(artist_name_guess="")
             .values_list("artist_name_guess", flat=True)
             .distinct())
    for name in names:
        mbid = search_mb_artist_mbid(name)
        time.sleep(1.05)  # be a decent citizen
        if mbid:
            art, _ = Artist.objects.get_or_create(name=name)
            if not art.mbid:
                art.mbid = mbid
                art.save()
        else:
            Artist.objects.get_or_create(name=name)  # create without mbid to avoid re-querying next time

    # Link TrackItems that now have an Artist row
    for ti in TrackItem.objects.filter(artist__isnull=True).exclude(artist_name_guess=""):
        try:
            ti.artist = Artist.objects.get(name=ti.artist_name_guess)
            ti.save()
        except Artist.DoesNotExist:
            pass

@shared_task
def build_snapshot():
    logger.info("Building snapshot…")
    mbids = (Artist.objects.exclude(mbid__isnull=True)
             .exclude(mbid__exact="")
             .filter(trackitem__blacklisted=False)
             .values_list("mbid", flat=True)
             .distinct())
    payload = [{"MusicBrainzId": mbid} for mbid in mbids]
    Snapshot.objects.create(payload=payload)
    logger.info("Snapshot created with %d items", len(payload))
    return len(payload)

@shared_task
def refresh_all_and_snapshot():
    refresh_playlists.delay()
    resolve_missing_mbids.delay()
    # Let MBIDs resolving queue up; then build after a pause is overkill here.
    build_snapshot.delay()
