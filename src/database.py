from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MediaUpdate:
    update_id: str
    platform: str
    artist_name: str
    title: str
    url: str
    publish_date: str
    album: str = ""
    kind: str = ""
    duration: str = ""


class TrackerDatabase:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "TrackerDatabase":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _create_tables(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS artists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                artist_id TEXT NOT NULL,
                artist_name TEXT NOT NULL,
                UNIQUE(platform, artist_id)
            );

            CREATE TABLE IF NOT EXISTS updates (
                update_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                artist_name TEXT NOT NULL,
                title TEXT NOT NULL,
                album TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL,
                publish_date TEXT NOT NULL,
                written INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                PRIMARY KEY(platform, update_id)
            );
            """
        )
        self._migrate_tables()
        self.connection.commit()

    def _migrate_tables(self) -> None:
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(updates)").fetchall()
        }
        if "status" not in columns:
            self.connection.execute(
                "ALTER TABLE updates ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'"
            )
        if "album" not in columns:
            self.connection.execute(
                "ALTER TABLE updates ADD COLUMN album TEXT NOT NULL DEFAULT ''"
            )

    def upsert_artist(self, platform: str, artist_id: str, artist_name: str) -> None:
        self.connection.execute(
            """
            INSERT INTO artists (platform, artist_id, artist_name)
            VALUES (?, ?, ?)
            ON CONFLICT(platform, artist_id)
            DO UPDATE SET artist_name = excluded.artist_name
            """,
            (platform, artist_id, artist_name),
        )
        self.connection.commit()

    def has_update(self, platform: str, update_id: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM updates WHERE platform = ? AND update_id = ?",
            (platform, update_id),
        ).fetchone()
        return row is not None

    def save_update(
        self,
        update: MediaUpdate,
        written: bool = True,
        status: str = "pending",
    ) -> None:
        self.connection.execute(
            """
            INSERT OR IGNORE INTO updates (
                update_id, platform, artist_name, title, album, url, publish_date, written, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                update.update_id,
                update.platform,
                update.artist_name,
                update.title,
                update.album,
                update.url,
                update.publish_date,
                int(written),
                status,
            ),
        )
        self.connection.commit()

    def update_status(self, platform: str, update_id: str, status: str) -> None:
        self.connection.execute(
            """
            UPDATE updates
            SET status = ?
            WHERE platform = ? AND update_id = ?
            """,
            (status, platform, update_id),
        )
        self.connection.commit()

    def get_status(self, platform: str, update_id: str) -> str | None:
        row = self.connection.execute(
            """
            SELECT status
            FROM updates
            WHERE platform = ? AND update_id = ?
            """,
            (platform, update_id),
        ).fetchone()
        if row is None:
            return None
        return str(row["status"])

    def get_all_music_titles(self, artist_name: str) -> set[str]:
        rows = self.connection.execute(
            """
            SELECT title
            FROM updates
            WHERE platform = 'music' AND artist_name = ?
            """,
            (artist_name,),
        ).fetchall()
        return {str(row["title"]) for row in rows}

    def pending_music_for_artists(self, artist_names: set[str]) -> list[MediaUpdate]:
        normalized_names = {name.casefold() for name in artist_names}
        if not normalized_names:
            return []

        rows = self.connection.execute(
            """
            SELECT update_id, platform, artist_name, title, album, url, publish_date
            FROM updates
            WHERE platform = 'music' AND status = 'pending'
            ORDER BY publish_date DESC, artist_name, title
            """
        ).fetchall()

        updates: list[MediaUpdate] = []
        for row in rows:
            if str(row["artist_name"]).casefold() not in normalized_names:
                continue
            updates.append(
                MediaUpdate(
                    update_id=str(row["update_id"]),
                    platform=str(row["platform"]),
                    artist_name=str(row["artist_name"]),
                    title=str(row["title"]),
                    album=str(row["album"]),
                    url=str(row["url"]),
                    publish_date=str(row["publish_date"]),
                )
            )
        return updates
