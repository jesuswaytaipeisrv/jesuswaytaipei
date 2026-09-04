# 台北樣教會網站 開發記錄（DEVLOG）

逐次修改記錄的完整內容。**由 `CLAUDE.md` 分流而來（2026-08-22）**——原本全部擠在 `CLAUDE.md`
裡，累積到 540 行、其中 84% 是這些逐次記錄，每次進專案都整份載入 context，稀釋掉真正的常設規則。

- **常設規則、技術棧、已知地雷** → 看 `CLAUDE.md`（該檔已濃縮，每次自動載入）
- **某次改了什麼、怎麼查出來的、當時的測試結果** → 看這裡（需要時才翻）
- 新增記錄請**加在最前面**，並在 `CLAUDE.md` 的「歷史修改記錄索引」補一行
- 早期幾段（2026-05／06）的先後順序原本就沒排整齊，分流時刻意維持原樣，未重排

---

## 本次修改記錄（2026-09-04）— 本週排程確認、告警改走 Telegram、誤報修掉、yt-dlp 升級

### 背景
使用者要求確認本週（09-03 週四）排程是否完成。查證結論是**完成**，但沿鏈路查的過程中發現
告警機制本身有兩個問題，一併修掉。**本次修改 `update_sunday.py` 與 workflow，未動網站內容。**

### 一、本週排程查證：完成，網站是最新的
沿整條鏈路走到正式站，逐段證據：

| 環節 | 結果 |
|---|---|
| launchd 觸發 | 09-03（四）21:00:02，`last exit code = 0` |
| 抓取 | 25 筆影片，樣青講堂 2026.08.30 為新內容 |
| 寫入 | `youth.html` 與 `en/youth.html` 都改到 |
| commit | `723425c` |
| push | `pull --rebase` 後推成 `e411787`，本機與遠端 0 差異 |
| Pages 部署 | 09-03 21:00 台北那次 deploy success |
| 正式站實際內容 | `youth.html`／`en/youth.html` 皆顯示 **2026.08.30** |

**主日停在 2026.08.23 是正確的**：`/streams` 最新主日就是 `cj9TAOIjbgU`，`upload_date` 實測
`20260823`；`/videos` 分頁最近 8 支全是敬拜音樂與樣青食堂，**教會尚未上 8/30 的線上主日**。

### 二、告警改走 Telegram（CI 端）
CI 端原本寄信到 `jesuswaytaipeisrv@gmail.com`，那不是會被看到的信箱（2026-08-06 事故即因此
整週未被察覺）。本次讓 `notify_failure()` 本機與 CI 共用：拿掉原本的 `GITHUB_ACTIONS` 早退，
CI 端的訊息改附該次 workflow 執行連結（本機仍附 log 路徑）。

- workflow 移除 `Send date-fetch-failed warning email` 步驟，改為 `Fail the run when dates could not be fetched`
  ——**同時把該次執行標成紅色失敗**。過去六次限流 workflow 全部回報 success，Actions 頁面的綠燈
  等於說謊；紅燈是 Telegram 之外的第二層訊號，就算 Telegram 壞了也看得出來。
- 新增 repo secrets `TELEGRAM_BOT_TOKEN`、`TELEGRAM_HOME_CHANNEL`（與本機 `~/.hermes/.env` 同一支
  Hermes bot，使用者 2026-09-04 明示採此做法）。值以 stdin 餵給 `gh secret set`，未進命令列參數。

### 三、把「⚠️ 誤報」真正修掉（2026-08-22 列為待辦，本次施作）
2026-08-22 已查證那封 ⚠️ 信是誤報，並寫下正解「改用 video_id 比對取代日期判斷」但**未施作**。
本次若只把告警改到 Telegram 而不修這個，**下週五起每週都會有一次紅燈加一則手機通知，且每次都是
假警報**——那會讓人開始忽略 Telegram，而本機真實故障的告警走同一條管道，比原本沒人看的信箱更糟。

改法：告警判斷不再看「日期是否解析成功」，改看**候選影片 ID 是否已在站上表格中**
（`fetch_latest_streams()` 內新增 `missing_from_site()`，沿用既有的 `is_video_in_table()`）。
比對 ID 不需要日期，天然繞開 YouTube 對 CI 的限流。只有「頻道上有、站上沒有」才告警。

