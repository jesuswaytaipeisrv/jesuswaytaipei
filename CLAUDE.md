# 台北樣教會網站 CLAUDE.md
# Claude Code 每次啟動時自動讀取此檔案

---

## 專案簡介

台北樣教會官方靜態網站，以職場年輕世代為核心。

- **路徑：** `~/documents/website/`
- **Repo：** `jesuswaytaipeisrv/jesuswaytaipei`（GitHub Pages）
- **版控工具：** GitHub Desktop（帳號：jesuswaytaipeisrv）

---

## 開發原則

1. **中英文同步**：每次修改網頁內容，中文版（根目錄）與英文版（`en/`）均須同步更新
2. **RWD 確認**：每次修改後確認手機與桌機版面正常
3. **不捏造內容**：文字、照片、影片連結須為教會實際資源，不假設或佔位
4. **自動化腳本**：`update_sunday.py` 由 launchd 排程執行，修改前確認邏輯不破壞既有表格結構

---

## 技術棧

- 純靜態 HTML（無框架、無後端）
- TailwindCSS（CDN）
- Google Fonts：Noto Sans TC
- 語言：繁體中文（`lang="zh-Hant"`）+ 英文（`en/`，`lang="en"`）

---

## 頁面結構（共 18 頁，9 中文 + 9 英文）

| 檔案 | 頁面 | 備註 |
|------|------|------|
| `index.html` | 首頁 | Hero 全版背景、三個特色區塊 |
| `about.html` | 關於我們 | 教會簡介、四張圓形照片、核心價值 |
| `sunday.html` | 主日信息 | 近10週直播表格（每週四 21:00 自動更新） |
| `youth.html` | 樣青講堂 | 近10次直播表格（每週四 21:30 自動更新） |
| `abbafood.html` | ABBAFOOD 職場讀書會 | 3 個據點卡片（東興/南軟/慕美學） |
| `worship.html` | WayWorship 敬拜團 | 4 支 YouTube 影片 |
| `creative.html` | 創意活動 | 2021/2022/2024/2025 年活動紀錄 |
| `contact.html` | 聯絡我們 | Line@ 按鈕、Email |
| `donate.html` | 奉獻資訊 | 華南銀行帳號 |

---

## 自動化

| 腳本 | 排程 | 功能 |
|------|------|------|
| `update_sunday.py` | 每週四 21:00（launchd） | 抓最新主日信息與樣青講堂，更新4個 HTML 表格，git commit |

- launchd 服務：`com.jesusway.update-sunday`（電腦關機時錯過，開機後補跑）
- 更新後須用 **GitHub Desktop 手動 push**
- Log：`logs/update_sunday.log`

**`update_sunday.py` 一次更新的檔案：**
- `sunday.html` + `en/sunday.html`（主日信息表格）
- `youth.html` + `en/youth.html`（樣青講堂表格）

---

## 設計規範

| 項目 | 規格 |
|------|------|
| 主色 | 黃色（yellow-400/600）|
| 背景色 | `#FAFAFA` |
| 字色 | `#333333` |
| 標題裝飾 | 左側黃色 border（`border-l-4 border-yellow-400`）|
| 圓角卡片 | `rounded-2xl shadow-sm border border-gray-100` |
| Hero 背景圖 | `assets/images/site_bkg.png` |

---

## 本次修改記錄（2026-05-30）

### 新增
- `youth.html` / `en/youth.html`：新增近10次樣青講堂直播表格（2025.05.18 ~ 2026.05.24）
  - 資料來源：yt-dlp 從 YouTube 頻道直播列表擷取，日期與影片連結均已驗證
  - 英文版標題已翻譯

### 修改
- `update_sunday.py`：擴充同時更新樣青講堂表格（原本只更新主日信息）
  - 新增 `fetch_latest_streams()`：一次掃描找主日和樣青，省去重複 yt-dlp 呼叫
  - 新增 `parse_youth_title_guest()`：解析樣青講堂標題與來賓
  - `translate_to_english()` 加 `context` 參數，主日/樣青用不同翻譯 prompt
  - `git_commit()` 接受檔案列表，一次 commit 四個檔案

