from __future__ import annotations

import json
import urllib.parse
import urllib.request

from config_loader import MusicArtist
from database import MediaUpdate
from music_keys import build_canonical_music_key, build_music_update_id


class ITunesClient:
    api_root = "https://itunes.apple.com"

    def __init__(self, countries: list[str] | str | None = None) -> None:
        if countries is None:
            self.countries = ["TW"]
        elif isinstance(countries, str):
            self.countries = [countries.strip().upper()]
        else:
            self.countries = [
                country.strip().upper()
                for country in countries
                if country.strip()
            ]

    def get_artist_tracks(
        self,
        artist: MusicArtist,
        limit: int = 100,
    ) -> list[MediaUpdate]:
        tracks: list[MediaUpdate] = []
        seen_keys: set[str] = set()
        per_country_limit = max(limit, 1)
        for country in self.countries:
            artist_id = artist.artist_id or self._find_artist_id(artist.name, country)
            if not artist_id:
                continue

            payload = self._lookup_artist_tracks(artist_id, country, per_country_limit)
            for track in self._tracks_from_payload(payload, artist):
                key = build_canonical_music_key(
                    track.artist_name,
                    track.title,
                    track.album,
                )
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                tracks.append(track)

        tracks.sort(key=lambda update: update.publish_date, reverse=True)
        return tracks[:limit]

    def _tracks_from_payload(
        self,
        payload: dict,
        artist: MusicArtist,
    ) -> list[MediaUpdate]:
        tracks: list[MediaUpdate] = []
        for item in payload.get("results", []):
            if item.get("wrapperType") != "track" or item.get("kind") != "song":
                continue

            title = item.get("trackName", "").strip()
            artist_name = artist.name
            album = item.get("collectionName", "").strip()
            publish_date = item.get("releaseDate", "")[:10] or "Unknown date"

            if not title:
                continue

            tracks.append(
                MediaUpdate(
                    update_id=build_music_update_id(artist_name, title, album),
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

    def _find_artist_id(self, artist_name: str, country: str) -> str:
        params = urllib.parse.urlencode(
            {
                "term": artist_name,
                "country": country,
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

    def _lookup_artist_tracks(self, artist_id: str, country: str, limit: int) -> dict:
        params = urllib.parse.urlencode(
            {
                "id": artist_id,
                "country": country,
                "entity": "song",
                "limit": str(limit),
            }
        )
        return self._get_json(f"{self.api_root}/lookup?{params}")

    def _get_json(self, url: str) -> dict:
        request = urllib.request.Request(url)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
