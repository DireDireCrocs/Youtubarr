from django.contrib import admin
from django.urls import path
from youtubarr import views

urlpatterns = [
    path("admin/", admin.site.urls),  # <-- use Django's admin
    path("", views.settings_view, name="settings"),
    path("playlists/", views.playlists_view, name="playlists"),
    path("items/", views.items_view, name="items"),

    # HTMX endpoints
    path("items/<int:item_id>/row/", views.item_row, name="item-row"),
    path("items/<int:item_id>/toggle-blacklist/", views.toggle_blacklist, name="toggle-blacklist"),
    path("items/<int:item_id>/edit/", views.edit_item, name="edit-item"),
    path("items/<int:item_id>/delete/", views.delete_item, name="delete-item"),

    path("api/v1/lidarr", views.lidarr_youtubarr_view, name="lidarr-youtubarr"),
    path("healthz", views.healthz, name="health"),
]
