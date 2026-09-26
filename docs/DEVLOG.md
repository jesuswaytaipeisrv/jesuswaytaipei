# 台北樣教會網站 開發記錄（DEVLOG）

逐次修改記錄的完整內容。**由 `CLAUDE.md` 分流而來（2026-08-22）**——原本全部擠在 `CLAUDE.md`
裡，累積到 540 行、其中 84% 是這些逐次記錄，每次進專案都整份載入 context，稀釋掉真正的常設規則。

- **常設規則、技術棧、已知地雷** → 看 `CLAUDE.md`（該檔已濃縮，每次自動載入）
- **某次改了什麼、怎麼查出來的、當時的測試結果** → 看這裡（需要時才翻）
- 新增記錄請**加在最前面**，並在 `CLAUDE.md` 的「歷史修改記錄索引」補一行
- 早期幾段（2026-05／06）的先後順序原本就沒排整齊，分流時刻意維持原樣，未重排

---

## 本次修改記錄（2026-09-26，第五段）— RWD 三寬度實機驗證（家用機，09-26 待辦結案）

驗的是 09-26 動到的 `youth.html` 與 `en/youth.html` 最新一列（樣青 2026.09.20），直接開線上正式站。

**方法**：Playwright（MCP）`setViewportSize` 設精確 viewport，再以同源 iframe（`max-width:none`、寬度＝viewport）
量測 `innerWidth`、`documentElement.scrollWidth`、最新列各 `<td>` 的 computed `display`、「Watch →」按鈕右緣。
⚠️ 踩到一次：父頁 viewport 還是 390 時開 1280 的 iframe，iframe 會被夾成 390（量到 `innerWidth=390`），
那組數據作廢；改成「先把 viewport 設成目標寬度，再開同寬 iframe」才正確。**看 `innerWidth` 是否等於目標值再採信。**

| 頁面 | 寬度 | innerWidth | scrollWidth | 來賓欄 | Watch 右緣 | 導航 |
|---|---|---|---|---|---|---|
| en/youth | 390 | 390 | 390 | 隱藏 | 353 | 漢堡選單 |
| youth | 390 | 390 | 390 | 隱藏 | 353 | `mobile-menu-button` |
| en/youth | 768 | 768 | 768 | 顯示 | 723 | — |
| youth | 768 | 768 | 768 | 顯示 | 723 | — |
| en/youth | 1280 | 1280 | 1280 | 顯示 | 1227 | 桌面選單 |
| youth | 1280 | 1280 | 1280 | 顯示 | 1211 | 桌面選單 |

- 六組皆無水平捲動（scrollWidth＝viewport），按鈕都在畫面內；`hidden md:table-cell` 行為符合預期。
- 390px 英文長標題 *You're Not Useless — You're Just Stuck: Let VSAI Be Where You're Caught* 換成六行、
  列高 153px，截圖目視版面正常，未撐破表格。
- Console 只有既有的 Tailwind CDN 生產環境警告與 YouTube 內嵌 `compute-pressure` 權限政策訊息，與本次無關。
- 未涵蓋：只驗了 youth 兩頁（待辦指定範圍），其他頁未重驗；沒在實體手機上看。

---

## 本次修改記錄（2026-09-26，第四段）— 測試進版控（`tests/`，35 條，一個指令跑完）

先前三段的測試都寫在 session 的暫存區，關掉就沒了：程式與判準進了版控、**證據沒有**。
使用者 2026-09-26 指示整理進 `tests/`。

```
tests/
├── run_all.sh                 # bash tests/run_all.sh —— 全部 35 條，約 10 秒
├── README.md                  # 涵蓋範圍、為什麼 stub 只降到 git()、以及沒涵蓋的部分
├── test_heartbeat.py          # 27 條：12 條驗收條件 + code review 十項的回歸
├── test_git_commit.py         # 4 條：autoStash、只在真的卡住才 abort、autoStash × 真衝突
└── test_last_run_state.py     # 4 條：last_run.json 欄位齊全、SystemExit 也落盤、舊內容會被覆蓋
```

### 三台都能跑，不會有副作用
- **不需要網路、不需要 `yt-dlp`、不需要 `gh`**（家用機兩者都沒裝，這是刻意的前提）
- **不會發任何 Telegram**：token 在測試中置空，而 `load_env()` 用 `setdefault`，置空不會被 `~/.hermes/.env` 覆寫
- **不碰真實 repo 的 git 狀態**：每個情境用 `tempfile` 建獨立的 bare remote + 兩個 clone
- **路徑由測試檔自身推導**（`Path(__file__).resolve().parents[1]`）——三台的 repo 路徑各不相同
  （`~/documents/website`、`~/Documents/Claude/Projects/jesuswaytaipei`），寫死 `Path.home()` 在別台會 import 失敗

### 搬進來時順手補的一支：`test_last_run_state.py`
code review 第 10 項（`sys.exit(1)` 繞過 `write_last_run()`）當時是用一串手打的 bash 驗的，沒留下腳本。
現在寫成正式測試，並多釘兩條：JSON 欄位齊全（心跳的判準全靠那幾個欄位）、
**上一次的 `last_run.json` 一定要被覆蓋**——留著上週的內容會讓心跳誤判「本週沒跑」而看不出真正的故障。
這支不需要網路：`TEST_ALERT` 的自我檢查在 `fetch_latest_streams()` 之前就結束。

