# -*- coding: utf-8 -*-
"""Парсинг публичного Telegram-канала через веб (t.me/s/username)."""
import re
import time
import requests
from bs4 import BeautifulSoup

BASE = "https://t.me"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}


def normalize_username(s: str) -> str:
    s = (s or "").strip().lstrip("@")
    for prefix in ("https://t.me/s/", "http://t.me/s/", "t.me/s/", "https://t.me/", "t.me/"):
        if s.lower().startswith(prefix):
            s = s[len(prefix) :].split("?")[0].split("/")[0]
            break
    return s or ""


def parse_post(wrap) -> dict | None:
    msg = wrap.find(class_="tgme_widget_message")
    if not msg:
        return None
    data_post = msg.get("data-post")
    post_id = data_post.split("/")[-1].strip() if data_post and "/" in data_post else None
    text_blocks = wrap.find_all(class_="tgme_widget_message_text")
    text = ""
    for bl in text_blocks:
        t = bl.get_text(separator=" ", strip=True)
        if t and not t.startswith("Channel ") and "pinned" not in t.lower()[:20]:
            text = t
            break
    if not text and text_blocks:
        text = text_blocks[0].get_text(separator=" ", strip=True)
    date_el = wrap.find(class_="tgme_widget_message_date")
    date_str = ""
    if date_el:
        time_el = date_el.find("time")
        date_str = time_el["datetime"] if time_el and time_el.get("datetime") else date_el.get_text(strip=True)
    return {"id": post_id, "date": date_str, "text": text}


def get_page_posts(session: requests.Session, channel: str, before: str | None = None) -> tuple[list[dict], str | None]:
    url = f"{BASE}/s/{channel}"
    params = {"before": before} if before else {}
    r = session.get(url, headers=HEADERS, params=params or None, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    history = soup.find(class_="tgme_channel_history")
    if not history:
        return [], None
    wraps = history.find_all(class_="tgme_widget_message_wrap", recursive=False)
    posts = []
    oldest_id = None
    for w in wraps:
        p = parse_post(w)
        if p and (p["text"] or p["id"]):
            posts.append(p)
            if p["id"]:
                oldest_id = p["id"]
    next_before = None
    jump = history.find(class_="tgme_channel_history_jump")
    if jump and jump.get("href"):
        m = re.search(r"[?&]before=(\d+)", jump["href"])
        if m:
            next_before = m.group(1)
    if not next_before and oldest_id:
        next_before = oldest_id
    return posts, next_before


def fetch_posts(channel: str, limit: int = 10, delay: float = 0.4) -> list[dict]:
    channel = normalize_username(channel)
    if not channel:
        return []
    session = requests.Session()
    all_posts = []
    before = None
    while len(all_posts) < limit:
        posts, next_before = get_page_posts(session, channel, before=before)
        if not posts:
            break
        all_posts.extend(posts)
        if not next_before or next_before == before:
            break
        before = next_before
        time.sleep(delay)
    return all_posts[:limit]
