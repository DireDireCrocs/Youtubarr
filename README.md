# 🎵 Tubarr

Tubarr is a bridge between YouTube playlists and Lidarr.
It lets you sync YouTube playlists (e.g. "Liked Music" or your own playlists) into Lidarr as import lists, so Lidarr can automatically manage your music library.

# 🚀 Features

- Add YouTube playlists by ID.
- Automatically fetch videos and guess artist/title metadata.
- Expose a Lidarr-compatible Import List feed (/api/v1/lidarr?token=YOUR_TOKEN).
- Web interface with playlist management.
- Built with Django + Celery + Redis.
- Optional: OAuth2 support to fetch your Liked Music playlist (LM).

# 🛠 Requirements

- Docker & Docker Compose
- Redis (comes with docker-compose.yml)
- Google Cloud API Key (and OAuth2 credentials for "Liked Music" support)

# 🔑 Setup Google Cloud API keys
## Option A: Simple (API Key only)

1. Go to Google Cloud Console.
2. Enable the YouTube Data API v3.
3. Create an API key.
4. Copy the key and put it in .env:
```
YOUTUBE_API_KEY=your_api_key_here
```

⚠️ With API key only, you can access public playlists, but not your “Liked Music” (LM) playlist.

## Option B: OAuth2 (for LM / private playlists)

In Google Cloud Console:

- Create OAuth 2.0 Client ID (TVs and Limited Input devices).
- Go to "Google Auth Platform", then "Audience" and add yourself to the Test Users.

In your terminal:
- pip install ytmusicapi
- ytmusicapi oauth
- Follow the instructions to get your oauth.json, which you need to put in the directory you mount to /data

# ⚡ Running Tubarr

Clone the repo and build:
```
docker compose build
docker compose up -d
```

# 🎵 Adding Playlists

- Go to /playlists in the web UI.
- Paste your YouTube playlist ID.

Examples:
```
PL1234abcd
LM (only works if you did the OAuth2 procedure)
```

# 🎼 Connecting to Lidarr

- In Lidarr, go to Settings → Import Lists → + → New List.
- Select **Custom List** at the very bottom.
- Use this URL:

````
http://localhost:8000/api/v1/lidarr?token=YOUR_TOKEN
```

- Replace YOUR_TOKEN with your LIDARR_TOKEN from .env.
- Save it.

Lidarr will now treat Tubarr as a source of artists.