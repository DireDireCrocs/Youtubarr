import json
from django.conf import settings
from youtubarr.models import Snapshot

def test_lidarr_requires_token(client, settings):
    settings.LIDARR_TOKEN = "secret"
    Snapshot.objects.create(payload=[])
    r = client.get("/api/v1/lidarr")
    assert r.status_code == 403
    r = client.get("/api/v1/lidarr?token=secret")
    assert r.status_code == 200
    assert r.json() == []
