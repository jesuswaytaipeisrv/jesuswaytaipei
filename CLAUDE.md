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
- SEO（2026-10-06 起）：根目錄 `robots.txt`／`sitemap.xml`、18 頁 canonical＋hreflang、兩個首頁 Church JSON-LD。**新增頁面照 README「新增頁面檢查清單」**，漏貼會被 `tests/test_seo_head.py` 擋下

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
| `heartbeat.py` | 本機 launchd 週五 10:07（**只裝在龍蝦**，服務名 `com.jesusway.update-sunday-heartbeat`） | 事後複查上一晚的批次有沒有真的讓使用者看到新內容；異常才發 Telegram，純觀測不自動修。判準見「自動更新心跳」節 |

- launchd 服務：`com.jesusway.update-sunday-v2`（2026-07-17 起，取代舊的 `com.jesusway.update-sunday`，見下方修改記錄）
  - 舊的「電腦睡眠導致跳過觸發」推測**已證實是誤判**（2026-07-17 查證：當天電腦全程開機未睡眠，pmset log 無任何 sleep/wake 事件）。真正原因是 launchd 層級的 TCC 權限問題，見下方修改記錄
  - 若懷疑本機那次沒跑，以 GitHub Actions 的執行紀錄或 `sunday.html`/`youth.html` 內容為準，本機 log 沒紀錄不代表沒更新（GitHub Actions 不寫本機 log）
- GitHub Actions：`.github/workflows/update_sunday.yml`，**2026-08-09 起改為每週五 09:00（台北）**，即本機跑完隔天早上才跑，作為本機失敗時的補救層（原本與本機同排週四 21:00，備援從未被真正驗證過，見 2026-08-09 記錄）
- Log（僅本機執行會寫）：`logs/update_sunday.log`
- **失敗告警（2026-09-04 起，本機與 CI 統一走 Telegram）**：兩層都由 `notify_failure()` 發 Telegram，本機 token 取自 `~/.hermes/.env`、CI 取自 repo secrets `TELEGRAM_BOT_TOKEN`／`TELEGRAM_HOME_CHANNEL`（同一支 Hermes bot）。訊息會標明來源是「本機排程」還是「GitHub Actions 補救層」，本機附 log 路徑、CI 附該次 workflow 執行連結
  - **告警依據是「候選影片 ID 不在站上表格中」，不是「日期抓不到」**（2026-09-04 改）。CI 被 YouTube 限流抓不到日期是常態，用日期當依據會週週假警報；比對 ID 不需要日期，天然繞開限流
  - **CI 遇到這種情況會讓該次執行變紅色失敗**（2026-09-04 起）。在此之前六次限流 workflow 全部回報 success，Actions 頁面的綠燈等於說謊；紅燈是 Telegram 之外的第二層訊號
  - **要驗告警管道還通不通**：`gh workflow run update_sunday.yml -f test_alert=true`，會先發一則標明「測試訊息」的 Telegram 再照常執行更新。**送不出去該次執行會直接紅燈**（2026-09-04 複審後補），綠燈才代表管道真的通
  - 觸發告警的情形有三種，都會寫 workflow output `check_failed=true`（2026-09-04 由 `date_fetch_failed` 更名）：抓不到頻道清單、清單回 0 筆、候選影片 ID 不在站上表格中
  - 舊做法（已淘汰）：2026-07-17～09-04 CI 端是寄信到 `jesuswaytaipeisrv@gmail.com`，那不是日常會看的信箱，2026-08-06 那封警告信就是這樣被忽略的；且該信自 07-30 起連續六次都是誤報

**測試：** `bash tests/run_all.sh`（50 條：心跳判準 28、`git_commit()` 4、`last_run.json` 4、日期欄位順序 2、SEO head 12）。涵蓋範圍與**沒涵蓋的部分**寫在 `tests/README.md`。

**`update_sunday.py` 一次更新的檔案：**
- `sunday.html` + `en/sunday.html`（主日信息表格）
- `youth.html` + `en/youth.html`（樣青講堂表格）

---

## 自動更新心跳（judgement 定案 2026-09-26，逼問流程後）