### 四、其他修正
- **`GOOGLE_API_KEY` 注入的是不存在的 secret**：workflow 寫 `secrets.GOOGLE_API_KEY`，但 repo 裡的
  secret 名為 `GEMINI_API_KEY` → CI 拿到空字串 → 翻譯被靜默跳過、英文頁只會填中文標題。已改為
  `secrets.GEMINI_API_KEY`。這個 bug 一直沒被發現，是因為 CI 從沒真的寫入過內容。
- **新增 `TEST_ALERT` 自我檢查**：`workflow_dispatch` 加一個 `test_alert` 輸入，打開時先發一則測試
  Telegram 再照常執行。這個批次的歷史教訓就是「備援從未被驗證過」，而告警平時無從得知還通不通。
- **本機 yt-dlp 由 2026.03.17 升到 2026.08.19**（brew，非 pip——它的過期警告訊息會誤導）。

### 測試結果
| # | 測試 | 結果 |
|---|---|---|
| 1 | yt-dlp 升級後：`--flat-playlist` 頻道列表 | ✅ 正常取得 25 筆 |
| 2 | yt-dlp 升級後：`player_client=android` 取日期 | ✅ 回 `20260823`（僅有 SABR 格式警告，取 metadata 不受影響） |
| 3 | yt-dlp 升級後：預設 client 取日期 | ✅ 回 `20260823` |
| 4 | 完整腳本端對端（升級後、改動後各一次） | ✅ 兩支都正確判定「已在表格中，跳過」，無多餘 commit |
| 5 | 告警驗收 (a)：候選 ID 已在表格中 → 不告警 | ✅ `date_fetch_failed = False` |
| 6 | 告警驗收 (b)：候選 ID 不在表格中 → 仍告警 | ✅ `date_fetch_failed = True` |
| 7 | Telegram 本機模式 | ✅ 實際收到，附 log 路徑 |
| 8 | Telegram 模擬 CI 模式 | ✅ 實際收到，附 workflow 執行連結 |

第 5、6 項的手法：攔截 `subprocess.run` 讓「取日期」那支 yt-dlp 回空字串（等同 CI 被限流的實際
狀況），頻道列表那支仍走真實網路，確保測到的是真實候選影片；(b) 另以一份空表格的假站台目錄比對。
測試腳本寫在 scratchpad，未留在 repo。

### CI 端實測（run 33882433189，已結案）
push 後以 `gh workflow run update_sunday.yml -f test_alert=true` 觸發，**該次 CI 又真的被 YouTube
限流**，等於在真實故障條件下一次驗到三件事：

| 驗到什麼 | 證據 |
|---|---|
| secrets 有正確注入 | log 顯示 `TELEGRAM_BOT_TOKEN: ***`、`TELEGRAM_HOME_CHANNEL: ***` |
| CI 端 Telegram 發得出去 | `[INFO] 已發出 Telegram 失敗告警`，手機實際收到，訊息標明「GitHub Actions 補救層」 |
| 誤報已擋掉 | 兩支影片日期照樣抓不到，但 `cj9TAOIjbgU／Dv7X_mTSzHc 已在表格中，站上已是最新，不告警`，
`date_fetch_failed` 未觸發、執行維持綠燈、沒有發出假警報 |

**至此本次修改無待確認項目。**

### 五、`/code-review` 複審與後續修正（同日）
上述改動 push 後跑了一輪 `/code-review`（Claude Code 內建，等級 high，範圍 `e411787..baab025`），
提出五項發現，逐條實地查證後**五項全部屬實**，已全部修掉。

