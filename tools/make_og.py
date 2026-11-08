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


def plain_text(draw, xy, text, f, fill=INK):
    """文字だけを書く（2026-11-08 にマーカーをやめた。目印は sky_line の短い線）"""
    draw.text(xy, text, font=f, fill=fill)
    return draw.textlength(text, font=f)


def sky_line(draw, x, y, w=96):
    """見出しの下に置く、空色の短い線"""
    draw.rounded_rectangle([x, y, x + w, y + 8], radius=4, fill=SKY)


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
    sky_line(d, 72, 268)
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
        plain_text(d, (70, y), line, f)
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
        plain_text(d, (66, y), line, f)
        y += 108
    sky_line(d, 72, y + 8)
    frame(img, d)
    return img


def note_og(n):
    """曖昧ノートの共有画像"""
    img = Image.new("RGBA", (W, H), BASE + (255,))
    d = ImageDraw.Draw(img)
    d.ellipse([880, 90, 1140, 350], fill=BASE_YELLOW)
    paste_emoji(img, n["emoji"], (920, 130), 180)
    d.text((70, 70), "曖昧ノート", font=font(FONT_BOLD, 32), fill=SKY)
    size = 64
    while size > 40 and len(wrap(d, n["title"], font(FONT_HEAVY, size), 760)) > 3:
        size -= 4
    f = font(FONT_HEAVY, size)
    y = 140
    for line in wrap(d, n["title"], f, 760)[:4]:
        plain_text(d, (66, y), line, f)
        y += int(size * 1.45)
    sky_line(d, 72, y + 6)
    frame(img, d)
    return img


def result_og(w, i, label):
    """「私の〇〇は△△派でした」の共有画像"""
    img = Image.new("RGBA", (W, H), BASE + (255,))
    d = ImageDraw.Draw(img)
    d.ellipse([860, 90, 1140, 370], fill=BASE_YELLOW)
    paste_emoji(img, w["emoji"], (905, 135), 190)
    f_head = font(FONT_HEAVY, 46)
    head = f"私の「{w['word']}」は" if i != "n" else f"「{w['word']}」を"
    size = 46
    while size > 30 and d.textlength(head, font=font(FONT_HEAVY, size)) > 760:
        size -= 2
    d.text((70, 78), head, font=font(FONT_HEAVY, size), fill=INK)
    text = f"「{label}」派" if i != "n" else "知らなかった派"
    size = 72
    while size > 40 and len(wrap(d, text, font(FONT_HEAVY, size), 760)) > 2:
        size -= 4
    f = font(FONT_HEAVY, size)
    y = 170
    for line in wrap(d, text, f, 760)[:3]:
        plain_text(d, (66, y), line, f)
        y += int(size * 1.4)
    sky_line(d, 72, y + 6)
    d.text((70, y + 44), "あなたはどの意味で使ってる？", font=font(FONT_BOLD, 34), fill=SKY)
    frame(img, d)
    return img


def make_results(words):
    """意味派の画像は、名前が変わったものだけ作り直し、使われなくなったものは消す"""
    sys.path.insert(0, str(ROOT))
    import build
    rdir = OUT / "r"
    rdir.mkdir(parents=True, exist_ok=True)
    want, made = set(), 0
    for w in words:
        for i, _, label in build.poll_choices(w):
            name = build.result_og_name(w, i, label)
            want.add(name)
            if not (rdir / name).exists():
                result_og(w, i, label).convert("RGB").save(rdir / name, quality=70, optimize=True, progressive=True)
                made += 1
    for p in rdir.glob("*.jpg"):
        if p.name not in want:
            p.unlink()
    print(f"made {made} result images ({len(want)} in all)", file=sys.stderr)


def main():
    words = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "data" / "words").glob("*.json"))]
    OUT.mkdir(parents=True, exist_ok=True)
    make_results(words)
    ndir = OUT / "notes"
    ndir.mkdir(parents=True, exist_ok=True)
    for p in sorted((ROOT / "data" / "notes").glob("*.json")):
        n = json.loads(p.read_text(encoding="utf-8"))
        note_og(n).convert("RGB").save(ndir / f"{n['slug']}.png", optimize=True)
    for w in words:
        word_og(w).convert("RGB").save(OUT / f"{w['slug']}.png", optimize=True)
    site_og(words, ["その言葉、", "ほんとに同じ意味で", "使ってる？"], "流行ってるのに、意味がふわっとしてる言葉の辞典").convert("RGB").save(OUT / "site.png", optimize=True)
    print(f"made {len(words) + 1} images -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