### 為什麼 `tests/README.md` 特別寫「stub 只降到 `git()` 這一層」
那是這幾輪最有價值的一個修正，而且是靠 code review 才發現的：
原本把 `remote_page()` 整個換成假的，「`git fetch` 必須先於讀 `origin/main`」就永遠測不到，
而那正是 high 級缺陷所在。同理英文頁測資改用站上真實的雙語格式
（`王馥蓓｜Chief Sustainability Advisor, Dentsu Group`），原本純英文的假資料撞不到那個誤報來源。
**stub 放得太高，盲區就剛好落在「假資料與真實行為的差異」上**——這句寫進 README，
下次改判準的人（或下一輪的我）才不會重蹈覆轍。

### 文件同步
- 專案 `CLAUDE.md`：驗收條件段落開頭加「改判準或改 `heartbeat.py` 之前先跑 `bash tests/run_all.sh`」；
  自動化節補測試指令
- `README.md`：自動化章節補測試指令與前提

### 測試結果
`bash tests/run_all.sh` → 三個套件、**35 條全部通過**（心跳 27、`git_commit()` 4、`last_run.json` 4）。

---

## 本次修改記錄（2026-09-26，第三段）— 本機 `/code-review` 十項發現全數修掉

Codex CLI 不在這台（`which codex`、homebrew bin、npm global、`~/.local/bin` 全查過），
所以先用本機 `/code-review`（high，範圍 `0499fd0..0444ba5`）補一輪獨立審查——
`heartbeat.py` 那三百多行原本只有我自己的測試把關。
四頁 HTML 的新增列經審查無問題（class 逐欄一致、中英日期與 video_id 一致、`MAX_ROWS` 滾動正確），
十項全在兩支 Python。**關鍵四項我逐一自己驗過才動手，不照單全收。**

### 兩項 high
| # | 問題 | 修法 |
|---|---|---|
| ① | **`git fetch` 跑在讀 `origin/main` 之後**：`git show origin/main:` 在 `check_content()`（先呼叫），唯一那次 fetch 在 `check_unpushed()`（後呼叫），所以讀的是上次 pull/push 留下的舊 ref。後果正好打掉「排在 CI 之後」的排程理由——CI 週五補上的 push 本機看不到，四頁全報【沒推上去】 | 抽出 `fetch_remote()` 放在所有比對之前，**且 fetch 失敗就停在那裡不往下比對**（拿舊 ref 比出來的結論是錯的，多報幾項只會誤導） |
| ② | **CJK 偵測會誤報，而權威值 `en_fallback` 寫進 JSON 卻沒用**。`en/youth.html` 現有列本來就有中文姓名，而且是刻意的雙語格式：`王馥蓓｜Chief Sustainability Advisor, Dentsu Group`、`黃名仕｜Founder & CEO, Open AI Fab`。只要某週最新那支樣青的來賓是這種寫法就假警報；反向也會漏（標題與講員剛好全拉丁字母時，真 fallback 也偵測不到） | 改讀 `run["en_fallback"][label]`，CJK regex 整個移除。**判準本身也錯了**，`CLAUDE.md` 的驗收條件 4 一併改寫，並把「英文頁刻意保留中文姓名」寫成已知地雷 |

### 三項 medium
- **③ `git fetch` 回傳碼沒檢查** → 週五沒網路或 ssh key 失效時靜默降級成「拿舊 ref 算出 ahead 0、結論沒有未推的 commit」。併入 ① 的 `fetch_remote()` 一起修。
- **④ 任何無關的未推 commit 都觸發 ⚠️** → 這 repo 三台輪流維護、`CLAUDE.md` 與 DEVLOG 常手動編輯，週五上午留著一個沒推的文件 commit 就會收到「09-24 重演」的錯誤訊息。改成先 `git diff --name-only origin/main..HEAD -- <那四頁>`，只有動到內容才算。
- **⑤ 【抓不到頻道清單】標籤混了兩種失敗** → `failure_reason` 有兩個來源（真的取不到清單／抓到清單但日期解析失敗，後者是 CI 常態）。改成中性標籤【本機那次沒能確認最新內容】並引原文，不把排查導到錯的層。

### 五項 low
⑥ 存活訊號用 `>= timedelta(weeks=4)` 比 wall clock，差幾秒就跳一整週 → 改用日數比並留一天寬容；且首次執行原本會發「過去 4 週都正常」這種當下沒有依據的話 → 改成明說「這是第一次執行，沒有先前的紀錄可比」。
⑦ 頂層 `except` 的 `send()` 在例外發生於 `load_env()` 之前時必定靜默 → `load_env()` 提到 `__main__` 的 try 最前面。
⑧ `latest_thursday()` docstring 寫「週四＝2」，實際 Python `weekday()` 週四＝3，程式對、註解錯 → 修正（那是整個窗口判定的基準，照註解改會位移一天）。
⑨ `RUN_STATE["en_fallback"]` 重複賦值（我兩次編輯各加一次，死碼）→ 刪掉後者。
⑩ `TEST_ALERT` 送不出去走 `sys.exit(1)`，`SystemExit` 不是 `Exception` → 兩個 `write_last_run()` 都跳過，`last_run.json` 留舊內容，下週心跳只會報「本週沒跑」而看不出真正壞的是告警管道 → 補 `except SystemExit` 落盤後 `raise`。

