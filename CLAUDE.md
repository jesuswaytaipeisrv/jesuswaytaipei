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
| `update_sunday.py` | 每週四 21:00（launchd + GitHub Actions 雙備援） | 抓最新主日信息與樣青講堂，更新4個 HTML 表格，git commit **並自動 push**（2026-07-02 起兩邊都自動 push，不必手動） |

- launchd 服務：`com.jesusway.update-sunday-v2`（2026-07-17 起，取代舊的 `com.jesusway.update-sunday`，見下方修改記錄）
  - 舊的「電腦睡眠導致跳過觸發」推測**已證實是誤判**（2026-07-17 查證：當天電腦全程開機未睡眠，pmset log 無任何 sleep/wake 事件）。真正原因是 launchd 層級的 TCC 權限問題，見下方修改記錄
  - 若懷疑本機那次沒跑，以 GitHub Actions 的執行紀錄或 `sunday.html`/`youth.html` 內容為準，本機 log 沒紀錄不代表沒更新（GitHub Actions 不寫本機 log）
- GitHub Actions：`.github/workflows/update_sunday.yml`，作為主要備援，即使本機睡眠也會準時（或稍晚幾小時，屬 GH Actions 排程正常延遲）觸發並 push
- Log（僅本機執行會寫）：`logs/update_sunday.log`
- **失敗告警（2026-07-17 起）**：若找到符合關鍵字的候選影片、但 yt-dlp 抓不到日期（常見於 YouTube 對 GitHub Actions 限流），會寄警告信到 `jesuswaytaipeisrv@gmail.com`（主旨開頭 ⚠️），提醒人工確認或到 Actions 頁面 Re-run。這種情況 workflow 本身仍會顯示綠色 success，只能靠這封信才看得出來漏更新了

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

## 本次修改記錄（2026-08-06）— 導入 Google Analytics 4

### 內容

- 建立 GA4 帳戶「台北樣教會」／資源「台北樣教會官網」，網頁資料串流指向 `https://www.jesuswaytaipei.org`，評估 ID `G-6BH0T2SH0Y`。
- 全站 18 個 HTML（9 中文 + 9 英文）在 `</head>` 前插入 gtag.js 片段，每檔各 8 行，內容完全一致。
- 決定**不做 Cookie 同意橫幅**：訪客以台灣本地會友為主，GA4 預設已做 IP 匿名化。若日後海外流量佔比提高需重新評估。
- 評估 ID 屬設計上可公開的識別值（同 Firebase Web API key 性質），直接寫在前端 HTML 不算外洩，不需走環境變數。

### 與自動化的關係

`update_sunday.py` 的 `update_table()` 只在 `<tbody class="bg-white divide-y divide-gray-100">` 之後插入 `<tr>`，不觸碰 `<head>`，因此每週自動更新主日資料**不會洗掉 GA 片段**。

### 測試結果

- ✅ 18 檔各含且僅含一份片段（`grep -c` 每檔為 2，因片段內 ID 出現於 `src` 與 `config` 各一次）；`git diff --stat` 為 18 檔 × 8 行新增，無其他變更。
- ✅ 全站原本無任何 analytics 痕跡，確認非重複安裝。
- ⚠️ 本機瀏覽器驗證未能執行（非程式問題）：起 `python3 -m http.server 8899`，`curl` 回 200，但 Claude in Chrome 開 `127.0.0.1` / `localhost` 皆顯示錯誤頁，判定為瀏覽器擴充套件的網站權限未涵蓋 localhost。伺服器已於測試後關閉。改以正式站驗證（GA4 資料串流本就綁定該網域，正式站才是正確的驗證環境）。
- ✅ **正式站實際瀏覽器驗證通過**（push 後 GitHub Pages 部署完成，`last-modified: 2026-08-06 11:58:55 GMT`）：
  - `https://www.googletagmanager.com/gtag/js?id=G-6BH0T2SH0Y` → 200
  - 連續瀏覽 `/`、`/sunday.html`、`/about.html` 三頁，各發出一筆 `google-analytics.com/g/collect`，參數含 `tid=G-6BH0T2SH0Y`、`en=page_view`，且三筆 `cid` 相同（session 正確串接）
  - **GA4 即時報表確認收到**：`page_view` 3、`first_visit` 1、`session_start` 1；網頁標題列出「台北樣教會 JesuswayTaipei」「主日信息」「關於我們」各 1，與實際瀏覽路徑一致

