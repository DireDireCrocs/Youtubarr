import json
import responses
from django.conf import settings
from freezegun import freeze_time
from tubarr.models import Snapshot, Artist, TrackItem
from tubarr.tasks import refresh_playlists, resolve_missing_mbids, build_snapshot
from tests.factories import PlaylistFactory

YT_ITEMS = {
  "items": [
    {"snippet": {
      "position": 0,
      "title": "Foo - Bar",
      "channelTitle": "Foo - Topic",
      "publishedAt": "2024-01-01T00:00:00Z",
      "resourceId": {"videoId": "abc123"}
    }},
    {"snippet": {
      "position": 1,
      "title": "Baz - Qux",
      "channelTitle": "Baz - Topic",
      "publishedAt": "2024-01-02T00:00:00Z",
      "resourceId": {"videoId": "def456"}
    }}
  ]
}

YT_META = {
  "items": [{
    "snippet": {"title": "My Playlist", "channelTitle": "Owner"}
  }]
}

MB_RESP_FOO = {"artists": [{"id": "11111111-1111-1111-1111-111111111111"}]}
MB_RESP_BAZ = {"artists": [{"id": "22222222-2222-2222-2222-222222222222"}]}

@freeze_time("2025-01-01")
@responses.activate
def test_full_refresh_and_snapshot(settings):
    settings.YOUTUBE_API_KEY = "TESTKEY"
    settings.MB_USER_AGENT = "tests/1.0 (test@example.com)"

    pl = PlaylistFactory(playlist_id="PL_TEST")

    # Playlist meta + items
    responses.add(responses.GET,
                  "https://www.googleapis.com/youtube/v3/playlists",
                  json=YT_META, status=200)
    responses.add(responses.GET,
                  "https://www.googleapis.com/youtube/v3/playlistItems",
                  json=YT_ITEMS, status=200)

    # MusicBrainz lookups (Foo, Baz)
    responses.add(responses.GET,
                  "https://musicbrainz.org/ws/2/artist/",
                  match=[responses.matchers.query_param_matcher(
                      {"query": 'artist:"Foo"', "fmt": "json"})],
                  json=MB_RESP_FOO, status=200)
    responses.add(responses.GET,
                  "https://musicbrainz.org/ws/2/artist/",
                  match=[responses.matchers.query_param_matcher(
                      {"query": 'artist:"Baz"', "fmt": "json"})],
                  json=MB_RESP_BAZ, status=200)

    # 1) fetch playlist items
    assert refresh_playlists() == 2
    assert TrackItem.objects.count() == 2

    # 2) resolve mbids
    resolve_missing_mbids()
    assert Artist.objects.exclude(mbid="").count() == 2

    # 3) snapshot
    build_snapshot()
    snap = Snapshot.objects.order_by("-created_at").first()
    assert snap and {"MusicBrainzId": "11111111-1111-1111-1111-111111111111"} in snap.payload
    assert {"MusicBrainzId": "22222222-2222-2222-2222-222222222222"} in snap.payload
