# 热榜日报

每天抓取 12 个中文站点的热榜，生成一份静态日报。首页是**日报目录**（按时间线从新到旧），点进任意一期即为当天的热榜页面，支持浅色 / 深色切换。

- 站点：<https://vme999.github.io/hot-daily/>
- 纯 Python 标准库，无第三方依赖
- 页面自包含（CSS / JS 内联），可直接双击打开或托管到任意静态服务器

## 数据源

| 板块 | 来源 |
| --- | --- |
| 知乎热榜 | 知乎官方热榜接口 |
| 豆瓣热点 | 热门小组讨论，按回应数排序 |
| 微博热搜 | codelife 公开聚合接口 |
| 今日头条 | 头条热榜接口 |
| B站日榜 | B站排行榜接口 |
| IT之家 | codelife 公开聚合接口 |
| 中关村在线 | 站内新闻列表 |
| 爱范儿 | RSS |
| CSDN | 博客热榜接口 |
| 虎嗅 | codelife 公开聚合接口 |
| 值得买热门 | 精选好价 / 今日必买 |
| 掘金 | 掘金热榜接口 |

每个板块取前 10 条，只展示排名和标题，点击跳转原文。单个源失败不会影响其他板块。

## 快速开始

```bash
# 抓取当天数据并生成页面
./scripts/daily.sh

# 只重新渲染，不重新抓取
python3 scripts/build_page.py

# 重新生成某一天的存档页（同时刷新目录）
python3 scripts/build_page.py --date 2026-11-17
```

本地预览：

```bash
python3 -m http.server 8123 --directory site
# 打开 http://127.0.0.1:8123/
```

## 目录结构

```
.
├── scripts/
│   ├── fetch_data.py          # 抓取 12 个源，写入 data/YYYY-MM-DD.json
│   ├── build_page.py          # 生成日报目录与每日页面
│   └── daily.sh               # 抓取 + 生成
├── data/                      # 每日数据快照（JSON）
├── site/
│   ├── index.html             # 日报目录（时间线）
│   └── archive/
│       └── YYYY-MM-DD.html    # 每日热榜页面
├── .github/workflows/
│   ├── daily.yml              # 每天 09:00 / 14:00 / 19:00 抓取、提交并部署
│   └── deploy.yml             # 推送 site/ 变更时部署
└── .trae/skills/hot-daily/    # 维护该项目的 skill
```

## 每日自动更新

`.github/workflows/daily.yml` 每天 09:00、14:00、19:00（北京时间）各执行一次：抓取 → 生成页面 → 提交 `data/` 与 `site/` → 部署 GitHub Pages。同一天的文件会被直接覆盖，不会产生重复条目。

首次使用需在仓库 **Settings → Pages → Source** 选择 **GitHub Actions**，然后在 Actions 中手动运行一次 `Daily hot list`。

如果部署在自有服务器，用 cron 更稳定：

```cron
0 9,14,19 * * * /path/to/hot-daily/scripts/daily.sh >> /tmp/hot-daily.log 2>&1
```

## 自定义

在 `scripts/fetch_data.py` 中新增 `src_xxx()`，返回 `[{"title", "url", "hot"}]`（最多 10 条），再在 `SOURCES` 注册 `(id, 名称, 图标字, 品牌色, 站点首页, 函数)` 即可。

## 说明

- 部分平台对非中国大陆 IP 有访问限制，GitHub Actions 上个别板块可能抓取失败并显示空状态，重跑或改用国内服务器可解决。
- 值得买官方的「3 小时热门」接口有反爬限制，这里改用其公开的「精选好价」列表。
- 所有内容版权归原站点所有，本仓库仅做个人阅读用的聚合快照。