起因：09-24 排程**準時跑完、內容全對、commit 也建了，但沒 push**（版控中的 `.DS_Store` 擋住
`pull --rebase`），網站兩天沒更新而 log 看起來完全正常。09-17 原本設想的心跳判準是
「檢查當天 log 有沒有新段落」，那會把 09-24 這種失效判成成功。

**腳本**：`heartbeat.py`（進版控，三台都看得到）。**plist 只裝在龍蝦**（`com.jesusway.update-sunday-heartbeat`），
**每週五 10:07** 執行——排在 CI 補救層（週五 09:00）之後，結論才是「兩層都沒成功」，
也避開與主 job 被延遲補跑時的時序打架（09-17 主 job 是 21:43 才跑的）。

### 判準的組成（每一條都對應一次真實發生過的失效，沒有一條是為假想風險加的）
| 檢查 | 對應的事故 |
|---|---|
| 當天沒有執行紀錄 | 09-10（launchd 沒觸發）、07-17（TCC spawn 失敗） |
| 候選日期與 `origin/main` 四頁不一致 | 09-24（跑完沒 push） |
| `origin/main` 對了但線上網站還是舊的 | Pages 間歇逾時失敗（已知現象，解法是 Re-run） |
| 主 job 記下的 `en_fallback` 為 True（**不是**「頁面上有沒有中文」） | Gemini 回 503 時腳本靜默 fallback（09-24 樣青那列） |
| 抓不到頻道清單／候選為空（**該次 exit 仍是 0**） | 09-17（fetch 失敗時主 job 不 raise，寫完 `failure_reason` 就走到「無更新，結束」正常收場；那晚 `notify_failure()` 自己也沒網路發不出去，兩層都不出聲） |

**訊號來源是 `logs/last_run.json`，不是 log 的中文字串。** 主 job 每次執行都寫這份機器可讀的
狀態（`run_at`／`candidates`／`en_fallback`／`pushed`／`failure_reason`／`exit`）。判準綁在人類可讀
的措辭上，哪天改一句文案心跳就會靜默失效——而這個心跳唯一不能有的失效模式就是「自己壞掉卻安靜」。

**知識層失敗 vs 交付層失敗（2026-09-26 補判準時釘出來的分界）**
- **知識層**：`failure_reason` 有值＝本機那次**不知道最新是哪一支**（抓不到頻道清單、抓不到日期）。
  有東西無法確認，**一律 ⚠️**，即使可查的那幾頁剛好都對、即使該次 `exit` 是 0。
  不這樣做就會重演 09-17：主 job 靜默走完、告警自己也發不出去，整週沒人知道。
- **交付層**：候選完整、`failure_reason` 是 None，但 `exit≠0` 或沒推出去（09-24 的形狀）。
  若所有可查內容都正確，代表 CI 補救層或人工補上了 → 發**非 ⚠️** 的低調通知。
- 那一週頻道上只有其中一類（例如只有樣青、沒有主日）時**不誤報**——候選是唯一真相，不去猜頻道有沒有主日。

**沉默政策**：失敗才出聲；一切正常時完全安靜，但連續 **4 週**沒發過任何訊息就發一則存活訊號
（沿用 egress-audit「靜音＋沉默上限」的成例）。**不自動修**：只觀測，不 push、不 re-run。
**時間戳只在真的送出去時才更新**——送失敗卻記上去，等於讓「管道壞了」被沉默上限判斷成「剛通知過」，於是繼續安靜四週。這個缺陷 2026-09-26 實作當天就踩到並修掉（見 DEVLOG）。

