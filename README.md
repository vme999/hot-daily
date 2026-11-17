# 热榜日报

每天抓取 12 个中文站点的热榜，生成静态日报：首页是日期目录，点进去是对应一天的 12 个热榜板块，支持浅色 / 深色切换。

站点：<https://vme999.github.io/hot-daily/>

## 特性

- 12 个板块，每个取前 10 条，点击跳转原文
- 有热度数据时显示在标题右侧，没有则自动隐藏
- 每天 09:00、14:00、19:00（北京时间）抓取，当日快照直接覆盖
- 纯 Python 标准库，页面自包含，可双击打开或托管到任意静态服务器

数据源：知乎、豆瓣、微博、今日头条、B站、IT之家、中关村在线、爱范儿、CSDN、虎嗅、值得买、掘金。

## 使用

```bash
./scripts/daily.sh                       # 抓取并生成
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

## 说明

- 部分平台限制非中国大陆 IP，GitHub Actions 上个别板块可能为空，重跑或改用国内服务器即可
- 值得买官方「3 小时热门」有反爬，改用其公开的「精选好价」列表
- 内容版权归原站点所有，本仓库仅作个人阅读用的聚合快照