### 測試（全部重跑，共 31 條通過）
**測試架構本身也改了**：原本把 `remote_page()` 整個換成假的，所以「fetch 必須先於讀 `origin/main`」永遠測不到——
① 就藏在那個盲區裡。現在 **stub 降到 `git()` 這一層**，只有 HTTP 與 `send()` 還是假的，git 呼叫順序因此可觀察。
- 判準驗收 **27 條**（原 15 條 + review 回歸 12 條），含：fetch 先於 show 的順序、fetch 失敗不往下比對、
  **站上真實的雙語來賓格式不得誤報**、`en_fallback` 為 True 要指出補譯哪一頁、ahead 只動文件不誤報／動到四頁要報、
  標籤中性、首次執行措辭、28 天差幾秒的寬容、docstring 與程式一致、純觀測（git 只用 fetch/status/show/diff）
- `git_commit()` autoStash **3 條** + autoStash × 真衝突 **1 條**
- **⑩ 端對端**：在 repo 複本上 `TEST_ALERT=true` 且 token 置空實跑，確認 `last_run.json` 寫出且 `exit: 1`
- **真實環境冒煙兩次**（真 `git fetch`／`git show`／HTTP，token 置空不發訊）：
  真 repo（尚無 `last_run.json`）→ ⚠️ 正確；複本（有狀態、內容全對）→ exit 0，首次執行訊息措辭正確

### 我自己要認的
① 與 ② 都是**測試結構性看不到的**：判準測試把 `remote_page` 換成假的，所以 fetch 順序永遠不會被驗；
英文頁的假資料我寫的是純英文，所以撞不到站上真實的雙語姓名格式。端對端那次會過，
是因為我在跑之前手動 `git fetch` 過。**盲區剛好落在「stub 與真實資料的差異」上**——
這也是為什麼把 stub 降到 `git()` 層比多寫幾條測試更有價值。

---

## 本次修改記錄（2026-09-26，第二段）— 新增週五心跳：事後複查「使用者有沒有真的看到新內容」

### 為什麼做
09-24 那次排程準時跑完、內容全對、commit 也建了，卻因版控中的 `.DS_Store` 擋住 `pull --rebase`
而沒 push，網站兩天沒更新、log 看起來完全正常。09-17 段原本設想的心跳判準是「檢查當天 log
有沒有新段落」，那會把 09-24 判成成功。逼問流程跑完後改成以**結果**為判準。
判準與 11 條驗收條件寫在 `CLAUDE.md`「自動更新心跳」節（先寫條件、再寫程式）。

### 做了什麼
**1. `update_sunday.py` 每次執行寫 `logs/last_run.json`（機器可讀）**
`run_at`／`source`／`candidates{主日,樣青}`／`en_fallback`／`pushed`／`failure_reason`／`exit`。
成功與例外兩條路徑都寫（`write_last_run()` 在 `__main__` 的 try 與 except 各呼叫一次），
且**先落盤再發告警**——`notify_failure()` 本身在沒網路時也會失敗（09-17 實例），
那種情況心跳是唯一還會出聲的一層，不能讓它讀到上週的狀態。
判準不綁在 log 的中文措辭上：改一句文案就讓心跳靜默失效，是這個心跳唯一不能有的失效模式。

**2. 新增 `heartbeat.py`（進版控）＋ `com.jesusway.update-sunday-heartbeat` plist（只裝龍蝦）**
週五 10:07。四項判準各對應一次真實事故：當天沒有執行紀錄（09-10、07-17）／候選日期與
`origin/main` 不一致（09-24）／推上去了但線上還是舊的（Pages 間歇逾時）／線上英文頁最新列
是中文（Gemini 503 靜默 fallback）。另查本機有沒有 ahead。
異常才出聲；正常安靜；連續 4 週安靜發一則存活訊號；`exit≠0` 但內容正確時發**非 ⚠️** 的低調
通知（避免重演「綠燈說謊」——主層壞掉、整條鏈路悄悄只剩 CI 在撐）。**純觀測，不 push、不 re-run。**

### 測試
**判準（13 個情境，攔截 `send()`／`git()`／HTTP，不發訊息、不碰真實 repo）**：
沒觸發、只有上週紀錄、沒推上去、部署沒生效、英文頁是中文、沒新內容那週靜音、
本機層失敗但結果正確、連續 4 週安靜、JSON 壞掉、`run_at` 看不懂、本機 ahead、
測試入口送不出去要非 0 結束、純觀測（靜態檢查無 `push`/`commit`/`rerun`，實跑時 git 只用到
`fetch`/`status`/`show`）——**全部通過**，逐條對應 `CLAUDE.md` 的 11 條驗收條件。

**端對端（真實資料）**
- 把 repo `git clone` 到暫存區、`WEBSITE_DIR` 指向複本、Telegram token 置空（`load_env()` 用
  `setdefault`，所以置空不會被 `.env` 覆寫，確保不誤發訊息），實跑 `update_sunday.py`：
  正確抓到 `RdE18JKoivM`(09.13)／`fcmrvY8uMQc`(09.20)、兩支都判「已在表格中，跳過」、
  `last_run.json` 內容正確（candidates 兩筆、`exit: 0`、`pushed: false`）
