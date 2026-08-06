#!/usr/bin/env python3
"""Regenerate feed.xml from episodes/episodes.json. Run from repo root.

episodes.json: list of {"num": 1, "date": "2026-08-06", "title": "...",
"description": "...", "file": "ep001.mp3", "bytes": 13399407, "seconds": 1116}
"""
import json, email.utils, datetime, html

BASE = "https://playfundwin.github.io/daily-build-feed"

eps = json.load(open("episodes/episodes.json"))
eps.sort(key=lambda e: e["num"], reverse=True)

def rfc2822(datestr):
    dt = datetime.datetime.fromisoformat(datestr + "T05:30:00+00:00")
    return email.utils.format_datetime(dt)

items = []
for e in eps:
    dur = f'{e["seconds"]//60}:{e["seconds"]%60:02d}'
    items.append(f"""    <item>
      <title>{html.escape(e["title"])}</title>
      <description>{html.escape(e["description"])}</description>
      <enclosure url="{BASE}/episodes/{e["file"]}" length="{e["bytes"]}" type="audio/mpeg"/>
      <guid isPermaLink="false">daily-build-ep{e["num"]:03d}</guid>
      <pubDate>{rfc2822(e["date"])}</pubDate>
      <itunes:duration>{dur}</itunes:duration>
      <itunes:episode>{e["num"]}</itunes:episode>
    </item>""")

feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>The Daily Build</title>
    <link>{BASE}</link>
    <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>
    <language>en-gb</language>
    <description>Twenty minutes every morning: what shipped in AI in the last 48 hours, one small business you could build with Claude today, and what it means for your ventures. Real sources, real numbers, no fluff.</description>
    <itunes:author>The Daily Build</itunes:author>
    <itunes:image href="{BASE}/cover.png"/>
    <itunes:explicit>false</itunes:explicit>
    <itunes:category text="Business"/>
{chr(10).join(items)}
  </channel>
</rss>
"""
open("feed.xml", "w").write(feed)
print(f"feed.xml written with {len(eps)} episodes")
