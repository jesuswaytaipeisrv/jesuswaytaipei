"""驗收 SEO 基礎建設：canonical、hreflang、sitemap.xml、robots.txt、首頁 JSON-LD、GA 片段不被洗掉。

    python3 tests/test_seo_head.py

純讀檔、不需網路。頁面清單由檔案系統掃出來（根目錄與 en/ 的 *.html），不寫死，
所以日後新增頁面卻漏貼 canonical／hreflang／sitemap 時，這支會失敗（docs/SEO_HANDOFF.md V7）。
"""
import json
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]     # 路徑由測試檔自身推導
BASE = "https://www.jesuswaytaipei.org"
GA_ID = "G-6BH0T2SH0Y"
results = []


def ok(name, cond, detail=""):
    results.append((name, bool(cond), detail))


class HeadParser(HTMLParser):
    """收集 <head> 內的 og:url、canonical、hreflang、JSON-LD 內容。"""

    def __init__(self):
        super().__init__()
        self.in_head = False
        self.og_urls, self.canonicals, self.hreflangs, self.jsonld = [], [], [], []
        self._in_jsonld = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "head":
            self.in_head = True
        if not self.in_head:
            return
        if tag == "meta" and a.get("property") == "og:url":
            self.og_urls.append(a.get("content"))
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonicals.append(a.get("href"))
        elif tag == "link" and a.get("rel") == "alternate" and "hreflang" in a:
            self.hreflangs.append((a["hreflang"], a.get("href")))
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in_jsonld = True
            self.jsonld.append("")

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False
        elif tag == "script":
            self._in_jsonld = False

    def handle_data(self, data):
        if self._in_jsonld:
            self.jsonld[-1] += data


def expected_url(rel):
    """檔案相對路徑 → 標準網址。index.html 用目錄形式，其餘用檔名。"""
    p = Path(rel)
    prefix = "/en/" if p.parent.name == "en" else "/"
    return BASE + prefix + ("" if p.name == "index.html" else p.name)


def url_to_file(url):
    """標準網址 → repo 內檔案路徑；不是本站網址回傳 None。"""
    if not url or not url.startswith(BASE + "/"):
        return None
    path = url[len(BASE) + 1:]
    if path == "" or path.endswith("/"):
        path += "index.html"
    return REPO / path


zh_names = {p.name for p in REPO.glob("*.html")}
en_names = {p.name for p in (REPO / "en").glob("*.html")}
pages = sorted(zh_names) + sorted(f"en/{n}" for n in en_names)
heads = {}
for rel in pages:
    hp = HeadParser()
    hp.feed((REPO / rel).read_text(encoding="utf-8"))
    heads[rel] = hp

# 8. 中英頁一一對應（擋「新增頁面只做一邊」）
ok("8a 根目錄與 en/ 的 *.html 檔名集合相同",
   zh_names == en_names, f"只在中文={sorted(zh_names - en_names)} 只在英文={sorted(en_names - zh_names)}")
ok("8b 至少 18 頁（9 中 + 9 英）", len(pages) >= 18, f"共 {len(pages)} 頁")

# 1. canonical
bad = []
for rel, h in heads.items():
    if len(h.canonicals) != 1 or len(h.og_urls) != 1 or h.canonicals[0] != h.og_urls[0] \
            or h.canonicals[0] != expected_url(rel):
        bad.append(f"{rel}: canonical={h.canonicals} og:url={h.og_urls}")
ok("1 每頁恰好一個 canonical，等於 og:url 也等於檔名推得的標準網址", not bad, "; ".join(bad))

# 2. hreflang 三個、雙向一致
bad = []
for rel, h in heads.items():
    langs = sorted(lang for lang, _ in h.hreflangs)
    if langs != ["en", "x-default", "zh-Hant"]:
        bad.append(f"{rel}: {h.hreflangs}")
