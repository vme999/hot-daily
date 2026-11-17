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
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148"
)
DOUBAN_HEADERS = {"User-Agent": MOBILE_UA, "Referer": "https://m.douban.com/"}


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


def post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "User-Agent": UA,
        "Content-Type": "application/json",
        "Referer": "https://juejin.cn/",
    }
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8", "ignore"))


def clean_text(value) -> str:
    text = re.sub(r"<[^>]+>", "", str(value or ""))
    return re.sub(r"\s+", " ", htmllib.unescape(text)).strip()


def codelife(node_id: str) -> list[dict]:
    """通过 codelife 热榜接口取数（微博 / 虎扑 / IT之家）。"""
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


def src_douban() -> list[dict]:
    """豆瓣没有公开热榜，这里汇总当前热门小组的讨论并按回应数排序。"""
    feed = json_get(
        "https://m.douban.com/rexxar/api/v2/group/explore?start=0&count=20",
        DOUBAN_HEADERS,
    )
    groups: list[dict] = []
    for block in feed.get("feed", []):
        if block.get("module") == "top20_groups":
            groups = block.get("groups") or []
    groups = sorted(groups, key=lambda g: g.get("member_count") or 0,
                    reverse=True)[:5]

    rows, seen = [], set()
    for group in groups:
        gid = group.get("id")
        try:
            data = json_get(
                f"https://m.douban.com/rexxar/api/v2/group/{gid}/topics"
                "?start=0&count=20&sortby=hot",
                {"User-Agent": MOBILE_UA,
                 "Referer": f"https://m.douban.com/group/{gid}/"},
            )
        except Exception:  # noqa: BLE001 - 单个小组失败可忽略
            continue
        for topic in data.get("topics", []):
            title = clean_text(topic.get("title"))
            if not title or title in seen:
                continue
            seen.add(title)
            rows.append({
                "title": title,
                "url": (topic.get("url") or "").split("?")[0],
                "comments": topic.get("comments_count") or 0,
            })
        time.sleep(0.2)

    rows.sort(key=lambda r: r["comments"], reverse=True)
    return [{
        "title": row["title"],
        "url": row["url"],
        "hot": f'{row["comments"]} 回应' if row["comments"] else "",
    } for row in rows[:LIMIT]]


def src_weibo() -> list[dict]:
    return codelife("KqndgxeLl9")


def src_toutiao() -> list[dict]:
    data = json_get(
        "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc")
    items = []
    for row in data.get("data", []):
        title = clean_text(row.get("Title"))
        if not title:
            continue
        items.append({"title": title, "url": row.get("Url") or "", "hot": ""})
        if len(items) >= LIMIT:
            break
    return items


def src_bilibili() -> list[dict]:
    data = json_get(
        "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all")
    videos = (data.get("data") or {}).get("list") or []
    items = []
    for video in videos:
        title = clean_text(video.get("title"))
        if not title:
            continue
        views = (video.get("stat") or {}).get("view") or 0
        items.append({
            "title": title,
            "url": video.get("short_link_v2")
            or f"https://www.bilibili.com/video/{video.get('bvid')}",
            "hot": f"{views / 10000:.0f} 万" if views >= 10000 else str(views),
        })
        if len(items) >= LIMIT:
            break
    return items


def src_ithome() -> list[dict]:
    try:
        items = codelife("74Kvx59dkx")
        if items:
            return items
    except Exception:  # noqa: BLE001 - 回退到官方新闻列表
        pass
    data = json_get("https://api.ithome.com/json/newslist/news")
    rows = [n for n in data.get("newslist", []) if clean_text(n.get("title"))]
    rows.sort(key=lambda n: n.get("commentcount") or 0, reverse=True)
    return [{
        "title": clean_text(row.get("title")),
        "url": row.get("url") or "",
        "hot": f'{row.get("commentcount") or 0} 评',
    } for row in rows[:LIMIT]]


