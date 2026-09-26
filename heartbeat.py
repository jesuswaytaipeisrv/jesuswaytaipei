#!/usr/bin/env python3
"""
heartbeat.py
每週五 10:07 觸發（本機 launchd，只裝在龍蝦），檢查前一晚（週四 21:00）的自動更新
到底有沒有讓「使用者實際看到」新內容。

為什麼需要這一層：2026-09-24 那次排程準時跑完、內容全對、commit 也建了，
但被版控中的 .DS_Store 擋住 pull --rebase 而沒 push，網站兩天沒更新，
而 log 看起來完全正常。只檢查「有沒有跑」的心跳會把那次判成成功。

判準、每條決策的理由、以及 11 條驗收條件寫在專案 CLAUDE.md「自動更新心跳」節，
改判準之前先讀那裡。

設計上的鐵則：這個心跳唯一不能有的失效模式是「自己壞掉卻安靜」。
因此凡是讀不到、看不懂、對不上的情況，一律出聲，不得靜音當成正常。
"""

import json
import logging
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from update_sunday import WEBSITE_DIR, LAST_RUN_FILE, load_env  # noqa: E402

# ── 設定 ──────────────────────────────────────────────────────────────
# launchd 的 stdout/stderr 不可指向 ~/Documents（TCC 保護資料夾，會在 spawn 階段被靜默
# 拒絕，2026-07-17 查證）。心跳自己的 log 與 state 一併放在這個已驗證安全的目錄。
LOG_DIR     = Path.home() / "Library" / "Logs" / "jesusway"
LOG_FILE    = LOG_DIR / "heartbeat.log"
STATE_FILE  = LOG_DIR / "heartbeat_state.json"
SITE_BASE   = "https://www.jesuswaytaipei.org"
SILENCE_WEEKS = 4          # 連續這麼多週沒出聲就發一則存活訊號
HTTP_TIMEOUT  = 20

# 候選類別 → (中文頁, 英文頁)
PAGES = {
    "主日": ("sunday.html", "en/sunday.html"),
    "樣青": ("youth.html", "en/youth.html"),
}

DATE = re.compile(r"\d{4}\.\d{2}\.\d{2}")


def setup_logging():
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    logging.basicConfig(level=logging.INFO, handlers=[sh, fh])


