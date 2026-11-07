#!/usr/bin/env python3
"""現代曖昧単語辞典 ビルドスクリプト

data/words/*.json を読み、docs/ に静的HTMLを書き出す。
使い方: python3 build.py
"""
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "words"
OUT = ROOT / "docs"
ASSETS = ROOT / "assets"

SITE_TITLE = "現代曖昧単語辞典"
SITE_DESC = "流行っているのに、意味がはっきりしない言葉を、一語ずつ多様な観点から調べてまとめる辞典。"

METER_ORDER = ["曖昧度", "誤用度", "トゲ度", "定着度"]
METER_HELP = {
    "曖昧度": "人によって指す範囲がどれだけばらつくか",
    "誤用度": "本来の意味や出典とずれた使われ方がどれだけ多いか",
    "トゲ度": "人に向けて使ったときに攻撃的・失礼に響くおそれ",
    "定着度": "一部の界隈を越えて広く通じるか",
}
USAGE_TYPES = {"原義": "u-origin", "拡張": "u-extend", "誤用寄り": "u-misuse"}


def esc(s):
    return html.escape(str(s), quote=True)


def paras(text):
    """空行区切りの段落を <p> にする。**強調** だけ対応。"""
    out = []
    for block in str(text).strip().split("\n\n"):
        b = esc(block.strip()).replace("\n", "<br>")
        parts = b.split("**")
        b = "".join(f"<strong>{p}</strong>" if i % 2 else p for i, p in enumerate(parts))
        out.append(f"<p>{b}</p>")
    return "\n".join(out)


def meters_html(meters, compact=False):
    rows = []
    for key in METER_ORDER:
        if key not in meters:
            continue
        v = int(meters[key])
        dots = "".join(f'<i class="{"on" if i < v else ""}"></i>' for i in range(5))
        label = esc(key)
        if compact:
            rows.append(f'<div class="meter sm" title="{esc(METER_HELP[key])}"><span>{label}</span><b aria-label="{v}/5">{dots}</b></div>')
        else:
            rows.append(
                f'<div class="meter"><span>{label}</span><b aria-label="5段階中{v}">{dots}</b>'
                f'<small>{esc(METER_HELP[key])}</small></div>'
            )
    return f'<div class="meters{" compact" if compact else ""}">{"".join(rows)}</div>'


def head(title, desc, depth):
    pre = "../" * depth
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@600;800&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{pre}assets/style.css">
</head>
<body>
<header class="site-header"><div class="wrap">
<a class="brand" href="{pre}index.html"><span class="brand-mark">曖</span>{SITE_TITLE}</a>
<nav><a href="{pre}index.html#list">収録語</a><a href="{pre}about.html">この辞典について</a></nav>
</div></header>
"""


def foot(depth):
    pre = "../" * depth
    return f"""<footer class="site-footer"><div class="wrap">
<p>{SITE_TITLE} — 言葉の意味は使う人の数だけ揺れます。ここに書いたのは調べた時点での整理です。</p>
<p><a href="{pre}index.html">トップ</a> ・ <a href="{pre}about.html">この辞典について</a></p>
</div></footer>
<script src="{pre}assets/app.js"></script>
</body>
</html>
"""


def section(sid, num, title, body):
    return f"""<section class="sec" id="{sid}">
