"""驗收 update_sunday.py 寫給心跳的 logs/last_run.json。

    python3 tests/test_last_run_state.py

在 repo 複本上以子行程實跑腳本，**不碰真實 repo**。不需要網路也不需要 yt-dlp：
`TEST_ALERT` 的自我檢查在 `fetch_latest_streams()` 之前就結束，走不到抓 YouTube 那一步。
Telegram token 一律置空——`load_env()` 用 `setdefault`，置空就不會被 ~/.hermes/.env 覆寫，
所以測試絕不會發訊息出去。

為什麼要測這個：心跳的判準完全建立在這份 JSON 上。它沒寫、或寫成上一次的內容，
心跳就會報「本週的排程沒有跑」，看不出真正壞掉的是什麼（2026-09-26 code review 第 10 項）。
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]     # 路徑由測試檔自身推導
results = []


def ok(name, cond, detail=""):
    results.append((name, bool(cond), detail))


def sh(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def clone():
    tmp = Path(tempfile.mkdtemp())
    site = tmp / "website"
    sh("git", "clone", "-q", str(REPO), str(site))
    # 用工作樹目前的版本覆蓋（clone 拿到的是 HEAD commit，不含未提交的修改）
    (site / "update_sunday.py").write_text((REPO / "update_sunday.py").read_text(encoding="utf-8"),
                                           encoding="utf-8")
    (site / "logs").mkdir(exist_ok=True)
    lr = site / "logs" / "last_run.json"
    if lr.exists():
        lr.unlink()
    return site, lr


def run(site, **extra_env):
    env = dict(os.environ,
               WEBSITE_DIR=str(site),
               TELEGRAM_BOT_TOKEN="",          # 置空 → notify_failure 直接回 False，不發訊
               TELEGRAM_HOME_CHANNEL="",
               **extra_env)
    env.pop("GITHUB_ACTIONS", None)            # 要走本機那條路徑
    return subprocess.run([sys.executable, str(site / "update_sunday.py")],
                          cwd=site, capture_output=True, text=True, env=env)

# ── 1：TEST_ALERT 送不出去走 sys.exit(1) —— SystemExit 不是 Exception，也必須落盤 ──
site, lr = clone()
proc = run(site, TEST_ALERT="true")
state = json.loads(lr.read_text(encoding="utf-8")) if lr.exists() else None
ok("1 TEST_ALERT 送不出去（sys.exit(1)）→ last_run.json 仍寫出且 exit=1",
   proc.returncode == 1 and state is not None and state.get("exit") == 1,
   f"returncode={proc.returncode} state={state}")

# ── 2：那份 JSON 的欄位齊全，心跳讀得懂 ──
required = {"run_at", "source", "candidates", "en_fallback", "pushed", "failure_reason", "exit"}
ok("2 欄位齊全（心跳的判準全靠這幾個欄位）",
   state is not None and required <= set(state) and state.get("source") == "local",
   f"缺少={required - set(state or {})} source={(state or {}).get('source')}")

# ── 3：run_at 是這次執行的時間，不是上一次的殘留 ──
from datetime import datetime  # noqa: E402
run_at = None
if state:
    try:
        run_at = datetime.fromisoformat(state["run_at"])
    except (KeyError, TypeError, ValueError):
        run_at = None
ok("3 run_at 可被 datetime.fromisoformat 解析、且是剛剛的時間",
   run_at is not None and abs((datetime.now() - run_at).total_seconds()) < 300,
   f"run_at={state.get('run_at') if state else None}")

# ── 4：舊的 last_run.json 必須被這次執行覆蓋，不能留著上週的內容誤導心跳 ──
site2, lr2 = clone()
lr2.write_text(json.dumps({"run_at": "2026-09-17T21:43:43", "exit": 0, "candidates": {},
                           "source": "local", "en_fallback": {}, "pushed": False,
                           "failure_reason": None}), encoding="utf-8")
run(site2, TEST_ALERT="true")
after = json.loads(lr2.read_text(encoding="utf-8"))
ok("4 上一次的 last_run.json 會被覆蓋（否則心跳會誤判「本週沒跑」）",
   after.get("run_at") != "2026-09-17T21:43:43" and after.get("exit") == 1,
   f"覆蓋後 run_at={after.get('run_at')} exit={after.get('exit')}")

print("\n===== last_run.json 驗收 =====")
allok = True
for name, good, detail in results:
    print(f"{'✅' if good else '❌'} {name}")
    if detail and not good:
        print(f"      {detail}")
    allok &= good
print(f"\n共 {len(results)} 條 →", "全部通過" if allok else "有失敗")
sys.exit(0 if allok else 1)
