# tests — 週四批次與心跳的回歸測試

```bash
bash tests/run_all.sh          # 全部（35 條，約 10 秒）
python3 tests/test_heartbeat.py   # 單跑一支
```

**任何一台電腦都能跑**：不需要網路、不需要 `yt-dlp`、不需要 `gh`、不會發任何 Telegram、
不碰真實 repo 的 git 狀態（每個情境用 `tempfile` 建獨立的臨時 git repo）。
路徑由測試檔自身推導（`Path(__file__).resolve().parents[1]`）——三台電腦的 repo 路徑各不相同，
寫死 `Path.home()` 在別台會 import 失敗。

Telegram 一律安全：token 在測試中置空，而 `load_env()` 用 `setdefault`，
置空就不會被 `~/.hermes/.env` 覆寫。

| 檔案 | 條數 | 涵蓋 |
|---|---|---|
| `test_heartbeat.py` | 27 | `CLAUDE.md`「自動更新心跳」節的 12 條驗收條件，加上 2026-09-26 code review 十項修正的回歸 |
| `test_git_commit.py` | 4 | `git_commit()` 的 `rebase.autoStash`、只在真的卡住時才 abort、autoStash × 真衝突不留 stash |
| `test_last_run_state.py` | 4 | 心跳的訊號來源 `logs/last_run.json`：欄位齊全、`SystemExit` 路徑也落盤、舊內容會被覆蓋 |

## 為什麼 stub 只降到 `git()` 這一層

`test_heartbeat.py` 假造的只有 HTTP（`online_page`）與 `send()`，**`git()` 才是 stub 的邊界**，
`remote_page()` 走真實程式碼路徑。

原本的寫法是把 `remote_page()` 整個換成假的，結果「`git fetch` 必須先於讀 `origin/main`」
這個順序永遠測不到——而那正是 2026-09-26 code review 找到的 high 級缺陷所在：
fetch 跑在比對之後，CI 補救層推的內容本機完全看不到，會把「CI 已補上」誤判成「沒推上去」。

**教訓：stub 放得太高，盲區就剛好落在「假資料與真實行為的差異」上。**
同理，英文頁的測資刻意用站上真實的雙語格式（`王馥蓓｜Chief Sustainability Advisor, Dentsu Group`），
因為原本用純英文假資料，撞不到「英文頁本來就有中文姓名」這個誤報來源。

## 這裡沒有涵蓋的（要人工或另外驗）

- **RWD 三寬度**（390／768／1280）：需要實際瀏覽器，見 `CLAUDE.md` 待辦。
- **真實 Telegram 是否抵達**：只能手動驗，且要人在手機上確認——
  `HEARTBEAT_TEST_ALERT=true python3 heartbeat.py`（送不出去會以非 0 結束）。
  API 回 200 只代表受理，不代表收到。
- **真的抓 YouTube 的端對端**：會撞限流、且家用機沒裝 `yt-dlp`，刻意不放進套件。
  要驗就在 repo 複本上跑（`WEBSITE_DIR=<複本> python3 update_sunday.py`，token 置空），
  做法與結果記在 `docs/DEVLOG.md` 2026-09-26。
- **CI 端的 `git push` 路徑**：至今從未真的跑過，見 `CLAUDE.md` 待辦。
