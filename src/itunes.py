from __future__ import annotations

import json
import urllib.parse
import urllib.request

from config_loader import MusicArtist
from database import MediaUpdate
from music_keys import build_music_update_id


class ITunesClient:
    api_root = "https://itunes.apple.com"

    def __init__(self, country: str = "TW") -> None:
        self.country = country

    def get_artist_tracks(
        self,
        artist: MusicArtist,
        limit: int = 100,
    ) -> list[MediaUpdate]:
        artist_id = artist.artist_id or self._find_artist_id(artist.name)
        if not artist_id:
            return []

        payload = self._lookup_artist_tracks(artist_id, limit)
        tracks: list[MediaUpdate] = []
        for item in payload.get("results", []):
            if item.get("wrapperType") != "track" or item.get("kind") != "song":
                continue

            title = item.get("trackName", "").strip()
            artist_name = item.get("artistName", artist.name).strip()
            album = item.get("collectionName", "").strip()
            publish_date = item.get("releaseDate", "")[:10] or "Unknown date"
            track_id = str(item.get("trackId") or "")

            if not title:
                continue

            tracks.append(
                MediaUpdate(
                    update_id=track_id or build_music_update_id(artist_name, title, album),
                    platform="music",
                    artist_name=artist_name,
                    title=title,
                    album=album,
                    url=item.get("trackViewUrl", ""),
                    publish_date=publish_date,
                    kind="Song (iTunes)",
                )
            )
        return tracks

    def _find_artist_id(self, artist_name: str) -> str:
        params = urllib.parse.urlencode(
            {
                "term": artist_name,
                "country": self.country,
                "media": "music",
                "entity": "musicArtist",
                "attribute": "artistTerm",
                "limit": "10",
            }
        )
        payload = self._get_json(f"{self.api_root}/search?{params}")
        artists = payload.get("results", [])
        if not artists:
            return ""

        exact = [
            item
            for item in artists
            if item.get("artistName", "").casefold() == artist_name.casefold()
        ]
        selected = exact[0] if exact else artists[0]
        return str(selected.get("artistId") or "")

    def _lookup_artist_tracks(self, artist_id: str, limit: int) -> dict:
        params = urllib.parse.urlencode(
            {
                "id": artist_id,
                "country": self.country,
                "entity": "song",
                "limit": str(limit),
            }
        )
        return self._get_json(f"{self.api_root}/lookup?{params}")

    def _get_json(self, url: str) -> dict:
        request = urllib.request.Request(url)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
