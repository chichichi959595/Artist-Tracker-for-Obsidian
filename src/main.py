from __future__ import annotations

import argparse
import logging
from pathlib import Path

from config_loader import load_config
from database import MediaUpdate, TrackerDatabase
from env_loader import load_dotenv
from itunes import ITunesClient
from markdown_writer import MarkdownWriter
from music_keys import build_music_update_id
from obsidian_sync import parse_music_markdown, sync_music_status_from_markdown
from youtube import YouTubeClient


def main() -> int:
    args = parse_args()
    load_dotenv()
    setup_logging(args.log_level)

    config = load_config(args.config)
    writer = MarkdownWriter(config.output_path)

    with TrackerDatabase(args.db) as database:
        synced_count = sync_music_status_from_markdown(config.output_path, database)
        if synced_count:
            logging.info("Synced %s music status item(s) from Obsidian.", synced_count)

        restored_count = restore_missing_pending_music(config, database, writer)
        if restored_count:
            logging.info(
                "Restored %s pending music item(s) from SQLite.",
                restored_count,
            )

        if not args.youtube_only:
            run_music(config, database, writer)
        if not args.music_only:
            run_youtube(config, database, writer)

    logging.info("Tracker finished.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Track media updates into Obsidian.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.json"),
        help="Path to config JSON.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/tracker.db"),
        help="Path to SQLite database.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument("--music-only", action="store_true")
    parser.add_argument("--youtube-only", action="store_true")
    return parser.parse_args()


def setup_logging(log_level: str) -> None:
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs/tracker.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def run_music(config, database: TrackerDatabase, writer: MarkdownWriter) -> None:
    client = ITunesClient(config.options.itunes_country)

    new_updates: list[MediaUpdate] = []
    for artist in config.music:
        artist_id = artist.artist_id or artist.name
        database.upsert_artist("itunes", artist_id, artist.name)
        tracks = client.get_artist_tracks(
            artist,
            limit=config.options.music_track_limit,
        )
        tracks = _filter_music_by_min_year(
            tracks,
            config.options.music_min_year,
        )
        fresh = _filter_new(database, tracks)
        new_updates.extend(fresh)
        logging.info("iTunes %s: %s new update(s).", artist.name, len(fresh))

    writer.append_music(new_updates)
    _save_updates(database, new_updates)


def run_youtube(config, database: TrackerDatabase, writer: MarkdownWriter) -> None:
    client = YouTubeClient(config.credentials.youtube_api_key)
    if not client.is_configured():
        logging.warning("YouTube API key not configured. Skipping YouTube.")
        return

    new_updates: list[MediaUpdate] = []
    for channel in config.youtube:
        database.upsert_artist("youtube", channel.channel_id, channel.name)
        videos = client.get_channel_videos(
            channel,
            ignore_shorts=config.options.ignore_youtube_shorts,
            ignore_live=config.options.ignore_youtube_live,
        )
        fresh = _filter_new(database, videos)
        new_updates.extend(fresh)
        logging.info("YouTube %s: %s new update(s).", channel.name, len(fresh))

    writer.append_youtube(new_updates)
    _save_updates(database, new_updates)


def restore_missing_pending_music(
    config,
    database: TrackerDatabase,
    writer: MarkdownWriter,
) -> int:
    configured_artists = {artist.name for artist in config.music}
    pending_updates = database.pending_music_for_artists(configured_artists)
    if not pending_updates:
        return 0

    visible_ids = _visible_music_update_ids(config.output_path / "Music.md")
    missing_updates = [
        update for update in pending_updates if update.update_id not in visible_ids
    ]
    writer.append_music(missing_updates)
    return len(missing_updates)


def _visible_music_update_ids(music_file: Path) -> set[str]:
    if not music_file.exists():
        return set()

    return {
        build_music_update_id(item.artist_name, item.title, item.album)
        for item in parse_music_markdown(music_file.read_text(encoding="utf-8"))
        if item.status == "pending"
    }


def _filter_new(
    database: TrackerDatabase,
    updates: list[MediaUpdate],
) -> list[MediaUpdate]:
    return [
        update
        for update in updates
        if not database.has_update(update.platform, update.update_id)
    ]


def _filter_music_by_min_year(
    updates: list[MediaUpdate],
    min_year: int | None,
) -> list[MediaUpdate]:
    if min_year is None:
        return updates

    return [
        update
        for update in updates
        if _publish_year(update.publish_date) >= min_year
    ]


def _publish_year(publish_date: str) -> int:
    if len(publish_date) < 4 or not publish_date[:4].isdigit():
        return 0
    return int(publish_date[:4])


def _save_updates(database: TrackerDatabase, updates: list[MediaUpdate]) -> None:
    for update in updates:
        database.save_update(update, written=True)


if __name__ == "__main__":
    raise SystemExit(main())