- 實跑 `heartbeat.py`（真的 `git show origin/main:`、真的 HTTP 抓線上四頁）：四頁日期全對、
  英文頁無中文、無 ahead → 判定正常，因 state 空（首次執行）發存活訊號，exit 0
- **launchd spawn 驗證**：用臨時 plist（`TELEGRAM_BOT_TOKEN` 置空）`kickstart`，
  `runs = 1`、`last exit code = 1`、log 正確寫到 `~/Library/Logs/jesusway/`、
  正確判出「讀不到 `last_run.json`」（真實 repo 尚未用新版跑過）、Telegram 如預期沒送出。
  驗完已 `bootout` 並刪除臨時 plist。這一步是為了避開 07-17 那種「plist 設定看起來對、
  launchd 卻連 spawn 都失敗」的坑
- 正式 plist：`plutil -lint` OK、已 `bootstrap`，`launchctl print` 確認觸發器
  `Weekday 5 / Hour 10 / Minute 7` 已註冊

### ⚠️ 尚未驗證
**真實 Telegram 管道沒有實發過**。測試全程刻意把 token 置空以免誤發訊息到使用者手機，
所以「訊息真的會抵達」這件事只驗到程式路徑、沒驗到管道。
補驗方式（一行，會真的發一則標明「測試訊息」的訊息）：
```
HEARTBEAT_TEST_ALERT=true /opt/homebrew/bin/python3 ~/documents/website/heartbeat.py
```

### 實作當天就踩到並修掉的一個缺陷
`launchctl kickstart` 那次驗證留下的 `heartbeat_state.json` 露出問題：當時 Telegram 因 token 置空
**根本沒送出去，程式卻照樣把 `last_notified` 蓋上時間戳**。照原本的寫法，哪天管道真的壞了、
存活訊號送失敗，時間戳仍會更新 → 沉默上限判斷會以為「剛通知過」→ 繼續安靜四週。
那正是這個設計唯一不允許的失效模式（自己壞掉卻安靜），而且會在最需要它出聲的時候發生。

**修法**：三個發訊分支（⚠️ 異常、🫀 低調通知、🫀 存活訊號）都改成**只有 `send()` 回 True 才記
時間戳**，送失敗時明確寫 log「時間戳不更新，下次會重試」。補了兩條測試釘住：
「存活訊號送不出去 → `last_notified` 維持原值」「異常告警送不出去 → 同樣不更新」。
測試總數 13 → 16，全通過。

驗證用的假 state 檔已刪除，首次正式執行會從乾淨狀態開始。

### 真實 Telegram 管道（已補驗）
`HEARTBEAT_TEST_ALERT=true` 實跑一次，Telegram 回 200、exit 0、log 記「Telegram 已送出」。
**使用者當場確認手機收到**，所以這條是端到端驗完的，不只是 API 回 200。
（刻意分開記：200 只代表受理，送出與收到是兩件事——這個專案 09-13 那次就更正過一次
「以為告警沒被看到」的記載。以後再驗這個管道，同樣要拿到使用者的確認才算通。）

### 09-26 當天第二個缺陷：fetch 失敗那週心跳完全靜音（已修）
使用者要我說明「心跳只看最新一列」的盲區，查的過程順手驗出一個**比盲區更嚴重的實作缺陷**。

**形狀**（就是 09-17 那一晚）：`fetch_latest_streams()` 抓不到頻道清單時，主 job **不 raise** ——
它寫 `failure_reason`、發告警，然後一路走到「`=== 無更新，結束 ===`」正常收場，`exit` 是 **0**。
心跳原本用 `exit != 0` 判斷本機層失敗，候選又是空的（`check_content` 迴圈跑 0 圈）→
判定「本週一切正常，保持安靜」。實測確認：exit 0、0 則訊息。

而 09-17 那晚 `notify_failure()` 自己也因為沒網路發不出去——**兩層都不會出聲**，
正是這個心跳存在的理由，卻剛好漏掉那一種。

**修法**：`failure_reason` 有值、或候選為空 → 一律 ⚠️。沒有改主 job 的 exit code：
CI 端已用 `check_failed` 讓 workflow 紅燈，動 exit code 會連帶影響 workflow 判斷，風險大於收益。

**順帶釘出一個原本沒想清楚的分界**（改完測試 6 掛了才發現，是 fixture 不對而非判斷不對）：
| | 定義 | 處置 |
|---|---|---|
| **知識層失敗** | `failure_reason` 有值＝不知道最新是哪一支 | **一律 ⚠️**，即使可查的頁面剛好都對、即使 exit 0 |
| **交付層失敗** | 候選完整、`failure_reason` 為 None，但 `exit≠0` 或沒推出去（09-24 形狀） | 可查內容都正確 → **非 ⚠️** 低調通知（CI 補上了） |

測試 6 原本的 fixture 把 `failure_reason` 和「內容全對」放在一起，混了這兩件事；
已改成 09-24 的真實形狀（候選完整、`failure_reason=None`、`exit=1`），
並補 6b 釘住「知識層失敗不得因為可查內容剛好都對而降級」。
另補 13c：那一週頻道上只有樣青沒有主日時不誤報（候選是唯一真相，不猜）。
**測試 16 → 20，全通過。**

