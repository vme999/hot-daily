# Hot List Daily

A static daily digest of trending topics from 9 sources. The home page lists
snapshots by date; each snapshot holds 9 sections and supports light / dark mode.

Site: <https://vme999.github.io/hot-daily/>

Fixed entry <https://vme999.github.io/hot-daily/latest.html> always serves the
newest snapshot in place, so the URL never changes.

## Features

- 9 sections, top 10 items each, linking to the original posts
- Heat / score shown next to the title when the source provides it
- Updated at 09:00, 13:00, 17:00 (UTC+8); same-day snapshots are overwritten
- Pure Python standard library, self-contained pages

## Sources

| Section | Endpoint |
| --- | --- |
| Zhihu | official hot list API |
| The Paper | `rightSidebar` hot list API |
| Weibo | codelife aggregate API |
| ifanr | official RSS |
| SSPAI | official RSS |
| Huxiu | codelife aggregate API |
| GitHub Trending | codelife (Trending Today) |
| Hacker News | HN Algolia `front_page` |
| dev.to | dev.to API (top of last day, shows reactions) |

## Deployment

`daily.yml` runs fetch → build → commit → deploy three times a day. Enable
**Settings → Pages → Source: GitHub Actions** and run `Daily hot list` once.

Scheduling is driven by an external cron service (cron-job.org) calling the
`workflow_dispatch` API at 09:00 / 13:00 / 17:00 UTC+8. GitHub's built-in
`schedule` proved unreliable here and is no longer configured.

Self-hosted alternative:

```cron
0 9,13,17 * * * /path/to/hot-daily/scripts/daily.sh >> /tmp/hot-daily.log 2>&1
```
