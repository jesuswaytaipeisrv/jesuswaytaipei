"""驗收 update_sunday.py 主日標題的題目／講員解析（`parse_sunday_title_speaker`）。

    python3 tests/test_title_parse.py

純函式、不需要網路。標題一律抄週四批次 log 裡的真實 YouTube 標題。

起因：2026-10 起結尾段從「台北樣線上主日」改成「台北樣教會線上主日」，去雜訊只拿掉「台北樣教會」，
剩下的「線上主日」被當成講員，10.04、10.11 兩週站上講員欄寫成「線上主日」／Online Sunday Service。
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]     # 路徑由測試檔自身推導
sys.path.insert(0, str(REPO))
import update_sunday  # noqa: E402

results = []


def ok(name, cond, detail=""):
    results.append((name, bool(cond), detail))


CASES = [
    ("1 新格式「台北樣教會線上主日」結尾（10-15 log）",
     "2026.10.11 | 要剛強 必須先軟弱 |  吳必然 牧師 | 台北樣教會線上主日",
     "吳必然 牧師"),
    ("2 新格式（10-08 log）",
     "2026.10.04 | 有一種軟弱叫剛強 |  吳必然 牧師 | 台北樣教會線上主日",
     "吳必然 牧師"),
    ("3 舊格式「台北樣線上主日」結尾、講員帶外教會名（10-01 log）",
     "2026.09.29 | 獨一無二的呼召 |  台北靈糧堂 陳璽文 傳道 | 台北樣線上主日",
     "台北靈糧堂 陳璽文 傳道"),
]

for name, raw, speaker in CASES:
    got = update_sunday.parse_sunday_title_speaker(raw)
    ok(name, got[1] == speaker, f"got={got}")

passed = sum(1 for _, c, _ in results if c)
for name, cond, detail in results:
    print(f"  {'✅' if cond else '❌'} {name}" + ("" if cond else f"  ({detail})"))
print(f"{passed}/{len(results)} 通過")
sys.exit(0 if passed == len(results) else 1)
