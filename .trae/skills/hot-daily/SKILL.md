---
name: "hot-daily"
description: "Builds and maintains the hot-daily static digest of 12 Chinese trending lists. Invoke when the user asks to generate, update, schedule, or modify the daily hot-list page."
---

# 热榜日报

把 12 个中文站点的热榜抓取为每日静态页面，支持浅色 / 深色切换，只依赖 Python 标准库。

## 目录结构

- `scripts/fetch_data.py`：抓取数据，写入 `data/YYYY-MM-DD.json`
- `scripts/build_page.py`：读取 JSON，生成日报目录 `site/index.html` 与每日页面 `site/archive/YYYY-MM-DD.html`
- `scripts/daily.sh`：一次完成抓取 + 生成
- `.github/workflows/daily.yml`：每天 07:30（北京时间）自动运行并部署 GitHub Pages
- `.github/workflows/deploy.yml`：`site/` 有变更或手动触发时部署
- `site/`：生成结果，可直接托管或双击打开

## 常用命令

```bash
# 抓取当天数据并生成页面
./scripts/daily.sh

# 仅重新渲染（不重新抓取）
python3 scripts/build_page.py

# 重新生成某天的存档页
python3 scripts/build_page.py --date 2026-11-17
```

## 数据源

知乎热榜、豆瓣热点、微博热搜、今日头条、B站日榜、IT之家、中关村在线、爱范儿、CSDN、虎嗅、值得买热门、掘金。

- 知乎 / 今日头条 / B站 / 中关村在线 / 爱范儿 / CSDN / 掘金：官方接口或页面
- 微博 / 虎嗅 / IT之家：`api.codelife.cc` 公开聚合接口
- 豆瓣：没有公开热榜，汇总当前热门小组讨论并按回应数排序
- 值得买：官方「3 小时热门」有反爬，改用「精选好价 / 今日必买」页面

## 修改信息源

在 `scripts/fetch_data.py` 中：

1. 新增 `src_xxx()`，返回 `[{"title", "url", "hot"}]`，最多 10 条
2. 在 `SOURCES` 中登记 `(id, 名称, 图标字, 品牌色, 站点首页, 抓取函数)`

单个源失败不会中断整体抓取，页面对应卡片会显示空状态和原站链接。

## 页面约定

- 首页 `site/index.html` 是日报目录：按月份分组、从新到旧排列，最新一期带「最新」标记
- 每期页面 `site/archive/YYYY-MM-DD.html` 固定 12 张卡片，每张 10 条，只显示排名 + 标题
- 主题保存在 `localStorage["hot-theme"]`，默认跟随系统，目录页与日报页共用
- 页面为自包含单文件（CSS / JS 内联），可直接双击打开
- 点击条目在新标签页打开原文；iframe 预览中改为当前框架跳转

## 定时任务

- GitHub Actions：`.github/workflows/daily.yml`，cron `30 23 * * *`（UTC）= 07:30 北京时间；仓库 Pages 来源需设为「GitHub Actions」
- 本地 cron：`30 7 * * * /path/to/hot-daily/scripts/daily.sh >> /tmp/hot-daily.log 2>&1`

## 验证

```bash
python3 scripts/fetch_data.py   # 12 个源都应输出 [ok]
grep -c 'class="card"' site/index.html   # 应为 12
```
