from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from database import TrackerDatabase
from music_keys import build_music_update_id
from obsidian_sync import parse_music_markdown, sync_music_status_from_markdown


class ObsidianSyncTests(unittest.TestCase):
    def test_parse_music_table_reads_pending_and_listened_status(self) -> None:
        items = parse_music_markdown(
            "\n".join(
                [
                    "# Music",
                    "",
                    "| 歌曲名 | 日期 | 專輯 | 歌手 | 完成 |",
                    "| --- | --- | --- | --- | --- |",
                    "| Summer Rain | 2026-07-03 | A Flower Bookmark | IU | - |",
                    "| New Song | 2026 |  | SEVENTEEN |  |",
                ]
            )
        )

        self.assertEqual(items[0].title, "Summer Rain")
        self.assertEqual(items[0].publish_date, "2026-07-03")
        self.assertEqual(items[0].album, "A Flower Bookmark")
        self.assertEqual(items[0].artist_name, "IU")
        self.assertEqual(items[0].status, "listened")
        self.assertEqual(items[1].status, "pending")

    def test_sync_music_status_deletes_completed_rows_from_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            music_file = root / "Music.md"
            music_file.write_text(
                "# Music\n\n"
                "| 歌曲名 | 日期 | 專輯 | 歌手 | 完成 |\n"
                "| --- | --- | --- | --- | --- |\n"
                "| Summer Rain | 2026-07-03 |  | IU | - |\n"
                "| New Song | 2026 |  | SEVENTEEN |  |\n",
                encoding="utf-8",
            )

            with TrackerDatabase(root / "tracker.db") as database:
                count = sync_music_status_from_markdown(root, database)
                listened_id = build_music_update_id("IU", "Summer Rain")
                pending_id = build_music_update_id("SEVENTEEN", "New Song")

                content = music_file.read_text(encoding="utf-8")
                self.assertEqual(count, 2)
                self.assertEqual(database.get_status("music", listened_id), "listened")
                self.assertEqual(database.get_status("music", pending_id), "pending")
                self.assertNotIn("Summer Rain", content)
                self.assertIn("New Song", content)

    def test_separator_rows_are_not_parsed_as_music_items(self) -> None:
        items = parse_music_markdown(
            "\n".join(
                [
                    "| 歌曲名 | 日期 | 專輯 | 歌手 | 完成 |",
                    "|------|------|------|------|------|",
                    "| New Song | 2026 |  | SEVENTEEN |  |",
                ]
            )
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "New Song")


if __name__ == "__main__":
    unittest.main()
