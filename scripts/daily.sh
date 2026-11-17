#!/usr/bin/env bash
# 抓取当天热榜并重新生成静态页面。
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/fetch_data.py
python3 scripts/build_page.py
