# 台北樣教會網站 CLAUDE.md
# Claude Code 每次啟動時自動讀取此檔案

---

## 專案簡介

台北樣教會官方靜態網站，以職場年輕世代為核心。

- **路徑：** `~/documents/website/`
- **Repo：** `jesuswaytaipeisrv/jesuswaytaipei`（GitHub Pages）
- **版控工具：** GitHub Desktop（帳號：jesuswaytaipeisrv，供人工修改內容時使用）
- **自動化 push：** 走 SSH deploy key（`~/.ssh/id_ed25519_jesusway`，Host alias `github-jesusway`），`update_sunday.py` 執行後自動 commit + push，不經過 GitHub Desktop（2026-07-02 起）

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
- Google Analytics 4：評估 ID `G-6BH0T2SH0Y`（gtag.js，全 18 頁 `</head>` 前）

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
| `update_sunday.py` | 本機 launchd 週四 21:00（主）＋ GitHub Actions 週五 09:00（補救層，2026-08-09 起錯開） | 抓最新主日信息與樣青講堂，更新4個 HTML 表格，git commit **並自動 push**（2026-07-02 起兩邊都自動 push，不必手動） |

- launchd 服務：`com.jesusway.update-sunday-v2`（2026-07-17 起，取代舊的 `com.jesusway.update-sunday`，見下方修改記錄）
  - 舊的「電腦睡眠導致跳過觸發」推測**已證實是誤判**（2026-07-17 查證：當天電腦全程開機未睡眠，pmset log 無任何 sleep/wake 事件）。真正原因是 launchd 層級的 TCC 權限問題，見下方修改記錄
  - 若懷疑本機那次沒跑，以 GitHub Actions 的執行紀錄或 `sunday.html`/`youth.html` 內容為準，本機 log 沒紀錄不代表沒更新（GitHub Actions 不寫本機 log）
- GitHub Actions：`.github/workflows/update_sunday.yml`，**2026-08-09 起改為每週五 09:00（台北）**，即本機跑完隔天早上才跑，作為本機失敗時的補救層（原本與本機同排週四 21:00，備援從未被真正驗證過，見 2026-08-09 記錄）
- Log（僅本機執行會寫）：`logs/update_sunday.log`
- **失敗告警（2026-07-17 起）**：若找到符合關鍵字的候選影片、但 yt-dlp 抓不到日期（常見於 YouTube 對 GitHub Actions 限流），會寄警告信到 `jesuswaytaipeisrv@gmail.com`（主旨開頭 ⚠️），提醒人工確認或到 Actions 頁面 Re-run。這種情況 workflow 本身仍會顯示綠色 success，只能靠這封信才看得出來漏更新了
  - **⚠️ 這封信會誤報，收到不等於漏更新（2026-08-22 查證）**：判斷依據是「日期解析失敗」，但 CI 環境本來就常被 YouTube 限流而抓不到日期，只要頻道上還有符合關鍵字的影片就會週週寄信。07-30～08-20 連續 4 次都是誤報，網站實際都是最新的。收到信請先照 2026-08-22 記錄的方式確認候選影片是否已收錄，再決定要不要補跑
- **本機失敗告警（2026-08-09 起）**：本機 launchd 執行失敗時發 **Telegram** 訊息（token 取自 `~/.hermes/.env`）。CI 端的信箱 `jesuswaytaipeisrv@gmail.com` 不是日常會看的信箱，2026-08-06 那封警告信就是這樣被忽略的

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

## 已知地雷 / 別再重查的結論

以下每條都是查證過、推翻過錯誤假設才得到的結論，**排查時先看這裡，不要重走一次冤枉路**。
細節與當時的查證過程在 `@docs/DEVLOG.md` 對應日期。

**排程 / launchd**
- launchd 的 `StandardOutPath`/`StandardErrorPath` **不可指向 `~/Documents`**（TCC 保護資料夾），會在 spawn 階段被靜默拒絕、`exit 78 (EX_CONFIG)`，連 Python 都沒啟動。一律寫到 `~/Library/Logs/`。（2026-07-17）
- launchd plist 必須自設 `EnvironmentVariables` 的 `PATH` 含 `/opt/homebrew/bin`，否則腳本第一步就 `FileNotFoundError: yt-dlp`。（2026-07-17）
- **「電腦睡眠導致 launchd 跳過」是已推翻的誤判**，別再往這個方向查；`pmset -g log` 已證實當天無 sleep/wake。（2026-07-17）

