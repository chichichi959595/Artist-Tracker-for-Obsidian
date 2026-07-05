from __future__ import annotations

from datetime import datetime
from pathlib import Path

from database import MediaUpdate


MUSIC_TABLE_HEADER = "| 歌曲名 | 日期 | 專輯 | 歌手 | 完成 |"
MUSIC_TABLE_SEPARATOR = "| --- | --- | --- | --- | --- |"


class MarkdownWriter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def append_music(self, updates: list[MediaUpdate]) -> None:
        if not updates:
            return

        path = self.output_dir / "Music.md"
        if not path.exists():
            path.write_text(_music_table_document([]), encoding="utf-8")
        elif MUSIC_TABLE_HEADER not in path.read_text(encoding="utf-8"):
            with path.open("a", encoding="utf-8") as file:
                file.write(f"\n{MUSIC_TABLE_HEADER}\n{MUSIC_TABLE_SEPARATOR}\n")

        rows = [_format_music_table_row(update) for update in updates]
        with path.open("a", encoding="utf-8") as file:
            file.write("\n".join(rows) + "\n")

    def append_youtube(self, updates: list[MediaUpdate]) -> None:
        self._append_updates(
            filename="YouTube.md",
            title="# YouTube",
            section="## 未觀看",
            updates=updates,
            formatter=_format_youtube_item,
        )

    def _append_updates(
        self,
        filename: str,
        title: str,
        section: str,
        updates: list[MediaUpdate],
        formatter,
    ) -> None:
        if not updates:
            return

        path = self.output_dir / filename
        if not path.exists():
            path.write_text(
                f"{title}\n\nLast Update: {self._timestamp()}\n\n{section}\n\n",
                encoding="utf-8",
            )

        lines = [f"\n<!-- Tracker Update: {self._timestamp()} -->\n"]
        lines.extend(formatter(update) for update in updates)
        with path.open("a", encoding="utf-8") as file:
            file.write("\n".join(lines) + "\n")

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M")


def _music_table_document(rows: list[str]) -> str:
    lines = [
        "# Music",
        "",
        f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        MUSIC_TABLE_HEADER,
        MUSIC_TABLE_SEPARATOR,
    ]
    lines.extend(rows)
    return "\n".join(lines) + "\n"


def _format_music_table_row(update: MediaUpdate) -> str:
    return (
        f"| {_escape_table_cell(update.title)} "
        f"| {_escape_table_cell(update.publish_date)} "
        f"| {_escape_table_cell(update.album)} "
        f"| {_escape_table_cell(update.artist_name)} "
        "|  |"
    )


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _format_youtube_item(update: MediaUpdate) -> str:
    duration_line = f"  - {update.duration}\n" if update.duration else ""
    return (
        f"- [ ] {update.title}\n"
        f"  - {update.publish_date}\n"
        f"{duration_line}"
        f"  - {update.url}\n"
    )
