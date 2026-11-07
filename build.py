#!/usr/bin/env python3
"""現代曖昧単語辞典 ビルドスクリプト

data/words/*.json を読み、docs/ に静的サイトを書き出す。
使い方: python3 build.py
共有画像（docs/og/*.png）は tools/make_og.py で別に作る（Pillow が必要）。
"""
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "words"
OUT = ROOT / "docs"
ASSETS = ROOT / "assets"

SITE = "現代曖昧単語辞典"
BASE_URL = "https://gendai-aimai-tango-jiten.github.io"
HASHTAG = "現代曖昧単語辞典"
DESC = "流行ってるのに、意味がふわっとしている言葉の辞典。蛙化現象、メロい、ドパガキなどを、語源・意味のズレ・誤用されやすい点から一語ずつ調べました。"
BRAND_EMOJI = "1f914"


def asset_ver(name):
    """中身が変わるとURLも変わるようにして、ブラウザに古いファイルを使わせない"""
    import hashlib
    return hashlib.md5((ASSETS / name).read_bytes()).hexdigest()[:8]

METERS = [
    ("曖昧度", "人によって指す範囲がどれだけばらつくか"),
    ("誤用度", "本来の意味とずれた使われ方がどれだけ多いか"),
    ("通用度", "上の世代や別の界隈にも通じるか"),
]
USAGE = {
    "原義": ("u-origin", "もともとの意味"),
    "拡張": ("u-extend", "広がった使い方"),
    "誤用寄り": ("u-misuse", "出典から離れた使い方"),
}


def esc(s):
    return html.escape(str(s), quote=True)


def inline(s):
    t = esc(s.strip()).replace("\n", "<br>")
    parts = t.split("**")
    return "".join(f"<strong>{p}</strong>" if i % 2 else p for i, p in enumerate(parts))


def paras(text):
    return "\n".join(f"<p>{inline(b)}</p>" for b in str(text).strip().split("\n\n"))


def emoji(cp, cls="emo", size=None):
    s = f' width="{size}" height="{size}"' if size else ""
    return f'<img class="{cls}" src="/assets/emoji/{cp}.png" alt=""{s} loading="lazy" decoding="async">'


def meter_bars(meters, big=False):
    rows = []
    for key, help_ in METERS:
        v = int(meters.get(key, 0))
        cells = "".join(f'<i class="{"on" if i < v else ""}"></i>' for i in range(5))
        if big:
            rows.append(
                f'<div class="mbar"><div class="mbar-top"><b>{key}</b><span class="mbar-num">{v}<small>/5</small></span></div>'
                f'<div class="mbar-cells" role="img" aria-label="{key} 5段階中{v}">{cells}</div><p>{esc(help_)}</p></div>'
            )
        else:
            rows.append(f'<div class="mini-m"><span>{key}</span><b role="img" aria-label="5段階中{v}">{cells}</b></div>')
    return f'<div class="{"mbars" if big else "mini-ms"}">{"".join(rows)}</div>'