### 心跳的已知邊界：看不到表格中間的洞（未處理，交給 Codex 架構層評）
心跳問的問題是「頻道最新那一支有沒有在站上第一列」，所以**看不到中間缺一支**。
路徑：某週漏了 → ⚠️ 發了 → **但告警沒被處理** → 下一週更新的影片上站、第一列變成新的 →
候選與第一列相符 → 心跳從此靜音，那個洞再沒有任何機制提起。
09-11→09-13 真的這樣走過一次（告警有發、使用者有看到、還沒空處理，09-06 就變成非最新那支）。
`MAX_ROWS=10` 的滾動刪除會讓洞約十週後被滾出表格，缺失自然「過期」，但中間那段期間沒人知道。
這是「單週判定、無累積狀態」的必然結果，不是 bug。要解得靠累積狀態或比對整張表 vs 頻道近十支
（每週多打十次 yt-dlp、會撞限流），兩種都不便宜，列入 Codex 待辦第 3 題。

**實測也更正了一件我先前寫錯的事**：「同一週主日與樣青都漏」**不是**盲區——
候選是逐筆檢查的，四項（兩類 × 中英兩頁）會各自報出來。Codex 待辦的原描述已更正。

### 首次正式運作的時序
10-01（四）21:00 主 job 跑 → 寫 `last_run.json`（這會是 `rebase.autoStash` 的第一次實戰）；
10-02（五）10:07 心跳第一次正式執行。若 10-01 沒跑成，10-02 的 ⚠️ 就是它第一次真正發揮作用。
注意首次執行因 state 為空必定會發一則存活訊號，那是預期行為（等於安裝日順便驗一次管道）。

---

## 本次修改記錄（2026-09-26）— 09-24 排程的兩個尾巴收掉：.DS_Store 擋住 rebase、英文翻譯 503

### 09-24（四）那次的實際結果：內容全對，卡在 push 前一步
排程**準時觸發**（`21:00:05 === update_sunday.py 開始 ===`，`runs = 1`），
兩支影片都抓到、四個頁面都寫入、commit `5a8d7b8` 也建了，但：

```
[INFO] git pull --rebase：併入遠端變更
fatal: no rebase in progress
[ERROR] 執行失敗
RuntimeError: git pull --rebase 失敗，已 abort，需人工處理：
  error: cannot pull with rebase: You have unstaged changes.
```

`last exit code = 1`，**push 沒做，網站到 09-26 為止都還是舊的**。
這次 `notify_failure()` 的 Telegram **有正常發出**（與 09-17 的靜默失敗不同）。

**阻斷點是 `.DS_Store`**：它被納入版控（`.DS_Store` 與 `assets/.DS_Store` 兩個），
Finder 動過資料夾就會產生未暫存修改，而 `git pull --rebase` 遇到髒工作樹會整批拒絕。
這個檔案在 09-24 上午的稽核中就看到是 ` M .DS_Store`，當時被判斷成「整潔問題、留給使用者決定」，
**低估了它是自動 push 的實際阻斷點**。

第二個問題：樣青英文翻譯那次 Gemini 回 `503 UNAVAILABLE（This model is currently experiencing high demand）`，
腳本 fallback 成中文並留下 `[WARNING] 樣青英文版暫用中文，請 push 前手動確認`。

### CI 補救層（09-25 五 09:00）也補不上
run `36100831088` 紅燈，原因是老問題：YouTube 對 CI 共用 IP 限流，
`RdE18JKoivM` 與 `fcmrvY8uMQc` 兩支都「標題、upload_date、描述皆無法解析」，
於是判為「可能漏更新」→ 正確亮紅燈並發 Telegram。**這是設計行為，不是新 bug**；
CI 端至今仍沒有真正寫入過內容（`git push` 路徑依舊未驗）。

### 本次做了什麼
| # | 動作 | commit |
|---|---|---|
| 1 | `.DS_Store` 丟棄未暫存修改、兩個檔案 `git rm --cached` 移出版控、`.gitignore` 加 `.DS_Store` | `af1c5e3` |
| 2 | `en/youth.html` 人工補上英文題目與來賓（取代 fallback 的中文） | `af1c5e3` |
| 3 | `git_commit()` 的 `pull --rebase` 加 `-c rebase.autoStash=true`；`rebase --abort` 改為只在 `rebase_in_progress()` 為真時才呼叫 | `9c3edf8` |

英文補譯內容：
- 題目 *You’re Not Useless — You’re Just Stuck: Let VSAI Be Where You’re Caught*
- 來賓 *Thinking Mentor, Boya College, Tunghai University, Hsu Heng-chia*

### 測試
**`git_commit()` 用臨時 git repo 跑三個情境（bare remote + local/other 兩個 clone，未動真實 repo）**，
測試腳本放在 session 暫存區，未進 repo。`WEBSITE_DIR` 環境變數可覆寫，所以能直接對臨時 repo 呼叫函式本體：

| 情境 | 期望 | 結果 |
|---|---|---|
| 髒工作樹（已追蹤檔案有未提交修改）＋遠端被別台推過 | autoStash 生效、push 成功、雜項原樣還原、別台 commit 併入 | ✅ 三項都成立 |
| 同一行真衝突 | 拋 `RuntimeError`、abort 生效、repo 不卡在 rebase 中 | ✅ |
| 遠端不存在（rebase 未開始就失敗） | 錯誤訊息不含誤導的 `no rebase in progress`，且不嘗試 abort | ✅ |

