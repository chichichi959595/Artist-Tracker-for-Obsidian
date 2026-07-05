from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from database import MediaUpdate, TrackerDatabase


class DatabaseTests(unittest.TestCase):
    def test_save_update_defaults_to_pending_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with TrackerDatabase(Path(tmp) / "tracker.db") as database:
                update = MediaUpdate(
                    update_id="1",
                    platform="music",
                    artist_name="IU",
                    title="Summer Rain",
                    album="A Flower Bookmark",
                    url="https://example.com",
                    publish_date="2026-07-03",
                )

                database.save_update(update)

                self.assertEqual(database.get_status("music", "1"), "pending")

    def test_pending_music_for_artists_filters_by_status_and_artist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with TrackerDatabase(Path(tmp) / "tracker.db") as database:
                database.save_update(_update("1", "IU", "Summer Rain"))
                database.save_update(_update("2", "IU", "Old Song"), status="listened")
                database.save_update(_update("3", "Other", "Other Song"))

                pending = database.pending_music_for_artists({"iu"})

                self.assertEqual([item.title for item in pending], ["Summer Rain"])


def _update(update_id: str, artist_name: str, title: str) -> MediaUpdate:
    return MediaUpdate(
        update_id=update_id,
        platform="music",
        artist_name=artist_name,
        title=title,
        album="",
        url="https://example.com",
        publish_date="2026-07-03",
    )


if __name__ == "__main__":
    unittest.main()