def share_bar(text, url, label="シェアする", cls=""):
    return (
        f'<div class="share {cls}" data-text="{esc(text)}" data-url="{esc(url)}">'
        f'<span class="share-label">{esc(label)}</span>'
        '<button type="button" class="sbtn sx" data-share="x" aria-label="Xでシェア"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>ポスト</button>'
        '<button type="button" class="sbtn sf" data-share="facebook" aria-label="Facebookでシェア"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M24 12.07C24 5.41 18.63 0 12 0S0 5.4 0 12.07C0 18.1 4.39 23.1 10.13 24v-8.44H7.08v-3.49h3.04V9.41c0-3.02 1.8-4.7 4.54-4.7 1.31 0 2.68.24 2.68.24v2.97h-1.5c-1.5 0-1.96.93-1.96 1.89v2.26h3.32l-.53 3.5h-2.8V24C19.62 23.1 24 18.1 24 12.07"/></svg>Facebook</button>'
        '<button type="button" class="sbtn st" data-share="threads" aria-label="Threadsでシェア"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.7 11.1c-.1 0-.2-.1-.3-.1-.2-3-1.8-4.7-4.6-4.7h-.1c-1.7 0-3.1.7-3.9 2l1.6 1.1c.6-.9 1.6-1.1 2.3-1.1 1 0 1.7.3 2.2.9.3.4.6 1 .7 1.7-.8-.1-1.7-.2-2.6-.1-2.6.1-4.3 1.7-4.2 3.8.1 1.1.6 2 1.5 2.6.8.5 1.8.8 2.8.7 1.4-.1 2.5-.6 3.2-1.6.6-.7.9-1.7 1-2.9.7.4 1.2.9 1.5 1.6.5 1.1.5 2.9-1 4.4-1.3 1.3-2.8 1.8-5.1 1.8-2.6 0-4.5-.8-5.8-2.5C5.6 17.1 5 15 5 12.4s.6-4.7 1.9-6.3C8.2 4.4 10.1 3.6 12.7 3.6c2.6 0 4.6.8 5.9 2.5.6.8 1.1 1.8 1.5 3l1.9-.5c-.4-1.5-1.1-2.7-1.9-3.8C18.4 2.7 15.9 1.6 12.7 1.6h-.1C9.4 1.6 7 2.7 5.4 4.8 3.9 6.6 3.1 9.2 3.1 12.4s.8 5.7 2.3 7.6c1.6 2.1 4.1 3.2 7.2 3.2h.1c2.8 0 4.7-.7 6.3-2.3 2.1-2.1 2-4.7 1.3-6.3-.5-1.2-1.4-2.1-2.6-2.7zm-4.9 4.6c-1.1.1-2.3-.4-2.4-1.5 0-.8.6-1.7 2.4-1.8h.6c.7 0 1.3.1 1.9.2-.2 2.6-1.4 3-2.5 3.1z"/></svg>Threads</button>'
        '<button type="button" class="sbtn sc" data-share="copy" aria-label="リンクをコピー">リンクをコピー</button>'
        "</div>"
    )


