from __future__ import annotations

import re


def build_music_update_id(artist_name: str, title: str, album: str = "") -> str:
    parts = [_normalize(artist_name), _normalize(title)]
    if album:
        parts.append(_normalize(album))
    return ":".join(parts)


def _normalize(value: str) -> str:
    value = value.casefold().strip()
    return re.sub(r"\s+", " ", value)
