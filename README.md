# Personal Media Tracker

把你關心的內容更新自動整理到 Obsidian。音樂來源使用 Apple iTunes Search API，預設只查台灣 storefront；YouTube 仍可用來追蹤頻道影片。

## Features

- Track music from Apple iTunes Search API with `country=TW`.
- Track YouTube channel videos.
- Write music items to an Obsidian table.
- Remove completed music rows when the `完成` column is `-`.
- Restore deleted pending music rows from SQLite.
- Append new YouTube items to an Obsidian checklist.
- Config-driven, no GUI.

## Setup

Copy the example files:

```powershell
Copy-Item config\config.example.json config\config.json
Copy-Item .env.example .env
```

Edit `config/config.json`:

```json
{
  "music": [
    { "name": "SEVENTEEN", "artist_id": "" },
    { "name": "IU", "artist_id": "" }
  ],
  "youtube": [
    { "name": "SEVENTEEN", "channel_id": "UC..." }
  ],
  "obsidian_vault": "C:/Users/Hayden Ho/Desktop/notes",
  "output_folder": "_固定/Entertainment",
  "options": {
    "itunes_countries": ["TW"],
    "music_track_limit": 100,
    "music_min_year": null,
    "ignore_youtube_shorts": false,
    "ignore_youtube_live": false
  }
}
```

Edit `.env` only if you use YouTube:

```text
YOUTUBE_API_KEY=your-youtube-api-key
```

iTunes Search API does not need an API key. The default `itunes_countries` is `["TW"]` to keep results cleaner. You can still add other storefronts later, but that may introduce duplicate localized releases.

## Artist Accuracy

You can leave `artist_id` empty. The script will search iTunes by artist name first.

If results are wrong, fill `artist_id` with the iTunes artist ID. You can find it from an Apple Music / iTunes artist URL. For example, if the URL ends with:

```text
/artist/iu/1249595
```

then use:

```json
{ "name": "IU", "artist_id": "1249595" }
```

## Run

```powershell
python src/main.py
```

Useful options:

```powershell
python src/main.py --music-only
python src/main.py --youtube-only
python src/main.py --config config/config.json --db data/tracker.db --log-level DEBUG
```

To clear only music rows from SQLite before reloading:

```powershell
python scripts/clear_music_db.py
```

If `Music.md` is created but empty, check `music_min_year`. Setting it to `2026` only keeps tracks released in 2026 or later; setting it to `null` shows all fetched tracks.

## Results

The tracker writes to:

```text
<obsidian_vault>/<output_folder>/Music.md
<obsidian_vault>/<output_folder>/YouTube.md
```

`Music.md` uses a table:

```markdown
| 歌曲名 | 日期 | 專輯 | 歌手 | 完成 |
| --- | --- | --- | --- | --- |
| Summer Rain | 2026-07-03 | A Flower Bookmark | IU |  |
```

When you finish listening, type `-` in the `完成` column:

```markdown
| Summer Rain | 2026-07-03 | A Flower Bookmark | IU | - |
```

The next time you run the script, that row is removed from `Music.md`, and SQLite stores the item as `listened`.

If you accidentally delete pending rows or the whole music table from Obsidian, the script restores any `pending` music rows from `data/tracker.db` as long as that artist is still listed in `config/config.json`. Rows marked `listened` are not restored.
