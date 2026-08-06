# 台北樣教會網站 JesuswayTaipei

教會官方網站，以職場年輕世代為核心。

- **網址 repo：** `jesuswaytaipeisrv/jesuswaytaipei`
- **本機路徑：** `~/documents/website`
- **版控工具：** GitHub Desktop（帳號：jesuswaytaipeisrv，人工修改內容時使用）
- **自動化 push：** SSH deploy key（`github-jesusway` host alias），詳見下方「自動化」章節

---

## 技術棧

- 純靜態 HTML（無框架、無後端）
- TailwindCSS（CDN）
- Google Fonts：Noto Sans TC
- 響應式設計（桌面／手機版導覽列切換）
- Google Analytics 4（gtag.js，評估 ID `G-6BH0T2SH0Y`）

### 網站分析

全站 18 頁的 `</head>` 前都有一段 GA4 gtag.js。**新增頁面時務必一併加入**，否則該頁不會被統計：

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-6BH0T2SH0Y"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-6BH0T2SH0Y');
</script>
```

報表在 https://analytics.google.com/ 查看。GA4 免費版即可，無費用。

---

## 頁面結構

| 檔案 | 頁面 |
|------|------|
| `index.html` | 首頁 |
| `about.html` | 關於我們 |
| `sunday.html` | 主日信息 |
| `youth.html` | 樣青講堂 |
| `abbafood.html` | ABBAFOOD 職場讀書會 |
| `worship.html` | WayWorship 敬拜團 |
| `creative.html` | 創意活動 |
| `contact.html` | 聯絡我們 |
| `donate.html` | 奉獻資訊 |

---

## 自動化

| 腳本 | 說明 |
|------|------|
| `update_sunday.py` | 每週四 21:00 自動抓最新主日信息與樣青講堂、更新表格、git commit & push（本機、CI 皆自動 push，2026-07-02 起） |

- 一次執行同時更新 `sunday.html`、`en/sunday.html`、`youth.html`、`en/youth.html`（各維持10筆）
- **本機：** launchd 服務 `com.jesusway.update-sunday-v2`（2026-07-17 起，取代舊的 `com.jesusway.update-sunday`），每週四 21:00，使用 `/opt/homebrew/bin/python3`
  - 舊版曾因 macOS TCC 保護 `~/Documents` 資料夾，導致 launchd 幫 job 設定 stdout/stderr 重導向時 spawn 直接失敗（`EX_CONFIG`），跟電腦睡眠無關（先前記載的睡眠假設有誤，已更正）。新版把 launchd 層的 log 改寫到 `~/Library/Logs/jesusway/`（不受 TCC 限制），並補上原本缺少的 `PATH`/`HOME` 環境變數
  - push 走 SSH deploy key（`~/.ssh/id_ed25519_jesusway`，僅此 repo write 權限），remote 為 `git@github-jesusway:jesuswaytaipeisrv/jesuswaytaipei.git`，不再需要 GitHub Desktop
- **GitHub Actions：** `.github/workflows/update_sunday.yml`，每週四 13:00 UTC（= 21:00 UTC+8）自動觸發（實際常晚幾小時，屬 GH Actions 排程正常延遲），自動 push，並寄更新通知信至 jesuswaytaipeisrv@gmail.com
  - 若找到候選影片但 yt-dlp 抓不到日期（常見於 YouTube 對 CI 限流），會寄警告信（⚠️ 開頭主旨），跟「本週真的沒新內容」明確區分，避免靜默漏更新
- 兩套機制互為備援
- Log：本機執行寫 `logs/update_sunday.log`（腳本自己的內容 log，不受 TCC 影響）+ `~/Library/Logs/jesusway/update_sunday_launchd.log`（launchd 層 stdout/stderr）
- 翻譯套件：`google-genai`，模型：`gemini-2.5-flash`（需 `GOOGLE_API_KEY`）
- GitHub repo secrets：`GOOGLE_API_KEY`（Gemini 翻譯）、`GMAIL_APP_PASSWORD`（Gmail 應用程式密碼）

### 手動補跑方式
```bash
# key 輸入不進 history（安全）
read -s GOOGLE_API_KEY && export GOOGLE_API_KEY && /opt/homebrew/bin/python3 ~/documents/website/update_sunday.py
```

### 日期取得邏輯（2026-07-02 更新）
1. 優先從標題開頭 `YYYY.MM.DD` 格式 parse（無額外網路呼叫）——**注意：頻道已於 2026-06 全面拿掉標題日期前綴，這條路徑目前實務上幾乎不會命中**
2. 標題無日期時，呼叫 yt-dlp 取 `upload_date`，優先用 `player_client=android`（CI 環境限流較少）
3. `upload_date` 仍拿不到時，改剖析同一次呼叫帶回的描述欄，找「日期：YYYY/MM/DD」格式（2026-07-02 新增）

---

## 圖片規範

| 項目 | 規格 |
|------|------|
| 格式 | WebP（主）+ JPG（fallback），以 `<picture>` 標籤包裝 |
| WebP 品質 | 85（ffmpeg libwebp） |
| 解析度 | 1920px 寬（標準），Hero 背景 `site_bkg.png` 為 PNG 不變 |
| 備份位置 | `~/documents/網站備份/images_backup_20260615/`（2026-06-15 轉換前備份） |
| 還原指令 | `cp -r ~/documents/網站備份/images_backup_20260615/* ~/documents/website/assets/images/` |

---

## 設計規範

| 項目 | 規格 |
|------|------|
| Navbar logo | `assets/images/logo.jpg`，`h-10 w-auto`，文字左側 flex 排版 |
| 英文頁 Navbar logo 路徑 | `../assets/images/logo.jpg` |
| 英文導覽列：樣青 | JesusWay Forum（非 Youth Ministry） |
| 講員吳必然英文 | Pastor Pijan Wu（非 Wu Biran / Wu Pi-Jan） |
| 奉獻帳戶名稱 | 社團法人台灣樣全人發展協會（中文正式名，不翻英文） |

---

## 維護規則

1. 每次修改後，中文版（根目錄）與英文版（`en/`）必須同步
2. 每次修改後確認 RWD（手機與桌機版面）

---

## 資安原則

| 風險 | 規範 |
|------|------|
| 敏感資料進 git | commit 前確認無帳號、密碼、金鑰等敏感內容 |
| Public repo | 所有內容公開可見，上傳前確認圖片與文字無隱私疑慮 |
| 外部連結 | 嵌入的 YouTube 影片、Line@ 連結定期確認有效性 |