### 已知誤導：`/g/collect` 顯示 503

Chrome 開發者工具／自動化工具會把 `/g/collect` 的回應顯示成 **503**，但 GA4 即時報表確實收到全部事件。原因是 gtag 以 `sendBeacon`／`keepalive` 送出，攔截層對這類請求的狀態碼判讀不準。**日後排查請以 GA4 即時報表為準，不要因為看到 503 就以為安裝失敗。**

### 待辦 / 觀察重點

- GA4 標準報表需 24–48 小時才有數字，即時報表約 30 秒內可見；驗證當下只能確認「資料送出且 GA 收到」。
- 可考慮在 GA4 設定「排除內部流量」，避免自己維護網站時的瀏覽灌水統計。

---

## 本次修改記錄（2026-07-17）— 週四批次漏更新排查、補跑、失敗告警機制、本機 launchd TCC 權限修復

### 背景
用戶回報「週四晚間批次又失敗了」。查起初以為是本機 launchd（`com.jesusway.update-sunday`）當晚電腦睡眠導致觸發被跳過，但使用者指出當天電腦確定沒關機/沒睡眠，追問「補跑會成功、排程卻失敗」的矛盾，進一步深查後發現真正原因跟睡眠完全無關（見下方「本機 launchd 根本原因」）。

### 本機 launchd 根本原因（2026-07-17 深查後確認，推翻先前的睡眠假設）
用 `launchctl print` 查詢發現 `last exit code = 78 (EX_CONFIG)`、`runs = 1`（系統自 2026-07-11 開機後只觸發過一次，時間點吻合週四 21:00），且完全沒進到 Python 的第一行 log——代表**連 Python 直譯器都還沒啟動，launchd 在 spawn 階段本身就失敗了**，不是腳本邏輯錯誤，也不是電腦睡眠跳過（`pmset -g log` 查證當天 07-16 全天無任何 sleep/wake 事件）。

用一系列對照測試（同一支 `/opt/homebrew/bin/python3` + 同一支 script，只改 `StandardOutPath`/`StandardErrorPath` 指向哪裡）鎖定成因：
- 輸出導到 `/tmp/...` → 正常成功（exit 0）
- 輸出導到 `~/documents/website/logs/update_sunday.log`（也就是舊 plist 原本的設定）→ 100% 重現 `EX_CONFIG`，無法 spawn

**結論：launchd 幫背景程式設定 `StandardOutPath`/`StandardErrorPath` 這個動作，在寫入 `~/Documents/...`（macOS 的 TCC 保護資料夾，跟 Desktop/Downloads 同級）時會被系統靜默拒絕，導致整個 job 連 spawn 都失敗**——這跟「該行程本身」有沒有讀寫 Documents 的權限是兩回事：同一支 python3 一旦成功啟動後，腳本自己用 `RotatingFileHandler` 寫同一個路徑完全正常（已驗證）。只有 launchd 自己在 spawn 那一刻要開檔導向 stdout/stderr 這個動作特別受限。時間點上跟 `macOS Tahoe 26.5.2`（2026-07-02 安裝）這次系統更新吻合，推測是這次更新收緊了 launchd 對 TCC 保護資料夾的檢查。

過去每一筆「成功」的本機 log 記錄（06-05、06-19、07-02、07-09），時間都不是準點 21:00（例如 22:46、09:16、13:10），代表其實**從來就不是 launchd 準時自動觸發成功過**，全部都是後續手動補跑覆蓋掉的結果——先前 CLAUDE.md 記載的「睡眠導致跳過」是誤判，真正問題可能已存在一段時間，只是每次都被手動補跑蓋過去，沒人發現排程本身沒在真正運作。

