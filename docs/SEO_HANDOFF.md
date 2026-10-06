# SEO 基礎建設 — 移轉需求（交給 CLI 施作）

> 建立：2026-10-06（家用機，VS Code 對話整理）。施作者讀完本檔即可開工，不需回頭看原對話。
> 本專案是 2026-07-26 前的既有專案：**不套用 think.md 骨架**，紀錄寫 `docs/DEVLOG.md`＋`CLAUDE.md` 索引。
> 完成後把本檔標成「已完成」並在頂端註明完成日期與 commit，不要刪檔。

---

## 1. 目標與範圍

讓 Google（以及會讀網頁的 AI 搜尋）正確理解本站：哪些頁要收錄、中英文頁是同一頁的兩種語言、
教會的名稱／地址／聯絡方式是什麼。全部是 `<head>` 與根目錄靜態檔的修改，**頁面外觀零變動**。

**做（本次範圍）**

| # | 項目 | 檔案 |
|---|---|---|
| A | 新增 `robots.txt` | 根目錄 |
| B | 新增 `sitemap.xml`（18 個網址） | 根目錄 |
| C | 18 頁加 `<link rel="canonical">` | 全部 `*.html`、`en/*.html` |
| D | 18 頁加 hreflang（zh-Hant／en／x-default） | 同上 |
| E | 首頁加 JSON-LD 結構化資料（Church） | `index.html`、`en/index.html` |
| F | 新增回歸測試 `tests/test_seo_head.py` 並納入 `run_all.sh` | `tests/` |
| G | 文件：README「新增頁面檢查清單」、DOMAIN_SETUP 階段二補註、DEVLOG、CLAUDE.md 索引 | 文件 |

**不做（範圍外，別順手改）**

- 頁面 `<title>`、`meta description`、內文文案：這些要使用者決定，本次不動
- 新增頁面、改版面、改 Tailwind／字型
- Cloudflare 任何設定（**灰雲是刻意的，不可改橘雲**，見 `CLAUDE.md`〈已知地雷〉）
- Google Search Console 驗證、Google 商家檔案：要使用者本人操作，見第 6 節，CLI 只負責寫操作步驟

---

## 2. 已確認的事實（2026-10-06 從 repo 實查，直接用，不要另外編）

- 正式網址：`https://www.jesuswaytaipei.org`（`CNAME` 檔）。未來會換 `.org.tw`，見 `DOMAIN_SETUP.md` 階段二
- 頁面：9 中文（根目錄）＋9 英文（`en/`），檔名兩邊一一對應：
  `index` `about` `sunday` `youth` `abbafood` `worship` `creative` `contact` `donate`
- 中文頁 `<html lang="zh-Hant">`，英文頁 `<html lang="en">`
- **每頁現有 `og:url` 就是標準網址**，canonical／hreflang／sitemap 一律跟它完全一致：
  - 首頁用目錄形式：`https://www.jesuswaytaipei.org/`、`https://www.jesuswaytaipei.org/en/`
  - 其餘用檔名：`https://www.jesuswaytaipei.org/about.html`、`https://www.jesuswaytaipei.org/en/about.html`
- 地址（中）：`台北市中山區松江路206號十四樓之一`（`contact.html` 第 139 行）
- 地址（英）：`14F-1, No. 206, Songjiang Rd., Zhongshan Dist., Taipei`（`en/contact.html` 第 137 行）
- Email：`jesuswaytaipei@gmail.com`
- YouTube 頻道：`https://www.youtube.com/@JesuswayTaipei`
- LINE 官方帳號：`https://lin.ee/p8f0vyq`
- Logo／分享圖：`https://www.jesuswaytaipei.org/assets/images/site_bkg.png`（og:image 現用的）
- **站上沒有寫主日聚會時間、沒有電話**。JSON-LD **不要填** `openingHours`、`event`、`telephone`，不得自行推測
- 站上沒有 Instagram／Facebook 連結，`sameAs` 只放 YouTube 與 LINE
- 每頁 `</head>` 前有 GA4 片段（`G-6BH0T2SH0Y`），**不可動到、不可重複**
- `update_sunday.py` 只在 `sunday.html`／`youth.html`（含英文版）的 `<tbody>` 插列，不碰 `<head>`。
  本次修改不影響週四排程，但 **commit 前要跑 `bash tests/run_all.sh` 確認**

---

## 3. 各項規格

### A. `robots.txt`

```text
User-agent: *
Allow: /
Disallow: /docs/
Disallow: /tests/
Disallow: /CLAUDE
Disallow: /README
Disallow: /DOMAIN_
Disallow: /update_sunday.py
Disallow: /heartbeat.py

Sitemap: https://www.jesuswaytaipei.org/sitemap.xml
```

- Disallow 那幾行是為了不讓開發文件被收錄。GitHub Pages 有跑 Jekyll（repo 沒有 `.nojekyll`），
  `.md` 可能被轉成 `.html` 對外提供。**施作前先 `curl -sI https://www.jesuswaytaipei.org/CLAUDE.html`
  與 `/docs/DEVLOG.html`、`/CLAUDE.md` 實查**實際對外的路徑，依結果調整規則（前綴比對，`/CLAUDE` 可同時涵蓋 `.md`／`.html`）。
