#!/usr/bin/env python3
"""抓取各站热榜，生成当天的数据快照 data/YYYY-MM-DD.json（仅使用标准库）。"""

from __future__ import annotations

import gzip
import html as htmllib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
TZ = timezone(timedelta(hours=8))
LIMIT = 10

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def request(url: str, headers: dict | None = None, timeout: int = 20,
            encoding: str = "utf-8") -> str:
    hdrs = {
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    hdrs.update(headers or {})
    last: Exception | None = None
    for _ in range(2):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
            return raw.decode(encoding, "ignore")
        except Exception as exc:  # noqa: BLE001 - 单个源失败不应中断整体抓取
            last = exc
            time.sleep(1)
    raise last  # type: ignore[misc]


def json_get(url: str, headers: dict | None = None) -> dict:
    return json.loads(request(url, headers))


def clean_text(value) -> str:
    text = re.sub(r"<[^>]+>", "", str(value or ""))
    return re.sub(r"\s+", " ", htmllib.unescape(text)).strip()


def codelife(node_id: str) -> list[dict]:
    """通过 codelife 热榜接口取数（微博 / 微信 / 抖音等）。"""
    data = json_get(f"https://api.codelife.cc/api/top/list?lang=cn&id={node_id}")
    items = []
    for row in data.get("data", []):
        title = clean_text(row.get("title"))
        if not title:
            continue
        items.append({
            "title": title,
            "url": row.get("link") or "",
            "hot": clean_text(row.get("hotValue")),
        })
        if len(items) >= LIMIT:
            break
    return items


def src_weibo() -> list[dict]:
    return codelife("KqndgxeLl9")


def src_zhihu() -> list[dict]:
    data = json_get("https://api.zhihu.com/topstory/hot-list?limit=50")
    items = []
    for row in data.get("data", []):
        target = row.get("target") or {}
        title = clean_text(target.get("title"))
        if not title:
            continue
        kind, qid = target.get("type"), target.get("id")
        if kind == "question":
            url = f"https://www.zhihu.com/question/{qid}"
        elif kind == "article":
            url = f"https://zhuanlan.zhihu.com/p/{qid}"
        else:
            url = target.get("url") or ""
        items.append({
            "title": title,
            "url": url,
            "hot": clean_text(row.get("detail_text")),
        })
        if len(items) >= LIMIT:
            break
    return items


def src_thepaper() -> list[dict]:
    data = json_get(
        "https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar",
        {"Referer": "https://www.thepaper.cn/"},
    )
    rows = (data.get("data") or {}).get("hotNews") or []
    items = []
    for row in rows:
        title = clean_text(row.get("name"))
        cont_id = row.get("contId")
        if not title or not cont_id:
            continue
        items.append({
            "title": title,
            "url": f"https://www.thepaper.cn/newsDetail_forward_{cont_id}",
            "hot": "",
        })
        if len(items) >= LIMIT:
            break
    return items


def src_sspai() -> list[dict]:
    root = ET.fromstring(request("https://sspai.com/feed"))
    items = []
    for node in root.findall("./channel/item"):
        title = clean_text(node.findtext("title"))
        link = (node.findtext("link") or "").split("?")[0]
        if not title or not link:
            continue
        items.append({"title": title, "url": link, "hot": ""})
        if len(items) >= LIMIT:
            break
    return items


def src_huxiu() -> list[dict]:
    return codelife("5VaobgvAj1")


def src_ifanr() -> list[dict]:
    root = ET.fromstring(request("https://www.ifanr.com/feed"))
    items = []
    for node in root.findall("./channel/item"):
        title = clean_text(node.findtext("title"))
        link = (node.findtext("link") or "").split("?")[0]
        if not title or not link:
            continue
        items.append({"title": title, "url": link, "hot": ""})
        if len(items) >= LIMIT:
            break
    return items


def src_github() -> list[dict]:
    return codelife("rYqoXQ8vOD")


def src_hackernews() -> list[dict]:
    data = json_get(
        "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=20")
    items = []
    for story in data.get("hits", []):
        title = clean_text(story.get("title"))
        if not title:
            continue
        points = story.get("points") or 0
        items.append({
            "title": title,
            "url": story.get("url")
            or f'https://news.ycombinator.com/item?id={story.get("objectID")}',
            "hot": f"{points} 分" if points else "",
        })
        if len(items) >= LIMIT:
            break
    return items


def src_devto() -> list[dict]:
    data = json_get(
        "https://dev.to/api/articles?top=1&per_page=20",
        {"Accept": "application/json"},
    )
    items = []
    for row in data if isinstance(data, list) else []:
        title = clean_text(row.get("title"))
        url = row.get("url") or ""
        if not title or not url:
            continue
        reactions = row.get("public_reactions_count") or 0
        items.append({
            "title": title,
            "url": url,
            "hot": f"{reactions} 赞" if reactions else "",
        })
        if len(items) >= LIMIT:
            break
    return items


SOURCES = [
    ("zhihu", "知乎热榜", "知", "#0084ff", "https://www.zhihu.com/hot", src_zhihu),
    ("thepaper", "澎湃新闻", "澎", "#e60012", "https://www.thepaper.cn/", src_thepaper),
    ("weibo", "微博热搜", "微", "#e6162d", "https://s.weibo.com/top/summary", src_weibo),
    ("ifanr", "爱范儿", "爱", "#ff5a36", "https://www.ifanr.com/", src_ifanr),
    ("sspai", "少数派", "少", "#1f8aa8", "https://sspai.com/", src_sspai),
    ("huxiu", "虎嗅", "嗅", "#ff6a00", "https://www.huxiu.com/", src_huxiu),
    ("github", "GitHub 趋势", "GH", "#24292f", "https://github.com/trending", src_github),
    ("hackernews", "Hacker News", "HN", "#ff6600", "https://news.ycombinator.com/", src_hackernews),
    ("devto", "dev.to", "dev", "#6366f1", "https://dev.to/", src_devto),
]


def main() -> int:
    now = datetime.now(TZ)
    result = {
        "date": now.strftime("%Y-%m-%d"),
        "generated_at": now.isoformat(timespec="seconds"),
        "time": now.strftime("%H:%M"),
        "sources": [],
    }
    failed = 0
    for sid, name, icon, color, home, handler in SOURCES:
        error = ""
        try:
            items = handler()
            if not items:
                raise RuntimeError("没有抓到条目")
            ok = True
        except Exception as exc:  # noqa: BLE001 - 记录失败但继续其他源
            items, ok, error = [], False, str(exc)[:200]
            failed += 1
        result["sources"].append({
            "id": sid,
            "name": name,
            "icon": icon,
            "color": color,
            "home": home,
            "ok": ok,
            "error": error,
            "items": items,
        })
        print(f"[{'ok' if ok else 'FAIL'}] {name}: {len(items)} 条 {error}",
              file=sys.stderr)

    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f'{result["date"]}.json')
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(path)
    return 0 if failed < len(SOURCES) else 1


if __name__ == "__main__":
    sys.exit(main())
