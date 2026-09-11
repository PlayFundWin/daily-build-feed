#!/usr/bin/env python3
"""Generate bedford/cover.png (1400x1400 podcast artwork) for The Bedford Town
Briefing. Run from repo root. Mirrors tools/make_cover.py's approach and palette."""
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

d.text((100, 420), "THE", font=med, fill="#8fa1bd")
d.text((92, 500), "BEDFORD", font=big, fill="#ffffff")
d.text((92, 690), "TOWN", font=big, fill="#f2b234")
d.text((100, 930), "Team news, every matchday morning", font=med, fill="#c6d2e4")
d.text((100, W - 118), "FOR THE COACHING STAFF  •  DAILY", font=small, fill="#0e1420")
os.makedirs("bedford", exist_ok=True)
img.save("bedford/cover.png", optimize=True)
print("bedford/cover.png written")