- 不要加 `Disallow: /assets/`（og:image 在裡面，擋了社群分享預覽與圖片搜尋會失效）。

### B. `sitemap.xml`

- 列 18 個網址，`<loc>` 與各頁 `og:url` 逐字相同
- **不放 `<lastmod>`、`<changefreq>`、`<priority>`**：後兩者 Google 忽略；`lastmod` 沒有自動維護機制，
  寫死的日期很快就不準，不準的 lastmod 比沒有更糟
- hreflang 寫在 HTML 裡（D 項），sitemap 不重複寫 `xhtml:link`
- 標準格式：`<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">`

### C. canonical

每頁一行，自我指向，值等於該頁 `og:url`：

```html
<link rel="canonical" href="https://www.jesuswaytaipei.org/about.html">
```

### D. hreflang

每頁三行，**中英對應的兩頁內容完全相同**（hreflang 必須雙向，少一邊 Google 會整組忽略）：

```html
<link rel="alternate" hreflang="zh-Hant" href="https://www.jesuswaytaipei.org/about.html">
<link rel="alternate" hreflang="en" href="https://www.jesuswaytaipei.org/en/about.html">
<link rel="alternate" hreflang="x-default" href="https://www.jesuswaytaipei.org/about.html">
```

- 首頁用 `https://www.jesuswaytaipei.org/` 與 `https://www.jesuswaytaipei.org/en/`
- 位置：C、D 放在 `og:url` 那行之後、`<title>` 之前，與現有 meta 縮排一致（4 空格）
- 18 頁是機械式插入，**用腳本做、腳本放 `work/` 或用完即刪，不進版控**；插入後逐頁 diff 檢查只多了這 4 行

### E. JSON-LD（只放兩個首頁）

放在 `<head>` 內 GA 片段之前。中文首頁：

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Church",
  "name": "台北樣教會",
  "alternateName": "JesuswayTaipei",
  "url": "https://www.jesuswaytaipei.org/",
  "image": "https://www.jesuswaytaipei.org/assets/images/site_bkg.png",
  "email": "jesuswaytaipei@gmail.com",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "松江路206號十四樓之一",
    "addressLocality": "中山區",
    "addressRegion": "台北市",
    "addressCountry": "TW"
  },
  "sameAs": [
    "https://www.youtube.com/@JesuswayTaipei",
    "https://lin.ee/p8f0vyq"
  ]
}
</script>
```

英文首頁：`name` 改 `"JesuswayTaipei"`、`alternateName` 改 `"台北樣教會"`、`url` 改 `/en/`，
`address` 改用英文（`streetAddress: "14F-1, No. 206, Songjiang Rd."`、`addressLocality: "Zhongshan Dist."`、
`addressRegion: "Taipei"`），其餘相同。

- 不加 `postalCode`、`geo`、`openingHours`、`telephone`（站上沒有，不得自編）
- 寫完到 <https://validator.schema.org/> 貼原始碼驗證，**0 error** 才算過（warning 要列出來回報）

### F. `tests/test_seo_head.py`

比照現有測試風格：純 Python stdlib、不需網路、路徑由 `Path(__file__).resolve().parents[1]` 推導、
直接 `python3 tests/test_seo_head.py` 可跑，並加進 `tests/run_all.sh` 的清單與 `tests/README.md` 的表格。
至少檢查：

1. 18 頁每頁恰好一個 canonical，值等於該頁 `og:url`
2. 18 頁每頁恰好三個 hreflang（zh-Hant／en／x-default），且中英對應頁的三個值完全相同（雙向）
3. hreflang 指到的網址都對應到 repo 內真實存在的檔案
4. `sitemap.xml` 可被 `xml.etree` 解析，`<loc>` 集合 == 18 頁 `og:url` 集合（不多不少）
5. `robots.txt` 含 `Sitemap:` 行且指向 `sitemap.xml`，且沒有 `Disallow: /` 全擋或擋到 `/assets/`
6. 兩個首頁的 JSON-LD 可被 `json.loads` 解析、`@type == "Church"`、沒有 `openingHours`／`telephone`
7. 18 頁仍各恰好一個 `G-6BH0T2SH0Y` 的 gtag 片段（防止插入腳本洗掉或重複 GA）
8. **防止日後新增頁面漏貼**：根目錄與 `en/` 下的 `*.html` 檔名集合必須相同，且都在 sitemap 裡

### G. 文件

- `README.md`：在「網站分析」段附近新增「新增頁面檢查清單」：GA 片段、canonical、hreflang（雙向，兩頁都要改）、
  sitemap 加一行。本次之後新增頁面最容易漏的就是這四件事
- `DOMAIN_SETUP.md` 階段二「全站寫死網址置換」那步，補一句：置換範圍包含 `robots.txt`、`sitemap.xml`、
  JSON-LD，且要用 grep 掃 `*.html *.xml *.txt`，不只 `*.html`；換完到 Search Console 申報「網址變更」
- `docs/DEVLOG.md` 最前面加一段本次修改紀錄（含測試命令與結果、未驗證項目）；`CLAUDE.md`「歷史修改記錄索引」補一行
- `CLAUDE.md`「待辦（跨機器）」：移除指向本檔的那條，改寫成第 6 節「使用者要做的事」中尚未完成的項目

---

## 4. 驗收條件（commit 前逐條對照，沒測到的要明講，不得默認通過）

| # | 驗收條件（使用者做得到 X） | 怎麼驗 |
|---|---|---|
| V1 | 任何人在瀏覽器開 `/robots.txt` 能看到 sitemap 位置，且不會看到首頁或 `assets/` 被擋 | 本機 `python3 -m http.server` 開；上線後再開正式網址一次 |
| V2 | 使用者把 `https://www.jesuswaytaipei.org/sitemap.xml` 提交到 Search Console 時，18 個網址都能被讀到 | 測試 F-4；上線後對 18 個 `<loc>` 逐一 `curl -s -o /dev/null -w '%{http_code}'` 全部 200 |
| V3 | 使用者在任一中文頁按 EN（或反過來），兩頁在 head 互相標示為對方的語言版本 | 測試 F-2、F-3 |
| V4 | 使用者把首頁原始碼貼進 validator.schema.org，看到 Church、0 error，名稱／地址／email／YouTube 正確 | 手動驗證，截圖或貼結果到 DEVLOG |
| V5 | 訪客看到的每一頁和改之前一模一樣，GA 即時報表照樣收得到 | 瀏覽器實開中英首頁＋任兩頁，390／1280 兩種寬度各看一次；測試 F-7；上線後開 GA4 即時報表確認有自己那筆 |
| V6 | 週四 21:00 自動更新照常寫入、不因本次修改出錯 | `bash tests/run_all.sh` 全過（原 38 條＋新增） |
| V7 | 下次有人新增頁面時，漏貼 canonical／hreflang／sitemap 會被測試擋下來 | 測試 F-8：臨時複製一頁成 `zz.html` 跑測試應失敗，刪掉後通過 |

