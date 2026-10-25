"""驗收 fetch_latest_streams() 會把整份 flat-playlist 清單與選中的候選序號寫進 log。

    python3 tests/test_list_logging.py

起因：2026-10-22 本機排程沒選到已公開三天的樣青 qPTkqGyKPj0，log 只記「取得 25 筆」，
事後分不出是不在清單、標題當時沒有關鍵字、還是排在舊片之後。stub 邊界同 test_date_fields.py：
PATH 上的假 `yt-dlp`，不需要網路、不發 Telegram、不碰真實 repo，log 只收進記憶體不寫正式 log 檔。
清單標題抄 2026-10-25 頻道 `/streams` 的真實值。
"""
import logging
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]     # 路徑由測試檔自身推導
results = []

# 假 yt-dlp：flat-playlist 回三支（主日、樣青、舊樣青）；單支查詢一律回固定日期
FAKE_YTDLP = r'''#!/usr/bin/env python3
import sys
args = sys.argv[1:]
if "--flat-playlist" in args:
    print("D7bUJi5Sr_o\t進入應許前的預備  |  極光教會 黃仁鵬 傳道 | 台北樣教會線上主日")
    print("qPTkqGyKPj0\t《樣青講堂》 | 科學＋跨界的能力，跟別人創業有什麼關係？ |  善僕資本合夥人 陸子鈞")
    print("fcmrvY8uMQc\t《樣青講堂》 | 不是你太廢，是狀態卡住了！ |  東海大學博雅書院思維導師 許恆嘉")
    sys.exit(0)
print("20261018\x1f")
'''


def ok(name, cond, detail=""):
    results.append((name, bool(cond), detail))


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


with tempfile.TemporaryDirectory() as tmp:
    fake = Path(tmp) / "yt-dlp"
    fake.write_text(FAKE_YTDLP)
    fake.chmod(0o755)
    os.environ["PATH"] = f"{tmp}{os.pathsep}{os.environ['PATH']}"
    sys.path.insert(0, str(REPO))
    import update_sunday  # noqa: E402

    h = ListHandler()
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.INFO)
    update_sunday.fetch_latest_streams()
    root.removeHandler(h)
    log = "\n".join(h.lines)

    ok("1 清單每一筆（序號＋ID）都寫進 log",
       all(f"清單 #{i:02d} {vid}" in log for i, vid in
           ((1, "D7bUJi5Sr_o"), (2, "qPTkqGyKPj0"), (3, "fcmrvY8uMQc"))), log)
    ok("2 記下主日／樣青各自選中清單第幾筆",
       "主日候選：清單 #01 D7bUJi5Sr_o" in log and "樣青候選：清單 #02 qPTkqGyKPj0" in log, log)

passed = sum(1 for _, c, _ in results if c)
for name, cond, detail in results:
    print(f"  {'✅' if cond else '❌'} {name}" + ("" if cond else f"  ({detail})"))
print(f"{passed}/{len(results)} 通過")
sys.exit(0 if passed == len(results) else 1)
