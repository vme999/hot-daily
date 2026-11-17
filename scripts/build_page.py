#!/usr/bin/env python3
"""把每日快照渲染为自包含的静态页面：site/index.html（日报目录）与 site/archive/YYYY-MM-DD.html。"""

from __future__ import annotations

import glob
import html
import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
SITE_DIR = os.path.join(ROOT, "site")
ARCHIVE_DIR = os.path.join(SITE_DIR, "archive")
WEEKDAYS = "一二三四五六日"

CSS = """
:root {
  --bg: #f1f2f5;
  --card: #ffffff;
  --text: #1c2026;
  --muted: #8a919e;
  --line: #edeff2;
  --hover: #f6f7f9;
  --accent: #e5484d;
  --rank: #b9c0cb;
  --shadow: 0 1px 2px rgba(16, 24, 40, .04), 0 8px 24px rgba(16, 24, 40, .045);
  --radius: 12px;
}
[data-theme="dark"] {
  --bg: #14161b;
  --card: #1e2129;
  --text: #e7e9ee;
  --muted: #818896;
  --line: #2a2e38;
  --hover: #272b35;
  --accent: #ff5d5d;
  --rank: #5b6270;
  --shadow: 0 1px 2px rgba(0, 0, 0, .3), 0 10px 30px rgba(0, 0, 0, .2);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  background-color: var(--bg);
  background-image: radial-gradient(1100px 380px at 50% -120px, rgba(229, 72, 77, .07), transparent 70%);
  background-repeat: no-repeat;
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  transition: background-color .25s ease, color .25s ease;
}
.topbar {
  max-width: 1440px;
  margin: 0 auto;
  padding: 24px 24px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.brand { display: flex; align-items: center; gap: 12px; min-width: 0; }
.logo {
  width: 40px; height: 40px; flex: none;
  display: grid; place-items: center;
  border-radius: 12px;
  background: linear-gradient(135deg, #ff6a5e, #e5484d 55%, #c9282d);
  color: #fff;
  font-size: 19px; font-weight: 800;
  box-shadow: 0 6px 16px rgba(229, 72, 77, .28);
}
.brand-text { min-width: 0; }
.brand-text h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: .2px;
}
.brand-text p {
  margin: 3px 0 0;
  font-size: 12px;
  color: var(--muted);
}
.theme-toggle {
  flex: none;
  border: 1px solid var(--line);
  background: var(--card);
  color: var(--text);
  font-size: 12.5px;
  font-weight: 500;
  padding: 8px 14px;
  border-radius: 999px;
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: border-color .18s ease, color .18s ease, background-color .25s ease;
}
.theme-toggle:hover { border-color: var(--accent); color: var(--accent); }
.grid {
  max-width: 1440px;
  margin: 0 auto;
  padding: 8px 24px 34px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  align-items: start;
}
.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 13px 14px 9px;
  transition: background-color .25s ease, border-color .18s ease,
    transform .18s ease, box-shadow .18s ease;
}
.card:hover {
  transform: translateY(-2px);
  border-color: rgba(229, 72, 77, .28);
}
.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 2px 7px;
}
.badge {
  width: 24px; height: 24px; flex: none;
  display: grid; place-items: center;
  border-radius: 7px;
  background: var(--brand, var(--accent));
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: -.2px;
}
.badge.wide { font-size: 9.5px; }
.card-head h2 {
  margin: 0;
  font-size: 14px;
  font-weight: 650;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-meta {
  margin-left: auto;
  flex: none;
  font-size: 11px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.list { list-style: none; margin: 0; padding: 0; }
.list li + li { border-top: 1px solid var(--line); }
.list a {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 4px;
  border-radius: 7px;
  color: var(--text);
  font-size: 13px;
  line-height: 1.45;
  text-decoration: none;
  transition: background-color .15s ease;
}
.list a:hover { background: var(--hover); }
.list a:hover .title { color: var(--accent); }
.rank {
  flex: none;
  width: 15px;
  text-align: center;
  font-size: 12px;
  color: var(--rank);
  font-variant-numeric: tabular-nums;
}
.list li:nth-child(-n+3) .rank {
  color: var(--accent);
  font-weight: 700;
}
.title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  transition: color .15s ease;
}
.empty {
  padding: 20px 6px 18px;
  text-align: center;
  font-size: 12.5px;
  line-height: 1.8;
  color: var(--muted);
}
.empty a { color: var(--accent); text-decoration: none; }
.empty a:hover { text-decoration: underline; }
.footer {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px 38px;
  text-align: center;
  font-size: 11.5px;
  line-height: 1.9;
  color: var(--muted);
}
.footer a {
  color: var(--muted);
  text-decoration: none;
  border-bottom: 1px dotted currentColor;
}
.footer a:hover { color: var(--accent); }
.timeline {
  max-width: 900px;
  margin: 0 auto;
  padding: 10px 24px 44px;
}
.month + .month { margin-top: 28px; }
.month-title {
  margin: 0 0 10px;
  padding-left: 2px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .8px;
  color: var(--muted);
}
.entries {
  list-style: none;
  margin: 0;
  padding: 0;
  border-left: 2px solid var(--line);
}
.entries li { position: relative; padding-left: 16px; }
.entries li::before {
  content: "";
  position: absolute;
  left: -5px;
  top: 26px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--rank);
}
.entries li:first-child::before { background: var(--accent); }
.entry {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 8px;
  padding: 13px 16px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  color: var(--text);
  text-decoration: none;
  transition: border-color .18s ease, transform .18s ease, background-color .25s ease;
}
.entry:hover {
  border-color: rgba(229, 72, 77, .32);
  transform: translateX(3px);
}
.entry-date { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.entry-date b { font-size: 15px; font-weight: 650; }
.entry-date span { font-size: 11.5px; color: var(--muted); }
.entry-meta {
  margin-left: auto;
  flex: none;
  font-size: 11.5px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.entry-meta .tag { margin-right: 6px; color: var(--accent); font-weight: 600; }
.entry-arrow {
  flex: none;
  font-size: 13px;
  color: var(--muted);
  transition: color .18s ease, transform .18s ease;
}
.entry:hover .entry-arrow { color: var(--accent); transform: translateX(2px); }
a:focus-visible, .theme-toggle:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
@media (max-width: 1180px) {
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 680px) {
  .topbar { padding: 18px 16px 10px; }
  .brand-text h1 { font-size: 16px; }
  .grid { grid-template-columns: 1fr; padding: 6px 16px 26px; gap: 12px; }
  .footer { padding: 0 16px 28px; }
  .timeline { padding: 6px 16px 30px; }
  .entry { padding: 12px 14px; }
  .entry-meta { display: none; }
  .title {
    white-space: normal;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  .list a { align-items: flex-start; }
}
"""

