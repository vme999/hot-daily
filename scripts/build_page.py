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

BADGE_COLORS = {
    "知乎热榜": "#0A84FF",
    "澎湃新闻": "#FF9F0A",
    "微博热搜": "#FF453A",
    "爱范儿": "#BF5AF2",
    "少数派": "#1F8AA8",
    "虎嗅": "#34C759",
    "GitHub 趋势": "#FF2D92",
    "Hacker News": "#FF6A00",
    "dev.to": "#6366F1",
}

CSS = """
:root {
  --bg: #fbfbfd;
  --surface: #ffffff;
  --text: #1d1d1f;
  --muted: #6e6e73;
  --line: rgba(0, 0, 0, .08);
  --hover: rgba(0, 0, 0, .035);
  --accent: #0071e3;
  --accent-soft: rgba(0, 113, 227, .1);
  --radius: 20px;
  --shadow: 0 1px 2px rgba(0, 0, 0, .04);
}
[data-theme="dark"] {
  --bg: #000000;
  --surface: #1c1c1e;
  --text: #f5f5f7;
  --muted: #a1a1a6;
  --line: rgba(255, 255, 255, .1);
  --hover: rgba(255, 255, 255, .06);
  --accent: #2997ff;
  --accent-soft: rgba(41, 151, 255, .14);
  --shadow: none;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  min-height: 100vh;
  background-color: var(--bg);
  background-image:
    radial-gradient(42% 42% at 14% 6%, rgba(10, 132, 255, .16), transparent 70%),
    radial-gradient(36% 36% at 86% 14%, rgba(191, 90, 242, .12), transparent 70%),
    radial-gradient(46% 46% at 50% 104%, rgba(255, 159, 10, .10), transparent 70%);
  background-attachment: fixed;
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
    "Helvetica Neue", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  transition: background-color .3s ease, color .3s ease;
}
[data-theme="dark"] body {
  background-image:
    radial-gradient(42% 42% at 14% 6%, rgba(10, 132, 255, .22), transparent 70%),
    radial-gradient(36% 36% at 86% 14%, rgba(191, 90, 242, .18), transparent 70%),
    radial-gradient(46% 46% at 50% 104%, rgba(255, 159, 10, .12), transparent 70%);
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.theme-toggle {
  position: fixed;
  right: 24px;
  top: 24px;
  z-index: 30;
  appearance: none;
  width: 44px;
  height: 44px;
  padding: 0;
  display: grid;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, .6);
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255, 255, 255, .72), rgba(255, 255, 255, .42));
  -webkit-backdrop-filter: blur(22px) saturate(180%);
  backdrop-filter: blur(22px) saturate(180%);
  color: var(--text);
  box-shadow:
    0 10px 30px rgba(0, 0, 0, .12),
    inset 0 1px 0 rgba(255, 255, 255, .85);
  cursor: pointer;
  transition: transform .2s ease, border-color .2s ease, background-color .25s ease;
}
[data-theme="dark"] .theme-toggle {
  border-color: rgba(255, 255, 255, .16);
  background: linear-gradient(135deg, rgba(58, 58, 60, .66), rgba(28, 28, 30, .45));
  box-shadow:
    0 10px 30px rgba(0, 0, 0, .5),
    inset 0 1px 0 rgba(255, 255, 255, .18);
}
.theme-toggle:hover {
  transform: scale(1.06);
  border-color: rgba(255, 255, 255, .8);
}
@supports not (backdrop-filter: blur(1px)) {
  .theme-toggle,
  [data-theme="dark"] .theme-toggle { background: var(--surface); }
}
.theme-toggle svg { width: 20px; height: 20px; display: none; }
.theme-toggle .icon-moon { display: block; }
[data-theme="dark"] .theme-toggle .icon-moon { display: none; }
[data-theme="dark"] .theme-toggle .icon-sun { display: block; }
.hero {
  max-width: 1280px;
  margin: 0 auto;
  padding: 84px 28px 34px;
}
.eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .06em;
  color: var(--accent);
}
.hero h1 {
  margin: 10px 0 0;
  font-size: clamp(34px, 5.4vw, 56px);
  line-height: 1.07;
  letter-spacing: -.02em;
  font-weight: 700;
}
.hero .sub {
  margin: 14px 0 0;
  font-size: 17px;
  line-height: 1.5;
  color: var(--muted);
  letter-spacing: -.01em;
}
.grid {
  max-width: 1280px;
  margin: 0 auto;
  padding: 6px 28px 64px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
  align-items: start;
}
.card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 26px;
  box-shadow:
    0 12px 40px rgba(0, 0, 0, .08),
    inset 0 1px 0 rgba(255, 255, 255, .9);
  padding: 20px 16px 12px;
  transition: background-color .3s ease, border-color .2s ease;
}
[data-theme="dark"] .card {
  box-shadow:
    0 12px 40px rgba(0, 0, 0, .5),
    inset 0 1px 0 rgba(255, 255, 255, .07);
}
.card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px 10px;
}
.badge {
  width: 30px;
  height: 30px;
  flex: none;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: color-mix(in srgb, var(--brand) 20%, transparent);
  color: color-mix(in srgb, var(--brand) 88%, var(--text));
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0;
}
[data-theme="dark"] .badge {
  background: color-mix(in srgb, var(--brand) 28%, transparent);
  color: color-mix(in srgb, var(--brand) 78%, #ffffff);
}
.badge.wide { font-size: 10.5px; }
.card-head h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.list { list-style: none; margin: 0; padding: 0; }
.list li + li { border-top: 1px solid var(--line); }
.list a {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 8px;
  margin: 0 -8px;
  border-radius: 9px;
  color: var(--text);
  font-size: 14px;
  line-height: 1.45;
  letter-spacing: -.006em;
  text-decoration: none;
  transition: background-color .15s ease;
}
.list a:hover { background: var(--hover); text-decoration: none; }
.list a:hover .title { color: var(--accent); }
.rank {
  flex: none;
  width: 16px;
  text-align: center;
  font-size: 12px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.list li:nth-child(-n+3) .rank { font-weight: 600; }
.list li:nth-child(1) .rank { color: color-mix(in srgb, var(--brand) 82%, var(--text)); }
.list li:nth-child(2) .rank { color: color-mix(in srgb, var(--brand) 64%, var(--text)); }
.list li:nth-child(3) .rank { color: color-mix(in srgb, var(--brand) 46%, var(--text)); }
.title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  transition: color .15s ease;
}
.hot {
  flex: none;
  margin-left: auto;
  font-size: 12px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.empty {
  padding: 22px 8px 18px;
  text-align: center;
  font-size: 13px;
  line-height: 1.7;
  color: var(--muted);
}
.empty a { color: var(--accent); }
.timeline {
  max-width: 980px;
  margin: 0 auto;
  padding: 0 28px 64px;
}
.filters {
  position: sticky;
  top: 0;
  z-index: 20;
  max-width: 980px;
  margin: 0 auto;
  padding: 12px 76px 14px 28px;
  display: grid;
  gap: 8px;
  background: transparent;
  -webkit-backdrop-filter: blur(18px) saturate(180%);
  backdrop-filter: blur(18px) saturate(180%);
}
.year-row, .month-row {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
  scrollbar-width: none;
}
.year-row::-webkit-scrollbar, .month-row::-webkit-scrollbar { display: none; }
.chip {
  flex: none;
  appearance: none;
  padding: 6px 13px;
  border: 1px solid var(--line);
  border-radius: 980px;
  background: var(--surface);
  color: var(--text);
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .01em;
  cursor: pointer;
  transition: background-color .2s ease, color .2s ease, border-color .2s ease;
}
.chip:hover { border-color: rgba(0, 113, 227, .45); }
.chip[aria-pressed="true"] {
  background: var(--accent-soft);
  border-color: transparent;
  color: var(--accent);
}
.month-row .chip { font-weight: 500; color: var(--muted); }
.month-row .chip:hover { color: var(--text); }
.month { scroll-margin-top: 112px; }
.month-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 30px 0 12px;
  padding: 2px 4px;
  list-style: none;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .06em;
  color: var(--muted);
  cursor: pointer;
}
.month-title::-webkit-details-marker { display: none; }
.month-count { margin-left: auto; font-weight: 500; }
.month-chevron { transition: transform .2s ease; }
details[open] > .month-title .month-chevron { transform: rotate(90deg); }
.entries {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
}
.entry {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 19px 24px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  color: var(--text);
  text-decoration: none;
  transition: background-color .2s ease, border-color .2s ease;
}
.entry:hover {
  border-color: rgba(0, 113, 227, .45);
  text-decoration: none;
}
.entry-date { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.entry-date b {
  font-size: 19px;
  font-weight: 600;
  letter-spacing: -.02em;
}
.entry-date span { font-size: 13px; color: var(--muted); }
.entry-meta {
  margin-left: auto;
  flex: none;
  font-size: 13px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.entry-chevron {
  flex: none;
  font-size: 22px;
  line-height: 1;
  color: var(--muted);
  transition: transform .2s ease, color .2s ease;
}
.entry:hover .entry-chevron { color: var(--accent); transform: translateX(2px); }
.footer {
  max-width: 1280px;
  margin: 0 auto;
  padding: 4px 28px 84px;
  text-align: center;
  font-size: 12px;
  line-height: 1.8;
  color: var(--muted);
}
.footer a { color: var(--accent); }
a:focus-visible, .theme-toggle:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
}
@media (max-width: 1100px) {
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 700px) {
  .theme-toggle { right: 16px; top: 16px; }
  .hero { padding: 64px 20px 26px; }
  .hero .sub { font-size: 15px; }
  .grid { grid-template-columns: 1fr; padding: 4px 20px 44px; gap: 14px; }
  .timeline { padding: 0 20px 44px; }
  .entry { padding: 16px 18px; gap: 12px; }
  .entry-date { flex: 1; }
  .entry-meta { display: none; }
  .footer { padding: 4px 20px 44px; }
  .title {
    white-space: normal;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  .hot { font-size: 11px; }
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
  if (!btn) return;
  btn.addEventListener("click", function () {
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("hot-theme", next); } catch (e) {}
  });

  // 在 IDE 预览等受限 iframe 中，浏览器会拦截新标签页，改为当前框架内跳转
  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest("a[href^='http']");
    if (!link || window.self === window.top) return;
    event.preventDefault();
    window.location.href = link.href;
  });
})();"""

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#ff453a"/>
  <text x="32" y="45" text-anchor="middle" font-family="-apple-system, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif" font-size="40" font-weight="600" fill="#ffffff">热</text>