| # | 問題 | 具體後果 | 修法 |
|---|---|---|---|
| 1 | `fetch_latest_streams()` 在 flat-playlist 失敗時 `return None, None`（兩元組），`main()` 卻解三個值 | **正好在限流時炸掉**——`ValueError: not enough values to unpack`，Telegram 收到的是「排程執行失敗：ValueError」而非真正原因，`$GITHUB_OUTPUT` 也永遠寫不進去 | 改回傳三元組，第三個值由 bool 改為**失敗原因字串** |
| 2 | `entries` 為空（exit code 0 但空清單，限流時常見）完全沒防護 | 兩個 candidate 都是 None → 新的 ID 比對法無 ID 可比 → 判定「本週無新內容」、綠燈、不告警。正是本次要消滅的靜默漏更新 | 0 筆直接視為失敗並帶原因 |
| 3 | `TEST_ALERT` 自我檢查在管道壞掉時照樣綠燈 | `notify_failure()` 送不出去只 `logging.error`，不影響 exit code；token 被輪替後跑自我檢查會誤判「管道正常」 | `notify_failure()` 回傳成敗，`TEST_ALERT` 模式送不出去就 `sys.exit(1)` |
| 4 | 站上比對只看中文頁 | 中文寫成功、英文那次拋錯時，中文檔案已落地，之後每次都判定「站上已是最新」→ **英文頁永遠補不上且不告警**，違反中英同步規則 | `missing_from_site()` 改吃多個檔名，中英文都比對 |
| 5 | workflow 沒宣告 `permissions` | 以 API 查得該 repo `default_workflow_permissions` 是 **`read`**，補救層真的輪到它 push 時會被 403 擋掉。CI 從未真的寫入過，所以這個問題一直沒暴露 | 加上 `permissions: contents: write` |

第 4 項連帶改掉 `main()` 的跳過判斷：原本「中文頁有這支 ID 就整段跳過」，改為新的
`sync_video_row()` **逐檔判斷、已有的略過、缺的才補**，所以半完成狀態下次執行會自動修復，
也不會重複插入。第 1、2 項連帶把 workflow output 由 `date_fetch_failed` 更名為 `check_failed`
（現在的意思是「無法確認站上是否最新」，涵蓋抓不到清單與抓不到日期兩種），workflow 對應的
step 條件與名稱同步改掉。

#### 複審後的測試結果
| # | 測試 | 結果 |
|---|---|---|
| A | flat-playlist 失敗（模擬 429）→ 回三元組不炸 | ✅ 帶原因「yt-dlp 取不到頻道影片列表：HTTP Error 429…」 |
| B | exit 0 但 0 筆 → 判為失敗 | ✅ 帶原因，不再靜默通過 |
| C | 真實站台、ID 中英文皆有 → 不告警 | ✅ `reason is None`（誤報仍然沒有回來） |
| D | ID 不在站上 → 告警 | ✅ |
| E | 中文頁有、英文頁缺 → 告警 | ✅ 修正前這裡會誤判成「已是最新」 |
| F | `sync_video_row()` 只補缺的那頁 | ✅ 回 `['en/sunday.html']`，中文頁維持 1 次出現、未重複插入 |
| G | `TEST_ALERT=true` 但 token 不存在 | ✅ exit code = 1（修正前是 0） |
| H | `notify_failure()` 送出成功回傳 `True` | ✅（攔截 `urlopen`，未真的發訊息） |
| I | 完整腳本真實端對端 | ✅ 25 筆、兩支都「中英文表格皆已有，跳過」、無 commit、exit 0 |

A～H 的手法同前：攔截 `subprocess.run` 控制 yt-dlp 的回傳，另建一份「中文有、英文缺」的假站台
目錄測半完成狀態。測試腳本在 scratchpad，未留在 repo。

#### 複審後的 CI 端實測（run 33883980587）
push 後以 `gh workflow run update_sunday.yml` 觸發，**該次 CI 又被 YouTube 限流**（日期照樣抓不到），
正好在真實故障條件下驗到：

| 驗到什麼 | 證據 |
|---|---|
| 權限修正生效 | 「Set up job」的 `GITHUB_TOKEN Permissions` 區塊由原本的唯讀變成 **`Contents: write`** |
| 中英文比對走的是新路徑 | `cj9TAOIjbgU／Dv7X_mTSzHc 日期抓不到，但中英文表格皆已有，站上已是最新，不告警`（訊息文字是新版的） |
| 沒有 `ValueError`、沒有假警報 | 25 筆取得成功、`check_failed` 未觸發、執行 **success**、Telegram 無訊息 |

#### 尚未驗證（誠實記錄）
- **CI 真的 `git push` 成功這件事仍未驗過**。token 現在確實帶著 `Contents: write`（上表），
  但要驗到最後一哩，得剛好遇到「本機失敗 + CI 沒被限流 + 頻道上真的有新影片」三件事同時發生。
- 下次真的輪到補救層寫入時，這是第一個要看的地方。

---

## 本次修改記錄（2026-08-22）— 週四排程執行確認：排程正常，⚠️ 警告信查證為誤報