for name in zh_names & en_names:
    zh, en = heads[name], heads[f"en/{name}"]
    if sorted(zh.hreflangs) != sorted(en.hreflangs):
        bad.append(f"{name} 與 en/{name} 的 hreflang 不同")
    d = dict(zh.hreflangs)
    if d.get("zh-Hant") != expected_url(name) or d.get("en") != expected_url(f"en/{name}") \
            or d.get("x-default") != expected_url(name):
        bad.append(f"{name}: hreflang 值不對 {d}")
ok("2 每頁恰好三個 hreflang（zh-Hant／en／x-default），中英對應頁完全相同", not bad, "; ".join(bad))

# 3. hreflang 指向真實檔案
bad = [f"{rel}: {href}" for rel, h in heads.items() for _, href in h.hreflangs
       if not (url_to_file(href) and url_to_file(href).is_file())]
ok("3 hreflang 指到的網址都對應到 repo 內真實存在的檔案", not bad, "; ".join(bad))

# 4. sitemap
try:
    tree = ET.parse(REPO / "sitemap.xml")
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [e.text.strip() for e in tree.getroot().findall("s:url/s:loc", ns)]
    og_set = {h.og_urls[0] for h in heads.values() if h.og_urls}
    ok("4 sitemap.xml 可解析，<loc> 集合 == 全部頁面 og:url（不多不少、不重複）",
       set(locs) == og_set and len(locs) == len(set(locs)) == len(pages),
       f"多={sorted(set(locs) - og_set)} 少={sorted(og_set - set(locs))} "
       f"loc 共 {len(locs)}、頁面共 {len(pages)}")
    ok("8c 每個 *.html 的標準網址都在 sitemap 裡",
       {expected_url(rel) for rel in pages} <= set(locs),
       f"缺={sorted({expected_url(rel) for rel in pages} - set(locs))}")
except (OSError, ET.ParseError) as e:
    ok("4 sitemap.xml 可解析", False, repr(e))

# 5. robots.txt
try:
    lines = [l.strip() for l in (REPO / "robots.txt").read_text(encoding="utf-8").splitlines()]
    disallows = [l.split(":", 1)[1].strip() for l in lines if l.lower().startswith("disallow:")]
    ok("5a robots.txt 有 Sitemap 行指向 sitemap.xml",
       f"Sitemap: {BASE}/sitemap.xml" in lines, f"lines={lines}")
    blocked = [d for d in disallows if d == "/" or "/assets/".startswith(d) or d.startswith("/assets")
               or "/index.html".startswith(d) or "/en/".startswith(d)]
    ok("5b robots.txt 沒有全擋、沒擋到 /assets/、首頁或 /en/", not blocked, f"blocked={blocked}")
except OSError as e:
    ok("5 robots.txt 存在", False, repr(e))

# 6. 首頁 JSON-LD
for rel in ("index.html", "en/index.html"):
    blocks = heads[rel].jsonld
    try:
        data = json.loads(blocks[0]) if len(blocks) == 1 else None
    except json.JSONDecodeError as e:
        data, blocks = None, [repr(e)]
    ok(f"6 {rel} 恰好一段 JSON-LD，@type=Church、url 正確、沒有自編的 openingHours／telephone",
       data is not None and data.get("@type") == "Church" and data.get("url") == expected_url(rel)
       and not {"openingHours", "telephone", "event"} & data.keys(), f"blocks={blocks}")

# 7. GA 片段沒被洗掉或重複
bad = []
for rel in pages:
    text = (REPO / rel).read_text(encoding="utf-8")
    if text.count(f"gtag/js?id={GA_ID}") != 1 or text.count(f"gtag('config', '{GA_ID}')") != 1:
        bad.append(rel)
ok("7 每頁恰好一個 GA4 gtag 片段", not bad, f"異常={bad}")

passed = sum(1 for _, c, _ in results if c)
for name, cond, detail in results:
    print(f"  {'✅' if cond else '❌'} {name}" + ("" if cond else f"  ({detail})"))
print(f"{passed}/{len(results)} 通過")
sys.exit(0 if passed == len(results) else 1)