</svg>
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="description" content="%%DATE_SHORT%%今日摘要：9 个信息源的每日内容摘要。">
<title>%%TITLE%%</title>
<link rel="icon" href="%%FAVICON%%" type="image/svg+xml">
<script>%%THEME_INIT%%</script>
<style>%%CSS%%</style>
</head>
<body>
<main>
  <section class="hero">
    <p class="eyebrow">阅读列表</p>
    <h1>今日摘要</h1>
    <p class="sub">%%DATE_LONG%% · %%TIME%% 更新</p>
  </section>
  <div class="grid">%%CARDS%%</div>
</main>
%%FOOTER%%
<button id="themeToggle" class="theme-toggle" type="button" aria-label="切换浅色 / 深色模式">
  <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.6 14.4A8.5 8.5 0 1 1 9.6 3.4a7 7 0 0 0 11 11Z"/></svg>
  <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2.6v2.4M12 19v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.6 12h2.4M19 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7"/></svg>
</button>
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
<meta name="description" content="今日摘要：每天 09:18、13:18、17:18 聚合 9 个公开信息源，按日期归档。">
<title>热榜日报</title>
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<script>%%THEME_INIT%%</script>
<style>%%CSS%%</style>
</head>
<body>
<main>
  <section class="hero">
    <p class="eyebrow">每日更新</p>
    <h1>热榜日报</h1>
    <p class="sub">聚合公开信息源，每天自动生成内容摘要。</p>
  </section>
