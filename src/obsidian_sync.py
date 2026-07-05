from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from database import MediaUpdate, TrackerDatabase
from music_keys import build_music_update_id


MUSIC_TABLE_HEADER = "| 歌曲名 | 日期 | 專輯 | 歌手 | 完成 |"
MUSIC_TABLE_SEPARATOR = "| --- | --- | --- | --- | --- |"


@dataclass(frozen=True)
class ParsedMusicItem:
    artist_name: str
    title: str
    publish_date: str
    album: str
    status: str

    @property
    def update(self) -> MediaUpdate:
        return MediaUpdate(
            update_id=build_music_update_id(
                self.artist_name,
                self.title,
                self.album,
            ),
            platform="music",
            artist_name=self.artist_name,
            title=self.title,
            url="",
            publish_date=self.publish_date,
            album=self.album,
        )


def sync_music_status_from_markdown(
    output_dir: Path,
    database: TrackerDatabase,
) -> int:
    music_file = output_dir / "Music.md"
    if not music_file.exists():
        return 0

    content = music_file.read_text(encoding="utf-8")
    items = parse_music_markdown(content)
    count = 0
    kept_items: list[ParsedMusicItem] = []

    for item in items:
        update = item.update
        database.save_update(update, written=True, status=item.status)
        database.update_status(update.platform, update.update_id, item.status)
        count += 1

        if item.status != "listened":
            kept_items.append(item)

    if len(kept_items) != len(items):
        music_file.write_text(build_music_table_document(kept_items), encoding="utf-8")

    return count


def parse_music_markdown(content: str) -> list[ParsedMusicItem]:
    items: list[ParsedMusicItem] = []
    for line in content.splitlines():
        if not _is_table_data_row(line):
            continue

        cells = _split_table_row(line)
        if len(cells) != 5:
            continue

        title, publish_date, album, artist_name, done = cells
        if _is_separator_cells(cells):
            continue
        if not title or not artist_name:
            continue

        items.append(
            ParsedMusicItem(
                artist_name=artist_name,
                title=title,
                publish_date=publish_date or "Unknown date",
                album=album,
                status="listened" if done.strip() == "-" else "pending",
            )
        )
    return items


def build_music_table_document(items: list[ParsedMusicItem]) -> str:
    lines = [
        "# Music",
        "",
        MUSIC_TABLE_HEADER,
        MUSIC_TABLE_SEPARATOR,
    ]
    lines.extend(_format_table_row(item) for item in items)
    return "\n".join(lines) + "\n"


def _is_table_data_row(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return False

    cells = _split_table_row(stripped)
    if [cell.strip() for cell in cells] == ["歌曲名", "日期", "專輯", "歌手", "完成"]:
        return False
    if _is_separator_cells(cells):
        return False
    return True


def _is_separator_cells(cells: list[str]) -> bool:
    if not cells:
        return False
    normalized = [cell.replace(" ", "") for cell in cells]
    return all(cell and set(cell) <= {"-", ":"} for cell in normalized)


def _split_table_row(line: str) -> list[str]:
    cells: list[str] = []
    current = ""
    escaped = False

    for char in line.strip()[1:-1]:
        if escaped:
            current += char
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "|":
            cells.append(current.strip())
            current = ""
            continue
        current += char

    cells.append(current.strip())
    return cells


def _format_table_row(item: ParsedMusicItem) -> str:
    done = "-" if item.status == "listened" else ""
    return (
        f"| {_escape_table_cell(item.title)} "
        f"| {_escape_table_cell(item.publish_date)} "
        f"| {_escape_table_cell(item.album)} "
        f"| {_escape_table_cell(item.artist_name)} "
        f"| {done} |"
    )


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()