### 背景
使用者要求確認 2026-08-20（週四）的排程是否執行完成。本次**未修改任何程式碼**，只做查證與文件更新。

### 查證結果：兩層排程都正常，網站沒有漏更新
- **本機 launchd（主）準時完成**：commit `6fa86a0 feat: 自動更新 主日 2026.08.16「華麗變身 甚至忘了己身（帖撒」`，時間 2026-08-20 13:00:11 UTC＝台北 **21:00:11**，準點。
- **內容確實上站**（不是只有 commit）：`https://www.jesuswaytaipei.org/sunday.html` HTTP 200，表格最新一列為 **2026.08.16**。
- **GitHub Actions（補救層）依 2026-08-09 的錯開設定正常運作**：run #13 於 2026-08-21 02:24 UTC＝台北 10:24 觸發（排程為週五 01:00 UTC，GH 延遲約 1.4 小時，屬正常範圍），判定 `changed=false`，未重複 push。錯開設計如預期生效。

### ⚠️ 警告信是誤報（本次最重要的結論）
GitHub Actions 已連續 4 次（07-30、08-06、08-13、08-20 各週）寄出 ⚠️ 警告信，但**每一次網站其實都是最新的**。

run #13 log 顯示兩支候選影片的日期都抓不到：
```
[WARNING] 標題無日期，改用 yt-dlp 抓取：9IplXYflXjI
[WARNING] android client 失敗，改用預設 client 重試：9IplXYflXjI
[ERROR]   無法取得 9IplXYflXjI 的上傳日期（標題、upload_date、描述皆無法解析）
[ERROR]   無法取得 kAjSqxnf1JU 的上傳日期
[ERROR]   有候選影片但日期解析失敗，本次可能漏更新，請人工確認
```
繞過 yt-dlp、改用 YouTube oEmbed + watch page 直接查這兩支影片，證實兩支都早已收錄：

| 候選 ID | 標題 | 上傳日 | 站上狀態 |
|---|---|---|---|
| `9IplXYflXjI` | 華麗變身 甚至忘了己身（帖後 1:1-12）｜吳必然 牧師 | 2026-08-16 | 已在 `sunday.html`，即本機排程當晚寫入那筆 |
| `kAjSqxnf1JU` | 《樣青講堂》想戀愛又想做自己，真的可以嗎？｜Flora | **2026-05-24** | 已在 `youth.html`，就是最新那一列 |

**樣青講堂自 2026.05.24 後頻道上就沒有新影片**，表格停在 05.24 是正確的，不是被跳過。

**誤報成因：** `update_sunday.py` 用「日期解析失敗」當作漏更新的判斷依據，但在 CI 環境日期本來就常被 YouTube 限流而抓不到，於是無法區分「已是最新」與「真的漏了」，只要頻道上還有符合關鍵字的影片就會週週誤報。

### 已釐清的舊疑點：youth.html 沒有 2026.06.28 那列是正常的
`4820b3d` 曾寫入「樣青 2026.06.28」，但目前頁面上沒有該列——查證後確認是 `cb6589f remove: 2026.06.28 葉如凡場次影片已下架，移除樣青講堂列表項目` 刻意人工移除，非漏更新或被覆蓋。**日後再看到這個落差不必重查。**

### 查證方式（可重複執行，皆為唯讀）
```bash
# 1. 排程執行紀錄與逐步驟結果（公開 repo，免認證）
curl -s "https://api.github.com/repos/jesuswaytaipeisrv/jesuswaytaipei/actions/workflows/update_sunday.yml/runs?per_page=5"
curl -s "https://api.github.com/repos/jesuswaytaipeisrv/jesuswaytaipei/actions/runs/<run_id>/jobs"
# 關鍵：看 "Send date-fetch-failed warning email" 這步是 success 還是 skipped，
#      success 就代表當次寄了 ⚠️ 信；workflow 整體仍為綠色 success，看 conclusion 看不出來

# 2. 完整 log（需 PAT，取自 Keychain）
TOK=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill | sed -n 's/^password=//p')
curl -sL -H "Authorization: Bearer $TOK" \
  "https://api.github.com/repos/jesuswaytaipeisrv/jesuswaytaipei/actions/runs/<run_id>/logs" -o run.zip

# 3. 不靠 yt-dlp 查影片標題與上傳日（繞過 CI 限流，本機沒裝 yt-dlp 也能查）
curl -s "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=<vid>&format=json"
curl -s "https://www.youtube.com/watch?v=<vid>" | grep -oE '"uploadDate":"[^"]+"'

# 4. 判斷影片是否已收錄（不需要日期）
grep -c '<vid>' sunday.html en/sunday.html youth.html en/youth.html
```

