# 台北樣教會網站 JesuswayTaipei

教會官方網站，以職場年輕世代為核心。

- **網址 repo：** `jesuswaytaipeisrv/jesuswaytaipei`
- **本機路徑：** `~/documents/website`
- **版控工具：** GitHub Desktop（帳號：jesuswaytaipeisrv）

---

## 技術棧

- 純靜態 HTML（無框架、無後端）
- TailwindCSS（CDN）
- Google Fonts：Noto Sans TC
- 響應式設計（桌面／手機版導覽列切換）

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
| `update_sunday.py` | 每週四 21:00 自動抓最新主日信息與樣青講堂、更新表格、git commit |

- 一次執行同時更新 `sunday.html`、`en/sunday.html`、`youth.html`、`en/youth.html`（各維持10筆）
- launchd 服務：`com.jesusway.update-sunday`（電腦關機時錯過，開機後補跑）
- 執行後用 **GitHub Desktop 手動 push**
- Log：`logs/update_sunday.log`

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