### 修復（本機 launchd）
- 停用舊的 `com.jesusway.update-sunday`（plist 改名為 `.disabled_20260717` 保留在 `~/Library/LaunchAgents/`，未刪除）
- 新增 `com.jesusway.update-sunday-v2`，關鍵差異：
  - `StandardOutPath` / `StandardErrorPath` 改指到 `~/Library/Logs/jesusway/update_sunday_launchd.log`（TCC 不保護的路徑），避開 spawn 階段被拒絕的問題
  - 新增 `EnvironmentVariables`（`PATH` 含 `/opt/homebrew/bin`、`HOME`）——原本 plist 完全沒設環境變數，launchd 預設 `PATH` 只有 `/usr/bin:/bin:/usr/sbin:/sbin`，就算 spawn 問題沒發生，腳本第一步呼叫 `yt-dlp` 也會找不到指令（`FileNotFoundError: yt-dlp`），這是另一個獨立於 TCC 問題之外、原本就存在的隱藏 bug，這次一併修掉
  - 排程時間、腳本路徑、其餘設定不變（每週四 21:00）
- 腳本自己寫的 `logs/update_sunday.log`（`~/documents/website/logs/`）不受影響，繼續正常寫入，歷史紀錄延續
- 已用 `launchctl kickstart -k` 實際觸發驗證：exit code 0，完整跑完全流程，兩份 log 都正確寫入

### 根本原因（GitHub Actions 備援層，跟本機 launchd 問題各自獨立）
本機沒跑不是新問題，真正的問題是**連 GitHub Actions 備援那次也沒有實際更新網站，卻回報 success**：
- 2026-07-16 的 workflow run 確實有觸發，也確實掃到新的主日信息候選影片（`uyHATNU9p5w`，2026.07.12「每當我想贏的時候 就要像王一樣思考」）
- 但該影片標題已不含日期前綴（YouTube 頻道標題格式又變了，同一類問題先前已發生兩次），必須 fallback 呼叫 yt-dlp 個別抓 `upload_date`
- `android` client、預設 client 兩次個別呼叫在 GitHub Actions 環境**都失敗**（本機用同一支影片 ID 測試完全正常，確認是 YouTube 對 GitHub Actions 共用 IP 限流，非程式邏輯錯誤）
- 舊邏輯把「候選影片存在但日期解析失敗」跟「本週真的沒有新影片」一視同仁，兩者都只是 log 印一行 warning、workflow 照樣 `success`、也不會觸發 email 通知 → **漏更新完全沒人知道**

### 修復
- **手動補跑**：本機直接執行 `update_sunday.py`，本機環境抓日期正常，成功補上 2026.07.12 主日信息（中英文皆已透過 Gemini 正常翻譯，非暫用中文），commit `8d87cf6`
- **`update_sunday.py`**：`fetch_latest_streams()` 新增回傳 `date_fetch_failed` 旗標（候選影片存在但日期解析失敗時為 `True`，跟「本週無新內容」明確區分）；`GITHUB_ACTIONS` 環境下寫入 `$GITHUB_OUTPUT`
- **`.github/workflows/update_sunday.yml`**：「Run update script」步驟加 `id: update`；新增一個條件式 step，`date_fetch_failed == 'true'` 時寄一封警告信（主旨 ⚠️ 開頭），提醒到 Actions 頁面 Re-run 或本機手動補跑