%%FILTERS%%
  <section class="timeline" aria-label="日报目录">
%%ENTRIES%%
  </section>
</main>
<footer class="footer"><a href="index.html">查看最新一期 →</a></footer>
<button id="themeToggle" class="theme-toggle" type="button" aria-label="切换浅色 / 深色模式">
  <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.6 14.4A8.5 8.5 0 1 1 9.6 3.4a7 7 0 0 0 11 11Z"/></svg>
  <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2.6v2.4M12 19v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.6 12h2.4M19 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7"/></svg>
</button>
<script>%%INDEX_JS%%</script>
<script>%%THEME_JS%%</script>
</body>
</html>
"""

INDEX_JS = """(function () {
  var years = Array.prototype.slice.call(document.querySelectorAll(".year-chip"));
  var months = Array.prototype.slice.call(document.querySelectorAll(".month-chip"));
  function selectYear(year) {
    years.forEach(function (chip) {
      chip.setAttribute("aria-pressed", String(chip.dataset.year === year));
    });
    months.forEach(function (chip) {
      chip.hidden = chip.dataset.year !== year;
    });
  }
  function openMonth(section) {
    var details = section && section.querySelector("details");
    if (details) details.open = true;
  }
  function jump(section) {
    if (!section) return;
    selectYear(section.dataset.year);
    openMonth(section);
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  years.forEach(function (chip) {
    chip.addEventListener("click", function () {
      jump(document.querySelector('.month[data-year="' + chip.dataset.year + '"]'));
    });
  });
  months.forEach(function (chip) {
    chip.addEventListener("click", function () {
      jump(document.getElementById(chip.dataset.target));
    });
  });
  var hash = location.hash.replace("#", "");
  if (hash) {
    var target = document.getElementById(hash);
    if (target && target.classList.contains("month")) {
      selectYear(target.dataset.year);
      openMonth(target);
    }
  }
})();"""


def escape(value) -> str:
    return html.escape(str(value or ""), quote=True)


def render_card(source: dict) -> str:
    icon = escape(source.get("icon"))
    wide = " wide" if len(str(source.get("icon") or "")) > 1 else ""
    brand = BADGE_COLORS.get(source.get("name"), source.get("color") or "#8E8E93")
    rows = []
    for index, item in enumerate(source.get("items") or [], 1):
        hot = escape(item.get("hot"))
        hot_html = f'<span class="hot">{hot}</span>' if hot else ""
        rows.append(
            '<li><a href="{url}" target="_blank" rel="noopener noreferrer">'
            '<span class="rank">{rank}</span>'
            '<span class="title" title="{title}">{title}</span>'
            "{hot}"
            "</a></li>".format(
                url=escape(item.get("url")),
                rank=index,
                title=escape(item.get("title")),
                hot=hot_html,
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
        f'<section class="card" style="--brand:{escape(brand)}">'
        '<div class="card-head">'
        f'<span class="badge{wide}">{icon}</span>'
        f'<h2>{escape(source.get("name"))}</h2>'
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
    groups: dict[str, list[dict]] = {}
    for record in records:
        groups.setdefault(record["date"][:7], []).append(record)

    sections = []
    for position, (year_month, rows) in enumerate(groups.items()):
        year, month = year_month.split("-")
        entries = []
        for record in rows:
            entries.append(
                '<li><a class="entry" href="archive/{date}.html">'
                '<span class="entry-date"><b>{month}月{day}日</b>'
                "<span>星期{weekday}</span></span>"
                '<span class="entry-meta">{sources} 个板块 · {items} 条</span>'
                '<span class="entry-chevron" aria-hidden="true">›</span>'
                "</a></li>".format(**record)
            )
        opened = " open" if position == 0 else ""
        sections.append(
            f'<section class="month" id="m-{year_month}" data-year="{year}">'
            f'<details class="month-details"{opened}>'
            '<summary class="month-title">'
            f"<span>{year} 年 {int(month)} 月</span>"
            f'<span class="month-count">{len(rows)} 天</span>'
            '<span class="month-chevron" aria-hidden="true">›</span>'
            "</summary>"
            f'<ol class="entries">{"".join(entries)}</ol>'
            "</details></section>"
        )

    years: list[str] = []
    for year_month in groups:
        if not years or years[-1] != year_month[:4]:
            years.append(year_month[:4])
    filters = ""
    if groups:
        year_chips = "".join(
            f'<button type="button" class="chip year-chip" data-year="{year}" '
            f'aria-pressed="{str(index == 0).lower()}">{year}</button>'
            for index, year in enumerate(years)
        )
        month_chips = "".join(
            f'<button type="button" class="chip month-chip" data-year="{year_month[:4]}" '
            f'data-target="m-{year_month}"'
            f'{" hidden" if year_month[:4] != years[0] else ""}>'
            f"{int(year_month[5:])}月</button>"
            for year_month in groups
        )
        filters = (
            '<nav class="filters" aria-label="按年月筛选">'
            f'<div class="year-row">{year_chips}</div>'
            f'<div class="month-row">{month_chips}</div>'
            "</nav>"
        )

    replacements = {
        "%%CSS%%": CSS,
        "%%THEME_INIT%%": THEME_INIT,
        "%%THEME_JS%%": THEME_TOGGLE_JS,
        "%%INDEX_JS%%": INDEX_JS,
        "%%COUNT%%": str(len(records)),
        "%%FILTERS%%": filters,
        "%%ENTRIES%%": "".join(sections),
    }
    page = INDEX_TEMPLATE
    for token, value in replacements.items():
        page = page.replace(token, value)
    return page


def render(data: dict, archive: bool, root: bool = False) -> str:
    day = datetime.strptime(data["date"], "%Y-%m-%d")
    sources = data.get("sources") or []
    cards = "\n".join(render_card(s) for s in sources)
    base = "" if root else "../"
    footer = (
        f'<footer class="footer"><a href="{base}directory.html">查看往期日报</a></footer>'
        if archive else ""
    )
    replacements = {
        "%%FAVICON%%": f"{base}favicon.svg",
        "%%TITLE%%": f"今日摘要 · {day.month}月{day.day}日",
        "%%DATE_SHORT%%": f"{day.month}月{day.day}日",
        "%%DATE_LONG%%": f"{day.year} 年 {day.month} 月 {day.day} 日",
        "%%TIME%%": data.get("time", ""),
        "%%CSS%%": CSS,
        "%%THEME_INIT%%": THEME_INIT,
        "%%THEME_JS%%": THEME_TOGGLE_JS,
        "%%CARDS%%": cards,
        "%%FOOTER%%": footer,
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


def write_directory(records: list[dict]) -> str:
    path = os.path.join(SITE_DIR, "directory.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_index(records))
    return path


def write_favicon() -> str:
    path = os.path.join(SITE_DIR, "favicon.svg")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(FAVICON)
    return path


def write_home(data: dict | None) -> str:
    """生成站点首页 index.html，直接展示最新一期内容。"""
    if data:
        page = render(data, archive=True, root=True)
    else:
        page = (
            '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n'
            '<meta charset="utf-8">\n'
            "<title>今日摘要</title>\n"
            "</head>\n<body>\n"
            "<p>还没有内容，请先运行抓取脚本。</p>\n"
            "</body>\n</html>\n"
        )
    path = os.path.join(SITE_DIR, "index.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
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

    files = data_files()
    records = [archive_record(load_json(path)) for path in files]
    newest = None
    if files:
        newest = load_json(max(files))
        newest["date"] = newest.get("date") or os.path.basename(max(files))[:-5]
    print(write_favicon())
    print(write_directory(records))
    print(write_home(newest))
    stale = os.path.join(SITE_DIR, "latest.html")
    if os.path.exists(stale):
        os.remove(stale)
    return 0


if __name__ == "__main__":
    sys.exit(main())
