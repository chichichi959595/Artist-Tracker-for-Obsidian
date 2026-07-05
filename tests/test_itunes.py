from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config_loader import MusicArtist
from itunes import ITunesClient


class ITunesClientTests(unittest.TestCase):
    def test_get_artist_tracks_maps_song_results(self) -> None:
        client = FakeITunesClient()

        tracks = client.get_artist_tracks(MusicArtist(name="IU", artist_id="123"))

        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].title, "Summer Rain")
        self.assertEqual(tracks[0].album, "A Flower Bookmark")
        self.assertEqual(tracks[0].artist_name, "IU")
        self.assertEqual(tracks[0].publish_date, "2026-07-03")
        self.assertEqual(tracks[0].update_id, "456")

    def test_find_artist_id_prefers_exact_artist_name(self) -> None:
        client = FakeITunesClient()

        self.assertEqual(client._find_artist_id("IU"), "123")


class FakeITunesClient(ITunesClient):
    def __init__(self) -> None:
        super().__init__("TW")

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


if __name__ == "__main__":
    unittest.main()