### 待辦
- ~~`abbafood.html`：3 張據點卡片圖片仍用 Unsplash 占位（東興/南軟/慕美學）~~ → 已移除占位圖（2026-06-06）

---

## 本次修改記錄（2026-06-12，第二次）

### Bug 修正（update_sunday.py）

經 DeepSeek V4 Pro code review 發現並修正三個問題：

| 問題 | 修法 |
|------|------|
| `fetch_date` 呼叫 yt-dlp 逾時時未捕捉 `TimeoutExpired`，整個腳本會 crash | 加 `try/except TimeoutExpired`，逾時改為回傳 `None` |
| `update_table` 無條件刪最後一筆，表格筆數不滿 10 時會誤刪資料 | 插入後計算筆數，超過 `MAX_ROWS=10` 才刪 |
| `main()` 忽略 `update_table` 回傳值，更新失敗仍繼續 git commit | 接收回傳值，失敗時 `return` 中止，不 commit 損壞檔案 |

---

## 本次修改記錄（2026-06-12）

### 文字修改
- `en/*.html`（全站 9 個英文頁面）：導覽列「Youth Ministry」一律改為「JesusWay Forum」（32 處）
- `en/sunday.html`：講員吳必然英文統一為「Pastor Pijan Wu」（共 6 處，修正 Wu Biran / Wu Pi-Jan 兩種錯誤寫法）
- `en/donate.html`：Account Name 由「Taiwan Jesusway Holistic Development Association」改為「社團法人台灣樣全人發展協會」（含 meta description / og:description，共 3 處）

### 新增
- `assets/images/logo.jpg`：教會 logo 圖示（17KB）
- 全站 18 個頁面（9 中文 + 9 英文）導覽列品牌區加入 logo 圖，位置在「台北樣教會 JesuswayTaipei」文字左側，`h-10 w-auto`，flex 排版垂直置中

### 講員翻譯規則（已儲存至 Claude 記憶）
- 吳必然 → **Pastor Pijan Wu**（不用 Wu Biran / Wu Pi-Jan）

### 待辦
- 無

---

## 本次修改記錄（2026-06-07）

### 文字修改
- `sunday.html` / `en/sunday.html`：講員稱謂更新
  - 中文：呂冠緯 → 呂冠緯弟兄
  - 英文：Kuan-Wei Lu → Brother Kuan-Wei Lu

### 待辦
- 無

---

## 本次修改記錄（2026-06-06）

### 文字修改
- `creative.html` / `en/creative.html`：副標題「不只是舉辦，而是創造一段被記住的經歷」→「創造一段值得紀念的體驗」
- `about.html`：「最美好的自己」→「最美好的模樣」（英文版不需更動）
- `sunday.html` / `en/sunday.html`：區塊標題「信息剪影」→「2026年三個信息主題」
- `index.html` / `en/index.html`：首頁 ABBAFOOD 說明文字更新為與使命一致的描述

### abbafood.html 全面重構（中英文同步）
依據 PDF 文件重新設計頁面架構與全部文字，新增以下區塊：

| 區塊 | 說明 |
|------|------|
| 開場 Hook | 保留原有引言卡片，文字精簡 |
| AbbaFood 的使命 | 兩欄圖示卡片（實體＋屬靈食物 / 真誠陪伴） |
| 主要目標對象 ＋ 特色 | 兩欄白色卡片並排 |
| 進行方式 | 三欄卡片（週間午餐 / 晚間假日 / 講堂） |
| 食物 | 兩欄淺綠底（實體食物 / 屬靈食物：標竿人生、路加福音） |
| 服事團隊 | 單欄卡片 |
| 三個參考據點 | 保留既有卡片，已移除 Unsplash 占位圖 |

### 待辦
- 無

---

## 本次修改記錄（2026-06-05）