THEME_INIT = """(function () {
  try {
    var saved = localStorage.getItem("hot-theme");
    var theme = saved || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
  } catch (e) {}
})();"""

THEME_TOGGLE_JS = """(function () {
  var root = document.documentElement;
  var btn = document.getElementById("themeToggle");
  function label() {
    btn.textContent = root.getAttribute("data-theme") === "dark" ? "☀️ 浅色" : "🌙 深色";
  }
  btn.addEventListener("click", function () {
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("hot-theme", next); } catch (e) {}
    label();
  });
  label();

  // 在 IDE 预览等受限 iframe 中，浏览器会拦截新标签页，改为当前框架内跳转
  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest("a[href^='http']");
    if (!link || window.self === window.top) return;
    event.preventDefault();
    window.location.href = link.href;
  });
})();"""

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>%%TITLE%%</title>
<script>%%THEME_INIT%%</script>
<style>%%CSS%%</style>
</head>
<body>
<header class="topbar">
  <div class="brand">
    <div class="logo">热</div>
    <div class="brand-text">
      <h1>热榜日报</h1>
      <p>%%DATE_LABEL%% · %%TIME%% 更新</p>
    </div>
  </div>
  <button id="themeToggle" class="theme-toggle" type="button" aria-label="切换浅色 / 深色模式">🌙 深色</button>
</header>
<main class="grid" aria-label="今日热榜">
%%CARDS%%
</main>
%%FOOTER%%
<script>%%THEME_JS%%</script>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>%%TITLE%%</title>
<script>%%THEME_INIT%%</script>
<style>%%CSS%%</style>
</head>
<body>
<header class="topbar">
  <div class="brand">
    <div class="logo">热</div>
    <div class="brand-text">
      <h1>热榜日报</h1>
      <p>共 %%COUNT%% 期 · 每日 07:30 更新</p>
    </div>
  </div>
  <button id="themeToggle" class="theme-toggle" type="button" aria-label="切换浅色 / 深色模式">🌙 深色</button>
