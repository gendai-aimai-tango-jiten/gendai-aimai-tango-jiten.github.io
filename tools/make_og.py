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


def phrase_chunks(t):
    """タイトルを、言葉の途中で折り返さないよう助詞やかっこの切れ目で区切る"""
    out, cur, inq = [], "", False
    for i, ch in enumerate(t):
        if ch == "「":
            if cur:
                out.append(cur)
                cur = ""
            inq = True
        cur += ch
        nxt = t[i + 1] if i + 1 < len(t) else ""
        two = t[i - 1:i + 1]
        if ch == "」":
            inq = False
            continue
        if inq:  # かっこの中では区切らない
            continue
        end = (ch in "のをはがにでへやもと、" and nxt not in "」、。") or two in ("から", "った", "した", "って", "よる")
        if ch == "に" and nxt == "も":
            end = False
        if end:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out


def phrase_wrap(d, text, f, width, max_lines):
    """切れ目ごとに詰め、行数が少なく、行の長さがなるべくそろう分け方を選ぶ"""
    cs, best = phrase_chunks(text), None

    def rec(i, lines):
        nonlocal best
        if len(lines) > max_lines:
            return
        if i == len(cs):
            ws = [d.textlength(x, font=f) for x in lines]
            score = (len(lines), max(ws) - min(ws))
            if best is None or score < best[0]:
                best = (score, list(lines))
            return
        s = ""
        for j in range(i, len(cs)):
            s += cs[j]
            if d.textlength(s, font=f) > width:
                break
            rec(j + 1, lines + [s])

    rec(0, [])
    return best[1] if best else None


def word_pills(img, d, words, x0, y0, x1, size=30, max_rows=3):
    """収録語を絵つきの札で並べる。入りきらない分は「ほかN語」にまとめる"""
    f = font(FONT_HEAVY, size)
    ph, pad, gap, es = int(size * 1.9), int(size * 0.7), 12, int(size * 1.15)
    x, y, row = x0, y0, 1
    for k, w in enumerate(words):
        tw = d.textlength(w["word"], font=f) + pad * 2 + es + 8
        if x + tw > x1:
            row, x, y = row + 1, x0, y + ph + gap
        rest = len(words) - k
        more = f"ほか{rest}語"
        mw = d.textlength(more, font=f) + pad * 2
        if row > max_rows or (row == max_rows and rest > 1 and x + tw + gap + mw > x1):
            if row > max_rows:  # 前の行の末尾に「ほかN語」を置ける幅はない場合
                break
            d.rounded_rectangle([x, y, x + mw, y + ph], radius=ph // 2, fill=(232, 238, 245))
            d.text((x + pad, y + ph / 2), more, font=f, fill=(21, 104, 166), anchor="lm")
            return
        d.rounded_rectangle([x, y, x + tw, y + ph], radius=ph // 2, fill=(255, 255, 255), outline=(214, 222, 232), width=2)
        paste_emoji(img, w["emoji"], (int(x + pad), int(y + (ph - es) / 2)), es)
        d.text((x + pad + es + 8, y + ph / 2), w["word"], font=f, fill=INK, anchor="lm")
        x += tw + gap


def note_og(n, words_by_slug):
    """曖昧ノートの共有画像。タイトルの下に収録語を札で並べる（2026-11-20 黒田さんが4案からAを選んだ）"""
    img = Image.new("RGBA", (W, H), BASE + (255,))
    d = ImageDraw.Draw(img)
    d.ellipse([960, 52, 1150, 242], fill=BASE_YELLOW)
    paste_emoji(img, n["emoji"], (990, 82), 130)
    d.text((70, 62), "曖昧ノート", font=font(FONT_BOLD, 30), fill=SKY)
    for size in range(64, 38, -4):
        f = font(FONT_HEAVY, size)
        lines = phrase_wrap(d, n["title"], f, 860, 2)
        if lines:
            break
    else:
        lines = wrap(d, n["title"], f, 860)[:2]
    y = 112
    for line in lines:
        d.text((66, y), line, font=f, fill=INK)
        y += int(size * 1.38)
    words = [words_by_slug[it["slug"]] for it in n.get("items", []) if it["slug"] in words_by_slug]
    word_pills(img, d, words, 70, y + 26, W - 70, size=30, max_rows=3)
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
        note_og(n, {w['slug']: w for w in words}).convert("RGB").save(ndir / f"{n['slug']}.png", optimize=True)
    for w in words:
        word_og(w).convert("RGB").save(OUT / f"{w['slug']}.png", optimize=True)
    site_og(words, ["その言葉、", "ほんとに同じ意味で", "使ってる？"], "流行ってるのに、意味がふわっとしてる言葉の辞典").convert("RGB").save(OUT / "site.png", optimize=True)
    print(f"made {len(words) + 1} images -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