### 新增
- `.github/workflows/update_sunday.yml`：GitHub Actions 排程，每週四 13:00 UTC（= 21:00 UTC+8）自動觸發
  - 安裝 `yt-dlp`、`google-generativeai`
  - 注入 `GEMINI_API_KEY`（GitHub repo secret）
  - script 執行後自動 `git push`，不再依賴 GitHub Desktop

### 修改
- `update_sunday.py`：支援 CI 環境執行
  - `WEBSITE_DIR`：支援環境變數覆蓋（GitHub Actions 注入 `github.workspace`）
  - `setup_logging()`：CI 環境只輸出 stdout，不寫本機 log 檔
  - `load_env()`：CI 環境（`GITHUB_ACTIONS=true`）跳過讀取本機 `.env`
  - `git_commit()`：CI 環境執行完 commit 後自動 `git push`

### 排程現況
| 環境 | 觸發方式 | Push 方式 |
|------|----------|-----------|
| 本機 | launchd 每週四 21:00 | GitHub Desktop 手動 |
| GitHub Actions | cron 每週四 13:00 UTC | 自動 push |

> 兩者邏輯一致，script 用 `GITHUB_ACTIONS` 環境變數區分行為。

### 待辦
- `abbafood.html`：3 張據點卡片圖片仍用 Unsplash 占位（東興/南軟/慕美學），等使用者提供實際照片

---

## 本次修改記錄（2026-06-05，第二次）

### 問題修復

#### 1. fetch_latest_streams() 抓取不穩定
- **原因：** 逐一對每支影片跑 yt-dlp 取 metadata，遇網路延遲/YouTube 限速時回傳空值被跳過
- **修法：** 改為一次 flat-playlist 取 ID + 標題，關鍵字篩選後僅對符合的 1~2 支影片抓日期，API 呼叫從最多 25 次降為 2 次

#### 2. 翻譯從未成功（長期存在）
- **原因：** script 用 `GEMINI_API_KEY`，.env 實際是 `GOOGLE_API_KEY`；且 `google-generativeai` 套件已棄用，`gemini-2.0-flash` 模型已下架
- **修法：** 改用 `google-genai` 新套件 + `GOOGLE_API_KEY` + `gemini-2.5-flash`

#### 3. 講員解析邏輯錯誤
- **原因：** `parse_sunday_title_speaker` 把含雜訊關鍵字的整段過濾掉，導致「台北樣教會 吳必然 牧師」整段消失
- **修法：** 改為從段落中去除關鍵字文字、保留剩餘內容（「台北樣教會 吳必然 牧師」→「吳必然 牧師」）
- **補救：** 手動修正 sunday.html / en/sunday.html 2026.05.31 講員欄位

### 新增功能
- **GitHub Actions 郵件通知：** 排程執行完畢且有更新時，自動寄信至 `jesuswaytaipeisrv@gmail.com`
  - 使用 `dawidd6/action-send-mail@v3`，走 Gmail SMTP（port 465）
  - 信件內容：更新摘要（git commit message）+ 主日/樣青網頁連結
  - 需 GitHub Secret：`GMAIL_APP_PASSWORD`（Gmail 應用程式密碼，非登入密碼）

### GitHub Secrets 一覽（截至本次）
| Secret | 用途 |
|--------|------|
| `GOOGLE_API_KEY` | Gemini 翻譯（gemini-2.5-flash） |
| `GMAIL_APP_PASSWORD` | Gmail SMTP 發信授權 |

---

## 補充說明（2026-06-05）

### 英文翻譯歷史
- 表格初始 10 筆（2026.03.01 ~ 2026.05.17）：由前次對話 Claude 直接翻譯後手寫入 HTML，**未使用 Gemini**
- `update_sunday.py` 的 Gemini 翻譯功能自建立起即故障（API key 名稱不符 + 套件未安裝），首次自動新增的 2026.05.31 因此用中文暫代
- 本次修復後，往後每週自動新增的筆數才真正走 Gemini（gemini-2.5-flash）翻譯