<h2><span class="sec-num">{num}</span>{esc(title)}</h2>
{body}
</section>"""


def word_page(w, all_words):
    slug_map = {x["word"]: x["slug"] for x in all_words}
    secs = []
    toc = []

    def add(sid, title, body):
        n = len(secs) + 1
        secs.append(section(sid, f"{n:02d}", title, body))
        toc.append(f'<li><a href="#{sid}">{esc(title)}</a></li>')

    add("definition", "ひとことで言うと", paras(w["definition"]))

    if w.get("usages"):
        items = []
        for u in w["usages"]:
            cls = USAGE_TYPES.get(u["type"], "u-extend")
            items.append(
                f'<li class="{cls}"><span class="u-tag">{esc(u["type"])}</span>'
                f'<div><h3>{esc(u["label"])}</h3>{paras(u["desc"])}</div></li>'
            )
        legend = '<p class="legend">いま使われている意味の幅。<span class="u-tag u-origin">原義</span>もともとの意味 <span class="u-tag u-extend">拡張</span>広がった使い方 <span class="u-tag u-misuse">誤用寄り</span>出典からは離れた使い方</p>'
        add("usages", "意味の地図", legend + f'<ol class="usage-map">{"".join(items)}</ol>')

    add("etymology", "語源・成り立ち", paras(w["etymology"]))

    if w.get("timeline"):
        rows = "".join(
            f'<li><time>{esc(t["date"])}</time><div>{paras(t["event"])}</div></li>' for t in w["timeline"]
        )
        add("timeline", "広まった経緯", f'<ol class="timeline">{rows}</ol>')

    if w.get("misuses"):
        items = "".join(
            f'<div class="card warn"><h3>{esc(m["title"])}</h3>{paras(m["body"])}</div>' for m in w["misuses"]
        )
        add("misuses", "ズレやすいポイント・誤解", f'<div class="cards">{items}</div>')

    if w.get("examples"):
        items = []
        for e in w["examples"]:
            mark = {"ok": ("○", "ex-ok", "自然"), "ng": ("×", "ex-ng", "ズレている"), "warn": ("△", "ex-warn", "注意")}[e["verdict"]]
            items.append(
                f'<li class="{mark[1]}"><span class="ex-mark" aria-label="{mark[2]}">{mark[0]}</span>'
                f'<div><q>{esc(e["text"])}</q><small>{esc(e["note"])}</small></div></li>'
            )
        add("examples", "使用例で見る", f'<ul class="examples">{"".join(items)}</ul>')

    if w.get("perspectives"):
        items = "".join(
            f'<div class="persp"><h3>{esc(p["label"])}</h3>{paras(p["body"])}</div>' for p in w["perspectives"]
        )
        add("perspectives", "多様な観点から", f'<div class="persps">{items}</div>')

    if w.get("who_where"):
        add("who", "誰が・どこで使うか", paras(w["who_where"]))

    if w.get("paraphrase"):
        rows = "".join(
            f'<tr><th>{esc(p["context"])}</th><td>{esc(p["text"])}</td></tr>' for p in w["paraphrase"]
        )
        add("paraphrase", "言い換えるなら", f'<table class="para"><tbody>{rows}</tbody></table>')

    if w.get("related"):
        items = []
        for r in w["related"]:
            name = esc(r["word"])
            if r["word"] in slug_map:
                name = f'<a href="{slug_map[r["word"]]}.html">{name}</a>'
            items.append(f'<li><b>{name}</b><span>{esc(r["note"])}</span></li>')
        add("related", "関連語・対になる語", f'<ul class="related">{"".join(items)}</ul>')

    if w.get("sources"):
        items = "".join(
            f'<li><a href="{esc(s["url"])}" rel="noopener" target="_blank">{esc(s["title"])}</a>'
            + (f' <small>{esc(s["note"])}</small>' if s.get("note") else "")
            + "</li>"
            for s in w["sources"]
        )
        add("sources", "出典・参考", f'<ol class="sources">{items}</ol>')

    tags = "".join(f'<a class="tag" href="../index.html?tag={esc(t)}#list">{esc(t)}</a>' for t in w["tags"])
    title = f'{w["word"]}とは｜{SITE_TITLE}'
    others = [x for x in all_words if x["slug"] != w["slug"]]
    nav = "".join(
        f'<a class="mini" href="{x["slug"]}.html"><b>{esc(x["word"])}</b><span>{esc(x["oneliner"])}</span></a>'
        for x in others[:6]
    )

    return (
        head(title, w["oneliner"], 1)
        + f"""<main class="wrap word-layout">
<article class="entry">
<div class="entry-head">
<p class="crumb"><a href="../index.html">{SITE_TITLE}</a> › 収録語</p>
<h1 class="headword">{esc(w["word"])}</h1>
<p class="reading">【{esc(w["reading"])}】<span class="pos">{esc(w["pos"])}</span></p>
<p class="oneliner">{esc(w["oneliner"])}</p>
<div class="tags">{tags}</div>
<dl class="facts">
<div><dt>初出・発祥</dt><dd>{esc(w["origin_date"])}</dd></div>
<div><dt>流行のピーク</dt><dd>{esc(w["peak"])}</dd></div>
<div><dt>最終更新</dt><dd>{esc(w["updated"])}</dd></div>
</dl>
{meters_html(w["meters"])}
</div>
{"".join(secs)}
</article>
<aside class="side">
<div class="toc"><p class="side-title">目次</p><ol>{"".join(toc)}</ol></div>
</aside>
</main>
<section class="wrap more"><h2 class="more-title">ほかの曖昧な言葉</h2><div class="minis">{nav}</div></section>
"""
        + foot(1)
    )


def index_page(words, planned):
    cards = []
    all_tags = []
    for w in words:
        for t in w["tags"]:
            if t not in all_tags:
                all_tags.append(t)
        cards.append(
            f'<a class="wcard" href="words/{w["slug"]}.html" data-tags="{esc("|".join(w["tags"]))}" '
            f'data-search="{esc(w["word"] + w["reading"] + w["oneliner"] + "".join(w["tags"]))}" '
            f'data-amb="{w["meters"].get("曖昧度", 0)}" data-mis="{w["meters"].get("誤用度", 0)}" data-date="{esc(w["updated"])}" data-kana="{esc(w["reading"])}">'
            f'<span class="wcard-reading">{esc(w["reading"])}</span>'
            f'<span class="wcard-word">{esc(w["word"])}</span>'
            f'<span class="wcard-one">{esc(w["oneliner"])}</span>'
            f'{meters_html(w["meters"], compact=True)}'
            f'<span class="wcard-tags">{"".join(f"<i>{esc(t)}</i>" for t in w["tags"])}</span>'
            f"</a>"
        )
    tag_btns = '<button class="chip active" data-tag="">すべて</button>' + "".join(
        f'<button class="chip" data-tag="{esc(t)}">{esc(t)}</button>' for t in all_tags
    )
    planned_html = "".join(f"<li>{esc(p)}</li>" for p in planned)
    meter_help = "".join(f"<li><b>{esc(k)}</b>{esc(v)}</li>" for k, v in METER_HELP.items())

    return (
        head(SITE_TITLE, SITE_DESC, 0)
        + f"""<main>
