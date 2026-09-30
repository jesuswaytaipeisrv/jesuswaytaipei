"""驗收 heartbeat.py：12 條驗收條件（CLAUDE.md「自動更新心跳」節）+ code review 十項修正的回歸。

    python3 tests/test_heartbeat.py

不需要網路、不需要 yt-dlp、不會發任何 Telegram、不碰真實 repo 的 git 狀態。

設計要點（review 後改）：**stub 降到 git() 這一層**，不再假造 remote_page。
原本把 remote_page 整個換掉，導致「fetch 必須先於讀 origin/main」這個順序永遠測不到,
那正是 review 找到的 high 級缺陷所在。只有 HTTP（online_page）與 send 仍是假的。
"""
import json, os, sys, tempfile
from datetime import datetime, timedelta
from pathlib import Path

os.environ["TELEGRAM_BOT_TOKEN"] = "dummy"
os.environ["TELEGRAM_HOME_CHANNEL"] = "dummy"
# 路徑由測試檔自身推導。三台電腦的 repo 路徑各不相同（~/documents/website、
# ~/Documents/Claude/Projects/jesuswaytaipei 等），寫死 Path.home() 在別台會 import 失敗。
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
import heartbeat as hb  # noqa: E402

# ── 隔離正式 log ────────────────────────────────────────────────────
# 測試絕不能寫進 ~/Library/Logs/jesusway/heartbeat.log。2026-09-26 踩過：測試只覆寫了
# LAST_RUN_FILE 與 STATE_FILE，setup_logging() 照樣寫進正式 log，留下 596 行看起來像真警報
# 的紀錄（還寫著「Telegram 已送出」——那是 send stub 回 True）。心跳的價值就是那份 log 可信，
# 污染它等於把假警報搬進 log 裡。**必須在第一次呼叫 main() 之前覆寫**：
# logging.basicConfig 只有第一次會真的安裝 handler。
PROD_LOG = hb.LOG_FILE
_PROD_BEFORE = (PROD_LOG.exists(), PROD_LOG.stat().st_size if PROD_LOG.exists() else 0)
_TMP_LOG_DIR = Path(tempfile.mkdtemp())
hb.LOG_DIR = _TMP_LOG_DIR
hb.LOG_FILE = _TMP_LOG_DIR / "heartbeat.log"
hb.STATE_FILE = _TMP_LOG_DIR / "state.json"

THU = "2026-09-24T21:00:05"
NOW = datetime.fromisoformat("2026-09-26T10:07:00")
ROW = '<tbody class="x">\n<tr class="hover"><td>{d}</td><td>{t}</td><td>{g}</td></tr>\n</tr>'


def page(d, t="Life Is Meant to Be Amazing", g="Pastor Pijan Wu"):
    return ROW.format(d=d, t=t, g=g)


