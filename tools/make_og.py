#!/usr/bin/env python3
"""共有画像（1200×630）を docs/og/ に作る。

使い方: python3 tools/make_og.py   （Pillow が必要。build.py の後に実行する）
書体は macOS のヒラギノ角ゴシックを使う。ほかの環境では FONT_* を書き換える。
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "og"
EMOJI = ROOT / "tools" / "emoji512"
FONT_HEAVY = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"

W, H = 1200, 630
BASE = (247, 249, 251)
INK = (26, 29, 35)
SUB = (94, 99, 107)
SKY = (24, 116, 184)
YELLOW = (245, 197, 24)
BASE_YELLOW = (255, 243, 196)


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, f, width):
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=f) > width and cur:
            # 行頭に句読点が来ないようにする
            if ch in "、。」）！？":
                cur += ch
                continue
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def marker_text(draw, xy, text, f, fill=INK):
    x, y = xy
    tw = draw.textlength(text, font=f)
    asc, desc = f.getmetrics()
    h = asc + desc
    draw.rectangle([x - 4, y + h * 0.58, x + tw + 4, y + h * 0.92], fill=YELLOW)
    draw.text((x, y), text, font=f, fill=fill)
    return tw


def paste_emoji(img, cp, box, size):
    p = EMOJI / f"{cp}.png"
    if not p.exists():
        return
    e = Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS)
    img.alpha_composite(e, box)


def frame(img, d):
    # 下の帯
    d.rectangle([0, H - 72, W, H], fill=INK)
    paste_emoji(img, "1f914", (60, H - 60), 48)
    d.text((122, H - 58), "現代曖昧単語辞典", font=font(FONT_HEAVY, 30), fill=(255, 255, 255))
    d.text((W - 60, H - 52), "gendai-aimai-tango-jiten.github.io", font=font(FONT_BOLD, 20), fill=(214, 217, 222), anchor="ra")


def word_og(w):
    img = Image.new("RGBA", (W, H), BASE + (255,))
    d = ImageDraw.Draw(img)
    # 右の円と絵文字
    d.ellipse([820, 70, 1140, 390], fill=BASE_YELLOW)
    paste_emoji(img, w["emoji"], (870, 120), 220)
    d.text((70, 70), w["reading"], font=font(FONT_BOLD, 30), fill=SUB)
    # 見出し語は右の円にかからない幅（720px）に収まるまで小さくする
    size = 132
    while size > 56 and d.textlength(w["word"], font=font(FONT_HEAVY, size)) > 720:
        size -= 4
    d.text((64, 108 + (132 - size) // 2), w["word"], font=font(FONT_HEAVY, size), fill=INK)
    # 句点ごとに行を分け、収まるまで文字を小さくする。収まらなければ均等に折り返す
    sents = [s + "。" for s in w["catch"].split("。") if s]
    size = 42
    while size > 32 and any(d.textlength(s, font=font(FONT_HEAVY, size)) > 740 for s in sents):
        size -= 2
    f = font(FONT_HEAVY, size)
    if any(d.textlength(s, font=f) > 740 for s in sents):
        n = len(wrap(d, w["catch"], f, 740))
        sents = wrap(d, w["catch"], f, d.textlength(w["catch"], font=f) / n + 80)
    y = 300
    for line in sents[:3]:
        marker_text(d, (70, y), line, f)
        y += int(size * 1.55)
    d.rounded_rectangle([70, y + 18, 70 + d.textlength("意味・語源・使い方のズレ", font=font(FONT_BOLD, 24)) + 40, y + 66], radius=24, fill=(232, 238, 245))
    d.text((90, y + 28), "意味・語源・使い方のズレ", font=font(FONT_BOLD, 24), fill=(21, 104, 166))
    frame(img, d)
    return img


def site_og(words, title, sub, emoji_main=None):
    img = Image.new("RGBA", (W, H), BASE + (255,))
    d = ImageDraw.Draw(img)
    cps = [w["emoji"] for w in words][:3]
    spots = [((880, 70), 200), ((1010, 290), 140), ((820, 320), 120)]
    if emoji_main:
        d.ellipse([820, 70, 1140, 390], fill=BASE_YELLOW)
        paste_emoji(img, emoji_main, (870, 120), 220)
    else:
        for cp, (xy, s) in zip(cps, spots):
            d.ellipse([xy[0] - 16, xy[1] - 16, xy[0] + s + 16, xy[1] + s + 16], fill=BASE_YELLOW)
            paste_emoji(img, cp, xy, s)
    d.text((70, 80), sub, font=font(FONT_BOLD, 30), fill=SKY)
    f = font(FONT_HEAVY, 76)
    y = 140
    for line in title:
        marker_text(d, (66, y), line, f)
        y += 108
    frame(img, d)
    return img


def main():
    words = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "data" / "words").glob("*.json"))]
    OUT.mkdir(parents=True, exist_ok=True)
    for w in words:
        word_og(w).convert("RGB").save(OUT / f"{w['slug']}.png", optimize=True)
    site_og(words, ["その言葉、", "ほんとに同じ意味で", "使ってる？"], "流行ってるのに、意味がふわっとしてる言葉の辞典").convert("RGB").save(OUT / "site.png", optimize=True)
    print(f"made {len(words) + 1} images -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