### 待辦 / 觀察重點
- **【未做，待決定】改用 video_id 比對取代日期判斷來決定是否告警。** 候選影片的 ID 若已出現在表格的 `embed/<id>` 連結中即視為已收錄、不告警；完全不需要日期，天然繞開 YouTube 對 CI 的限流。已驗證可行性：`grep -c kAjSqxnf1JU youth.html` → 1、`grep -c 9IplXYflXjI sunday.html` → 1。改動範圍僅限 `update_sunday.py` 的告警判斷段（約 194–203、360–369 行），不動抓取與寫表邏輯。
  - 若要施作，驗收條件：(a) 候選 ID 已在表格中 → 不寄 ⚠️ 信；(b) 候選 ID 不在表格中 → 仍寄 ⚠️ 信。兩條路徑都要實測過才 commit。
- 在上述修法完成前，**收到 ⚠️ 信不要直接當成漏更新去補跑**，先用上面第 3、4 條指令確認候選影片是否已收錄。
- 本機無 `gh` CLI、亦未裝 `yt-dlp`（家用機），需要查排程一律走上面的 REST API 方式。

---

## 本次修改記錄（2026-08-09）— 08-06 漏更新排查、補推上線、git 併推與告警修復

### 事故：2026-08-06 週四批次，兩層排程同時失效

線上 `sunday.html` 停在 2026.07.26，缺 08.02「在我們中間的神國｜竹南清心教會 張紹軒 牧師」。查證後確認**兩層各自獨立地失敗**：

**第一層（本機 launchd）——內容做出來了，卡在 `git push`**

`logs/update_sunday.log` 顯示 8/6 21:00 排程準時執行、抓片與 Gemini 翻譯全部成功、中英版 HTML 都改好、commit `165db4d` 也建立了，但 push 被遠端拒絕：

```
! [rejected]  main -> main (fetch first)
subprocess.CalledProcessError: ... 'git', 'push' ... exit status 1
```

原因是**同一天在另一台電腦（`Gary Huang <garyhuang@Garydebijixingdiannao.local>`）推了 GA4 的三個 commit**（`50343f4`、`8c36284`、`d976aae`），本機 repo 從未 pull 過。舊的 `git_commit()` 是 `add → commit → push`，中間沒有 `pull --rebase`，**只要遠端被別台電腦動過就必爆**。且腳本內完全沒有告警機制（`grep smtp|mail|notify` 在 .py 內零命中，告警全寫在 workflow yml 裡），本機失敗只寫進沒人會看的 log 檔 → 完全靜默。

**第二層（GitHub Actions）——又被 YouTube 限流，且告警信寄到沒人看的信箱**

Actions run `31114567788` 標記 **success**，實際輸出「ℹ️ 無新內容，本週已是最新」，同時觸發了 2026-07-17 建立的 `date_fetch_failed` 警告信機制（信確實有寄出）。但**收件者是 `jesuswaytaipeisrv@gmail.com`，不是日常會看的信箱**，所以沒人注意到。根因仍是 YouTube 對 GH Actions 出口 IP 的間歇性限流，與 07-17 同一類問題。

**額外發現：所謂「雙備援」從未被驗證過**

本機 launchd 與 GH Actions 原本都排在週四 21:00。正常週永遠是本機先跑完並 push，Actions 跑起來看到已是最新就回報「無新內容」——**07-23、07-30 的綠燈 success 其實是「什麼都沒做」**，備援能力一次也沒被真正驗證過。8/6 這次兩邊剛好同時失效，缺口才暴露。

### 修復

**1. 補推 08.02 上線**

本機 `git pull --rebase` 併入 GA4 三個 commit，**無衝突**（GA4 只動 `<head>`，自動更新只動 `<tbody>`）。驗證中英版皆含 08.02、GA4 片段未被覆蓋後 push（`0be3232`）。

**2. `update_sunday.py`：`git_commit()` push 前先 `pull --rebase`**