### 驗收條件（每條都是「使用者做得到 X」，commit 前逐條對照）
**改判準或改 `heartbeat.py` 之前先跑 `bash tests/run_all.sh`（50 條）**，下面每一條都有對應測試釘住。測試不需要網路／`yt-dlp`／`gh`，也不會發 Telegram，任何一台都能跑。
1. 週四排程完全沒觸發時，使用者在週五上午收到一則 ⚠️，訊息明說「當天沒有任何執行紀錄」。
2. 排程跑了但內容沒推上 `origin/main` 時，使用者收到 ⚠️，訊息指出候選日期與站上日期各是什麼。
3. 內容已推上 `origin/main` 但線上網站還是舊的時候，使用者收到 ⚠️，且能從訊息分辨這是**部署層**而非更新層的問題。
4. 主 job 那次翻譯 fallback（`en_fallback` 為 True）時，使用者收到 ⚠️ 並知道要補譯哪一頁。**反面也要成立**：英文頁本來就有中文姓名的那幾列不得觸發告警（見下方地雷）。
5. 頻道上本來就沒有新主日／樣青的那週（例如 09-20），使用者**收不到任何訊息**。
6. **交付層**失敗（`exit≠0`／沒推出去，但候選完整）而網站結果正確時，使用者收到一則**非 ⚠️** 的低調通知，說明本機層失敗、CI 已補上。
7. 一切正常時使用者收不到訊息；但連續 4 週沒收到任何訊息時，第 4 週會收到一則存活訊號。
8. 心跳讀不到或看不懂 `logs/last_run.json` 時，使用者收到 ⚠️——**不得靜音當成正常**。
9. 使用者在任何一台電腦 `git pull` 後都看得到 `heartbeat.py` 與本節判準，並從「自動化」表看出 plist 只裝在龍蝦。
10. 使用者可以手動跑一次 `HEARTBEAT_TEST_ALERT=true` 驗證告警管道還通不通，且送不出去時該次執行以非 0 結束。**2026-09-26 已實發驗證：Telegram 回 200、exit 0，使用者當場確認手機收到。管道全程通。**
11. 心跳不會自行 commit、push 或重跑任何東西（純觀測）。
12. 本機排程那次**抓不到頻道清單或沒記下任何候選**時，使用者收到 ⚠️——即使該次是以 `exit 0` 正常收場（09-17 形態）。且 `failure_reason` 有值時不因「可查內容剛好都對」而降級成低調通知。

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
- **本機層兩次失效都緊貼系統更新作業**（2026-09-24 以 `system_profiler SPInstallHistoryDataType` 查得）：09-10 那次沒觸發的 21:00，前 22 分鐘剛裝完 `Command Line Tools for Xcode 27.0`（9/10 20:38）；09-17 那次延遲到 21:43 才跑、一開跑就 DNS 失敗，當晚 22:24 裝的是 **macOS 27.0** 大版本更新（`pmset -g log` 紀錄在 09-17 被重置、22:24 出現 Setup Assistant 可佐證）。⚠️ **這是時間相關，不是因果證明**，unified log 已過保留期。排查週四漏更新時，**先查當天有沒有系統更新**，比重查 launchd 設定快。（2026-09-24）
- **告警不是永遠發得出來**：09-17 那次 `notify_failure()` 本身也失敗（`Errno 51 Network is unreachable`），因為失敗原因就是沒網路。**「沒收到 Telegram 告警」不等於「那週沒問題」**，週四晚上機器有異動時仍要看 log 或站上內容。（2026-09-24）
- **工作樹只要有任何未提交修改，`git pull --rebase` 會整批拒絕**（`cannot pull with rebase: You have unstaged changes`），於是「內容做完、commit 也建了，卻沒 push」。2026-09-24 就是被兩個納入版控的 `.DS_Store` 擋掉整週更新。已於 2026-09-26 把 `.DS_Store` 移出版控並加進 `.gitignore`，`git_commit()` 也改用 `-c rebase.autoStash=true`。**教訓：查排程成敗不能只看「有沒有跑」，要看 `git status -sb` 的 ahead。**（2026-09-26）
- **Gemini 翻譯可能回 503（模型高負載）**，腳本會 fallback 成中文並留 `[WARNING] 樣青英文版暫用中文，請 push 前手動確認`。這種情況 commit 照建、push 照做，**不會觸發任何告警**——週四之後看到英文頁是中文就是踩到這個。（2026-09-26）
- 本機電源設定：AC `sleep 0`（不睡）、電池 `sleep 1`，且 `pmset -g sched` **沒有任何排定喚醒**。週四 21:00 沒插電源的話，排程要等人喚醒才補跑，補跑當下網路常還沒接回來。這**不推翻** 07-17 的結論（那兩次都查證機器醒著），只解釋 09-17 這種「延遲觸發＋沒網路」的形態。（2026-09-24）