class R:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def harness(last_run, remote, online, state=None, ahead=0, send_ok=True,
            fetch_ok=True, diff_files=None):
    """回傳 (exit_code, 送出的訊息, git 呼叫順序, 最終 state)"""
    tmp = Path(tempfile.mkdtemp())
    hb.LAST_RUN_FILE = tmp / "last_run.json"
    hb.STATE_FILE = tmp / "state.json"
    if last_run is not None:
        hb.LAST_RUN_FILE.write_text(
            last_run if isinstance(last_run, str) else json.dumps(last_run), encoding="utf-8")
    if state:
        hb.STATE_FILE.write_text(json.dumps(state), encoding="utf-8")

    sent = []
    hb.send = lambda text: (sent.append(text), send_ok)[1]
    hb.online_page = lambda p: online.get(p)
    hb.datetime = type("D", (), {"now": staticmethod(lambda: NOW),
                                 "fromisoformat": staticmethod(datetime.fromisoformat),
                                 "combine": staticmethod(datetime.combine),
                                 "min": datetime.min})
    calls = []

    def fake_git(*args):
        calls.append(args)
        if args[0] == "fetch":
            return R(0) if fetch_ok else R(1, "", "ssh: Could not resolve hostname github-jesusway")
        if args[0] == "status":
            return R(0, f"## main...origin/main [ahead {ahead}]" if ahead else "## main...origin/main")
        if args[0] == "show":
            content = remote.get(args[1].split(":", 1)[1])
            return R(0, content) if content is not None else R(128, "", "fatal: path does not exist")
        if args[0] == "diff":
            return R(0, "\n".join(diff_files or []))
        return R(0)
    hb.git = fake_git

    code = 0
    try:
        hb.main()
    except SystemExit as e:
        code = e.code or 0
    try:
        final = json.loads(hb.STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        final = {}
    return code, sent, calls, final


results = []


def ok(name, cond, detail=""):
    results.append((name, bool(cond), detail))


GOOD_RUN = {"run_at": THU, "source": "local", "pushed": True, "exit": 0, "failure_reason": None,
            "en_fallback": {"主日": False},
            "candidates": {"主日": {"id": "RdE18JKoivM", "date": "2026.09.13"}}}
GOOD = {p: page("2026.09.13") for p in ("sunday.html", "en/sunday.html")}
STALE = {p: page("2026.09.06") for p in ("sunday.html", "en/sunday.html")}
RECENT = {"last_notified": (NOW - timedelta(days=3)).isoformat()}
OLD = {"last_notified": (NOW - timedelta(weeks=5)).isoformat()}

# ═══ 12 條驗收條件 ═════════════════════════════════════════════════
code, sent, _, _ = harness(None, GOOD, GOOD)
ok("1 沒觸發 → ⚠️ 明說沒有執行紀錄",
   code == 1 and len(sent) == 1 and sent[0].startswith("⚠️") and "沒有留下任何執行紀錄" in sent[0])

code, sent, _, _ = harness(dict(GOOD_RUN, run_at="2026-09-17T21:43:43"), GOOD, GOOD)
ok("1b 只有上週的紀錄 → ⚠️ 本週的排程沒有跑", code == 1 and "本週的排程沒有跑" in sent[0])

code, sent, _, _ = harness(GOOD_RUN, STALE, GOOD)
ok("2 沒推上去 → ⚠️ 列出候選與站上日期",
   code == 1 and "【沒推上去】" in sent[0] and "2026.09.06" in sent[0] and "2026.09.13" in sent[0])

code, sent, _, _ = harness(GOOD_RUN, GOOD, STALE)
ok("3 部署沒生效 → ⚠️ 指出是部署層", code == 1 and "【部署沒生效】" in sent[0] and "Pages" in sent[0])

code, sent, _, _ = harness(GOOD_RUN, GOOD, GOOD, state=dict(RECENT))
ok("5 沒新內容那週 → 收不到任何訊息", code == 0 and sent == [], f"發了 {len(sent)} 則")

code, sent, _, _ = harness(dict(GOOD_RUN, exit=1, pushed=False), GOOD, GOOD, state=dict(RECENT))
ok("6 交付層失敗但結果正確 → 🫀 低調通知",
   code == 0 and len(sent) == 1 and sent[0].startswith("🫀") and "本機排程那次是失敗收場" in sent[0])

code, sent, _, _ = harness(dict(GOOD_RUN, exit=1, failure_reason="樣青講堂取得日期失敗"),
                           GOOD, GOOD, state=dict(RECENT))
ok("6b 知識層失敗即使內容全對 → 仍 ⚠️ 不降級", code == 1 and sent[0].startswith("⚠️"))

code, sent, _, _ = harness(GOOD_RUN, GOOD, GOOD, state=dict(OLD))
ok("7 連續 4 週安靜 → 🫀 存活訊號（含本週最新內容）",
   code == 0 and len(sent) == 1 and "存活訊號" in sent[0] and "主日 2026.09.13" in sent[0])

code, sent, _, _ = harness("{ 壞掉的 JSON", GOOD, GOOD)
ok("8 JSON 看不懂 → ⚠️ 不靜音", code == 1 and "不是合法 JSON" in sent[0])

code, sent, _, _ = harness(dict(GOOD_RUN, run_at="不是時間"), GOOD, GOOD)
ok("8b run_at 看不懂 → ⚠️ 不靜音", code == 1 and "run_at 看不懂" in sent[0])

code, sent, _, _ = harness(dict(GOOD_RUN, candidates={}, failure_reason="yt-dlp 取不到頻道影片列表"),
                           GOOD, GOOD, state=dict(RECENT))
ok("12 知識層失敗（exit 0、候選空）→ ⚠️ 不靜音",
   code == 1 and "【本機那次沒能確認最新內容】" in sent[0] and "exit 0 正常收場" in sent[0])

code, sent, _, _ = harness(dict(GOOD_RUN, candidates={}, failure_reason=None), GOOD, GOOD,
                           state=dict(RECENT))
ok("12b 候選為空且無 failure_reason → ⚠️ 不靜音", code == 1 and "【候選為空】" in sent[0])

YOUTH_RUN = {"run_at": THU, "exit": 0, "pushed": True, "failure_reason": None, "en_fallback": {},
             "candidates": {"樣青": {"id": "B", "date": "2026.09.20"}}}
youth = {p: page("2026.09.20") for p in ("youth.html", "en/youth.html")}
code, sent, _, _ = harness(YOUTH_RUN, youth, youth, state=dict(RECENT))
ok("12c 那週只有樣青沒有主日 → 不誤報", code == 0 and sent == [])

code, sent, _, st = harness(GOOD_RUN, GOOD, GOOD, state=dict(OLD), send_ok=False)
ok("存活訊號送不出去 → last_notified 不更新",
   code == 0 and st.get("last_notified") == OLD["last_notified"])

code, sent, _, st = harness(None, GOOD, GOOD, state=dict(OLD), send_ok=False)
ok("異常告警送不出去 → last_notified 不更新",
   code == 1 and st.get("last_notified") == OLD["last_notified"])

# ═══ code review 十項的回歸 ════════════════════════════════════════
code, sent, calls, _ = harness(GOOD_RUN, GOOD, GOOD, state=dict(RECENT))
verbs = [c[0] for c in calls]
ok("R1 fetch 必須先於任何 origin/main 讀取（high）",
   "fetch" in verbs and "show" in verbs and verbs.index("fetch") < verbs.index("show"),
   f"git 順序：{verbs}")

code, sent, calls, _ = harness(GOOD_RUN, GOOD, GOOD, state=dict(RECENT), fetch_ok=False)
ok("R1b fetch 失敗 → ⚠️ 且不拿舊 ref 往下比對（high＋medium）",
   code == 1 and "【連不上遠端】" in sent[0] and "show" not in [c[0] for c in calls],
   f"訊息={sent[0][:50] if sent else '無'}／git={[c[0] for c in calls]}")

bilingual = {p: page("2026.09.20", "Not Useless, Just Stuck",
                     "王馥蓓｜Chief Sustainability Advisor, Dentsu Group")
             for p in ("youth.html", "en/youth.html")}
code, sent, _, _ = harness(dict(YOUTH_RUN, en_fallback={"樣青": False}),
                           bilingual, bilingual, state=dict(RECENT))
ok("R2 英文頁本來就有中文姓名（站上真實格式）→ 不誤報（high）",
   code == 0 and sent == [], f"發了 {len(sent)} 則：{sent[0][:70] if sent else ''}")

code, sent, _, _ = harness(dict(YOUTH_RUN, en_fallback={"樣青": True}),
                           bilingual, bilingual, state=dict(RECENT))
ok("R2b en_fallback 為 True → ⚠️ 指出該補譯哪一頁（high）",
   code == 1 and "【英文頁暫用中文】" in sent[0] and "en/youth.html" in sent[0],
   sent[0][:80] if sent else "沒發訊息")

code, sent, _, _ = harness(GOOD_RUN, GOOD, GOOD, state=dict(RECENT), ahead=1, diff_files=[])
ok("R4 ahead 但只動到文件 → 不誤報（medium）",
   code == 0 and sent == [], f"發了 {len(sent)} 則：{sent[0][:70] if sent else ''}")

code, sent, _, _ = harness(GOOD_RUN, GOOD, GOOD, state=dict(RECENT), ahead=2,
                           diff_files=["sunday.html", "en/sunday.html"])
ok("R4b ahead 且動到那四頁 → ⚠️ 列出是哪幾頁（medium）",
   code == 1 and "【commit 沒推出去】" in sent[0] and "sunday.html" in sent[0])

code, sent, _, _ = harness(dict(GOOD_RUN, candidates={},
                                failure_reason="無法取得 RdE18JKoivM 的上傳日期"),
                           GOOD, GOOD, state=dict(RECENT))
ok("R5 標籤中性、不謊稱抓不到頻道清單（medium）",
   code == 1 and "抓不到頻道清單】" not in sent[0] and "日期解析失敗" in sent[0],
   sent[0][:80] if sent else "沒發訊息")

code, sent, _, _ = harness(GOOD_RUN, GOOD, GOOD, state=None)
ok("R6 首次執行 → 說「第一次執行」，不謊稱過去 4 週都正常（low）",
   code == 0 and len(sent) == 1 and "第一次執行" in sent[0]
   and "過去 4 週的週四批次都正常" not in sent[0], sent[0][:70] if sent else "沒發訊息")

almost = {"last_notified": (NOW - timedelta(days=28) + timedelta(seconds=8)).isoformat()}
code, sent, _, _ = harness(GOOD_RUN, GOOD, GOOD, state=dict(almost))
ok("R6b 差幾秒不足 28 天 → 仍發存活訊號，不整整跳過一週（low）",
   code == 0 and len(sent) == 1 and "存活訊號" in sent[0], f"發了 {len(sent)} 則")

ok("R8 latest_thursday docstring 不再寫錯星期編號（low）",
   "週四＝3" in hb.latest_thursday.__doc__ and "週四＝2" not in hb.latest_thursday.__doc__,
   hb.latest_thursday.__doc__)
ok("R8b 週四/五/六/次週一都算到同一個週四",
   all(str(hb.latest_thursday(datetime.fromisoformat(d))) == "2026-09-24"
       for d in ("2026-09-24T21:00", "2026-09-25T09:00", "2026-09-26T10:07", "2026-09-28T09:00")))

src = (REPO / "heartbeat.py").read_text(encoding="utf-8")
banned = [w for w in ('"push"', '"commit"', '"rerun"', '"rebase"', '"add"', '"reset"') if w in src]
_, _, calls, _ = harness(GOOD_RUN, GOOD, GOOD, state=dict(RECENT), ahead=1, diff_files=[])
ok("11 純觀測（git 只用 fetch/status/show/diff）",
   not banned and {c[0] for c in calls} <= {"fetch", "status", "show", "diff"},
   f"可疑字串={banned or '無'} git={sorted({c[0] for c in calls})}")

# ── 守門：跑完整套測試不得動到正式 log ─────────────────────────────
_after = (PROD_LOG.exists(), PROD_LOG.stat().st_size if PROD_LOG.exists() else 0)
ok("G 跑測試不會寫進正式 log（~/Library/Logs/.../heartbeat.log）",
   _after == _PROD_BEFORE,
   f"測試前={_PROD_BEFORE} 測試後={_after} → 正式 log 被動到了，setup_logging() 又寫出去了")

print("\n===== 驗收 =====")
allok = True
for name, good, detail in results:
    print(f"{'✅' if good else '❌'} {name}")
    if detail and not good:
        print(f"      {detail}")
    allok &= good
print(f"\n共 {len(results)} 條 →", "全部通過" if allok else "有失敗")
sys.exit(0 if allok else 1)