衝突時自動 `rebase --abort` 並拋 `RuntimeError`，**不讓 repo 卡在 rebase 中影響下週排程**（這點很重要：若卡住，下週會以另一種方式再失敗一次）。

**3. `update_sunday.py`：本機失敗告警（Telegram）**

新增 `notify_failure()`，走 `~/.hermes/.env` 的 `TELEGRAM_BOT_TOKEN`／`TELEGRAM_HOME_CHANNEL`（僅單向讀 token 發訊息，**不涉及 Hermes agent 的任何授權，網站專案未納入 Hermes 管控範圍**）。`__main__` 包 try/except，任何未攔截例外都發告警並 `exit 1`；`date_fetch_failed` 在本機也改為發 Telegram（原本只寫 `$GITHUB_OUTPUT`，本機執行時那個變數根本不存在，等於沒作用）。另把兩處 `update_table` 失敗的靜默 `return` 改為 `raise`，讓它們也走得到告警。

**4. 排程錯開：GH Actions 改為週五 09:00（台北）**

`cron: '0 13 * * 4'` → `'0 1 * * 5'`。本機週四 21:00 為主，Actions 隔天早上才跑，本機失敗時它才真正有機會補上——這樣備援才是備援。

### 測試結果

- ✅ **`pull --rebase` 正常路徑**：scratchpad 建 bare repo + 兩個 clone，模擬「另一台電腦先推了 commit」（即 8/6 的真實情境）。舊版必爆的情況下，新版自動 rebase 後 push 成功，遠端兩邊 commit 都在。
- ✅ **rebase 衝突路徑**：兩邊改同一檔同一行，正確拋出 `RuntimeError`，且 `.git/rebase-merge`／`rebase-apply` 均不存在，**確認 abort 乾淨、不會卡到下週**。
- ✅ **Telegram 告警管道實測**：實際呼叫 `notify_failure()` 發出測試訊息，API 未拋錯、log 顯示「已發出 Telegram 失敗告警」，**用戶已確認實際收到訊息**，管道端對端可用。
- ✅ **端對端（launchd 實跑）**：`launchctl kickstart -k` 觸發 `com.jesusway.update-sunday-v2`，`last exit code = 0`，完整跑完並正確判定「主日 ph4CzZdSHAE 已在表格中，跳過 → 無更新，結束」，確認改動未破壞正常流程。
- ✅ **正式站已更新**：Pages 部署 `31289925701` success，`https://www.jesuswaytaipei.org/sunday.html` 最新一筆為 **2026.08.02**，`last-modified: Sun, 09 Aug 2026 02:14:58 GMT`。
- ✅ Python 語法檢查 `py_compile` 通過。
- ⚠️ **未執行：正式站的實際瀏覽器畫面／RWD 驗證**（用戶中止該步驟）。本次只新增一列表格資料、未動版面與 CSS，風險低，但依規則此項仍屬**未驗證**，不宣稱通過。
- ⚠️ **未驗證：修好的排程在真實排程時間自動跑一次**。下次真實驗證點見待辦。

### 待辦 / 觀察重點

- ~~確認 Telegram 是否收到測試告警~~ → **已確認收到（2026-08-09）**，`~/.hermes/.env` 的 `TELEGRAM_HOME_CHANNEL` 就是有效收件頻道，本機失敗不再靜默。
- **2026-08-13（週四）21:00** 觀察本機是否自動成功；**2026-08-14（週五）09:00** 觀察 GH Actions 補救層是否正確回報「無新內容」。這是排程錯開後的第一次真實驗證。
- YouTube 對 CI 限流屬間歇性問題，這次仍未根治（只是讓它不再是唯一防線）。若警告持續出現，再考慮加 retry 或改用 YouTube Data API。
- 多台電腦共用此 repo 的情況會持續發生，**在別台電腦改網站後，本機下次動手前先 `git pull`**，可減少 rebase 衝突機率。

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
- **決定不設「排除內部流量」（2026-08-06）**：對外 IP 反查為 `dynamic-ip.hinet.net`（中華電信浮動 IP），重撥即變、規則會默默失效且無告警；三台開發電腦分屬不同網路（公司為共用出口，設了會連同事一起排除），手機瀏覽也管不到。維護成本高於它能消除的雜訊。若日後真要處理，改用 Google 官方的 GA Opt-out 瀏覽器擴充（不依賴 IP，三台各裝一次），別走 IP 排除。

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