- **`en/` 英文頁刻意保留中文姓名**，例如 `王馥蓓｜Chief Sustainability Advisor, Dentsu Group`、
  `黃名仕｜Founder & CEO, Open AI Fab`（中文姓名｜英文職稱的雙語格式）。
  所以**不能用「頁面上有沒有中文」判斷翻譯是不是失敗**——那會週週假警報，而假警報正是這個批次的歷史病根。
  要判翻譯 fallback 一律讀 `logs/last_run.json` 的 `en_fallback`，那是主 job 自己記下的事實。（2026-09-26）
- **讀 `origin/main` 之前一定要先 `git fetch`**，而且要檢查 fetch 的回傳碼。
  remote-tracking ref 是上次 pull/push 留下的快照：CI 補救層從 GitHub 端推的內容，本機不 fetch 就完全看不到，
  會把「CI 已經補上」誤判成「沒推上去」。fetch 失敗也不能默默往下比對（會拿舊 ref 算出 ahead 0）。（2026-09-26）
- **「本機領先 origin/main」不等於「網站內容沒送出去」**：這 repo 三台輪流維護、`CLAUDE.md` 與 DEVLOG 常手動編輯，
  把任何未推 commit 都當成問題會週週假警報。判準要限定在「ahead 的 commit 有動到那四頁 HTML」。（2026-09-26）

**YouTube 抓取**
- YouTube 對 GitHub Actions 共用 IP 限流是常態，**CI 抓不到日期不是程式 bug**（本機同一支影片 ID 測試正常）。（2026-07-02、2026-07-17）
- 頻道標題格式會變（日期前綴曾被整批拿掉）。日期解析依序：標題前綴 → `release_date`（無則 `upload_date`）→ 描述欄「日期：YYYY/MM/DD」。格式再變時先檢查這三層。（2026-06-19、2026-07-02）
- **直播日期一律以 `release_date` 為準，不可改回 upload 優先**：重播檔處理完 YouTube 才更新 `upload_date`，可能比開播日晚兩天。2026-10-01 `_o_9r6qJUPw`（09-27 主日）就被寫成 2026.09.29；10-03 改 release 優先並手動更正、`tests/test_date_fields.py` 釘住。（2026-10-03）
- ⚠️ 舊的警告信會週週誤報（依據是「日期解析失敗」）。**2026-09-04 已改為比對候選影片 ID 是否已在表格中，並改走 Telegram**；現在收到告警＝頻道上有、站上沒有，才需要處理。（2026-08-22 查證、2026-09-04 修）
- **這個 repo 的 `GITHUB_TOKEN` 預設權限是 `read`**（2026-09-04 以 API 查證），所以 workflow 必須自己宣告 `permissions: contents: write`，否則補救層真的要 push 時會被 403 擋掉。**CI 的寫入路徑至今從未真的跑過**，第一次輪到它時要先看這裡。（2026-09-04）
- 判斷「這支影片是不是已經在站上」時，**中英文兩頁都要比對**。只看中文頁的話，「中文寫成功、英文那次失敗」的半完成狀態會被判成最新，英文頁永遠補不上也不會告警。`sync_video_row()` 已改為逐檔判斷、缺的才補，不會重複插入。（2026-09-04 複審發現）
- workflow 注入 `GOOGLE_API_KEY` 時要引用 **`secrets.GEMINI_API_KEY`**（兩邊名稱不同）。2026-09-04 前寫成 `secrets.GOOGLE_API_KEY`（不存在）→ 空字串 → CI 的翻譯被靜默跳過。（2026-09-04）
- 本機 yt-dlp 是 **brew 裝的**（`brew upgrade yt-dlp`）。它自己的過期警告會說「你是用 pip 裝的」，那是誤導。（2026-09-04）
- `youth.html` 沒有 2026.06.28 那列是**影片下架後刻意移除**（`cb6589f`），不是漏更新。（2026-08-22）

