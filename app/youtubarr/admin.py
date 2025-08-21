from django.contrib import admin
from .models import AppSettings, Playlist, TrackItem, Artist, Snapshot
admin.site.register(AppSettings)
admin.site.register(Playlist)
admin.site.register(TrackItem)
admin.site.register(Artist)
admin.site.register(Snapshot)
