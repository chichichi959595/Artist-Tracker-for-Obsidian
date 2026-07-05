from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from database import MediaUpdate
from markdown_writer import MarkdownWriter


class MarkdownWriterTests(unittest.TestCase):
    def test_append_music_writes_table_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            writer = MarkdownWriter(output_dir)
            writer.append_music(
                [
                    MediaUpdate(
                        update_id="1",
                        platform="music",
                        artist_name="IU",
                        title="Summer Rain",
                        album="A Flower Bookmark",
                        url="https://example.com",
                        publish_date="2026-07-03",
                        kind="Single",
                    )
                ]
            )

            content = (output_dir / "Music.md").read_text(encoding="utf-8")
            self.assertIn("| 歌曲名 | 日期 | 專輯 | 歌手 | 完成 |", content)
            self.assertIn("| Summer Rain | 2026-07-03 | A Flower Bookmark | IU |  |", content)


if __name__ == "__main__":
    unittest.main()
