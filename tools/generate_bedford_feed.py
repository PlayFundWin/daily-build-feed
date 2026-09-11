#!/usr/bin/env python3
"""Regenerate bedford/feed.xml from bedford/episodes/episodes.json. Run from repo root.

Mirrors tools/generate_feed.py, namespaced under bedford/ for The Bedford Town
Briefing -- a separate show in this same repo, for James (Bedford Town FC) rather than
Steve. See RUNBOOK.md's Bedford Town section.
"""
import json, email.utils, datetime, html

BASE = "https://playfundwin.github.io/daily-build-feed/bedford"

eps = json.load(open("bedford/episodes/episodes.json"))
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
      <guid isPermaLink="false">bedford-briefing-ep{e["num"]:03d}</guid>
      <pubDate>{rfc2822(e["date"])}</pubDate>
      <itunes:duration>{dur}</itunes:duration>
      <itunes:episode>{e["num"]}</itunes:episode>
    </item>""")

feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>The Bedford Town Briefing</title>
    <link>{BASE}</link>
    <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>
    <language>en-gb</language>
    <description>A daily insider briefing on Bedford Town FC and the National League North -- team news, the wider divisional picture, and what's moving in the tiers above and below. Built for the people who run the club.</description>
    <itunes:author>The Bedford Town Briefing</itunes:author>
    <itunes:image href="{BASE}/cover.png"/>
    <itunes:explicit>false</itunes:explicit>
    <itunes:category text="Sports"/>
{chr(10).join(items)}
  </channel>
</rss>
"""
open("bedford/feed.xml", "w").write(feed)
print(f"bedford/feed.xml written with {len(eps)} episodes")
