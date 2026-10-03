"""驗收 update_sunday.py 標題無日期時的 yt-dlp 日期欄位順序：release_date 優先、upload_date 後備。

    python3 tests/test_date_fields.py

用 PATH 上的假 `yt-dlp` 取代真的（stub 邊界在子行程，`fetch_latest_streams()` 走真實程式碼路徑），
不需要網路、不會發任何 Telegram、不碰真實 repo。假 yt-dlp 只模擬 `%(a,b)s` 的
「第一個有值的欄位」語意——這個語意已用真的 yt-dlp 實測過（docs/DEVLOG.md 2026-10-03）。

起因：2026-10-01 主日直播 `_o_9r6qJUPw` 於 09-27 開播，重播檔 09-29 才處理完，
upload_date 變成 20260929；原本 upload 優先，站上被寫成 2026.09.29。
"""
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]     # 路徑由測試檔自身推導
results = []

# 假 yt-dlp：flat-playlist 回一支標題無日期的主日；單支查詢依 FAKE_RELEASE／FAKE_UPLOAD 解 --print 模板
FAKE_YTDLP = r'''#!/usr/bin/env python3
import os, re, sys
args = sys.argv[1:]
if "--flat-playlist" in args:
    print("VID00000001\t獨一無二的呼召 | 陳璽文 傳道 | 台北樣線上主日")
    sys.exit(0)
fields = {"release_date": os.environ.get("FAKE_RELEASE", ""),
          "upload_date": os.environ.get("FAKE_UPLOAD", ""),
          "description": ""}
def resolve(m):
    for name in m.group(1).split(","):
        if fields.get(name):
            return fields[name]
    return "NA"
print(re.sub(r"%\(([^)]+)\)s", resolve, args[args.index("--print") + 1]))
'''


def ok(name, cond, detail=""):
    results.append((name, bool(cond), detail))


def run_case(release, upload):
    """以假 yt-dlp 跑 fetch_latest_streams()，回傳主日候選的日期。"""
    os.environ["FAKE_RELEASE"] = release
    os.environ["FAKE_UPLOAD"] = upload
    latest_sunday, _, _ = update_sunday.fetch_latest_streams()
    return latest_sunday[0] if latest_sunday else None


with tempfile.TemporaryDirectory() as tmp:
    fake = Path(tmp) / "yt-dlp"
    fake.write_text(FAKE_YTDLP)
    fake.chmod(0o755)
    os.environ["PATH"] = f"{tmp}{os.pathsep}{os.environ['PATH']}"
    sys.path.insert(0, str(REPO))
    import update_sunday  # noqa: E402

    got = run_case("20260927", "20260929")
    ok("1 直播重播檔晚兩天處理（release=0927、upload=0929）→ 寫開播日 2026.09.27",
       got == "2026.09.27", f"got={got}")

    got = run_case("", "20260913")
    ok("2 非直播影片沒有 release_date → 退回 upload_date",
       got == "2026.09.13", f"got={got}")

passed = sum(1 for _, c, _ in results if c)
for name, cond, detail in results:
    print(f"  {'✅' if cond else '❌'} {name}" + ("" if cond else f"  ({detail})"))
print(f"{passed}/{len(results)} 通過")
sys.exit(0 if passed == len(results) else 1)