**內容驗證**
- 四頁表格各 10 列（`MAX_ROWS` 滾動正常），最新列：`sunday.html`／`en/sunday.html` = 2026.09.13，`youth.html`／`en/youth.html` = 2026.09.20
- 兩支影片 ID 各只出現在對應的兩頁，各 1 次
- Pages 部署兩次都綠燈（`36211624780`、`36211711137`）
- **線上四頁實查**（部署後）：
  - `sunday.html` 最新 2026.09.13「人生本該精彩 就看你行不行？」吳必然 牧師
  - `en/sunday.html` 最新 2026.09.13 *Life Is Meant to Be Amazing: Will You Make It Happen?* / Pastor Pijan Wu
  - `youth.html` 最新 2026.09.20「不是你太廢，是狀態卡住了！」許恆嘉
  - `en/youth.html` 最新 2026.09.20 *You’re Not Useless — You’re Just Stuck…* / Hsu Heng-chia

### ⚠️ 沒驗到的部分
**RWD 三寬度（390／768／1280）沒有用實際瀏覽器驗**——Claude 的 Chrome 擴充當下未連線。
替代檢查：新增列的 `<tr>`／`<td>` class 與既有列**逐欄完全一致**（來賓欄同樣是 `hidden md:table-cell`），
表格結構與 CSS 皆未變動，唯一變數是英文標題字串較長（只影響該格換行行數，不影響版面結構）。
要補驗的話，把擴充連上後看 `youth.html` 與 `en/youth.html` 這兩頁即可。

### 仍未處理
- 本機層心跳（09-17 段提的「週四 21:30 檢查當天有沒有 log」）**仍未施作**。這次證明了「準時觸發」不是唯一風險，
  「跑完卻沒 push」也會發生，心跳若只檢查 log 有沒有新段落，這次會誤判為正常——真要做得檢查 `git status -sb` 的 ahead。
- CI 端 `git push` 路徑仍未實際跑過。

---

## 本次修改記錄（2026-09-24）— 全機排程稽核：09-17 失敗歸因、站上目前缺兩支（純文件，未改程式）

### 背景
使用者要求確認**本機所有排程**有無異常（不限本專案）。九支 launchd＋三支 hermes cron 逐一查過，
只有這支 `com.jesusway.update-sunday-v2` 有異常。**本次只讀 log、唯讀查 YouTube，沒有改任何程式、plist 或網站內容。**

### 09-17（四）那次：有跑，但落在系統大版本更新的空窗期，失敗且告警也送不出去
| 證據 | 內容 |
|---|---|
| `~/Library/Logs/jesusway/update_sunday_launchd.log` | `2026-09-17 21:43:43 === update_sunday.py 開始 ===`——排程是 21:00，**遲了 43 分鐘**才觸發 |
| 同一段 | `yt-dlp flat-playlist 失敗：Failed to resolve 'www.youtube.com' ([Errno 8] nodename nor servname provided)`，結尾寫「無更新，結束」 |
| 同一段 | `發送 Telegram 告警失敗：<urlopen error [Errno 51] Network is unreachable>`——**這次連告警都沒發出去，是真正的靜默失敗** |
| `system_profiler SPInstallHistoryDataType` | **macOS 27.0 安裝時間 2026/9/17 晚上 10:24** |
| `pmset -g log` | 電源管理紀錄**最早一筆就是 2026-09-17**（更新時被重置）；22:24 起出現 `loginwindow` 的 `minibuddysleepassert` 與 `Setup Assistant`（PID 1134），確認那晚跑過系統更新後的首次啟動流程 |

**歸因**：09-17 是 macOS 26.6.2 → 27.0 大版本更新當晚。43 分鐘的延遲觸發、一開跑就 DNS 解析不到 YouTube、
連 Telegram 都送不出，三者都吻合「更新／重啟前後的網路空窗」。
⚠️ **這是時間吻合，不是因果證明**——21:00～21:43 之間的 launchd 逐筆紀錄已過 unified log 保留期，查不到了。

### 順帶回頭看 09-10（補充 09-17 那段查不到的部分）
`Command Line Tools for Xcode 27.0` 的安裝時間是 **2026/9/10 晚上 8:38**，就落在 09-17 段記的
「21:00 沒觸發、21:19 人工重開機」之前 22 分鐘。**兩次失效都緊貼系統更新作業**，
這比 09-17 段當時只能寫的「系統處於準備重開的異常狀態」具體一些，但同樣只有時間相關性，不能證因果。

### 站上目前缺什麼（2026-09-24 上午唯讀查證）
| 項目 | 影片 ID / 標題 | yt-dlp 日期 | 站上狀態 |
|---|---|---|---|
| 主日 | `RdE18JKoivM`「人生本該精彩 就看你行不行？」吳必然 牧師 | upload=release=**20260913** | 中英 `sunday.html` **皆無 → 漏** |
| 樣青 | `fcmrvY8uMQc`「不是你太廢，是狀態卡住了！…許恆嘉」 | upload=release=**20260920** | 中英 `youth.html` **皆無 → 漏** |
| 09.20 主日 | — | 頻道上 09.13 之後沒有主日直播 | **不是漏**，那週只有樣青 |
| 08.30 主日 | — | 頻道上 09.06 往下一支主日就是 08.23 | **不是漏**（與 09-13 段的結論一致；`youth.html` 裡的 2026.08.30 是樣青那支，兩者極易混淆） |

