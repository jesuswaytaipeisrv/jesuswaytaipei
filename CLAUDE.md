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

## 本次修改記錄（2026-06-19）— 批次補跑 & update_sunday.py 修復

### 背景
週四（2026-06-18）本機關機，launchd 未執行；CI（GitHub Actions）雖觸發但因 yt-dlp 取不到日期而跳過。另發現 2026.06.07 的影片從未被加入表格。

### 手動補入缺失資料
- `sunday.html` / `en/sunday.html`：補入 2026.06.07「清楚明白，神為我們劃的界線 / 吳必然 牧師」（英文：The Clear Boundaries God Drew for Us / Pastor Pijan Wu）
- 2026.06.14「上帝為什麼管我這麼嚴格？」已由本機補跑寫入，英文標題同步修正

### update_sunday.py 修改
| 問題 | 修法 |
|------|------|
| CI 上 `yt-dlp --skip-download --print %(upload_date)s` 被 YouTube 限流，回傳空值 | 新增 `parse_date_from_title()`：優先從標題開頭 `YYYY.MM.DD` 格式 parse 日期，免去額外 yt-dlp 呼叫 |
| 標題無日期時 yt-dlp 在 CI 仍失敗 | `fetch_date()` 改用 `player_client=android`（走不同 API endpoint，CI 限流較少），fallback 才用預設 client |
| 翻譯失敗（本機補跑時） | `google-genai` 未安裝在 `/usr/bin/python3`；launchd 用 `/opt/homebrew/bin/python3`（已有套件），本機補跑需用同一 python |

### 根本原因（記錄供日後參考）
台北樣教會 YouTube 頻道**在 2026.06 前後改變標題格式**，舊格式含日期（`2026.05.31 | 題目 | ...`），新格式不含（`題目 | 台北樣教會 吳必然 牧師 | ...`）。舊腳本依賴 yt-dlp 個別呼叫取日期，在 CI 環境不穩定，導致新格式影片被跳過。

### 本機執行補跑方式
```bash
# GOOGLE_API_KEY 未存 Keychain 前，用此方式安全輸入（不進 history）
read -s GOOGLE_API_KEY && export GOOGLE_API_KEY && /opt/homebrew/bin/python3 ~/documents/website/update_sunday.py
```

---

## 本次修改記錄（2026-06-17）— 自訂網域階段一上線

### 內容
- DNS 確認已生效：`www.jesuswaytaipei.org` CNAME → `jesuswaytaipeisrv.github.io`，apex 四筆 GitHub Pages A 記錄皆在（Cloudflare 代管、DNS only 灰雲）
- 全站 18 個 HTML 的 `og:image` / `og:url` 由 `jesuswaytaipeisrv.github.io/jesuswaytaipei/` 子路徑改為自訂網域根目錄 `https://www.jesuswaytaipei.org/`，並 grep 確認 HTML 無殘留舊網址
- 新增 `DOMAIN_SETUP.md`（兩階段網域規劃）、`DOMAIN_CHECKLIST.md`（STEP 1–6 操作清單）
- 已 commit + push（`829478e`）。GitHub Pages 已用自訂網域以 **HTTP 正常服務**（curl 回 200）

### HTTPS 上線完成（2026-06-17 補記）
- GitHub Pages 綁定 Custom domain `www.jesuswaytaipei.org`、DNS check 綠勾、Enforce HTTPS 已開
- **憑證曾卡住**：第一次綁定後等超過 1 小時憑證都沒簽出（DNS / CAA / ACME 路徑經查全正確）。
  解法是做**一次**乾淨的 Remove → 等 2 分鐘 → 重填 Custom domain 重新觸發，即成功
- 憑證：**Let's Encrypt，到期 2026-09-15，GitHub 自動續簽**
- 驗證全通過：`https://` 回 200、`http→https` 301、`apex→www` 301、RWD 正常
- ✅ 階段一（`.org`）完成。階段二（`.org.tw`）待 TWNIC 註冊商申請下來再做，步驟見 `DOMAIN_SETUP.md`

---

## 本次修改記錄（2026-06-15）

### 圖片格式升級：WebP

- 全站 34 張照片（`.jpg`）轉換為 WebP 格式（品質 85），平均縮小 55~70%
- 中英文 18 個 HTML 頁面，所有 `<img>` 圖片標籤（共 72 個）改以 `<picture>` 包裝：
  - 現代瀏覽器自動讀取 `.webp`；舊瀏覽器退回 `.jpg` fallback
  - logo.jpg / favicon 未變更（非照片，原本即小檔）
- 轉換工具：`ffmpeg -c:v libwebp -quality 85`
- 備份：轉換前原始 JPG 備份至 `~/documents/網站備份/images_backup_20260615/`
- Hero 背景圖（`assets/images/site_bkg.png`）為 PNG，**本次未異動**

### 注意事項
- `update_sunday.py` 只更新表格文字，不觸及 `<img>` 標籤，WebP 包裝不受排程影響

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