**GA4 / 網域**
- `/g/collect` 顯示 **503 是假象**（gtag 走 `sendBeacon`／`keepalive`，攔截層狀態碼判讀不準），一律以 GA4 即時報表為準。（2026-08-06）
- 刻意**不設「排除內部流量」**（對外是 HiNet 浮動 IP，規則會默默失效）。要做請改用 GA Opt-out 瀏覽器擴充。（2026-08-06）
- GitHub Pages 憑證卡住不簽出時，解法是做**一次**乾淨的 Remove → 等 2 分鐘 → 重填 Custom domain。（2026-06-17）
- **Pages 部署可能卡在 `waiting` 不動**（build 成功、deploy job 永遠等，不會變失敗）。本 repo 的 `github-pages` 環境**沒有核准關卡**（無 reviewers、wait_timer 0，只有 `main` 分支規則），所以不是在等人核准，是 GitHub 端卡住。解法：**Cancel → Re-run**，家用機沒 `gh` 就用 Keychain PAT 打 `POST /actions/runs/<id>/cancel` 再 `…/rerun`。正常部署 1 分鐘內完成，超過 10 分鐘就當卡住處理。（2026-10-06）

**Gemini API key**
- 變數名是 `GOOGLE_API_KEY`，**不是** `GEMINI_API_KEY`。全部專案裡只有這裡不一樣，是刻意保留的現狀；三處必須一致：`update_sunday.py`（翻譯函式）、`.github/workflows/update_sunday.yml`、GitHub repo secret。2026-06 就是因為 script 寫 `GEMINI_API_KEY`、`.env` 實際是 `GOOGLE_API_KEY` 而壞過一次（見 `@docs/DEVLOG.md`），要改名三處一起改。（2026-08-30）
- **這把 key 屬於 Cloud 專案 `website-jesusway`（`gen-lang-client-0734466101`，2026-06-05 建立）**。AI Studio 是**一個專案配一把 key**，依專案名稱與建立日對應而得（來源：使用者的 Gemini 計費架構筆記）。secret 的值本身讀不回來（單向寫入），也不需要讀——要換就直接在該專案下開新 key 覆蓋 secret。⚠️ 換的時候留意：Google 已對**新建立的專案**停售 `gemini-2.5-flash`，而 `update_sunday.py` 正是用它，所以新 key 必須開在 `website-jesusway` 底下，不要另開專案。（2026-08-30）

**環境差異（三台電腦輪流維護）**
- 本機路徑因機器而異（`~/documents/website/`、`~/Documents/Claude/Projects/jesuswaytaipei/`），**這是正常的，不要「修正」成單一路徑**。動手前先 `git pull`。
- 自動化 push 用的 SSH deploy key 只在實際跑排程那台；其他機器用 HTTPS + Keychain PAT push，兩者並存正常。
- 家用機**沒裝 `yt-dlp`、也沒有 `gh` CLI**，查排程走 REST API（指令見 `@docs/DEVLOG.md` 2026-08-22 段）。

**Cloudflare Security Insights 報告（2026-09-28 判讀，下次收到同樣內容不必重查）**
- **Dangling A Record ×3 ＝ 誤報**：`185.199.108–111.153` 是 GitHub Pages 官方 IP（GitHub 用 Fastly 當 CDN），根網域實測 301 → `www`、服務正常。
  真正要防的「網域被別人在 GitHub 認領」要靠 **GitHub 網域驗證**（見待辦），不是刪 DNS 記錄——**刪了網站就掛了**。
- **Unproxied A ×3／CNAME ×1 ＝ 刻意設定，不可照建議改橘雲**：見 `DOMAIN_SETUP.md` 灰雲規定，GitHub Pages 要自己簽 Let's Encrypt。
  所謂「來源 IP 外露」是 GitHub 公開 IP，沒東西可藏。
- **HSTS／Bot Fight Mode／AI Labyrinth／Security.txt ＝ 可忽略**：前三者都只在橘雲生效，灰雲下開了也無作用；
  `www` 已由 GitHub 送 HSTS（實測 `max-age=31556952`）；靜態站無漏洞通報需求。
