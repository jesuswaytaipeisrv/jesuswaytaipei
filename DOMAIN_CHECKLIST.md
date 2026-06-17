# 自訂網域 + HTTPS 憑證 操作清單（階段一：www.jesuswaytaipei.org）

照順序勾選即可。HTTPS 憑證由 GitHub Pages 自動簽發（Let's Encrypt，免費、免手動申請），
你只需把 DNS 設對、勾 Enforce HTTPS，等它自動發。完整背景見 `DOMAIN_SETUP.md`。

---

## STEP 1：在 Cloudflare 買網域

- [x] 登入 Cloudflare → **Domain Registration → Register Domains**
- [x] 搜尋 `jesuswaytaipei.org` → 結帳購買
- [x] 購買完成後，Cloudflare 自動建立該網域的 zone（DNS 由 Cloudflare 代管）

## STEP 2：在 Cloudflare 設 DNS 紀錄

進該網域 → **DNS → Records**，新增以下 5 筆。
**Proxy status 全部點成「DNS only（灰雲☁️）」** —— 這步沒做對，STEP 5 憑證會發不出來。

- [x] A　　`@`　`185.199.108.153`　灰雲
- [x] A　　`@`　`185.199.109.153`　灰雲
- [x] A　　`@`　`185.199.110.153`　灰雲
- [x] A　　`@`　`185.199.111.153`　灰雲
- [x] CNAME　`www`　`jesuswaytaipeisrv.github.io`　灰雲
  > ⚠️ 此筆最容易漏。漏了會出現 `InvalidDNSError`。

## STEP 3：等 DNS 生效後再 push 程式碼

- [x] 驗證 DNS 已生效（任一）：
  - 終端機：`dig +short www.jesuswaytaipei.org`　應回傳 `jesuswaytaipeisrv.github.io`
  - 或上 https://dnschecker.org 查 `www.jesuswaytaipei.org`（CNAME）
- [ ] DNS 生效後再 push（含全站網址置換 + 本文件）：
  ```bash
  cd ~/Documents/Claude/Projects/jesuswaytaipei && git push
  ```

## STEP 4：在 GitHub 綁定自訂網域

- [ ] Repo `jesuswaytaipeisrv/jesuswaytaipei` → **Settings → Pages**
- [ ] **Custom domain** 欄位填 `www.jesuswaytaipei.org` → Save
- [ ] 等下方出現 **DNS check successful（綠色勾）**（可能需數分鐘）
  > **設定一次就好，不要反覆 Remove/重填** —— 每次都會把 DNS 驗證與憑證簽發的計時器歸零，反而卡住。

## STEP 5：啟用 HTTPS 憑證（自動）

- [ ] DNS check 通過後，**Enforce HTTPS** 選項才會可勾 → 勾選它
- [ ] 等 GitHub 自動簽發憑證（Let's Encrypt，通常數分鐘～最多 1 小時）
  > 期間 Enforce HTTPS 顯示灰色 / unavailable，屬正常，**耐心等、別一直按 Remove**。
  > **不需要自己去任何地方申請憑證或付費。**

## STEP 6：驗證

- [ ] 瀏覽器開 `https://www.jesuswaytaipei.org` → 網址列顯示🔒鎖頭、無憑證警告
- [ ] 首頁背景圖、各分頁、圖片、導覽連結都正常（確認網址置換無誤）
- [ ] 開 `http://www.jesuswaytaipei.org`（http）→ 應自動轉成 https
- [ ] 開 `https://jesuswaytaipei.org`（無 www）→ GitHub 應自動轉到 www
- [ ] 手機寬度檢查 RWD 排版正常

---

## 卡關排解

| 症狀 | 原因 / 處理 |
|------|-------------|
| `InvalidDNSError` / DNS record could not be retrieved | 多為 (a) `www` CNAME 漏建，或 (b) 剛 Remove/重填造成的暫時狀態。先用 `dig` 確認 DNS 正確，正確就「設一次、放著等 15~30 分鐘」別再動 |
| Enforce HTTPS 灰色不能勾 | 憑證還沒簽好（DNS check 通過後才會開始發）。耐心等，別反覆 Remove |
| 一直「Certificate not yet created」 | 多等一會；確認 5 筆紀錄都是 **DNS only 灰雲**；確認沒有反覆 Remove 重置計時器 |
| 網站 404「There isn't a GitHub Pages site here」 | repo 尚未 push `CNAME`，或 Custom domain 未設；確認 STEP 3、4 完成 |
| 圖片 / 樣式破圖 | HTML 內仍有舊網址；本次已置換，若日後換網域記得再置換一次 |
| 想加 Cloudflare 加速（橙雲） | **等 STEP 5 憑證發好、HTTPS 正常後**再開橙雲，並把 SSL/TLS 模式設 **Full**。順序不可顛倒 |

---

## 階段二預告（.org.tw 申請下來後）

切換正式網域並把 .org 設 301 轉址，步驟見 `DOMAIN_SETUP.md`〈階段二〉。屆時本清單重做一次，
網域改成 `www.jesuswaytaipei.org.tw` 即可。
