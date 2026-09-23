"""Render the landing page's social-share image (frontend/public/og.png, 1200x630).

Draws the hero composition — headline, the mint Path through four grade nodes and a
recommendation card — from the same fixtures the landing uses, so the preview never
drifts from the product. Needs Pillow; uses a system sans font when one is available.

Run from the repo root:  python backend/scripts/render_og_image.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "public" / "og.png"
W, H = 1200, 630
INK, MINT, PINE, WHITE, MUTED = (16, 38, 31), (185, 229, 180), (31, 107, 87), (255, 255, 255), (107, 124, 118)
FONT_CANDIDATES = [
    "/System/Library/Fonts/SFNS.ttf", "/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            try:
                face = ImageFont.truetype(candidate, size)
            except OSError:
                continue
            if bold:
                try:
                    face.set_variation_by_name("Semibold")
                except (OSError, ValueError, AttributeError):
                    pass
            return face
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, face, width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=face) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line]


def main() -> None:
    hero = json.loads((ROOT / "frontend" / "src" / "landing" / "fixtures.json").read_text())["hero"]
    image = Image.new("RGB", (W, H), INK)

    glow = Image.new("RGB", (W, H), INK)
    ImageDraw.Draw(glow).ellipse((620, -260, 1420, 540), fill=(38, 78, 62))
    image = Image.blend(image, glow.filter(ImageFilter.GaussianBlur(120)), 0.9)
    draw = ImageDraw.Draw(image)

    # The Path: a smooth mint S-curve that crosses its axis exactly at the four grade nodes.
    x0, nodes = 86, [190, 320, 450, 580]
    points = [(x0 + 18 * math.sin((y - 60) / 130 * math.pi), y) for y in range(40, H + 1, 2)]
    draw.line(points, fill=MINT, width=4, joint="curve")
    for index, y in enumerate(nodes):
        lit = index < 3
        draw.ellipse((x0 - 9, y - 9, x0 + 9, y + 9), fill=MINT if lit else INK, outline=MINT, width=3)
        draw.text((x0 + 20, y - 9), ["JUNIOR", "MIDDLE", "SENIOR", "LEAD"][index], font=font(14), fill=(185, 229, 180) if lit else MUTED)

    # Wordmark and headline.
    draw.rounded_rectangle((170, 64, 206, 100), radius=9, fill=MINT)
    draw.text((180, 66), "↗", font=font(24), fill=INK)
    draw.text((220, 71), "CAREER QUEST", font=font(20, bold=True), fill=WHITE)
    title = font(50, bold=True)
    y = 150
    for line in wrap(draw, "Every employee deserves to know where they’re going.", title, 560):
        draw.text((170, y), line, font=title, fill=WHITE)
        y += 60
    draw.text((170, y + 18), "The AI decision layer for employee growth", font=font(22), fill=MINT)

    # Recommendation card.
    card = hero["card"]
    cx, cy, cw, ch = 780, 150, 360, 330
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((cx + 8, cy + 18, cx + cw + 8, cy + ch + 18), radius=26, fill=(0, 0, 0, 110))
    image.paste(shadow.filter(ImageFilter.GaussianBlur(18)), (0, 0), shadow.filter(ImageFilter.GaussianBlur(18)))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=26, fill=WHITE)
    pct = round(hero["readiness"]["pct"])
    draw.arc((cx + 28, cy + 28, cx + 108, cy + 108), start=0, end=360, fill=(230, 239, 234), width=7)
    draw.arc((cx + 28, cy + 28, cx + 108, cy + 108), start=-90, end=-90 + 3.6 * pct, fill=PINE, width=7)
    draw.text((cx + 68, cy + 68), f"{pct}%", font=font(22, bold=True), fill=INK, anchor="mm")
    draw.text((cx + 126, cy + 44), f"readiness for {hero['target']['grade']}", font=font(16), fill=MUTED)
    draw.text((cx + 126, cy + 68), f"{hero['employee']['role']}", font=font(16), fill=INK)
    draw.rounded_rectangle((cx + 28, cy + 140, cx + 92, cy + 166), radius=13, fill=INK)
    draw.text((cx + 60, cy + 153), "AI", font=font(14, bold=True), fill=MINT, anchor="mm")
    draw.text((cx + 28, cy + 182), card["title"], font=font(26, bold=True), fill=INK)
    chip = card["factor_labels"]["en"][0]
    draw.rounded_rectangle((cx + 28, cy + 228, cx + 28 + draw.textlength(chip, font=font(15)) + 28, cy + 258), radius=15, fill=(234, 243, 238))
    draw.text((cx + 42, cy + 235), chip, font=font(15), fill=PINE)
    draw.text((cx + 28, cy + 282), f"Readiness after: {card['readiness_after']}%", font=font(16), fill=MUTED)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
