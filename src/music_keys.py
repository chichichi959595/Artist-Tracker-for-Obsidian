from __future__ import annotations

import re


def build_music_update_id(artist_name: str, title: str, album: str = "") -> str:
    parts = [_normalize(artist_name), _normalize(title)]
    if album:
        parts.append(_normalize(album))
    return ":".join(parts)


def build_canonical_music_key(artist_name: str, title: str, album: str = "") -> str:
    parts = [
        _normalize(artist_name),
        _canonical_title(title),
    ]
    if album:
        parts.append(_canonical_album(album))
    return ":".join(part for part in parts if part)


def _normalize(value: str) -> str:
    value = value.casefold().strip()
    return re.sub(r"\s+", " ", value)


def _canonical_title(value: str) -> str:
    value = _normalize(value)
    value = re.sub(r"\s*[-–—]\s*(single|ep|album|edit|remaster(?:ed)?|version)\b.*$", "", value)
    value = re.sub(r"\s*\([^)]*(?:version|ver\.?|remaster(?:ed)?|edit|mix|feat\.?|featuring|instrumental|karaoke|japanese|english|chinese|mandarin|korean|acoustic|live)[^)]*\)", "", value)
    value = re.sub(r"\s*\[[^\]]*(?:version|ver\.?|remaster(?:ed)?|edit|mix|feat\.?|featuring|instrumental|karaoke|japanese|english|chinese|mandarin|korean|acoustic|live)[^\]]*\]", "", value)
    value = re.sub(r"\s+(feat\.?|featuring)\s+.+$", "", value)
    return _normalize(value)


def _canonical_album(value: str) -> str:
    value = _normalize(value)
    value = re.sub(r"\s*[-–—]\s*(single|ep)$", "", value)
    value = re.sub(r"\s*\([^)]*(?:single|ep|version|ver\.?)[^)]*\)", "", value)
    return _normalize(value)
