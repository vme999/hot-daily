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