- **Cloudflare 的 Always Use HTTPS 不必開**：灰雲下無作用。HTTP→HTTPS 由 GitHub Pages「Enforce HTTPS」負責，2026-09-28 實測根網域與 `www` 的 `http://` 都 301 到 `https://www.jesuswaytaipei.org/`。（isdsdesk.com 是橘雲，才需要在 Cloudflare 開。）
- 當時憑證實測：Let's Encrypt，2026-08-16 簽、**11-14 到期**，GitHub 自動續簽正常（記憶中「9/15 到期」那張已被取代）。
- 同報告的 **Cloudflare 帳號未開 MFA 是真問題**（帳號同時管本站網域、isdsdesk.com、兩個 R2 備份 bucket），屬帳號層級。**2026-09-28 已處理**：使用者另設 Cloudflare 帳號密碼（原本只用 Google SSO、從沒設過），MFA 改用**驗證器 App**、郵件驗證已停用（郵件與 SSO 同一個 Gmail，當第二因素等於沒有）。

---

## 待辦（跨機器）

- **SEO 上線後要使用者本人做的事**（程式部分 2026-10-06 已完成，見 `@docs/DEVLOG.md` 同日段；完整步驟在 `@docs/SEO_HANDOFF.md` 第 6 節）：
  1. ~~**Google Search Console**~~ **已完成（2026-10-06）**：「網域」資源 `jesuswaytaipei.org`，擁有者帳號 **`jesuswaytaipeisrv@gmail.com`**
     （不是 `jesuswaytaipei@gmail.com`，使用者選的；通知信寄到這個信箱）。Cloudflare 根網域 `@` 有一筆 `google-site-verification=…` TXT
     ——**不可刪，刪了資源會失去驗證**。sitemap 已提交成功；中英首頁都已要求建立索引（中文首頁原本就有收錄、英文首頁原本「Google 無法辨識」）。
     1–2 週後回 Search Console 看「網頁」與「成效」報表。
  2. **Google 商家檔案**（效果最大）：先在 Google 地圖搜「台北樣教會」，有就認領、沒有就到 business.google.com 新增；
     用 `jesuswaytaipei@gmail.com` 建、類別「教會」。完成後若有商家檔案網址，可加進兩個首頁 JSON-LD 的 `sameAs`。
  3. **GA4 即時報表**確認改版後仍收得到自己那筆（CLI 只驗了 gtag 有載入）。
  4. （待決定）主日聚會時間要不要放上網站——放了才能補 JSON-LD 的聚會時間；
     以及要不要把 JSON-LD 改成 `["Church", "Organization"]` 消掉 validator 的 `email` 警告（目前 0 error、1 warning，不影響使用）。
- **（選做，不急）GitHub 網域驗證**：GitHub 頭像 → Settings → Pages → Add a domain → `jesuswaytaipei.org`，照指示在 Cloudflare 加 `_github-pages-challenge-jesuswaytaipeisrv` TXT（灰雲）→ Verify。防止 repo 自訂網域設定被拿掉時他人認領本網域（2026-09-28 Security Insights 判讀的衍生待辦）。
- ~~查 09-10（四）本機 launchd 為何沒推 09-06 主日~~ **已在龍蝦查過（2026-09-17）**：兩份 log 09-10 都**一行沒有**，launchd 根本沒觸發；
  機器當時醒著、設定正確、21:19 人工重開機；unified log 已輪替，觸發為何被跳過查不到。詳見 `@docs/DEVLOG.md` 2026-09-17 段。
  ~~**09-17（四）21:00 跑完要看 `update_sunday_launchd.log` 有沒有新段落**~~ **已看（2026-09-24）**：有新段落，但**遲到 21:43 才觸發**且一開跑就 DNS 失敗——當晚 22:24 裝了 macOS 27.0。所以 09-17 不是「沒觸發」，是「在系統更新空窗期觸發並失敗」。本機層心跳**仍未施作**，要不要做等今晚（09-24）這次的結果再定。