V5 只改 `<head>`、無版面變動，所以只看兩種寬度；若施作中有任何 `<body>` 變動，改回全域規則的 390／768／1280 三種寬度。

---

## 5. 施作注意（已知地雷）

- **動手前先 `git fetch && git status -sb`**，落後就先 pull。這個 repo 有排程會自動 commit＋push
- **避開週四 21:00–22:00、週五 09:00–10:30**（本機排程、CI 補救層、心跳）。commit 前再 pull 一次
- 兩台電腦本機路徑不同（`~/documents/website/` 與 `~/Documents/Claude/Projects/jesuswaytaipei/`），
  `CLAUDE.md` 第 10 行路徑不同是正常的，**不要「修正」**
- macOS 會產生 `.DS_Store`（09-24 擋過一次 rebase），commit 前 `git status` 確認沒混進去
- 插入用的一次性腳本不得留在根目錄；`__pycache__/` 已在 `.gitignore`
- push 到 main＝GitHub Pages 立刻上線，所以 push 前測試要全過

---

## 6. 使用者要做的事（CLI 做不到，完成後在回報裡列清楚步驟給使用者）

1. **Google Search Console**（push 上線後）
   - 新增資源 → 選「網域」→ `jesuswaytaipei.org`
   - 拿到 `google-site-verification=...` TXT → Cloudflare DNS 新增 TXT 紀錄（名稱 `@`，**灰雲**）→ 回 Search Console 按驗證
   - 驗證後：Sitemap → 提交 `https://www.jesuswaytaipei.org/sitemap.xml`
   - 網址審查 → 輸入首頁 → 要求建立索引
   - 這個 TXT 跟待辦裡「GitHub 網域驗證」的 TXT 可以同一次登入 Cloudflare 一起加
2. **Google 商家檔案**（效果最大的一項，跟網站程式無關）
   - 先到 Google 地圖搜「台北樣教會」看是否已有地點：有 → 「擁有這個商家？」認領；沒有 → business.google.com 新增
   - 建議用教會的 `jesuswaytaipei@gmail.com` 帳號建立，避免掛在個人帳號
   - 類別選「教會」，填地址、網站、聚會時間、照片；Google 會寄明信片或視訊驗證
   - 完成後若有商家檔案網址，可回頭加進 JSON-LD 的 `sameAs`
3. **（日後再決定）** 主日聚會時間要不要放上網站。放了之後才能補 JSON-LD 的聚會時間，對「台北 主日 教會」這類搜尋有幫助

---

## 7. 交付回報格式

完成後回報：每條驗收 V1–V7 的結果（通過／未驗證＋原因）、`run_all.sh` 輸出摘要、validator 結果、
commit hash、是否已 push，以及第 6 節的使用者待辦清單。
