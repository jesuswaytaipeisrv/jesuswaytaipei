#!/usr/bin/env python3
"""
update_sunday.py
每週四 09:00 由 launchd 自動執行，更新台北樣教會主日信息表格。
電腦關機時錯過排程，開機後 launchd 會補跑一次。
"""

import os
import re
import json
import subprocess
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ── 設定 ──────────────────────────────────────────────────────────────
WEBSITE_DIR  = Path.home() / "documents" / "website"
LOG_FILE     = WEBSITE_DIR / "logs" / "update_sunday.log"
ENV_FILE     = Path.home() / ".hermes" / ".env"
CHANNEL_URL  = "https://www.youtube.com/@JesuswayTaipei/streams"

# ── Logging ───────────────────────────────────────────────────────────
def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logging.basicConfig(level=logging.INFO, handlers=[fh, sh])

# ── 環境變數 ──────────────────────────────────────────────────────────
def load_env():
    if not ENV_FILE.exists():
        return
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# ── YouTube 抓取 ──────────────────────────────────────────────────────
def fetch_latest_sunday():
    """抓最新 20 筆直播，回傳第一筆主日信息的 (date, raw_title, video_id)"""
    logging.info("抓取 YouTube 頻道直播列表")
    r = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--playlist-end", "20",
         "--print", "%(id)s", CHANNEL_URL],
        capture_output=True, text=True, timeout=60
    )
    ids = [i.strip() for i in r.stdout.strip().split("\n") if i.strip()]

    for vid in ids:
        r = subprocess.run(
            ["yt-dlp", "--skip-download", "--print", "%(upload_date)s|%(title)s",
             f"https://www.youtube.com/watch?v={vid}"],
            capture_output=True, text=True, timeout=30
        )
        line = r.stdout.strip()
        if "|" not in line:
            continue
        date_str, title = line.split("|", 1)
        # 只保留主日信息，排除樣青講堂
        if "主日" in title and "樣青講堂" not in title:
            date_fmt = f"{date_str[:4]}.{date_str[4:6]}.{date_str[6:8]}"
            logging.info(f"最新主日信息：{date_fmt} | {title[:40]}")
            return date_fmt, title.strip(), vid

    logging.warning("找不到新的主日信息")
    return None

# ── 標題與講員解析 ────────────────────────────────────────────────────
def parse_title_speaker(raw_title):
    """從 YouTube 標題解析題目與講員"""
    # 移除 hashtag
    raw = re.sub(r"#\S+", "", raw_title).strip()
    parts = [p.strip() for p in raw.split("|") if p.strip()]

    # 過濾教會/頻道標籤
    noise_keywords = ["台北樣線上主日", "台北樣教會", "台北樣"]
    clean = [p for p in parts if not any(n in p for n in noise_keywords)]

    title = clean[0] if clean else raw
    # 移除標題中多餘空白
    title = re.sub(r"\s{2,}", " ", title).strip()

    # 講員：clean 最後一項（若有）
    speaker = clean[-1] if len(clean) > 1 else ""
    # 移除括號內說明
    speaker = re.sub(r"（.*?）|\(.*?\)", "", speaker).strip()
    speaker = re.sub(r"\s{2,}", " ", speaker).strip()

    return title, speaker

# ── Gemini 翻譯 ───────────────────────────────────────────────────────
def translate_to_english(zh_title, zh_speaker):
    """用 Gemini 翻譯標題與講員，失敗回傳 (None, None)"""
    try:
        import google.generativeai as genai
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            logging.warning("GEMINI_API_KEY 未設定，跳過翻譯")
            return None, None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = (
            "請將台灣教會主日信息的標題與講員名譯成英文。\n"
            "只回傳 JSON，格式：{\"title\": \"...\", \"speaker\": \"...\"}\n"
            f"標題：{zh_title}\n"
            f"講員：{zh_speaker}"
        )
        resp = model.generate_content(prompt)
        text = re.sub(r"```json|```", "", resp.text).strip()
        data = json.loads(text)
        return data.get("title", ""), data.get("speaker", "")
    except Exception as e:
        logging.error(f"Gemini 翻譯失敗：{e}", exc_info=True)
        return None, None

