# 自訂網域設定說明（DOMAIN_SETUP）

本站為 GitHub Pages 靜態網站，repo：`jesuswaytaipeisrv/jesuswaytaipei`。
規劃同時持有兩個網域，**以 `.org.tw` 為最終正式網域**，但分兩階段上線。

- 正式網域（最終）：`www.jesuswaytaipei.org.tw`
- 過渡 / 轉址網域：`www.jesuswaytaipei.org`

> 注意：本站是 **project page**（repo 名非 `*.github.io`），綁自訂網域後網站會服務在
> 網域**根目錄**（例：`https://www.jesuswaytaipei.org/index.html`），原本的 `/jesuswaytaipei/`
> 子路徑會消失。因此所有 HTML 內寫死的絕對網址需與正式網域根目錄一致。

---

## GitHub Pages 用的 DNS 紀錄（兩個網域共用同一組格式）

要讓某個網域指向 GitHub Pages，在該網域 DNS 設定：

| 類型 | 名稱 | 內容 | 說明 |
|------|------|------|------|
| A | `@` | `185.199.108.153` | GitHub Pages |
| A | `@` | `185.199.109.153` | GitHub Pages |
| A | `@` | `185.199.110.153` | GitHub Pages |
| A | `@` | `185.199.111.153` | GitHub Pages |
| CNAME | `www` | `jesuswaytaipeisrv.github.io` | GitHub Pages |

> 若用 Cloudflare 代管 DNS，上述紀錄一律設 **DNS only（灰雲）**，否則橙雲代理會卡住
> GitHub Pages 的 HTTPS 憑證簽發。憑證簽好後要不要再開橙雲代理皆可。

---

## 階段一（目前）：只有 .org，以 .org 正式上線

正式網域 = `www.jesuswaytaipei.org`（本 repo 目前 `CNAME` 檔內容）。

### 步驟
1. **在 Cloudflare 買 `jesuswaytaipei.org`**
   Dashboard → Domain Registration → Register Domains。買完自動建立 zone 並改用
   Cloudflare 名稱伺服器。
2. **Cloudflare DNS 設定**（上方「GitHub Pages 用的 DNS 紀錄」，全部 **灰雲 DNS only**）。
   - ⚠️ 易漏：`www` 那筆 CNAME 一定要建，否則 GitHub 回 `InvalidDNSError`。
3. **Repo 設定**：
   - `CNAME` 檔內容：`www.jesuswaytaipei.org`
   - 全站寫死網址已置換為 `https://www.jesuswaytaipei.org/`
   - DNS 生效後再 push，避免綁到尚未生效的網域導致網站短暫無法開啟。
4. **GitHub Pages 綁定**：Repo → Settings → Pages → Custom domain 填
   `www.jesuswaytaipei.org` → 等 DNS 檢查通過（綠勾）→ 勾 **Enforce HTTPS**
   （憑證為 GitHub 自動簽發，可能需數分鐘至一小時；**勿反覆 Remove/重填**，會重置計時器）。
5. **驗證**：瀏覽器開 `https://www.jesuswaytaipei.org`，確認首頁、圖片、各分頁正常。
   無 www 的 `jesuswaytaipei.org` 會由 GitHub 自動轉到 www。

---

## 階段二（之後）：.org.tw 申請下來，切換正式網域 + .org 轉址

`.org.tw` 為台灣 ccTLD，**Cloudflare 不販售**，須向 TWNIC 受理註冊商（如 Gandi 台灣經銷、
Hinet、網路家庭 PChome 等）申請；組織型 `.org.tw` 通常需附立案 / 登記文件。

### 步驟
1. **買 `jesuswaytaipei.org.tw`**，並設定 DNS 指向 GitHub Pages（上方那組 A + www CNAME）。
2. **Repo 切換正式網域**：
   - `CNAME` 檔改為 `www.jesuswaytaipei.org.tw`
   - 全站寫死網址置換：`https://www.jesuswaytaipei.org/` → `https://www.jesuswaytaipei.org.tw/`
   - commit & push。
3. **GitHub Pages**：Custom domain 改填 `www.jesuswaytaipei.org.tw`，重新勾 Enforce HTTPS。
4. **把 .org 改成 301 轉址到 .org.tw**（用 Cloudflare）：
   - 移除 / 停用 `.org` zone 內指向 GitHub Pages 的 A、CNAME 紀錄
   - 新增 Redirect Rule（Rules → Redirect Rules）：
     - 來源：`*jesuswaytaipei.org/*`
     - 目標：`https://www.jesuswaytaipei.org.tw/${1}`（保留路徑）
     - 類型：**301 永久轉址**
5. **驗證**：開 `www.jesuswaytaipei.org` 應 301 跳轉到 `www.jesuswaytaipei.org.tw`；
   直接開 `www.jesuswaytaipei.org.tw` 正常顯示。

---

## 備忘
- 轉址一律用 **301（永久）**，對 SEO 與快取較佳。
- 兩個網域都持有以防搶註 / 混淆，但同一時間只有一個當正式站，另一個純轉址。
- 每次更換正式網域，記得同步置換 HTML 內寫死的絕對網址（圖片、og:image、canonical、導覽連結）。
