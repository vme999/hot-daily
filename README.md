# 热榜日报

每天抓取 9 个信息源的热榜，生成静态日报：首页是日期目录，点进去是对应一天的 9 个热榜板块，支持浅色 / 深色切换。

站点：<https://vme999.github.io/hot-daily/>

固定入口 <https://vme999.github.io/hot-daily/latest.html> 永远跳转到最新一期。

## 特性

- 9 个板块，每个取前 10 条，点击跳转原文
- 有热度数据时显示在标题右侧，没有则自动隐藏
- 每天 09:00、14:00、19:00（北京时间）抓取，当日快照直接覆盖
- 纯 Python 标准库，页面自包含，可双击打开或托管到任意静态服务器

数据源：知乎热榜、澎湃新闻、微博热搜、爱范儿、36氪、虎嗅、GitHub 趋势、Hacker News、X 趋势。

## 使用

```bash
./scripts/daily.sh                       # 抓取并生成
python3 scripts/build_page.py            # 只重新渲染
python3 scripts/build_page.py --date 2026-11-17   # 重建某天的存档

python3 -m http.server 8123 --directory site      # 本地预览
```

## 结构

```
scripts/fetch_data.py   # 抓取，写入 data/YYYY-MM-DD.json
scripts/build_page.py   # 生成 site/index.html 与 site/archive/YYYY-MM-DD.html
data/                   # 每日数据快照
site/                   # 生成的页面
.github/workflows/      # daily.yml 定时任务，deploy.yml 部署
```

## 自动部署

`daily.yml` 每天 3 次执行：抓取 → 生成 → 提交 → 部署。首次需在仓库 **Settings → Pages → Source** 选择 **GitHub Actions**，再手动运行一次 `Daily hot list`。

自有服务器可用 cron：

```cron
0 9,14,19 * * * /path/to/hot-daily/scripts/daily.sh >> /tmp/hot-daily.log 2>&1
```

## 说明

- 部分平台限制非中国大陆 IP，GitHub Actions 上个别板块可能为空，重跑或改用国内服务器即可
- 内容版权归原站点所有，本仓库仅作个人阅读用的聚合快照
