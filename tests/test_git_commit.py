"""驗收 update_sunday.py 的 git_commit()：rebase.autoStash 與「只在真的卡住時才 abort」。

    python3 tests/test_git_commit.py

每個情境用獨立的臨時 git repo（bare remote + local/other 兩個 clone），**不碰真實 repo**，
不需要網路、不需要 yt-dlp、不會發任何 Telegram。

起因：2026-09-24 那次排程內容全對、commit 也建了，卻因工作樹有一個已納入版控的 .DS_Store
未提交修改，`git pull --rebase` 整批拒絕（cannot pull with rebase: You have unstaged changes），
網站兩天沒更新。修法與判準見 docs/DEVLOG.md 2026-09-26。
"""
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]     # 路徑由測試檔自身推導，三台電腦的 repo 路徑不同
logging.basicConfig(level=logging.INFO, format="    [log] %(message)s")


def sh(*args, cwd=None, check=True):
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)


def make_repo(tmp):
    """bare 遠端 + 兩個 clone：local＝被測機器、other＝別台電腦。

    工作樹裡的 `junk` 扮演 .DS_Store 的角色（已納入版控、會被 Finder 改動的雜項）。
    """
    remote = tmp / "remote.git"
    sh("git", "init", "--bare", "-q", str(remote))
    for name in ("local", "other"):
        sh("git", "clone", "-q", str(remote), str(tmp / name))
        sh("git", "config", "user.email", "t@t", cwd=tmp / name)
        sh("git", "config", "user.name", "t", cwd=tmp / name)
    loc = tmp / "local"
    (loc / "page.html").write_text("row1\n")
    (loc / "junk").write_text("v1\n")
    sh("git", "add", "-A", cwd=loc)
    sh("git", "commit", "-qm", "init", cwd=loc)
    sh("git", "push", "-q", "origin", "main", cwd=loc)
    sh("git", "pull", "-q", cwd=tmp / "other")
    return loc, tmp / "other"


def load_module(website_dir):
    """以 WEBSITE_DIR 指向臨時 repo 重新載入 update_sunday（模組層級會讀這個環境變數）。"""
    os.environ["WEBSITE_DIR"] = str(website_dir)
    os.environ["GITHUB_ACTIONS"] = "1"          # 不要寫 log 檔
    sys.modules.pop("update_sunday", None)
    sys.path.insert(0, str(REPO))
    import update_sunday
    return update_sunday


def other_pushes(other, filename, content, msg):
    (other / filename).write_text(content)
    sh("git", "add", "-A", cwd=other)
    sh("git", "commit", "-qm", msg, cwd=other)
    sh("git", "push", "-q", cwd=other)


results = []


def ok(name, cond, detail=""):
    results.append((name, bool(cond), detail))


# ── 1：髒工作樹（09-24 的阻斷）＋ 遠端被別台推過 → autoStash 應讓 push 成功 ──
with tempfile.TemporaryDirectory() as d:
    tmp = Path(d)
    loc, other = make_repo(tmp)
    other_pushes(other, "unrelated.txt", "from another machine\n", "別台的 commit")
    (loc / "junk").write_text("v2-dirty\n")              # 就是 .DS_Store 的角色
    (loc / "page.html").write_text("row1\nrow2-new\n")   # 本次要推的內容
    us = load_module(loc)
    try:
        us.git_commit(["page.html"], "feat: 自動更新")
        pushed = "自動更新" in sh("git", "log", "--oneline", "-1", cwd=tmp / "remote.git").stdout
        junk_kept = (loc / "junk").read_text() == "v2-dirty\n"
        merged = "別台的 commit" in sh("git", "log", "--oneline", cwd=loc).stdout
        ok("1 髒工作樹＋遠端領先 → push 成功、雜項原樣還原、別台 commit 併入",
           pushed and junk_kept and merged,
           f"push={pushed} 雜項還原={junk_kept} 併入別台={merged}")
    except Exception as e:
        ok("1 髒工作樹＋遠端領先 → push 成功、雜項原樣還原、別台 commit 併入", False, f"丟出例外：{e}")

# ── 2：真衝突 → 應拋 RuntimeError、abort 生效、repo 不卡在 rebase ──
with tempfile.TemporaryDirectory() as d:
    tmp = Path(d)
    loc, other = make_repo(tmp)
    other_pushes(other, "page.html", "row1\nOTHER-EDIT\n", "別台改同一行")
    (loc / "page.html").write_text("row1\nLOCAL-EDIT\n")
    us = load_module(loc)
    raised = None
    try:
        us.git_commit(["page.html"], "feat: 自動更新")
        raised = False
    except RuntimeError:
        raised = True
    except Exception as e:
        raised = f"錯的例外型別：{type(e).__name__}"
    ok("2 真衝突 → 拋 RuntimeError 且不卡在 rebase 中",
       raised is True and us.rebase_in_progress() is False,
       f"拋錯={raised} 仍卡在rebase={us.rebase_in_progress()}")

# ── 3：rebase 根本沒開始就失敗 → 訊息不應含誤導的 no rebase in progress ──
with tempfile.TemporaryDirectory() as d:
    tmp = Path(d)
    loc, _ = make_repo(tmp)
    sh("git", "remote", "set-url", "origin", str(tmp / "no-such-repo.git"), cwd=loc)
    (loc / "page.html").write_text("row1\nrow2\n")
    us = load_module(loc)
    msg = ""
    try:
        us.git_commit(["page.html"], "feat: 自動更新")
    except RuntimeError as e:
        msg = str(e)
    except Exception as e:
        msg = f"錯的例外型別：{type(e).__name__}: {e}"
    ok("3 rebase 未開始就失敗 → 訊息不含誤導的 no rebase in progress",
       "no rebase in progress" not in msg and msg.startswith("git pull --rebase 失敗")
       and not us.rebase_in_progress(), msg[:90])

# ── 4：autoStash × 真衝突同時發生 → stash 不得殘留、雜項不得不見 ──
with tempfile.TemporaryDirectory() as d:
    tmp = Path(d)
    loc, other = make_repo(tmp)
    other_pushes(other, "page.html", "row1\nOTHER\n", "別台改同一行")
    (loc / "junk").write_text("v2-dirty\n")          # 會觸發 autostash
    (loc / "page.html").write_text("row1\nLOCAL\n")  # 必衝突
    us = load_module(loc)
    try:
        us.git_commit(["page.html"], "feat: 自動更新")
    except RuntimeError:
        pass
    stash = sh("git", "stash", "list", cwd=loc).stdout.strip()
    ok("4 autoStash × 真衝突 → 無 stash 殘留、雜項保留、沒卡在 rebase",
       not stash and (loc / "junk").read_text() == "v2-dirty\n" and not us.rebase_in_progress(),
       f"stash={stash or '（空）'} junk={(loc / 'junk').read_text()!r}")

print("\n===== git_commit() 驗收 =====")
allok = True
for name, good, detail in results:
    print(f"{'✅' if good else '❌'} {name}")
    if detail and not good:
        print(f"      {detail}")
    allok &= good
print(f"\n共 {len(results)} 條 →", "全部通過" if allok else "有失敗")
sys.exit(0 if allok else 1)