- ~~**09-17（四）跑完檢查 `RdE18JKoivM` 的日期**~~ **已驗證，本條結案（2026-09-24）**：實測 `upload_date` 已變成 **20260913**，與 `release_date` 相同——預排直播開播後 YouTube 會把 upload_date 改成實際開播日。現有 upload 優先的邏輯不會寫錯，`fetch_date()` 維持原樣。**⚠️ 這個結論只對預排直播成立，2026-10-03 被推翻**：一般直播的 upload_date 會晚於開播日，已改 release 優先（見已知地雷〈YouTube 抓取〉）。
- ~~**2026-09-24（四）21:00 這次要驗**~~ **已驗並收尾（2026-09-26）**：排程準時觸發、兩支都寫入四頁，但因 `.DS_Store` 擋住 `pull --rebase` 而沒 push；09-26 已補英文翻譯、移除 `.DS_Store`、修 `git_commit()` 改用 autoStash，內容已上線（線上四頁實查過）。詳見 `@docs/DEVLOG.md` 2026-09-26 段。
- ~~**RWD 三寬度（390／768／1280）尚未實機驗**~~ **已在家用機驗完，本條結案（2026-09-26）**：`youth.html`／`en/youth.html`
  六組皆無水平捲動、Watch 按鈕在畫面內、來賓欄 390 隱藏／768 起顯示。詳見 `@docs/DEVLOG.md` 2026-09-26 第五段。
- ~~**待覆核：10-01（四）主 job 與 10-02（五）心跳的首次正式執行**~~ **已在龍蝦覆核，本條結案（2026-10-03）**：
  10-01 log 無 `cannot pull with rebase`／`no rebase in progress`（autoStash 有效）；心跳 `runs = 1`、`last exit code = 0`、
  首次訊號已送出；`last_run.json`、`git status -sb`、線上四頁三方一致，心跳判定正確。詳見 `@docs/DEVLOG.md` 2026-10-03（龍蝦）段。
- **這五個跨層問題目前沒有人會審，是已知的未審風險**（範圍 `e411787..03739ed`）。
  **2026-09-26 使用者決定不在家用機跑 Codex review**，此前的計畫（在有 Codex CLI 的那台跑架構層複審）取消。
  實作層已由本機 `/code-review`（high）審過並修完十項，但下面這五題屬於跨層行為，**沒有被任何人審查過**。
  要動這個批次的架構之前先讀這五題；哪天有 Codex 或別的獨立審查可用，這就是現成的清單。
  動到程式的只有三個檔：`update_sunday.py`、`heartbeat.py`、`.github/workflows/update_sunday.yml`。
  實作層已審過（附測試），以下是**沒有被審過的跨層行為**：
  1. **三層同一週都失敗時如何收斂**。現在有本機週四 21:00、CI 週五 09:00、心跳週五 10:07 三層。
     心跳只比對「最新一列」，若 CI 在 10:07 前後正在補寫（例如有人手動 re-run），心跳可能讀到半完成狀態。
  2. **`MAX_ROWS=10` 的滾動刪除 × `sync_video_row()` 補寫半完成狀態**會不會互相打架（原本那題，仍未審）。
  3. **心跳只看最新一列的盲區**（2026-09-26 實測釐清：「同一週漏兩支」**不是**盲區，四項會各自報出來；
     寫錯的原描述已更正）。真正的盲區是**表格中間的洞**：某週漏了、⚠️ 也發了，但**告警沒被處理**，
     下一週更新的影片上站後站上第一列變成新的 → 候選與第一列相符 → 心跳從此靜音，那個洞再沒有機制提起。
     09-11→09-13 真的這樣走過一次（告警有發、有看到、還沒空處理，結果 09-06 變成非最新那支）。
     心跳是單週判定、無累積狀態，這是判準的邊界不是 bug。要解得靠累積狀態或比對整張表 vs 頻道近十支
     （每週多打十次 yt-dlp、會撞限流），兩種都不便宜，**請從架構層評值不值得**。
  4. **`last_run.json` 是本機狀態且不進版控**：本機那週完全沒跑時，心跳讀到的是上週的 JSON，
     會報「本週沒跑」⚠️ 即使 CI 已補上內容。這是刻意 fail loud（判準寫在「自動更新心跳」節），
     但值得從架構層判斷該不該區分「本機沒跑但結果正確」與「兩層都沒成功」。
  5. **兩支腳本各自實作 Telegram 發訊**（`notify_failure()` 與 `heartbeat.send()`，共用同一組
     `~/.hermes/.env` token）。刻意分開的理由寫在 `heartbeat.send()` 的 docstring，
     但這是「安全邊界重複實作」，值得確認要不要收斂。

  **已經測過的不必重跑**（結果都在 `@docs/DEVLOG.md` 2026-09-26 三段）：`git_commit()` 三情境、
  心跳判準 16 情境、主程式與心跳的真實資料端對端、launchd spawn、以及
  **autoStash 與真衝突同時發生**（git 會自己 `Applied autostash.`，無 stash 殘留、雜項保留、沒卡在 rebase）。
