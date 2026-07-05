from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config_loader import MusicArtist
from itunes import ITunesClient
from music_keys import build_canonical_music_key, build_music_update_id


class ITunesClientTests(unittest.TestCase):
    def test_get_artist_tracks_maps_song_results(self) -> None:
        client = FakeITunesClient()

        tracks = client.get_artist_tracks(MusicArtist(name="IU", artist_id="123"))

        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].title, "Summer Rain")
        self.assertEqual(tracks[0].album, "A Flower Bookmark")
        self.assertEqual(tracks[0].artist_name, "IU")
        self.assertEqual(tracks[0].publish_date, "2026-07-03")
        self.assertEqual(
            tracks[0].update_id,
            build_music_update_id("IU", "Summer Rain", "A Flower Bookmark"),
        )

    def test_find_artist_id_prefers_exact_artist_name(self) -> None:
        client = FakeITunesClient()

        self.assertEqual(client._find_artist_id("IU", "TW"), "123")

    def test_get_artist_tracks_uses_configured_artist_name_for_display(self) -> None:
        client = LocalizedArtistITunesClient()

        tracks = client.get_artist_tracks(MusicArtist(name="Olivia Rodrigo", artist_id="123"))

        self.assertEqual(tracks[0].artist_name, "Olivia Rodrigo")

    def test_get_artist_tracks_deduplicates_across_storefront_versions(self) -> None:
        client = DuplicateITunesClient(["TW", "US"])

        tracks = client.get_artist_tracks(MusicArtist(name="IU", artist_id="123"))

        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].title, "Summer Rain")

    def test_canonical_key_ignores_common_version_suffixes(self) -> None:
        self.assertEqual(
            build_canonical_music_key("IU", "Summer Rain (Japanese Version)", "Album"),
            build_canonical_music_key("iu", "Summer Rain", "Album"),
        )


class FakeITunesClient(ITunesClient):
    def __init__(self) -> None:
        super().__init__(["TW"])

    def _get_json(self, url: str) -> dict:
        if "/search?" in url:
            return {
                "results": [
                    {"artistName": "Not IU", "artistId": 999},
                    {"artistName": "IU", "artistId": 123},
                ]
            }
        return {
            "results": [
                {"wrapperType": "artist", "artistName": "IU"},
                {
                    "wrapperType": "track",
                    "kind": "song",
                    "trackId": 456,
                    "trackName": "Summer Rain",
                    "collectionName": "A Flower Bookmark",
                    "artistName": "IU",
                    "releaseDate": "2026-07-03T12:00:00Z",
                    "trackViewUrl": "https://example.com",
                },
                {
                    "wrapperType": "track",
                    "kind": "music-video",
                    "trackName": "Video",
                },
            ]
        }


class DuplicateITunesClient(ITunesClient):
    def _get_json(self, url: str) -> dict:
        return {
            "results": [
                {"wrapperType": "artist", "artistName": "IU"},
                {
                    "wrapperType": "track",
                    "kind": "song",
                    "trackId": 1,
                    "trackName": "Summer Rain",
                    "collectionName": "Album",
                    "artistName": "IU",
                    "releaseDate": "2026-07-03T12:00:00Z",
                },
                {
                    "wrapperType": "track",
                    "kind": "song",
                    "trackId": 2,
                    "trackName": "Summer Rain (Japanese Version)",
                    "collectionName": "Album",
                    "artistName": "IU",
                    "releaseDate": "2026-07-03T12:00:00Z",
                },
            ]
        }


class LocalizedArtistITunesClient(ITunesClient):
    def __init__(self) -> None:
        super().__init__(["TW"])

    def _get_json(self, url: str) -> dict:
        return {
            "results": [
                {
                    "wrapperType": "track",
                    "kind": "song",
                    "trackId": 1,
                    "trackName": "drivers license",
                    "collectionName": "SOUR",
                    "artistName": "オリヴィア・ロドリゴ",
                    "releaseDate": "2021-01-08T12:00:00Z",
                }
            ]
        }


if __name__ == "__main__":
    unittest.main()