### 待辦 / 觀察重點
- 這類 YouTube 對 CI 限流的問題屬間歇性，未來仍可能發生；這次修的是「讓失敗看得見」，不是徹底根除限流本身
- 若警告信開始頻繁出現，可考慮加 retry（多次重試 + 間隔）或改用 cookies 驗證降低被限流機率
- 下週四（07-23）21:00 觀察 `com.jesusway.update-sunday-v2` 是否準時自動觸發成功（`~/Library/Logs/jesusway/update_sunday_launchd.log` 有無新內容、`launchctl print` 的 `last exit code` 是否為 0），這是第一次真正驗證排程本身能自動跑，先前所有「成功」紀錄都是手動補跑
- 舊 plist `com.jesusway.update-sunday.plist.disabled_20260717` 先保留在 `~/Library/LaunchAgents/`，確認新版穩定一陣子後可以刪除
- macOS 對 `~/Documents`/`~/Desktop`/`~/Downloads` 的 TCC 保護會影響任何指向這些資料夾的 launchd `StandardOutPath`/`StandardErrorPath`，往後新增任何 launchd job 都要避開，改寫到 `~/Library/Logs/` 之類的位置

---

## 本次修改記錄（2026-07-02）— 根本原因排查、日期解析加固、SSH 自動 push

### 背景
發現 `sunday.html`/`youth.html` 停在 2026.06.14 沒更新，2026.06.18、2026.06.25 兩個週四都沒有新內容進來。

### 根本原因
- 教會 YouTube 頻道在 2026.06.19 前後，把**全頻道（含舊影片）標題裡的日期前綴整個拿掉**（不是只有新片，用同一支影片 `1sf6qDYKu0E` 同一天前後兩次抓取結果對照確認：09:16 抓到時標題還有 `2026.06.14 | `，13:10 再抓就沒了）
- 這代表 `parse_date_from_title()` 這條免呼叫捷徑，從此對所有影片都會失效，每支影片都得 fallback 到 `fetch_date()` 逐支呼叫 yt-dlp
- `fetch_date()` 這條路徑在 GitHub Actions 環境本來就容易被 YouTube 限流失敗；失敗時只會 `logging.warning` 並整個跳過該筆，workflow 仍視為 `success`，導致漏更新完全看不出來
- 實際漏掉：主日 2026.06.21「我的人生創業路｜張英樹弟兄」（`_VZUN11qY9E`）、樣青 2026.06.28「訂雞排不揪！是霸凌嗎？｜葉如凡」（`GAwhyWQeQIo`）

### update_sunday.py 修改
- `fetch_date()` 新增第三層 fallback：`upload_date` 也拿不到時，改剖析描述欄裡的「日期：YYYY/MM/DD」（兩支漏掉的影片描述欄都有 `🕑日期：2026/06/21` 這種固定格式）。同一次 yt-dlp 呼叫就把描述欄一起帶出（`%(upload_date,release_date)s\x1f%(description)s`），不多打一次 API
- `git_commit()`：**移除 `GITHUB_ACTIONS` 判斷，本機執行也會自動 `git push`**，不再需要 GitHub Desktop 手動 push

### 本機自動 push 設定（新增）
- 產生專屬 SSH deploy key：`~/.ssh/id_ed25519_jesusway`（僅此 repo write 權限，非個人帳號 key）
- `~/.ssh/config` 新增 Host alias `github-jesusway`（`IdentitiesOnly yes`，避免影響本機其他 GitHub SSH 設定）
- repo remote 由 HTTPS 改為 `git@github-jesusway:jesuswaytaipeisrv/jesuswaytaipei.git`
- Deploy key 加在 repo Settings → Deploy keys（勾選 Allow write access），非帳號層級 SSH key

### 已手動補跑
- 補入 2026.06.21 主日信息、2026.06.28 樣青講堂（中英文皆已 Gemini 翻譯成功，非暫用中文），commit `4820b3d` 已自動 push

### 待辦 / 觀察重點
- launchd 那次沒觸發是因為電腦在睡眠狀態，並非任何程式錯誤；「開機後補跑」這個假設已證實不可靠（見上方自動化章節）
- 之後若頻道標題格式再變，優先檢查 `parse_date_from_description()` 的 regex（目前只認「日期：」+ `YYYY/MM/DD` 或 `YYYY.MM.DD`）是否還吻合

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
- 張英樹 弟兄 → **Brother Yingshu Zhang**（2026-07-02：Gemini 譯成「Founder and CEO of Victory Foundation, Yingshu Zhang」，已手動改為與其他講員一致的簡潔格式）

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
