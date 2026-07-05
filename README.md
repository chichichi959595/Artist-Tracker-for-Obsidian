# Personal Media Tracker

一個自動化將你喜愛的音樂（Apple iTunes）與 YouTube 頻道更新整理到 Obsidian 筆記的工具。

本專案**僅使用 Python 內建標準庫**，不需要執行任何 `pip install`，開箱即用、無額外依賴。

---

## 核心功能 (Features)

1. **iTunes 音樂追蹤**：使用 Apple iTunes Search API，預設台灣地區 (`country=TW`)，追蹤喜愛歌手的最新歌曲。
2. **YouTube 影片追蹤**：追蹤指定頻道的最新影片，支援過濾 Shorts 短影音與 Live 直播。
3. **Obsidian 自動同步與清理**：
   - 音樂更新會以表格形式寫入 `Music.md`。當你聽完歌並在 `完成` 欄位填上 `-`，下次執行時會**自動將該列刪除**，並在資料庫標記為已聽。
   - YouTube 更新會以待辦清單 (`- [ ]`) 形式追加至 `YouTube.md`。
4. **SQLite 備份與防呆機制**：
   - 自動將已抓取的項目寫入 SQLite 資料庫以避免重複新增。
   - 若不小心在 Obsidian 中誤刪了尚未聽完的歌曲列，執行時會自動從資料庫還原（只要該歌手仍在設定檔中）。

---

## 事前準備 (Prerequisites)

- **Python 3.8+** (確認系統已安裝 Python 即可)
- **Obsidian** (需要知道你的 Vault 本地路徑)
- （選用）**YouTube Data API Key**（如果需要追蹤 YouTube 頻道影片才需要申請）

---

## 安裝與設定 (Setup)

### 1. 複製設定檔與環境變數範本

在專案目錄下開啟終端機（Windows PowerShell），執行以下指令複製範本：

```powershell
Copy-Item config\config.example.json config\config.json
Copy-Item .env.example .env
```

---

### 2. 編輯設定檔 `config/config.json`

打開 `config/config.json` 並填入你的設定：

```json
{
  "music": [
    { "name": "楊世暄", "artist_id": "1647124269" },
    { "name": "IU", "artist_id": "1249595" }
  ],
  "youtube": [
    { "name": "SEVENTEEN", "channel_id": "UCm2FQDuvqGbHUp5gOMtL_nQ" }
  ],
  "obsidian_vault": "C:/Users/你的用戶名/Desktop/notes",
  "output_folder": "_固定/Entertainment",
  "options": {
    "itunes_countries": ["TW"],
    "music_track_limit": 100,
    "music_min_year": 2025,
    "ignore_youtube_shorts": false,
    "ignore_youtube_live": false
  }
}
```

#### 欄位說明：
- **`music`**：要追蹤的音樂歌手列表。
  - `name`：歌手名稱（僅作為標示與同步比對用）。
  - `artist_id`：iTunes 歌手 ID。**強烈建議填寫**以保證精準度，若留空 `""` 則會先用名稱搜尋（可能不準）。
- **`youtube`**：要追蹤的 YouTube 頻道列表。
  - `name`：頻道名稱。
  - `channel_id`：YouTube 頻道 ID（格式通常是 `UC...` 開頭）。
- **`obsidian_vault`**：你的 Obsidian Vault 絕對路徑（注意：Windows 路徑中請使用斜線 `/`）。
- **`output_folder`**：Obsidian Vault 內要放置輸出檔案的資料夾路徑。
- **`options`**：
  - `itunes_countries`：查詢 iTunes 的國家代碼（預設 `["TW"]`，亦可增加 `"US"`, `"JP"`, `"KR"` 等，但多國可能會撈出重複的 local 版本）。
  - `music_track_limit`：每次查詢各歌手最多撈取幾首歌。
  - `music_min_year`：只追蹤幾年（含）以後發行的歌曲（設為 `null` 則不限年份）。
  - `ignore_youtube_shorts`：是否忽略 YouTube Shorts 短影音 (`true` / `false`)。
  - `ignore_youtube_live`：是否忽略 YouTube 直播影片 (`true` / `false`)。

---

### 3. 如何尋找 iTunes Artist ID 與 YouTube Channel ID

#### A. 尋找 iTunes Artist ID：
1. 前往網頁版 [Apple Music](https://music.apple.com/)。
2. 搜尋該歌手並進入歌手主頁。
3. 複製瀏覽器網址列，網址結尾的數字即為 ID。
   - *範例*：IU 的網址為 `https://music.apple.com/tw/artist/iu/1249595` -> ID 為 `1249595`。

#### B. 尋找 YouTube Channel ID：
1. 在瀏覽器打開該 YouTube 頻道主頁。
2. 右鍵點選「檢視網頁原始碼」（View Page Source）。
3. 搜尋 `channelId` 或 `UC`，通常會找到類似 `UC-lHJZR3Gqxm24_Vd_AJ5Yw` 這樣的 24 碼字串即為 Channel ID。

---

### 4. 編輯環境變數 `.env` (僅 YouTube 適用)

如果你需要追蹤 YouTube，請打開 `.env` 檔案並填入你的 API 金鑰：

```text
YOUTUBE_API_KEY=你的YouTube_API金鑰
```
*(若只使用音樂追蹤，此檔案可留空。)*

---

## 執行方式 (How to Run)

在專案目錄下執行：

```powershell
python src/main.py
```

### 常用參數選項：

```powershell
# 僅更新音樂
python src/main.py --music-only

# 僅更新 YouTube
python src/main.py --youtube-only

# 自訂設定檔與資料庫路徑，並啟用 DEBUG 日誌
python src/main.py --config config/my_config.json --db data/my_tracker.db --log-level DEBUG
```

### 清理資料庫指令：
如果你想清除資料庫中所有已記錄的音樂，重新讓程式去 iTunes 撈歌並在 Obsidian 重建，可以執行：

```powershell
python scripts/clear_music_db.py
```

---

## 工作原理與同步規則

### 1. 音樂同步 (`Music.md`)
程式會在 `obsidian_vault/output_folder` 下建立 `Music.md`，並使用以下格式的表格：

| 歌曲名 | 日期 | 專輯 | 歌手 | 完成 |
| --- | --- | --- | --- | --- |
| 三菜一湯 In the Middle | 2025-11-18 | 日常 Daily Diner - Single | 楊世暄 |  |

**已聽完的歌曲：**
- 當你聽完歌後，請在該列的 `完成` 欄位填上 `-`。
- 下次執行 `main.py` 時，程式會偵測到 `-`，並將該首歌從 Obsidian 刪除，並在 SQLite 資料庫中將其狀態更新為 `listened`。

**防呆防重複機制：**
- **防重複**：比對新歌時，程式會將歌名進行「標準化（忽略 `(feat. ...)`、`- Single`、`Remastered` 等後綴）」，如果資料庫已經有同歌手且同歌名的歌曲，不論專輯為何都會自動略過，避免 iTunes 單曲與專輯重複收錄的問題。
- **自動還原**：若你不小心整列刪除或刪掉了未完成的歌曲，下次執行時程式會自動從資料庫把狀態為 `pending` (未完成) 的歌重新寫回 Obsidian。

### 2. YouTube 同步 (`YouTube.md`)
程式會將新影片以 Checklist 格式追加到檔案底部：

```markdown
- [ ] [SEVENTEEN] 影片標題 (https://www.youtube.com/watch?v=...)
```
你可以直接利用 Obsidian 內建的待辦清單功能，手動勾選完成。
