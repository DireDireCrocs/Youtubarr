from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

class AppSettings(models.Model):
    """Singleton-style config."""
    youtube_api_key = models.CharField(max_length=256, blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce single row
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

YOUTUBE_PLAYLIST_ID_RE = RegexValidator(
    regex=r"^[A-Za-z0-9_-]{13,}$", message="Looks like an invalid playlist ID."
)

class Playlist(models.Model):
    playlist_id = models.CharField(max_length=64, unique=True, validators=[YOUTUBE_PLAYLIST_ID_RE])
    title = models.CharField(max_length=255, blank=True, default="")
    channel_title = models.CharField(max_length=255, blank=True, default="")
    enabled = models.BooleanField(default=True)
    last_synced = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title or self.playlist_id

class Artist(models.Model):
    name = models.CharField(max_length=255, unique=True)
    mbid = models.CharField(max_length=36, blank=True, null=True)  # UUID

    def __str__(self):
        return f"{self.name} [{self.mbid or 'no-mbid'}]"

class TrackItem(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name="items")
    video_id = models.CharField(max_length=32)
    title = models.CharField(max_length=512)
    channel_title = models.CharField(max_length=255, blank=True, default="")
    artist_name_guess = models.CharField(max_length=255, blank=True, default="")
    artist = models.ForeignKey(Artist, null=True, blank=True, on_delete=models.SET_NULL)
    blacklisted = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    position = models.IntegerField(default=0)

    class Meta:
        unique_together = ("playlist", "video_id")

class Snapshot(models.Model):
    """What we actually serve to Lidarr; newest wins."""
    created_at = models.DateTimeField(default=timezone.now)
    payload = models.JSONField()  # [{"MusicBrainzId": "..."}]