# ── Telegram ──────────────────────────────────────────────────────────
def send(text):
    """發 Telegram。回傳是否確實送出。

    刻意不重用 update_sunday.py 的 notify_failure()：那支的訊息固定頂著
    「台北樣教會網站自動更新（本機排程）」，會讓「主 job 當場失敗」和
    「事後查出沒成功」在手機上長得一樣，而這兩者要做的事不同。
    token 與 chat_id 沿用同一組（~/.hermes/.env），不新增任何設定。
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_HOME_CHANNEL")
    if not token or not chat_id:
        logging.error("未設定 TELEGRAM_BOT_TOKEN／TELEGRAM_HOME_CHANNEL，心跳無法出聲")
        return False
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            ok = r.status == 200
    except Exception as e:
        logging.error(f"Telegram 發送失敗：{type(e).__name__}: {e}")
        return False
    logging.info("Telegram 已送出" if ok else "Telegram 回非 200")
    return ok


# ── state（只為了「連續 N 週沒出聲就發存活訊號」而存在）─────────────────
def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        logging.error(f"寫入 {STATE_FILE.name} 失敗：{e}")


# ── 取內容 ────────────────────────────────────────────────────────────
def git(*args):
    return subprocess.run(["git", "-C", str(WEBSITE_DIR)] + list(args),
                          capture_output=True, text=True)


def newest_row(html):
    """表格第一列（最新那列）的原文。抓不到回 None。"""
    i = html.find("<tbody")
    if i == -1:
        return None
    j = html.find("</tr>", i)
    return html[i:j] if j != -1 else None


def newest_date(html):
    """表格最新一列的日期字串，例如 2026.09.13。抓不到回 None。"""
    row = newest_row(html)
    if not row:
        return None
    m = DATE.search(row)
    return m.group(0) if m else None


def fetch_remote():
    """更新 remote-tracking ref。回傳問題清單（空＝成功）。

    **必須在讀 origin/main 之前跑。** 讀到舊 ref 會把「CI 補救層已經推上去」看成
    「沒推上去」，正好打掉「心跳排在 CI 之後」這個排程理由（2026-09-26 code review 發現）。
    fetch 失敗也不能默默往下比對：那會拿舊 ref 算出 ahead 0、結論「沒有未推的 commit」，
    而那正是要抓的失效。
    """
    r = git("fetch", "--quiet", "origin")
    if r.returncode != 0:
        detail = r.stderr.strip() or f"returncode {r.returncode}"
        return [f"【連不上遠端】`git fetch` 失敗（{detail}），"
                f"origin/main 可能是舊的，本週狀態無法確認——先看網路與 ssh key。"]
    return []


def remote_page(page):
    """origin/main 上該頁的內容。取不到回 None。"""
    r = git("show", f"origin/main:{page}")
    return r.stdout if r.returncode == 0 else None


def online_page(page):
    """線上網站該頁的內容。取不到回 None。"""
    try:
        with urllib.request.urlopen(f"{SITE_BASE}/{page}", timeout=HTTP_TIMEOUT) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        logging.error(f"抓不到線上頁面 {page}：{type(e).__name__}: {e}")
        return None


# ── 判準 ──────────────────────────────────────────────────────────────
def latest_thursday(now):
    """今天或今天之前最近的那個週四。Python 的 weekday() 週一＝0，所以週四＝3。"""
    return (now - timedelta(days=(now.weekday() - 3) % 7)).date()


def read_last_run(now):
    """讀主 job 寫的機器可讀狀態。回傳 (state, 問題字串)；兩者只會有一個有值。"""
    try:
        run = json.loads(LAST_RUN_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"讀不到 {LAST_RUN_FILE}——本機排程當天沒有留下任何執行紀錄，可能根本沒觸發。"
    except (OSError, ValueError) as e:
        return None, f"{LAST_RUN_FILE.name} 讀不到或不是合法 JSON（{type(e).__name__}），無法判斷本週狀態。"

    raw = run.get("run_at")
    try:
        run_at = datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        return None, f"{LAST_RUN_FILE.name} 的 run_at 看不懂：{raw!r}，無法判斷本週狀態。"

    # 主 job 排在週四 21:00，被延遲補跑過（09-17 是 21:43）也算，所以用「週四 20:00 起」當窗口。
    window_start = datetime.combine(latest_thursday(now), datetime.min.time()) + timedelta(hours=20)
    if not (window_start <= run_at <= now):
        return None, (f"{LAST_RUN_FILE.name} 最後一次執行是 {run_at:%Y-%m-%d %H:%M}，"
                      f"不在本週四（{window_start:%m-%d} 20:00）之後——本週的排程沒有跑。")
    return run, None


def check_content(run):
    """比對候選與站上內容。回傳問題清單（空＝都對）。"""
    problems = []
    cands = run.get("candidates") or {}

    # 主 job 抓不到頻道清單時**不會 raise**：它寫 failure_reason、發告警，然後一路走到
    # 「無更新，結束」正常收場，exit 是 0（09-17 那晚 log 的結尾字面上就是這句）。
    # 所以只靠 exit≠0 判斷本機層失敗會整週靜音——而 09-17 那次 notify_failure() 自己也
    # 因為沒網路發不出去，兩層都不出聲，正是這個心跳要擋的情況。
    if run.get("failure_reason"):
        # 刻意不貼「抓不到頻道清單」這種具體標籤：failure_reason 有兩種來源——真的取不到清單，
        # 以及「抓到清單、候選也有 ID，只是日期解析失敗」（CI 環境的常態）。貼錯會把排查導到錯的層。
        problems.append(f"【本機那次沒能確認最新內容】排程回報：{run['failure_reason']}"
                        f"——該次以 exit 0 正常收場，光看 exit code 看不出問題。"
                        f"看上面原文判斷是取不到頻道清單，還是抓到了清單但日期解析失敗。")
    elif not cands:
        problems.append("【候選為空】本機排程那次沒有記下任何候選影片，"
                        "無法確認站上是不是最新。")

    for label, cand in cands.items():
        want = cand.get("date")
        pages = PAGES.get(label)
        if not want or not pages:
            problems.append(f"{label} 的候選資料不完整：{cand!r}")
            continue

        for page in pages:
            # 第一層：內容有沒有推上 origin/main
            html = remote_page(page)
            if html is None:
                problems.append(f"取不到 origin/main 的 {page}，無法確認內容有沒有推上去。")
                continue
            got = newest_date(html)
            if got != want:
                problems.append(f"【沒推上去】{page} 在 origin/main 的最新一列是 {got}，"
                                f"但本機排程抓到的最新{label}是 {want}。")
                continue

            # 第二層：推上去了，線上有沒有生效（Pages 間歇逾時失敗是已知現象）
            live = online_page(page)
            if live is None:
                problems.append(f"抓不到線上的 {page}，無法確認部署有沒有生效。")
                continue
            live_date = newest_date(live)
            if live_date != want:
                problems.append(f"【部署沒生效】{page} 已推上 origin/main（{want}），"
                                f"但線上網站的最新一列還是 {live_date}——"
                                f"這是 GitHub Pages 部署層的問題，Re-run 那次 deploy 即可。")
                continue

        # 英文欄位是不是真的英文。**權威值是主 job 自己記下的 en_fallback，不是「頁面上有沒有中文」**：
        # 這個站的英文頁刻意保留中文姓名（例如「王馥蓓｜Chief Sustainability Advisor, Dentsu Group」），
        # 拿 CJK 偵測會週週假警報——而假警報正是這個批次的歷史病根（2026-09-26 code review 發現）。
        if (run.get("en_fallback") or {}).get(label):
            problems.append(f"【英文頁暫用中文】{label} {want} 那次翻譯失敗（Gemini 通常回 503），"
                            f"英文欄位目前是中文，需人工補譯：{pages[1]}")
    return problems


def check_unpushed():
    """本機有沒有「動到那四頁卻沒推出去」的 commit。這是 09-24 的直接症狀。

    刻意不把任何未推 commit 都當成問題：這 repo 三台輪流維護、`CLAUDE.md` 與 `docs/DEVLOG.md`
    常手動編輯，只要本機留著一個沒推的文件 commit 就發 ⚠️ 會變成週週假警報
    （2026-09-26 code review 發現）。判準是「網站內容有沒有送出去」，不是「本機有沒有領先」。
    """
    r = git("status", "-sb")
    if r.returncode != 0:
        return [f"git status 失敗，無法確認有沒有沒推出去的 commit：{r.stderr.strip()}"]
    first = r.stdout.splitlines()[0] if r.stdout else ""
    m = re.search(r"\[ahead (\d+)", first)
    if not m:
        return []

    pages = [page for pair in PAGES.values() for page in pair]
    diff = git("diff", "--name-only", "origin/main..HEAD", "--", *pages)
    if diff.returncode != 0:
        return [f"本機比 origin/main 多 {m.group(1)} 個 commit，但 git diff 失敗、"
                f"無法確認是否動到那四頁：{diff.stderr.strip()}"]
    touched = [line for line in diff.stdout.splitlines() if line.strip()]
    if not touched:
        logging.info(f"本機領先 {m.group(1)} 個 commit，但都沒動到那四頁（{first.strip()}），不算問題")
        return []
    return [f"【commit 沒推出去】本機比 origin/main 多 {m.group(1)} 個 commit，"
            f"其中動到了 {'、'.join(touched)}。09-24 就是工作樹有未提交修改擋住 "
            f"pull --rebase 造成的，先看 git status。"]


# ── 主流程 ────────────────────────────────────────────────────────────
def main():
    setup_logging()
    logging.info("=== heartbeat.py 開始 ===")

    # 告警管道自我檢查。心跳平時安靜，管道壞掉時無從得知它還通不通，
    # 所以留一個手動入口；送不出去就讓這次執行失敗，否則驗了個寂寞。
    if os.environ.get("HEARTBEAT_TEST_ALERT") == "true":
        if not send("🫀 網站更新心跳【測試訊息，可忽略】：這是手動觸發的管道自我檢查，不是真實異常。"):
            logging.error("心跳告警自我檢查失敗：Telegram 沒送出去")
            sys.exit(1)
        logging.info("心跳告警自我檢查：Telegram 已送出")
        return

    now = datetime.now()
    state = load_state()
    state["last_run"] = now.isoformat(timespec="seconds")

    run, problem = read_last_run(now)
    if problem:
        problems = [problem]
    else:
        # 順序有意義：fetch 必須先於任何 origin/main 的讀取，且失敗就停在這裡——
        # 拿舊 ref 比對出來的結論會是錯的，多報幾項只會誤導。
        problems = fetch_remote()
        if not problems:
            problems = check_content(run) + check_unpushed()

    if problems:
        body = "\n\n".join(f"・{p}" for p in problems)
        text = (f"⚠️ 網站更新心跳（週四批次事後複查）發現問題：\n\n{body}\n\n"
                f"本機 log：{Path.home() / 'Library' / 'Logs' / 'jesusway' / 'update_sunday_launchd.log'}")
        sent = send(text)
        # 只有真的送出去才記時間戳。送失敗卻記上去，會讓「管道壞了」被後面的
        # 沉默上限判斷當成「剛通知過」，於是繼續安靜——正是這個心跳不允許的失效模式。
        if sent:
            state["last_notified"] = now.isoformat(timespec="seconds")
        save_state(state)
        logging.error(f"心跳判定異常 {len(problems)} 項，Telegram {'已送出' if sent else '送不出去'}")
        for p in problems:
            logging.error(f"  ・{p}")
        sys.exit(1)

    # 網站結果是對的，但本機層自己失敗過——CI 補救層或人工補上了。
    # 結果對就靜音會重演「綠燈說謊」：主層悄悄壞掉，整條鏈路退化成只剩 CI 在撐。
    if run.get("exit") not in (0, None):
        if send(f"🫀 網站更新心跳：網站內容正確，但本機排程那次是失敗收場"
                f"（exit={run.get('exit')}、failure_reason={run.get('failure_reason')}）。"
                f"應是 CI 補救層或人工補上的。本機層連續失敗會讓整條鏈路只剩 CI 在撐，值得看一下 log。"):
            state["last_notified"] = now.isoformat(timespec="seconds")
        save_state(state)
        logging.warning("網站內容正確，但本機層那次失敗，已發低調通知")
        return

    # 一切正常：安靜。但連續 SILENCE_WEEKS 週沒出聲就發一則存活訊號，
    # 否則「心跳自己死了」與「一切正常」在使用者眼中完全一樣。
    last_notified = state.get("last_notified")
    quiet_since = None
    if last_notified:
        try:
            quiet_since = datetime.fromisoformat(last_notified)
        except ValueError:
            quiet_since = None

    cands = run.get("candidates") or {}
    summary = "、".join(f"{label} {c.get('date')}" for label, c in cands.items()) or "（無候選）"
    text = None
    if quiet_since is None:
        # 第一次執行（或 state 被清掉）。**不能說「過去 4 週都正常」**——當下沒有那 4 週的資料。
        text = (f"🫀 網站更新心跳：這是第一次執行，沒有先前的紀錄可比，本週的檢查全部通過。"
                f"本週最新內容 {summary}。之後只有異常才會出聲，"
                f"連續 {SILENCE_WEEKS} 週安靜就會再發一則存活訊號。")
    elif (now.date() - quiet_since.date()).days >= SILENCE_WEEKS * 7 - 1:
        # 用日數比、並留一天寬容：兩端都是 launchd 實際觸發的 wall clock，
        # 差幾秒就會讓 >= 28 天不成立而整整跳過一週。
        text = (f"🫀 網站更新心跳：存活訊號。過去 {SILENCE_WEEKS} 週的週四批次都正常，"
                f"本週最新內容 {summary}。收到這則代表心跳本身還活著。")

    if text is None:
        logging.info("本週一切正常，保持安靜")
    elif send(text):
        state["last_notified"] = now.isoformat(timespec="seconds")
        logging.info("已發存活／首次執行訊號")
    else:
        # 時間戳刻意不更新：下次執行會再試一次，而不是安靜四週。
        logging.error("存活訊號送不出去，時間戳不更新，下次會重試")
    save_state(state)


if __name__ == "__main__":
    try:
        # load_env() 先跑：若例外發生在它之前，下面 except 裡的 send() 就沒有 token、
        # 只能安靜地寫 log 然後結束——那正是這支腳本唯一不允許的失效模式
        # （2026-09-26 code review 發現）。
        load_env()
        main()
    except Exception as e:
        logging.exception("心跳本身執行失敗")
        # 心跳自己爆掉也要出聲，否則就是「壞掉卻安靜」——這是設計上唯一不能有的失效模式。
        send(f"⚠️ 網站更新心跳自己執行失敗：{type(e).__name__}: {e}\n"
             f"心跳 log：{LOG_FILE}")
        sys.exit(1)