# ── HTML 行產生 ───────────────────────────────────────────────────────
def build_row(date, title, speaker, video_id, watch_label="觀看 →"):
    return (
        f'                        <tr class="hover:bg-yellow-50 transition">\n'
        f'                            <td class="px-5 py-4 text-gray-500 whitespace-nowrap">{date}</td>\n'
        f'                            <td class="px-5 py-4 font-medium text-gray-800">{title}</td>\n'
        f'                            <td class="px-5 py-4 text-gray-600 hidden md:table-cell">{speaker}</td>\n'
        f'                            <td class="px-5 py-4 text-center">'
        f'<a href="https://www.youtube.com/watch?v={video_id}" target="_blank" '
        f'class="inline-block bg-yellow-400 hover:bg-yellow-500 text-gray-800 text-xs font-semibold px-3 py-1.5 rounded-full transition">'
        f'{watch_label}</a></td>\n'
        f'                        </tr>\n'
    )

# ── HTML 更新 ─────────────────────────────────────────────────────────
def is_video_in_table(html_path, video_id):
    return video_id in html_path.read_text(encoding="utf-8")

def update_table(html_path, new_row):
    """在 tbody 頂端插入新行，移除最後一行（維持10筆）"""
    content = html_path.read_text(encoding="utf-8")

    # 插入位置：tbody 第一個換行後
    marker = '<tbody class="bg-white divide-y divide-gray-100">'
    pos = content.find(marker)
    if pos == -1:
        logging.error(f"找不到 tbody：{html_path.name}")
        return False
    insert_pos = content.find("\n", pos) + 1
    content = content[:insert_pos] + new_row + content[insert_pos:]

    # 移除最後一個 <tr>...</tr>
    last_end = content.rfind("</tr>") + len("</tr>")
    last_start = content.rfind('<tr class="hover:bg-yellow-50 transition">', 0, last_end)
    if last_start == -1:
        logging.error(f"找不到最後一個 <tr>：{html_path.name}")
        return False
    nl_before = content.rfind("\n", 0, last_start)
    content = content[:nl_before] + content[last_end:]

    html_path.write_text(content, encoding="utf-8")
    logging.info(f"已更新：{html_path.name}")
    return True

# ── Git Commit ────────────────────────────────────────────────────────
def git_commit(date, title_zh, en_fallback=False):
    note = "（英文標題暫用中文，請 push 前確認）" if en_fallback else ""
    msg = f"feat: 自動更新主日信息 {date}「{title_zh[:20]}」{note}"
    subprocess.run(["git", "-C", str(WEBSITE_DIR), "add", "sunday.html", "en/sunday.html"], check=True)
    subprocess.run(["git", "-C", str(WEBSITE_DIR), "commit", "-m", msg], check=True)
    logging.info(f"git commit：{msg}")

# ── 主流程 ────────────────────────────────────────────────────────────
def main():
    setup_logging()
    load_env()
    logging.info("=== update_sunday.py 開始 ===")

    result = fetch_latest_sunday()
    if not result:
        logging.info("無新主日信息，結束")
        return

    date, raw_title, video_id = result

    sunday_zh = WEBSITE_DIR / "sunday.html"
    if is_video_in_table(sunday_zh, video_id):
        logging.info(f"{video_id} 已在表格中，不需更新")
        return

    title_zh, speaker_zh = parse_title_speaker(raw_title)
    logging.info(f"中文 → 題目：{title_zh}  講員：{speaker_zh}")

    title_en, speaker_en = translate_to_english(title_zh, speaker_zh)
    en_fallback = not title_en
    if en_fallback:
        title_en, speaker_en = title_zh, speaker_zh
        logging.warning("英文版暫用中文標題，請 push 前手動確認")

    # 更新中文版
    row_zh = build_row(date, title_zh, speaker_zh, video_id, "觀看 →")
    update_table(sunday_zh, row_zh)

    # 更新英文版
    sunday_en = WEBSITE_DIR / "en" / "sunday.html"
    row_en = build_row(date, title_en, speaker_en, video_id, "Watch →")
    update_table(sunday_en, row_en)

    git_commit(date, title_zh, en_fallback)
    logging.info("=== 完成，請用 GitHub Desktop push ===")


if __name__ == "__main__":
    main()
