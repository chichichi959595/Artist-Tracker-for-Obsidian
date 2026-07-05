from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from config_loader import YouTubeChannel
from database import MediaUpdate


class YouTubeClient:
    api_base_url = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_channel_videos(
        self,
        channel: YouTubeChannel,
        ignore_shorts: bool = False,
        ignore_live: bool = False,
        max_results: int = 10,
    ) -> list[MediaUpdate]:
        search_payload = self._search_channel(channel.channel_id, max_results)
        video_ids = [
            item["id"]["videoId"]
            for item in search_payload.get("items", [])
            if item.get("id", {}).get("videoId")
        ]
        if not video_ids:
            return []

        details = self._get_video_details(video_ids)
        updates: list[MediaUpdate] = []
        for item in details.get("items", []):
            snippet = item.get("snippet", {})
            content_details = item.get("contentDetails", {})
            live_details = item.get("liveStreamingDetails")
            duration = content_details.get("duration", "")

            if ignore_live and live_details:
                continue
            if ignore_shorts and _is_probable_short(duration):
                continue

            updates.append(
                MediaUpdate(
                    update_id=item["id"],
                    platform="youtube",
                    artist_name=channel.name,
                    title=snippet.get("title", ""),
                    url=f"https://www.youtube.com/watch?v={item['id']}",
                    publish_date=snippet.get("publishedAt", "")[:10],
                    kind="Video",
                    duration=_format_iso8601_duration(duration),
                )
            )
        return updates

    def _search_channel(self, channel_id: str, max_results: int) -> dict:
        query = urllib.parse.urlencode(
            {
                "part": "snippet",
                "channelId": channel_id,
                "maxResults": str(max_results),
                "order": "date",
                "type": "video",
                "key": self.api_key,
            }
        )
        return _get_json(f"{self.api_base_url}/search?{query}")

    def _get_video_details(self, video_ids: list[str]) -> dict:
        query = urllib.parse.urlencode(
            {
                "part": "snippet,contentDetails,liveStreamingDetails",
                "id": ",".join(video_ids),
                "key": self.api_key,
            }
        )
        return _get_json(f"{self.api_base_url}/videos?{query}")


def _get_json(url: str) -> dict:
    request = urllib.request.Request(url)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _is_probable_short(duration: str) -> bool:
    seconds = _duration_to_seconds(duration)
    return 0 < seconds <= 60


def _format_iso8601_duration(duration: str) -> str:
    seconds = _duration_to_seconds(duration)
    if seconds <= 0:
        return duration
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _duration_to_seconds(duration: str) -> int:
    if not duration.startswith("PT"):
        return 0

    total = 0
    current = ""
    for char in duration[2:]:
        if char.isdigit():
            current += char
            continue
        if not current:
            continue
        value = int(current)
        current = ""
        if char == "H":
            total += value * 3600
        elif char == "M":
            total += value * 60
        elif char == "S":
            total += value
    return total