- **CI 的 `git push` 路徑仍未實際跑過**（見 `@docs/DEVLOG.md` 2026-09-04「尚未驗證」）。
  下次真的輪到補救層寫入時，第一個要看這裡。

---

## 歷史修改記錄索引

完整內容在 **`@docs/DEVLOG.md`**。大致新到舊，早期幾段的順序原本就沒排整齊，分流時維持原樣未動。

- **2026-10-06** — SEO 基礎建設：`robots.txt`、`sitemap.xml`、18 頁 canonical＋hreflang、兩首頁 Church JSON-LD、`test_seo_head.py`（12 條）；外觀逐像素比對零變動；測試 50 條；Pages 部署卡 `waiting` 以 cancel＋rerun 解，正式網址 18 頁驗過
- **2026-10-03（龍蝦）** — 10-01 主 job／10-02 心跳首次正式執行本機端覆核：autoStash 有效、心跳 exit 0、三方交叉一致，待辦結案
- **2026-10-03** — 10-01 排程有成功上線，但主日日期寫成 09.29（應為 09.27，upload_date 晚於開播日）：手動更正、yt-dlp 日期改 `release_date` 優先、新增 `test_date_fields.py`；測試 38 條
- **2026-09-30** — 測試會污染正式 `heartbeat.log`（596 行假紀錄，含假的「Telegram 已送出」）：測試改把 log 路徑導到暫存、加守門條 G、整檔清除；測試 36 條
- **2026-09-26，第五段** — RWD 三寬度實機驗證（youth 中英兩頁 × 390／768／1280，六組全過），待辦結案
- **2026-09-26，第四段** — 測試進版控：`tests/`（35 條，`bash tests/run_all.sh`），三台都能跑、不需網路／`yt-dlp`／`gh`、不發 Telegram；新增 `test_last_run_state.py`
- **2026-09-26，第三段** — 本機 `/code-review`（high）十項發現全數修掉（2 high：`git fetch` 跑在讀 `origin/main` 之後、CJK 偵測誤報而權威值 `en_fallback` 沒用）；測試 stub 降到 `git()` 層，共 31 條通過
- **2026-09-26，第二段** — 新增週五 10:07 心跳（`heartbeat.py` + 只裝龍蝦的 plist）：判準改以結果為準、訊號來源 `logs/last_run.json`、13 情境測試全通過；⚠️ 真實 Telegram 管道尚未實發
- **2026-09-26** — 09-24 排程結果：準時觸發、內容全對，但被納入版控的 `.DS_Store` 擋掉 `pull --rebase` 導致沒 push；補英文翻譯（Gemini 503 fallback 成中文）、`.DS_Store` 移出版控、`git_commit()` 改用 `rebase.autoStash`
- **2026-09-24** — 全機排程稽核：09-17 失敗歸因到 macOS 27.0 更新當晚的網路空窗（含告警靜默）、站上缺 `RdE18JKoivM`（09.13 主日）與 `fcmrvY8uMQc`（09.20 樣青）、⚠️ 09-13 留的 `upload_date` 日期疑慮已驗證解除
- **2026-09-17** — 09-10 本機層漏更新的龍蝦側 log 補查：launchd 根本沒觸發、機器醒著、21:19 人工重開機
- **2026-09-13** — 09-06 主日 `WqxohQJV9ao` 兩層都漏更新（第一次真漏、非誤報），家用機手動補上；⚠️ 09-13 那支預排直播 upload_date≠release_date，週四跑完要查日期
- **2026-09-04** — 本週排程確認、告警改走 Telegram、⚠️ 誤報修掉、yt-dlp 升級；同日 `/code-review` 複審後再修五項（限流時的 `ValueError`、空清單靜默通過、自我檢查假通過、只比對中文頁、CI 缺 `contents: write`）
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
