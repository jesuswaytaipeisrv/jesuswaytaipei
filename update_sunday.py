#!/usr/bin/env python3
"""
update_sunday.py
每週四 21:00 由 launchd 自動執行，更新台北樣教會主日信息與樣青講堂表格。
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

# ── YouTube 抓取（一次掃描同時找主日與樣青）────────────────────────────
def fetch_latest_streams(max_items=25):
    """
    抓最新 max_items 筆直播，一次掃描回傳：
      latest_sunday: (date_fmt, raw_title, video_id) 或 None
      latest_youth:  (date_fmt, raw_title, video_id) 或 None
    """
    logging.info("抓取 YouTube 頻道直播列表")
    r = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--playlist-end", str(max_items),
         "--print", "%(id)s", CHANNEL_URL],
        capture_output=True, text=True, timeout=60
    )
    ids = [i.strip() for i in r.stdout.strip().split("\n") if i.strip()]

    latest_sunday = None
    latest_youth  = None

    for vid in ids:
        if latest_sunday and latest_youth:
            break
        r = subprocess.run(
            ["yt-dlp", "--skip-download", "--print", "%(upload_date)s|%(title)s",
             f"https://www.youtube.com/watch?v={vid}"],
            capture_output=True, text=True, timeout=30
        )
        line = r.stdout.strip()
        if "|" not in line:
            continue
        date_str, title = line.split("|", 1)
        date_fmt = f"{date_str[:4]}.{date_str[4:6]}.{date_str[6:8]}"
        title = title.strip()

        if "樣青講堂" in title and latest_youth is None:
            logging.info(f"最新樣青講堂：{date_fmt} | {title[:40]}")
            latest_youth = (date_fmt, title, vid)
        elif "主日" in title and "樣青講堂" not in title and latest_sunday is None:
            logging.info(f"最新主日信息：{date_fmt} | {title[:40]}")
            latest_sunday = (date_fmt, title, vid)

    if not latest_sunday:
        logging.warning("找不到新的主日信息")
    if not latest_youth:
        logging.warning("找不到新的樣青講堂")
    return latest_sunday, latest_youth

# ── 主日：標題與講員解析 ──────────────────────────────────────────────
def parse_sunday_title_speaker(raw_title):
    """從主日信息 YouTube 標題解析題目與講員"""
    raw = re.sub(r"#\S+", "", raw_title).strip()
    parts = [p.strip() for p in raw.split("|") if p.strip()]

    noise_keywords = ["台北樣線上主日", "台北樣教會", "台北樣"]
    clean = [p for p in parts if not any(n in p for n in noise_keywords)]

    title = re.sub(r"\s{2,}", " ", clean[0]).strip() if clean else raw
    speaker = ""
    if len(clean) > 1:
        speaker = re.sub(r"（.*?）|\(.*?\)", "", clean[-1]).strip()
        speaker = re.sub(r"\s{2,}", " ", speaker).strip()
    return title, speaker

# ── 樣青：主題與來賓解析 ──────────────────────────────────────────────
def parse_youth_title_guest(raw_title):
    """從樣青講堂 YouTube 標題解析主題與來賓"""
    raw = re.sub(r"#\S+", "", raw_title).strip()
    # 移除《樣青講堂》前綴（含全形書名號與空白）
    raw = re.sub(r"《樣青講堂》\s*", "", raw).strip()
    raw = re.sub(r"\|", "|", raw)  # 全形豎線統一為半形
    parts = [p.strip() for p in re.split(r"[|｜]", raw) if p.strip()]

    title = re.sub(r"\s{2,}", " ", parts[0]).strip() if parts else raw
    guest = re.sub(r"\s{2,}", " ", parts[1]).strip() if len(parts) > 1 else ""
    return title, guest

# ── Gemini 翻譯 ───────────────────────────────────────────────────────
def translate_to_english(zh_title, zh_person, context="主日信息"):
    """用 Gemini 翻譯標題與人名，失敗回傳 (None, None)"""
    try:
        import google.generativeai as genai
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            logging.warning("GEMINI_API_KEY 未設定，跳過翻譯")
            return None, None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        if context == "主日信息":
            key2 = "speaker"
            prompt = (
                "請將台灣教會主日信息的標題與講員名譯成英文。\n"
                "只回傳 JSON，格式：{\"title\": \"...\", \"speaker\": \"...\"}\n"
                f"標題：{zh_title}\n"
                f"講員：{zh_person}"
            )
        else:  # 樣青講堂
            key2 = "guest"
            prompt = (
                "請將台灣教會樣青講堂的演講主題與來賓職稱名稱譯成英文。\n"
                "只回傳 JSON，格式：{\"title\": \"...\", \"guest\": \"...\"}\n"
                f"主題：{zh_title}\n"
                f"來賓：{zh_person}"
            )

        resp = model.generate_content(prompt)
        text = re.sub(r"```json|```", "", resp.text).strip()
        data = json.loads(text)
        return data.get("title", ""), data.get(key2, "")
    except Exception as e:
        logging.error(f"Gemini 翻譯失敗（{context}）：{e}", exc_info=True)
        return None, None

# ── HTML 行產生 ───────────────────────────────────────────────────────
def build_row(date, title, person, video_id, watch_label="觀看 →"):
    return (
        f'                        <tr class="hover:bg-yellow-50 transition">\n'
        f'                            <td class="px-5 py-4 text-gray-500 whitespace-nowrap">{date}</td>\n'
        f'                            <td class="px-5 py-4 font-medium text-gray-800">{title}</td>\n'
        f'                            <td class="px-5 py-4 text-gray-600 hidden md:table-cell">{person}</td>\n'
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

    marker = '<tbody class="bg-white divide-y divide-gray-100">'
    pos = content.find(marker)
    if pos == -1:
        logging.error(f"找不到 tbody：{html_path.name}")
        return False
    insert_pos = content.find("\n", pos) + 1
    content = content[:insert_pos] + new_row + content[insert_pos:]

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
def git_commit(updated_files, commit_msg):
    subprocess.run(["git", "-C", str(WEBSITE_DIR), "add"] + updated_files, check=True)
    subprocess.run(["git", "-C", str(WEBSITE_DIR), "commit", "-m", commit_msg], check=True)
    logging.info(f"git commit：{commit_msg}")

# ── 主流程 ────────────────────────────────────────────────────────────
def main():
    setup_logging()
    load_env()
    logging.info("=== update_sunday.py 開始 ===")

    latest_sunday, latest_youth = fetch_latest_streams()

    updated_files = []
    commit_parts  = []

    # ── 主日信息更新 ──────────────────────────────────────────────────
    if latest_sunday:
        date, raw_title, video_id = latest_sunday
        sunday_zh = WEBSITE_DIR / "sunday.html"

        if is_video_in_table(sunday_zh, video_id):
            logging.info(f"主日 {video_id} 已在表格中，跳過")
        else:
            title_zh, speaker_zh = parse_sunday_title_speaker(raw_title)
            logging.info(f"主日中文 → 題目：{title_zh}  講員：{speaker_zh}")

            title_en, speaker_en = translate_to_english(title_zh, speaker_zh, "主日信息")
            en_fallback = not title_en
            if en_fallback:
                title_en, speaker_en = title_zh, speaker_zh
                logging.warning("主日英文版暫用中文標題，請 push 前手動確認")

            update_table(sunday_zh, build_row(date, title_zh, speaker_zh, video_id, "觀看 →"))
            update_table(WEBSITE_DIR / "en" / "sunday.html",
                         build_row(date, title_en, speaker_en, video_id, "Watch →"))

            updated_files += ["sunday.html", "en/sunday.html"]
            note = "（英文暫用中文）" if en_fallback else ""
            commit_parts.append(f"主日 {date}「{title_zh[:15]}」{note}")

    # ── 樣青講堂更新 ──────────────────────────────────────────────────
    if latest_youth:
        date, raw_title, video_id = latest_youth
        youth_zh = WEBSITE_DIR / "youth.html"

        if is_video_in_table(youth_zh, video_id):
            logging.info(f"樣青 {video_id} 已在表格中，跳過")
        else:
            title_zh, guest_zh = parse_youth_title_guest(raw_title)
            logging.info(f"樣青中文 → 主題：{title_zh}  來賓：{guest_zh}")

            title_en, guest_en = translate_to_english(title_zh, guest_zh, "樣青講堂")
            en_fallback = not title_en
            if en_fallback:
                title_en, guest_en = title_zh, guest_zh
                logging.warning("樣青英文版暫用中文，請 push 前手動確認")

            update_table(youth_zh, build_row(date, title_zh, guest_zh, video_id, "觀看 →"))
            update_table(WEBSITE_DIR / "en" / "youth.html",
                         build_row(date, title_en, guest_en, video_id, "Watch →"))

            updated_files += ["youth.html", "en/youth.html"]
            note = "（英文暫用中文）" if en_fallback else ""
            commit_parts.append(f"樣青 {date}「{title_zh[:15]}」{note}")

    # ── Git Commit ────────────────────────────────────────────────────
    if updated_files:
        msg = "feat: 自動更新 " + "、".join(commit_parts)
        git_commit(updated_files, msg)
        logging.info("=== 完成，請用 GitHub Desktop push ===")
    else:
        logging.info("=== 無更新，結束 ===")


if __name__ == "__main__":
    main()
