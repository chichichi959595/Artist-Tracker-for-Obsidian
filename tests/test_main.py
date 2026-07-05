from __future__ import annotations

import sys
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from database import MediaUpdate
from database import TrackerDatabase
from main import _filter_music_by_min_year, restore_missing_pending_music
from markdown_writer import MarkdownWriter
from music_keys import build_music_update_id


class MainFilterTests(unittest.TestCase):
    def test_filters_music_before_min_year(self) -> None:
        updates = [
            _dated_update("old", "2025-12-31"),
            _dated_update("new", "2026-01-01"),
            _dated_update("year-only", "2026"),
            _dated_update("unknown", "Unknown date"),
        ]

        filtered = _filter_music_by_min_year(updates, 2026)

        self.assertEqual([item.title for item in filtered], ["new", "year-only"])

    def test_restore_missing_pending_music_recreates_deleted_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = SimpleNamespace(
                output_path=root,
                music=[SimpleNamespace(name="IU")],
            )

            with TrackerDatabase(root / "tracker.db") as database:
                database.save_update(_artist_update("Summer Rain", "IU"))

                restored = restore_missing_pending_music(
                    config,
                    database,
                    MarkdownWriter(root),
                )

            content = (root / "Music.md").read_text(encoding="utf-8")
            self.assertEqual(restored, 1)
            self.assertIn("Summer Rain", content)

    def test_restore_missing_pending_music_does_not_duplicate_visible_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Music.md").write_text(
                "# Music\n\n"
                "| 歌曲名 | 日期 | 專輯 | 歌手 | 完成 |\n"
                "| --- | --- | --- | --- | --- |\n"
                "| Summer Rain | 2026-07-03 |  | IU |  |\n",
                encoding="utf-8",
            )
            config = SimpleNamespace(
                output_path=root,
                music=[SimpleNamespace(name="IU")],
            )

            with TrackerDatabase(root / "tracker.db") as database:
                database.save_update(_artist_update("Summer Rain", "IU"))

                restored = restore_missing_pending_music(
                    config,
                    database,
                    MarkdownWriter(root),
                )

            content = (root / "Music.md").read_text(encoding="utf-8")
            self.assertEqual(restored, 0)
            self.assertEqual(content.count("Summer Rain"), 1)


def _dated_update(title: str, publish_date: str) -> MediaUpdate:
    return MediaUpdate(
        update_id=title,
        platform="music",
        artist_name="Artist",
        title=title,
        url="https://example.com",
        publish_date=publish_date,
        kind="Album",
    )


def _artist_update(title: str, artist_name: str) -> MediaUpdate:
    return MediaUpdate(
        update_id=build_music_update_id(artist_name, title),
        platform="music",
        artist_name=artist_name,
        title=title,
        album="",
        url="https://example.com",
        publish_date="2026-07-03",
    )


if __name__ == "__main__":
    unittest.main()