- 線上實查 `https://www.jesuswaytaipei.org/sunday.html`，最新五筆＝09.06／08.23／08.16／08.09／08.02，與 repo 內容一致。
- 本機與 `origin/main` 同為 `2b9ce69`，沒有未推的 commit——所以不是「補了但沒推」。

### ⚠️ 09-13 留的 `RdE18JKoivM` 日期問題：已驗證，`fetch_date()` 不必改（本條結案）
09-13 記的是 `upload_date=20260911`／`release_date=20260913`，擔心 upload 優先會把它寫成 2026.09.11（週五）。
**2026-09-24 實測：`upload_date` 已變成 20260913，與 release 相同**——預排直播開播後，YouTube 會把 upload_date
改成實際開播日。現有「upload 優先」的邏輯這次不會寫錯日期，維持原樣。

### 今晚（09-24 四）21:00 應可自動補上兩支，不需人工插列
09-13 記的「候選只取最新一支、漏的不是最新一支就得手動插」**這次沒有踩到**：
- 09-20 那週沒有主日直播 → `RdE18JKoivM`（09.13）**仍然是頻道上最新一支主日**
- 樣青最新就是 `fcmrvY8uMQc`（09.20）
- 兩支 ID 在中英四頁皆不存在，而判斷依據是 `video_id in html`（`update_sunday.py:361`）

→ 今晚會各自寫入中英兩頁並自動 push。**前提是 21:00 當下機器醒著且網路通。**

### 本機電源設定（供下次排查參考，本次未變更）
- `pmset -g custom`：AC `sleep 0`（不睡）、**電池 `sleep 1`**
- `pmset -g sched`：**空的，沒有任何排定喚醒**

週四 21:00 若沒插電源，這支排程就得等人喚醒才補跑，而補跑當下網路往往還沒接回來——09-17 就是這個樣態。
注意這**不等於**推翻 07-17「睡眠說是誤判」的結論：07-17 與 09-10 兩次都查證過機器是醒著的，
電源設定只解釋得了 09-17 這種「延遲觸發＋一開跑就沒網路」的形態。

### 待驗收（今晚 21:05，已排 Claude 一次性排程；session 關掉就不會觸發，屆時可改人工查）
1. launchd log 有無 `2026-09-24 21:0x === update_sunday.py 開始 ===`；若最後一筆仍是 09-17，就是**第二次「設定正確卻沒觸發」**
2. 結尾是「完成，已自動 push」還是 ERROR
3. `launchctl print gui/501/com.jesusway.update-sunday-v2` 的 `runs` 與 `last exit code`
4. repo 有無今晚的 feat commit，且已與 `origin/main` 同步
5. **關鍵**：`RdE18JKoivM` 要出現在 `sunday.html` 與 `en/sunday.html`；`fcmrvY8uMQc` 要出現在 `youth.html` 與 `en/youth.html`（中英同步規則）
6. 順帶看 `~/.hermes/logs/podcast.log`，21:15 的 podcast 排程有沒有接手 09.20 那集樣青

### 本次沒做的事
- **沒有手動補那兩支**——今晚排程應可自動補，人工先插會與自動寫入打架
- 沒有改任何程式、plist 或電源設定；沒有加本機層心跳（09-17 段提的對策仍未施作）

---

## 本次修改記錄（2026-09-17）— 09-10 本機層漏更新：龍蝦側 log 補查（純文件，未改程式）

### 背景
09-13 那筆寫「本機為什麼沒推：這台查不到」，要到裝 launchd 的那台（龍蝦）看。本次在龍蝦補查，**只讀 log，沒有改任何程式或網站內容**。

### 查到什麼
| 證據 | 內容 |
|---|---|
| `~/Library/Logs/jesusway/update_sunday_launchd.log` | 最後一筆是 **09-03 21:00** 那次（成功 push `e411787`）；**09-10 21:00 沒有任何一行**——不是跑了失敗，是 launchd 根本沒起這支 job |
| `logs/update_sunday.log`（腳本自己的 log） | 最後一筆 09-04 22:28 手動測試「無更新」；09-10 同樣一行都沒有 |
| `last reboot shutdown` | **09-10 21:19 shutdown、同分鐘 reboot**——是正常關機重開，不是當機 |
| `uptime`（09-16 查） | up 6 天，與 21:19 開機吻合；`~/.hermes/gateway-starts.log` 21:21 gateway 重啟也吻合 |
| `launchctl print` | job 目前已載入、`Weekday 4 / Hour 21 / Minute 0` 正確、`last exit code = (never exited)`＝開機後尚未觸發過（下次 09-17 21:00） |
| plist 修改時間 | 07-17，09-10 前後沒人動過 |
| 同時段機器狀態 | 20:51～21:04 龍蝦正在跑 Hermes worker 的中斷測試（`~/hermes-agent/CLAUDE.md` 2026-09-10 節），機器是醒著的 |
| macOS unified log | 09-10 的 launchd 紀錄已輪替掉，查不到 launchd 為何沒觸發 |