def src_zol() -> list[dict]:
    page = request("https://news.zol.com.cn/", encoding="gbk")
    pattern = re.compile(
        r'<a[^>]+href="((?:https?:)?//news\.zol\.com\.cn/\d+/\d+\.html)"'
        r"[^>]*>([\s\S]*?)</a>"
    )
    items, seen_url, seen_title = [], set(), set()
    for match in pattern.finditer(page):
        url = match.group(1)
        if url.startswith("//"):
            url = "https:" + url
        title = clean_text(match.group(2))
        if len(title) < 8 or url in seen_url or title in seen_title:
            continue
        seen_url.add(url)
        seen_title.add(title)
        items.append({"title": title, "url": url, "hot": ""})
        if len(items) >= LIMIT:
            break
    return items


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


def src_csdn() -> list[dict]:
    data = json.loads(request(
        "https://blog.csdn.net/phoenix/web/blog/hot-rank"
        "?page=0&pageSize=25&type=",
        {"Referer": "https://blog.csdn.net/"},
    ))
    items = []
    for row in data.get("data", []):
        title = clean_text(row.get("articleTitle"))
        url = row.get("articleDetailUrl") or ""
        if not title or not url:
            continue
        items.append({"title": title, "url": url, "hot": ""})
        if len(items) >= LIMIT:
            break
    return items


def src_huxiu() -> list[dict]:
    return codelife("5VaobgvAj1")


def src_smzdm() -> list[dict]:
    page = request("https://www.smzdm.com/jingxuan/",
                   {"User-Agent": MOBILE_UA})
    pattern = re.compile(
        r'articleid="(\d+)"[\s\S]{0,1200}?'
        r'<div class="feed-hot-title">([\s\S]*?)</div>'
        r'[\s\S]{0,400}?<span class="z-highlight">([\s\S]*?)</span>'
    )
    items, seen = [], set()
    for article_id, title, price in pattern.findall(page):
        title = clean_text(title)
        if not title or article_id in seen:
            continue
        seen.add(article_id)
        price_text = clean_text(price)
        match = re.match(r"^[\d.]+\s*元", price_text)
        items.append({
            "title": title,
            "url": f"https://www.smzdm.com/p/{article_id}/",
            "hot": match.group(0) if match else price_text[:10],
        })
        if len(items) >= LIMIT:
            break
    return items


def src_juejin() -> list[dict]:
    data = post_json(
        "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed",
        {"id_type": 2, "client_type": 2608, "sort_type": 200,
         "cursor": "0", "limit": 20},
    )
    items = []
    for row in data.get("data", []):
        info = (row.get("item_info") or {}).get("article_info") or {}
        title = clean_text(info.get("title"))
        article_id = info.get("article_id")
        if not title or not article_id:
            continue
        items.append({
            "title": title,
            "url": f"https://juejin.cn/post/{article_id}",
            "hot": "",
        })
        if len(items) >= LIMIT:
            break
    return items


SOURCES = [
    ("zhihu", "知乎热榜", "知", "#0084ff", "https://www.zhihu.com/hot", src_zhihu),
    ("douban", "豆瓣热点", "豆", "#2f9c46", "https://www.douban.com/group/", src_douban),
    ("weibo", "微博热搜", "微", "#e6162d", "https://s.weibo.com/top/summary", src_weibo),
    ("toutiao", "今日头条", "头", "#f04142", "https://www.toutiao.com/", src_toutiao),
    ("bilibili", "B站日榜", "B", "#00a1d6", "https://www.bilibili.com/v/popular/rank/all", src_bilibili),
    ("ithome", "IT之家", "IT", "#d22222", "https://www.ithome.com/", src_ithome),
    ("zol", "中关村在线", "Z", "#0b6fc2", "https://news.zol.com.cn/", src_zol),
    ("ifanr", "爱范儿", "爱", "#ff5a36", "https://www.ifanr.com/", src_ifanr),
    ("csdn", "CSDN", "C", "#fc5531", "https://blog.csdn.net/", src_csdn),
    ("huxiu", "虎嗅", "嗅", "#ff6a00", "https://www.huxiu.com/", src_huxiu),
    ("smzdm", "值得买热门", "值", "#e93b3d", "https://www.smzdm.com/jingxuan/", src_smzdm),
    ("juejin", "掘金", "掘", "#1e80ff", "https://juejin.cn/", src_juejin),
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