def page(title, desc, body, path="/", og="/og/site.png", cls=""):
    url = BASE_URL + path
    full = title if title == SITE else f"{title}｜{SITE}"
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{esc(full)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{BASE_URL}{og}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#f7f9fb">
<link rel="icon" href="/assets/emoji/{BRAND_EMOJI}.png">
<link rel="apple-touch-icon" href="/assets/emoji/{BRAND_EMOJI}.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css?v={asset_ver("style.css")}">
</head>
<body class="{cls}">
<a class="skip" href="#main">本文へ</a>
<header class="hd"><div class="wrap hd-in">
<a class="logo" href="/">{emoji(BRAND_EMOJI, "logo-emo", 28)}<span>{SITE}</span></a>
<nav class="hd-nav" aria-label="メニュー">
<a href="/#words">収録語</a>
<a href="/about/">この辞典について</a>
<button type="button" class="hd-dice" data-random aria-label="ランダムに1つ見てみる" title="ランダムに1つ見てみる">{emoji("1f3b2", "dice-emo", 22)}</button>
</nav>
</div></header>
<main id="main">
{body}
</main>
<footer class="ft"><div class="wrap">
<p class="ft-logo">{emoji(BRAND_EMOJI, "logo-emo", 24)}{SITE}</p>
<p>流行っているのに意味がふわっとしている言葉を一語ずつ調べてまとめています。</p>
<p class="ft-links"><a href="/">トップ</a><a href="/about/">この辞典について</a></p>
</div></footer>
<script src="/assets/site.js?v={asset_ver("site.js")}" defer></script>
</body>
</html>
"""


def word_card(w, rank=None):
    amb = w["meters"].get("曖昧度", 0)
    r = f'<span class="wc-rank">No.{rank}</span>' if rank else ""
    return (
        f'<a class="wc" href="/words/{w["slug"]}/">'
        f'{r}<span class="wc-circle">{emoji(w["emoji"], "wc-emo")}</span>'
        f'<span class="wc-reading">{esc(w["reading"])}</span>'
        f'<span class="wc-word">{esc(w["word"])}</span>'
        f'<span class="wc-catch">{esc(w["catch"])}</span>'
        f'<span class="wc-amb"><span>曖昧度</span><b style="--v:{amb}"></b><em>{amb}</em></span>'
        f'<span class="wc-tags">{"".join(f"<i>{esc(t)}</i>" for t in w["tags"][:3])}</span>'
        "</a>"
    )


def index_page(words):
    ranked = sorted(words, key=lambda w: (-w["meters"].get("曖昧度", 0), -w["meters"].get("誤用度", 0)))
    cards = "".join(word_card(w, i + 1) for i, w in enumerate(ranked))
    body = f"""
<section class="hero"><div class="wrap hero-in">
<h1 class="hero-title"><span class="mk">{SITE}</span></h1>
<p class="hero-catch">その言葉、<br class="sp">ほんとに<em>同じ意味</em>で<br class="sp">使ってる？</p>
<p class="hero-lead">「蛙化した」「メロい」「ドパガキ」。よく見かけるのに、聞く人によって意味がずれる言葉を、一語ずつ調べました。語源、広まった経緯、意味のズレ、誤用されやすい点までまとめています。</p>
<div class="hero-cta">
<div class="stat"><b data-count="{len(words)}">{len(words)}</b><span>収録語</span></div>
<button type="button" class="btn btn-main" data-random>{emoji("1f3b2", "btn-emo")}ランダムに1つ見てみる</button>
</div>
</div>
<div class="hero-float" aria-hidden="true">{"".join(emoji(w["emoji"], "fl fl" + str(i)) for i, w in enumerate(words))}</div>
</section>

<section class="wrap sec-block" id="words">
<div class="block-head"><h2 class="block-title"><span class="mk">曖昧度ランキング</span></h2>
<p class="block-sub">意味のばらつきが大きい順に並べています。気になる言葉から読んでみてください。</p></div>
<div class="wgrid">{cards}</div>
</section>

<section class="wrap sec-block">
<div class="panel guide">
<div class="guide-text">
<h2>{emoji("1f4d6", "inline-emo")}この辞典の読み方</h2>
<p>各ページでは、言葉の意味を「もともとの意味」「広がった使い方」「出典から離れた使い方」に分けて整理。正解を一つに決めるのではなくどこでズレが生まれたかを知ることができます。</p>
<p><a href="/about/">この辞典について詳しく</a></p>
</div>
<ul class="mhelp">{"".join(f"<li><b>{k}</b>{esc(v)}</li>" for k, v in METERS)}</ul>
</div>
</section>
"""
    return page(SITE, DESC, body, "/", "/og/site.png", "home")


def word_page(w, words):
    slug_map = {x["word"]: x["slug"] for x in words}
    url = f"{BASE_URL}/words/{w['slug']}/"
    toc = []
    secs = []

    def add(sid, icon, title, inner, extra=""):
        toc.append(f'<a href="#{sid}">{esc(title)}</a>')
        secs.append(f'<section class="wsec {extra}" id="{sid}"><h2 class="wsec-title">{emoji(icon, "inline-emo")}{esc(title)}</h2>{inner}</section>')

    # あなたはどの意味派？
    opts = "".join(
        f'<button type="button" class="poll-opt" data-type="{esc(u["type"])}" data-label="{esc(u["label"])}">'
        f'<span class="poll-tag {USAGE[u["type"]][0]}">{esc(u["type"])}</span>{esc(u["label"])}</button>'
        for u in w["usages"]
    )
    poll = f"""<div class="poll" data-word="{esc(w["word"])}" data-url="{esc(url)}">
<p class="poll-q">あなたは「{esc(w["word"])}」を、どの意味で使っていましたか？</p>
<div class="poll-opts">{opts}<button type="button" class="poll-opt" data-type="none" data-label="この言葉を知らなかった"><span class="poll-tag u-none">？</span>この言葉を知らなかった</button></div>
<div class="poll-result" hidden></div>
</div>"""
    add("poll", "1f914", "あなたはどの意味派？", poll, "wsec-poll")

    # 意味の変遷
    items = "".join(
        f'<li class="umap-item {USAGE[u["type"]][0]}"><span class="umap-tag">{esc(u["type"])}<small>{USAGE[u["type"]][1]}</small></span>'
        f'<h3>{esc(u["label"])}</h3>{paras(u["desc"])}</li>'
        for u in w["usages"]
    )
    add("map", "1f50d", "意味の変遷", f'<p class="wsec-lead">もともとの意味から、いまの使われ方までを順に並べています。下にいくほど出典から離れます。</p><ol class="umap">{items}</ol>')


    add("etymology", "1f4d6", "語源・成り立ち", paras(w["etymology"]))

    tl = "".join(f'<li><time>{esc(t["date"])}</time><div>{paras(t["event"])}</div></li>' for t in w["timeline"])
    add("timeline", "1f4e3", "広まった経緯", f'<ol class="tl">{tl}</ol>')

    mis = "".join(f'<div class="mis"><h3>{esc(m["title"])}</h3>{paras(m["body"])}</div>' for m in w["misuses"])
    add("misuses", "1f440", "ズレのポイント", f'<div class="miss">{mis}</div>')

    tabs = "".join(
        f'<button type="button" role="tab" class="ptab{" on" if i == 0 else ""}" aria-selected="{"true" if i == 0 else "false"}" data-i="{i}">{esc(p["label"].split(" ──")[0])}</button>'
        for i, p in enumerate(w["perspectives"])
    )
    panels = "".join(
        f'<div class="ppanel" role="tabpanel" data-i="{i}"{"" if i == 0 else " hidden"}><h3>{esc(p["label"])}</h3>{paras(p["body"])}</div>'
        for i, p in enumerate(w["perspectives"])
    )
    add("perspectives", "1f4ad", "多様な観点", f'<div class="ptabs" role="tablist">{tabs}</div><div class="ppanels">{panels}</div>')

    add("who", "1f4ac", "使用シーン", paras(w["who_where"]))


    rel = []
    for r in w["related"]:
        name = esc(r["word"])
        if r["word"] in slug_map:
            name = f'<a href="/words/{slug_map[r["word"]]}/">{name}</a>'
        rel.append(f'<li><b>{name}</b><span>{esc(r["note"])}</span></li>')
    add("related", "2728", "関連語", f'<ul class="rels">{"".join(rel)}</ul>')

    src = "".join(
        f'<li><a href="{esc(s["url"])}" rel="noopener" target="_blank">{esc(s["title"])}</a></li>'
        for s in w["sources"]
    )
    add("sources", "1f4dd", "出典・参考", f'<ol class="srcs">{src}</ol>')

    tldr = "".join(f"<li>{esc(t)}</li>" for t in w["tldr"])
    share_text = f"「{w['word']}」の意味、ちゃんと分かってる？ {w['catch']}"
    others = [x for x in words if x["slug"] != w["slug"]]
    body = f"""
<article class="word">
<header class="whero"><div class="wrap whero-in">
<p class="crumb"><a href="/">{SITE}</a><span>›</span><a href="/#words">収録語</a></p>
<div class="whero-main">
<span class="whero-circle">{emoji(w["emoji"], "whero-emo")}</span>
<div>
<p class="whero-reading">{esc(w["reading"])}<span class="pos">{esc(w["pos"])}</span></p>
<h1 class="whero-word">{esc(w["word"])}</h1>
</div>
</div>
<p class="whero-catch"><span class="mk">{esc(w["catch"])}</span></p>
<div class="whero-tags">{"".join(f"<span>{esc(t)}</span>" for t in w["tags"])}</div>
{share_bar(share_text, url, label="この言葉をシェア")}
</div></header>

<div class="wrap wbody">
<div class="wmain">
<section class="tldr">
<p class="tldr-title">{emoji("1f525", "inline-emo")}30秒でわかる「{esc(w["word"])}」</p>
<ol>{tldr}</ol>
<dl class="facts"><div><dt>初出・発祥</dt><dd>{esc(w["origin_date"])}</dd></div><div><dt>流行のピーク</dt><dd>{esc(w["peak"])}</dd></div><div><dt>最終更新</dt><dd>{esc(w["updated"])}</dd></div></dl>
</section>
<section class="wsec" id="meters"><h2 class="wsec-title">{emoji("1f3c6", "inline-emo")}曖昧メーター</h2>{meter_bars(w["meters"], big=True)}</section>
<section class="wsec" id="definition"><h2 class="wsec-title">{emoji("1f4d6", "inline-emo")}どういう意味？</h2>{paras(w["definition"])}</section>
{"".join(secs)}
<section class="endcta">
<p class="endcta-title">まわりの人は、どの意味で使ってる？</p>
<p>同じ言葉でも、人によって思い浮かべる意味が違います。友だちや家族に聞いてみてください。</p>
{share_bar(share_text, url, label="このページを送る", cls="share-big")}
</section>
</div>
<aside class="wside"><nav class="wtoc" aria-label="このページの目次"><p>目次</p><a href="#meters">曖昧メーター</a><a href="#definition">どういう意味？</a>{"".join(toc)}</nav></aside>
</div>
</article>

<section class="wrap sec-block">
<div class="block-head"><h2 class="block-title"><span class="mk">ほかの曖昧な言葉</span></h2></div>
<div class="wgrid">{"".join(word_card(x) for x in others)}</div>
</section>
"""
    return page(f"{w['word']}とは？意味・語源・使い方のズレ", f"{w['catch']} {w['oneliner']}", body,
                f"/words/{w['slug']}/", f"/og/{w['slug']}.png", "wordpage")


def about_page():
    body = """
<section class="wrap prose">
<h1 class="page-title"><span class="mk">この辞典について</span></h1>
<h2>なぜ作ったか</h2>
<p>SNSで流行する言葉は、広まる途中で意味が少しずつ変わります。もともとの意味を知らずに使う人、別の意味で受け取る人、皮肉として使う人が混ざり、同じ言葉で話していても話がかみ合わないことがあります。</p>
<p>この辞典では、そうした「流行っているのに意味がふわっとしている言葉」を一語一ページで取り上げます。正しい意味を一つに決めるのではなく、意味の幅と、ずれが生まれた経緯を見えるようにすることを目指しています。</p>
<h2>各ページの中身</h2>
<ul>
<li>30秒でわかる要点と、曖昧メーター</li>
<li>あなたはどの意味派？：自分の使い方を選ぶと、その意味の位置づけが分かります</li>
<li>意味の変遷：もともとの意味、広がった使い方、出典から離れた使い方</li>
<li>語源、広まった経緯、ズレのポイント</li>
<li>多様な観点：心理学、脳科学、言語学、世代論、海外との比較など</li>
<li>使用シーン、関連語、出典</li>
</ul>
<h2>曖昧メーター</h2>
<p>曖昧度・誤用度・通用度を5段階で示しています。調べた資料をもとに編集部が付けた目安で、統計的な指標ではありません。</p>
<h2>情報の扱い</h2>
<p>流行語の初出や語源は、確定できないことがよくあります。説が複数あるものは複数のまま書き、確認できなかったことは「〜とされる」と書いています。各ページの末尾に出典を載せていますので、あわせてご確認ください。</p>
</section>
"""
    return page("この辞典について", DESC, body, "/about/", "/og/site.png", "aboutpage")


def notfound_page():
    body = f"""<section class="wrap prose center"><p class="nf-emo">{emoji("1f914", "big-emo", 96)}</p>
<h1 class="page-title">そのページは見つかりませんでした</h1><p>言葉の意味と同じく、URLもずれていたのかもしれません。</p>
<p><a class="btn btn-main" href="/">トップへ戻る</a></p></section>"""
    return page("ページが見つかりません", DESC, body, "/404.html")


def main():
    words = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(DATA.glob("*.json"))]

    og_keep = OUT / "og"
    tmp_og = ROOT / ".og-tmp"
    if og_keep.exists():
        shutil.rmtree(tmp_og, ignore_errors=True)
        shutil.copytree(og_keep, tmp_og)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ASSETS, OUT / "assets")
    if tmp_og.exists():
        shutil.copytree(tmp_og, OUT / "og")
        shutil.rmtree(tmp_og)
    (OUT / ".nojekyll").write_text("")

    def write(rel, text):
        p = OUT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    write("index.html", index_page(words))
    write("about/index.html", about_page())
    write("404.html", notfound_page())
    for w in words:
        write(f"words/{w['slug']}/index.html", word_page(w, words))
    write("words.json", json.dumps([{"slug": w["slug"], "word": w["word"]} for w in words], ensure_ascii=False))

    urls = ["/", "/about/"] + [f"/words/{w['slug']}/" for w in words]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{BASE_URL}{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    print(f"built {len(words)} words -> {OUT}")


if __name__ == "__main__":
    main()