### 結論
本機層 09-10 **沒有執行**，且發生在一次人工重開機（21:19）前 19 分鐘。機器 21:00 當下醒著、job 設定正確，
為何 launchd 沒觸發，現有 log 已不足以斷定（unified log 已過保留期）。可能性只能列、不能證：
21:00 前後系統已處於準備重開的異常狀態，或 launchd 的 calendar 觸發在那段時間被跳過。
**這是本機層第一次「機器醒著、設定正確、卻沒起 job」**，與先前三種失敗模式（launchd spawn／TCC、yt-dlp 限流、push 被擋）都不同。

### 對策（未施作，供下次決定）
- 09-17（四）21:00 這次要盯：跑完看 `update_sunday_launchd.log` 有沒有新的一段，順便驗 09-13 記的 `RdE18JKoivM` 日期問題。
- 若再發生「醒著卻沒觸發」，考慮在 `com.jesusway.update-sunday-v2` 之外加一個「週四 21:30 檢查 launchd log 有沒有當天紀錄」的心跳，
  和 CI 補救層一樣走 Telegram；但 CI 週五那層本來就是為這種情況設的，這次它有正確亮紅燈，只是限流拿不到日期而補不上——
  真正的缺口在 09-13 記的「候選只取第一支」，不在本機層。

---

## 本次修改記錄（2026-09-13）— 09-06 主日漏更新排查與手動補上

### 背景
使用者回報「上週網站更新失敗」。查證結論：**09-06 主日信息 `WqxohQJV9ao`（能改變腦子，不是「聽」，而是「行」）確實漏了**，
本機 launchd（09-10 四）與 CI 補救層（09-11 五）兩層都沒寫進去。這是告警改走 Telegram 後第一次**真的**漏更新，
不是誤報。樣青講堂沒漏（頻道上最新仍是 08-30 那支，站上已有）；08-30 沒有主日直播，不是漏。

### 查證證據（在家用機做，唯讀 REST API＋本機 yt-dlp）
| 環節 | 結果 |
|---|---|
| 09-04 之後的 commit | 只有文件 commit，沒有任何「自動更新 主日」commit → 本機 09-10 那次沒推 |
| CI 09-11 排程 run `34567024225` | **紅燈**（新機制正確運作）：取得 25 筆、候選 `WqxohQJV9ao` 抓不到日期、且不在 sunday 中英文表格 → Telegram 已發、`exit 1` |
| 09-13 手動 `workflow_dispatch` run `34742412846` | 仍紅燈，同樣限流；但候選已變成 **`RdE18JKoivM`（09-13 當天直播中）**，09-06 那支已被擠到第二筆 |
| 本機 yt-dlp（家用網路） | `WqxohQJV9ao` upload=release=20260906 was_live，日期正常拿得到；CI 環境就是拿不到 |

### 為什麼不能等週四自動補
腳本只取頻道清單裡**第一支**符合「主日」的影片當候選。09-13 開播後第一支已是 `RdE18JKoivM`，
09-06 那支永遠不會再被當候選 → 不手動補就永久缺頁。這是 `fetch_latest_streams()` 的既有設計限制（一週只補一支）。

### 本機為什麼沒推：這台查不到
家用機沒有 launchd job、沒有 `logs/update_sunday.log`、沒有 `~/.hermes/.env`。要看本機那層的失敗原因，
得到裝 launchd 的那台看 `~/Library/Logs/jesusway/update_sunday_launchd.log` 與 `logs/update_sunday.log`（09-10 21:00 那段）。
**Telegram 那則 09-11 05:43（UTC）的告警有發出去、使用者也有看到**（09-13 確認），只是還沒空處理——告警管道本身沒問題，不必查。

### 補上方式
不用 Gemini 翻譯（家用機沒有 key），直接 `import update_sunday` 呼叫 `parse_sunday_title_speaker()` → `build_row()` → `sync_video_row()`，
英文標題人工翻：*What Changes the Mind Is Not "Hearing" but "Doing"* ／ Pastor Pijan Wu。
中英文各插一列、各滾掉最舊的 2026.06.14（維持 10 列）。commit 後 push，Pages 部署驗證見下。

### 測試
- `grep -c WqxohQJV9ao sunday.html en/sunday.html` 各 1；`<tr class="hover` 各 10 列
- diff 只動 `<tbody>` 內兩列（新增 09.06、移除 06.14），`<head>` 的 GA 片段未動
- 正式站驗證：push 後看 Pages deploy 與 `https://www.jesuswaytaipei.org/sunday.html` 是否出現 2026.09.06

### ⚠️ 下週要盯的點（未施作）
`RdE18JKoivM` 是預先排定的直播：yt-dlp 回 `upload_date=20260911`、`release_date=20260913`。
腳本 `fetch_date()` 用 `%(upload_date,release_date)s`，**upload_date 優先** → 09-17 週四自動更新可能把它寫成 `2026.09.11`（週五）。
過去幾支 was_live 的 upload 與 release 都相同所以沒踩到；這支開播後 upload_date 會不會被 YouTube 改成 09-13 未知，
週四跑完要檢查日期，錯了就手動改；若常態如此，改成 `release_date` 優先。

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