**YouTube 抓取**
- YouTube 對 GitHub Actions 共用 IP 限流是常態，**CI 抓不到日期不是程式 bug**（本機同一支影片 ID 測試正常）。（2026-07-02、2026-07-17）
- 頻道標題格式會變（日期前綴曾被整批拿掉）。日期解析依序：標題前綴 → `upload_date` → 描述欄「日期：YYYY/MM/DD」。格式再變時先檢查這三層。（2026-06-19、2026-07-02）
- ⚠️ 警告信會誤報，見上方「自動化」章節，收到不等於漏更新。（2026-08-22）
- `youth.html` 沒有 2026.06.28 那列是**影片下架後刻意移除**（`cb6589f`），不是漏更新。（2026-08-22）

**GA4 / 網域**
- `/g/collect` 顯示 **503 是假象**（gtag 走 `sendBeacon`／`keepalive`，攔截層狀態碼判讀不準），一律以 GA4 即時報表為準。（2026-08-06）
- 刻意**不設「排除內部流量」**（對外是 HiNet 浮動 IP，規則會默默失效）。要做請改用 GA Opt-out 瀏覽器擴充。（2026-08-06）
- GitHub Pages 憑證卡住不簽出時，解法是做**一次**乾淨的 Remove → 等 2 分鐘 → 重填 Custom domain。（2026-06-17）

**Gemini API key**
- 變數名是 `GOOGLE_API_KEY`，**不是** `GEMINI_API_KEY`。全部專案裡只有這裡不一樣，是刻意保留的現狀；三處必須一致：`update_sunday.py`（翻譯函式）、`.github/workflows/update_sunday.yml`、GitHub repo secret。2026-06 就是因為 script 寫 `GEMINI_API_KEY`、`.env` 實際是 `GOOGLE_API_KEY` 而壞過一次（見 `@docs/DEVLOG.md`），要改名三處一起改。（2026-08-30）
- **這把 key 屬於 Cloud 專案 `website-jesusway`（`gen-lang-client-0734466101`，2026-06-05 建立）**。AI Studio 是**一個專案配一把 key**，依專案名稱與建立日對應而得（來源：使用者的 Gemini 計費架構筆記）。secret 的值本身讀不回來（單向寫入），也不需要讀——要換就直接在該專案下開新 key 覆蓋 secret。⚠️ 換的時候留意：Google 已對**新建立的專案**停售 `gemini-2.5-flash`，而 `update_sunday.py` 正是用它，所以新 key 必須開在 `website-jesusway` 底下，不要另開專案。（2026-08-30）

**環境差異（三台電腦輪流維護）**
- 本機路徑因機器而異（`~/documents/website/`、`~/Documents/Claude/Projects/jesuswaytaipei/`），**這是正常的，不要「修正」成單一路徑**。動手前先 `git pull`。
- 自動化 push 用的 SSH deploy key 只在實際跑排程那台；其他機器用 HTTPS + Keychain PAT push，兩者並存正常。
- 家用機**沒裝 `yt-dlp`、也沒有 `gh` CLI**，查排程走 REST API（指令見 `@docs/DEVLOG.md` 2026-08-22 段）。

---

## 歷史修改記錄索引

完整內容在 **`@docs/DEVLOG.md`**。大致新到舊，早期幾段的順序原本就沒排整齊，分流時維持原樣未動。

- **2026-08-22** — 週四排程執行確認：排程正常，⚠️ 警告信查證為誤報
- **2026-08-09** — 08-06 漏更新排查、補推上線、git 併推與告警修復
- **2026-08-06** — 導入 Google Analytics 4
- **2026-07-17** — 週四批次漏更新排查、補跑、失敗告警機制、本機 launchd TCC 權限修復
- **2026-07-02** — 根本原因排查、日期解析加固、SSH 自動 push
- **2026-06-19** — 批次補跑 & update_sunday.py 修復
- **2026-06-17** — 自訂網域階段一上線（`.org` + HTTPS）
- **2026-06-15** — 全站圖片改用 WebP（34 張，`<picture>` 包裝）
- **2026-05-30** — 新增樣青講堂表格，`update_sunday.py` 擴充為同時更新兩張表
- **2026-06-12，第二次** — `update_sunday.py` 三個 bug 修正（逾時未捕捉、誤刪資料、失敗仍 commit）
- **2026-06-12** — 英文用語統一、講員譯名修正、全站加 logo
- **2026-06-07** — 講員稱謂更新
- **2026-06-06** — `abbafood.html` 全面重構與多處文案調整
- **2026-06-05** — 建立 GitHub Actions 排程、`update_sunday.py` 支援 CI 環境
- **2026-06-05，第二次** — 抓取穩定性、Gemini 翻譯、講員解析三項修復＋郵件通知
- **補充說明（2026-06-05）** — 英文翻譯的歷史沿革（哪幾筆不是 Gemini 翻的）