<section class="hero"><div class="wrap">
<p class="hero-kicker">GENDAI AIMAI TANGO JITEN</p>
<h1 class="hero-title">現代<br class="sp">曖昧<br class="sp">単語辞典</h1>
<p class="hero-lead">「蛙化した」「メロい」「ドパガキ」。よく見かけるのに、聞く人によって意味がずれる言葉があります。この辞典では、そうした言葉を一語ずつ取り上げ、語源、広まった経緯、意味の幅、誤用されやすい点を調べてまとめています。</p>
<div class="hero-stats"><div><b>{len(words)}</b><span>収録語</span></div><div><b>{len(planned)}</b><span>収録予定</span></div></div>
</div></section>

<section class="wrap" id="list">
<div class="list-head">
<h2 class="list-title">収録語</h2>
<div class="controls">
<label class="search"><span class="sr">言葉を探す</span><input id="q" type="search" placeholder="言葉・読み・タグで探す" autocomplete="off"></label>
<label class="sort"><span class="sr">並び順</span><select id="sort">
<option value="amb">曖昧度が高い順</option>
<option value="mis">誤用度が高い順</option>
<option value="date">更新が新しい順</option>
<option value="kana">五十音順</option>
</select></label>
</div>
</div>
<div class="chips" role="group" aria-label="タグで絞り込む">{tag_btns}</div>
<div class="grid" id="grid">{"".join(cards)}</div>
<p class="empty" id="empty" hidden>条件に合う言葉はまだ収録されていません。</p>
</section>

<section class="wrap twocol">
<div class="panel">
<h2>メーターの見方</h2>
<p>各項目を5段階で示しています。数値は調べた資料をもとにした編集部の目安です。</p>
<ul class="meter-help">{meter_help}</ul>
</div>
<div class="panel">
<h2>収録予定の言葉</h2>
<ul class="planned">{planned_html}</ul>
</div>
</section>
</main>
"""
        + foot(0)
    )


def about_page():
    return (
        head(f"この辞典について｜{SITE_TITLE}", SITE_DESC, 0)
        + """<main class="wrap prose">
<h1 class="page-title">この辞典について</h1>
<h2>なぜ作ったか</h2>
<p>SNSで流行する言葉は、広まる途中で意味が少しずつ変わります。もともとの意味を知らずに使う人、別の意味で受け取る人、皮肉として使う人が混ざり、同じ言葉で話していても話がかみ合わないことがあります。</p>
<p>この辞典は、そうした「流行っているが曖昧な言葉」を一語一ページで取り上げます。正しい意味を一つに決めるのではなく、意味の幅と、ずれが生まれた経緯を見えるようにすることを目指しています。</p>
<h2>各ページの構成</h2>
<ul>
<li>ひとことで言うと：いまの主な意味</li>
<li>意味の地図：原義、広がった使い方、出典から離れた使い方の整理</li>
<li>語源・成り立ち／広まった経緯</li>
<li>ズレやすいポイント・誤解</li>
<li>使用例：自然な例とズレた例</li>
<li>多様な観点から：心理学、脳科学、言語学、社会、マーケティングなど</li>
<li>言い換え・関連語・出典</li>
</ul>
<h2>情報の扱い</h2>
<p>流行語の初出や語源は、確定できないことが多くあります。説が複数あるものは複数のまま書き、確認できなかったことは確認できなかったと書いています。各ページの末尾に出典を載せていますので、気になる点は出典をあわせてご確認ください。</p>
<p>メーター（曖昧度・誤用度・トゲ度・定着度）は、調べた資料をもとにした編集上の目安で、統計的な指標ではありません。</p>
</main>
"""
        + foot(0)
    )


def main():
    words = []
    for p in sorted(DATA.glob("*.json")):
        words.append(json.loads(p.read_text(encoding="utf-8")))
    words.sort(key=lambda w: -w["meters"].get("曖昧度", 0))
    planned = json.loads((ROOT / "data" / "planned.json").read_text(encoding="utf-8"))

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "words").mkdir(parents=True)
    shutil.copytree(ASSETS, OUT / "assets")
    (OUT / ".nojekyll").write_text("")

    (OUT / "index.html").write_text(index_page(words, planned), encoding="utf-8")
    (OUT / "about.html").write_text(about_page(), encoding="utf-8")
    for w in words:
        (OUT / "words" / f'{w["slug"]}.html').write_text(word_page(w, words), encoding="utf-8")
    print(f"built {len(words)} words -> {OUT}")


if __name__ == "__main__":
    main()
