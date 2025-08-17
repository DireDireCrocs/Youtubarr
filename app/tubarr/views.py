from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib import messages
from django.conf import settings
from .models import AppSettings, Playlist, TrackItem, Snapshot

def settings_view(request):
    s = AppSettings.load()
    if request.method == "POST":
        s.youtube_api_key = request.POST.get("youtube_api_key","").strip()
        s.save()
        messages.success(request, "YouTube API key updated.")
        return redirect("settings")
    return render(request, "settings.html", {"settings": s, "env_has_key": bool(settings.YOUTUBE_API_KEY),"lidarr_token": getattr(settings, "LIDARR_TOKEN", None)})

@require_http_methods(["GET","POST"])
def playlists_view(request):
    if request.method == "POST":
        pid = (request.POST.get("playlist_id") or "").strip()
        if pid:
            Playlist.objects.get_or_create(playlist_id=pid)
            messages.success(request, f"Added {pid}")
        else:
            messages.error(request, "Playlist ID required.")
        return redirect("playlists")
    pls = Playlist.objects.all().order_by("-last_synced","playlist_id")
    return render(request, "playlists.html", {"playlists": pls})

def items_view(request):
    items = (TrackItem.objects
             .select_related("playlist","artist")
             .order_by("-published_at","-id")[:500])
    return render(request, "items.html", {"items": items})

# ---- HTMX helpers ----

def item_row(request, item_id):
    it = get_object_or_404(TrackItem.objects.select_related("playlist","artist"), id=item_id)
    return render(request, "partials/item_row.html", {"it": it})

@require_http_methods(["POST"])
def toggle_blacklist(request, item_id):
    it = get_object_or_404(TrackItem, id=item_id)
    # checkbox sends "on" when checked; missing when unchecked
    val = request.POST.get("blacklisted") == "on"
    if it.blacklisted != val:
        it.blacklisted = val
        it.save(update_fields=["blacklisted"])
    return item_row(request, item_id)

@require_http_methods(["POST"])
def edit_item(request, item_id):
    it = get_object_or_404(TrackItem, id=item_id)
    title = request.POST.get("title", it.title)
    artist_guess = request.POST.get("artist_name_guess", it.artist_name_guess)
    changed = []
    if title != it.title:
        it.title = title
        changed.append("title")
    if artist_guess != it.artist_name_guess:
        it.artist_name_guess = artist_guess
        changed.append("artist_name_guess")
    if changed:
        it.save(update_fields=changed)
    return item_row(request, item_id)

@require_http_methods(["POST"])
def delete_item(request, item_id):
    it = get_object_or_404(TrackItem, id=item_id)
    it.delete()
    # HTMX: tell client to remove the row
    return HttpResponse(status=204, headers={"HX-Trigger": "item-deleted"})

def healthz(request):
    return HttpResponse("ok")

def lidarr_tubarr_view(request):
    # token via ?token=... or X-Api-Key header
    token = request.GET.get("token") or request.headers.get("X-Api-Key")
    if not (settings.LIDARR_TOKEN and token == settings.LIDARR_TOKEN):
        return HttpResponseForbidden("missing/invalid token")
    snap = Snapshot.objects.order_by("-created_at").first()
    return JsonResponse(snap.payload if snap else [], safe=False)

def add_liked_music(request):
    if request.method == "POST":
        if not settings.YTMUSIC_COOKIE_JSON:
            return HttpResponse("YTMUSIC_COOKIE_JSON not configured", status=500)
        Playlist.objects.get_or_create(
            playlist_id="LM",
            defaults={"title": "Liked Music", "channel_title": "YouTube Music"}
        )
        return redirect("playlists")