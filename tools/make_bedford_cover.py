#!/usr/bin/env python3
"""Generate bedford/cover.png (1400x1400 podcast artwork) for JT Debrief, the
opposition-analytics breakdown for James (Bedford Town's assistant manager). Run from
repo root. Mirrors tools/make_cover.py's approach and palette. Renamed from "The
Bedford Town Briefing" to "JT Morning Brief" 2026-09-11, then to "JT Debrief"
2026-10-03.

NOTE: this script was updated for the rename but the actual bedford/cover.png binary
was NOT regenerated as part of that rename (no safe path to push a binary file from
the Cowork sandbox that produced this edit) -- the build workflow only regenerates it
when the file is missing, so the live cover will keep showing the old "JT MORNING
BRIEF" artwork until this script is actually run (or the existing file removed) in an
environment that can write the binary back. Flagged as a known follow-up.
"""
import os
from PIL import Image, ImageDraw, ImageFont

W = 1400
img = Image.new("RGB", (W, W), "#0e1420")
d = ImageDraw.Draw(img)
d.polygon([(0, W), (W, 0), (W, W * 0.35), (W * 0.35, W)], fill="#131c2e")
d.rectangle([(0, W - 160), (W, W)], fill="#f2b234")

def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

big = font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 168)
med = font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 62)
small = font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)

d.text((100, 420), "JT", font=med, fill="#8fa1bd")
d.text((92, 500), "DEBRIEF", font=big, fill="#ffffff")
d.text((100, 700), "Opposition analysis, on demand", font=med, fill="#f2b234")
d.text((100, 930), "Built for the coaching staff", font=med, fill="#c6d2e4")
d.text((100, W - 118), "BEDFORD TOWN FC  •  ON DEMAND", font=small, fill="#0e1420")
os.makedirs("bedford", exist_ok=True)
img.save("bedford/cover.png", optimize=True)
print("bedford/cover.png written")
