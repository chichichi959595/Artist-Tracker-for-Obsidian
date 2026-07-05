from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MusicArtist:
    name: str
    artist_id: str = ""


@dataclass(frozen=True)
class YouTubeChannel:
    name: str
    channel_id: str


@dataclass(frozen=True)
class TrackerOptions:
    music_track_limit: int = 100
    itunes_country: str = "TW"
    music_min_year: int | None = None
    ignore_youtube_shorts: bool = False
    ignore_youtube_live: bool = False


@dataclass(frozen=True)
class Credentials:
    youtube_api_key: str = ""


@dataclass(frozen=True)
class AppConfig:
    music: list[MusicArtist]
    youtube: list[YouTubeChannel]
    obsidian_vault: Path
    output_folder: str
    options: TrackerOptions = field(default_factory=TrackerOptions)
    credentials: Credentials = field(default_factory=Credentials)

    @property
    def output_path(self) -> Path:
        return self.obsidian_vault / self.output_folder


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}. Copy config/config.example.json first."
        )

    raw = json.loads(path.read_text(encoding="utf-8"))

    return AppConfig(
        music=[
            MusicArtist(name=item["name"], artist_id=str(item.get("artist_id", "")))
            for item in raw.get("music", [])
        ],
        youtube=[
            YouTubeChannel(name=item["name"], channel_id=item["channel_id"])
            for item in raw.get("youtube", [])
        ],
        obsidian_vault=Path(raw["obsidian_vault"]).expanduser(),
        output_folder=raw.get("output_folder", "Entertainment"),
        options=_load_options(raw.get("options", {})),
        credentials=_load_credentials(raw.get("credentials", {})),
    )


def _load_options(raw: dict[str, Any]) -> TrackerOptions:
    return TrackerOptions(
        music_track_limit=int(raw.get("music_track_limit", 100)),
        itunes_country=str(raw.get("itunes_country", "TW")),
        music_min_year=_optional_int(raw.get("music_min_year")),
        ignore_youtube_shorts=bool(raw.get("ignore_youtube_shorts", False)),
        ignore_youtube_live=bool(raw.get("ignore_youtube_live", False)),
    )


def _load_credentials(raw: dict[str, Any]) -> Credentials:
    return Credentials(
        youtube_api_key=str(raw.get("youtube_api_key", "")),
    )


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)