</header>
<main class="timeline" aria-label="日报目录">
%%ENTRIES%%
</main>
<script>%%THEME_JS%%</script>
</body>
</html>
"""


def escape(value) -> str:
    return html.escape(str(value or ""), quote=True)


def render_card(source: dict, time_label: str) -> str:
    icon = escape(source.get("icon"))
    wide = " wide" if len(str(source.get("icon") or "")) > 1 else ""
    rows = []
    for index, item in enumerate(source.get("items") or [], 1):
        rows.append(
            '<li><a href="{url}" target="_blank" rel="noopener noreferrer">'
            '<span class="rank">{rank}</span>'
            '<span class="title" title="{title}">{title}</span>'
            "</a></li>".format(
                url=escape(item.get("url")),
                rank=index,
                title=escape(item.get("title")),
            )
        )
    if rows:
        body = "".join(rows)
    else:
        body = (
            '<li class="empty">今天没有抓到内容<br>'
            f'<a href="{escape(source.get("home"))}" target="_blank" '
            'rel="noopener noreferrer">去原站看看 →</a></li>'
        )
    return (
        '<section class="card">'
        '<div class="card-head">'
        f'<span class="badge{wide}" style="--brand:{escape(source.get("color"))}">{icon}</span>'
        f'<h2>{escape(source.get("name"))}</h2>'
        f'<span class="card-meta">{escape(time_label)}</span>'
        "</div>"
        f'<ol class="list">{body}</ol>'
        "</section>"
    )


def data_files() -> list[str]:
    return sorted(glob.glob(os.path.join(DATA_DIR, "*.json")), reverse=True)


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def archive_record(data: dict) -> dict:
    day = datetime.strptime(data["date"], "%Y-%m-%d")
    sources = data.get("sources") or []
    return {
        "date": data["date"],
        "month": day.month,
        "day": day.day,
        "weekday": WEEKDAYS[day.weekday()],
        "sources": len(sources),
        "items": sum(len(s.get("items") or []) for s in sources),
    }


def render_index(records: list[dict]) -> str:
    records = sorted(records, key=lambda r: r["date"], reverse=True)
    newest = records[0]["date"] if records else ""
    groups: dict[str, list[dict]] = {}
    for record in records:
        groups.setdefault(record["date"][:7], []).append(record)

    sections = []
    for year_month, rows in groups.items():
        year, month = year_month.split("-")
        entries = []
        for record in rows:
            tag = '<span class="tag">最新</span>' if record["date"] == newest else ""
            entries.append(
                '<li><a class="entry" href="archive/{date}.html">'
                '<span class="entry-date"><b>{month}月{day}日</b>'
                "<span>星期{weekday}</span></span>"
                '<span class="entry-meta">{tag}{sources} 个板块 · {items} 条</span>'
                '<span class="entry-arrow">→</span>'
                "</a></li>".format(tag=tag, **record)
            )
        sections.append(
            f'<section class="month"><h2 class="month-title">{year} 年 {int(month)} 月</h2>'
            f'<ol class="entries">{"".join(entries)}</ol></section>'
        )

    replacements = {
        "%%TITLE%%": "热榜日报 · 日报目录",
        "%%CSS%%": CSS,
        "%%THEME_INIT%%": THEME_INIT,
        "%%THEME_JS%%": THEME_TOGGLE_JS,
        "%%COUNT%%": str(len(records)),
        "%%ENTRIES%%": "".join(sections),
    }
    page = INDEX_TEMPLATE
    for token, value in replacements.items():
        page = page.replace(token, value)
    return page


def render(data: dict, archive: bool) -> str:
    day = datetime.strptime(data["date"], "%Y-%m-%d")
    date_label = f"{day.year}年{day.month}月{day.day}日 星期{WEEKDAYS[day.weekday()]}"
    cards = "\n".join(render_card(s, data.get("time", "")) for s in data["sources"])
    archive_link = (
        '<footer class="footer"><p><a href="../index.html">← 返回日报目录</a></p></footer>'
        if archive else ""
    )
    replacements = {
        "%%TITLE%%": f"热榜日报 · {day.month}月{day.day}日",
        "%%CSS%%": CSS,
        "%%THEME_INIT%%": THEME_INIT,
        "%%THEME_JS%%": THEME_TOGGLE_JS,
        "%%DATE_LABEL%%": date_label,
        "%%TIME%%": data.get("time", ""),
        "%%CARDS%%": cards,
        "%%FOOTER%%": archive_link,
    }
    page = TEMPLATE
    for token, value in replacements.items():
        page = page.replace(token, value)
    return page


def write_archive(data: dict) -> str:
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    path = os.path.join(ARCHIVE_DIR, f'{data["date"]}.html')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render(data, archive=True))
    return path


def write_index(records: list[dict]) -> str:
    path = os.path.join(SITE_DIR, "index.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_index(records))
    return path


def main() -> int:
    only_date = None
    if len(sys.argv) >= 3 and sys.argv[1] == "--date":
        only_date = sys.argv[2]

    if only_date:
        path = os.path.join(DATA_DIR, f"{only_date}.json")
        if not os.path.exists(path):
            raise SystemExit(f"没有找到数据文件：{path}")
        print(write_archive(load_json(path)))
    else:
        files = data_files()
        if not files:
            raise SystemExit("没有数据文件，请先运行 scripts/fetch_data.py")
        for path in files:
            data = load_json(path)
            # 以数据中的日期为准，文件名仅用于排序
            data["date"] = data.get("date") or os.path.basename(path)[:-5]
            print(write_archive(data))

    records = [archive_record(load_json(path)) for path in data_files()]
    print(write_index(records))
    return 0


if __name__ == "__main__":
    sys.exit(main())
