#!/usr/bin/env python3
"""data/words/*.json の中身を点検する。

使い方: python3 tools/check_words.py [--links] [--only slug1,slug2]
--links を付けると、出典URLを実際に開いて確かめる（時間がかかる）。
--only を付けると、開く出典をその語のものだけにする（項目の点検は全語に行う）。
問題があれば一覧を出して終了コード1で終わる。
"""
import json
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["slug", "word", "reading", "pos", "emoji", "catch", "oneliner", "tldr", "tags", "origin_date", "peak",
            "added", "updated", "meters", "definition", "usages", "etymology", "timeline", "misuses", "perspectives",
            "who_where", "related", "sources"]
METERS = {"曖昧度", "誤用度", "通用度"}
TYPES = {"原義", "拡張", "誤用寄り"}


def check_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; jiten-linkcheck)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return url, r.status
    except urllib.error.HTTPError as e:
        return url, e.code
    except Exception as e:  # noqa: BLE001
        return url, str(e)[:60]


def main():
    problems = []
    words = {}
    for p in sorted((ROOT / "data" / "words").glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            problems.append(f"{p.name}: JSONとして読めない {e}")
            continue
        miss = [k for k in REQUIRED if k not in d]
        if miss:
            problems.append(f"{p.name}: 項目がない {miss}")
            continue
        if d["slug"] != p.stem:
            problems.append(f"{p.name}: slug がファイル名と違う")
        if set(d["meters"]) != METERS or not all(1 <= int(v) <= 5 for v in d["meters"].values()):
            problems.append(f"{p.name}: meters がおかしい {d['meters']}")
        if len(d["tldr"]) != 3:
            problems.append(f"{p.name}: tldr が3つでない")
        for u in d["usages"]:
            if u.get("type") not in TYPES:
                problems.append(f"{p.name}: usages の type がおかしい {u.get('type')}")
        if not (ROOT / "assets" / "emoji" / f"{d['emoji']}.png").exists():
            problems.append(f"{p.name}: 絵文字の画像がない {d['emoji']}")
        if len(d["sources"]) < 2:
            problems.append(f"{p.name}: 出典が2つ未満")
        if d["word"] in words:
            problems.append(f"{p.name}: 見出し語が {words[d['word']]} と重複")
        words[d["word"]] = p.name

    if "--links" in sys.argv:
        only = None
        if "--only" in sys.argv:
            only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
        urls = sorted({s["url"] for p in (ROOT / "data" / "words").glob("*.json")
                       if only is None or p.stem in only
                       for s in json.loads(p.read_text(encoding="utf-8")).get("sources", [])})
        # 自動のアクセスを断るがブラウザでは開けるサイトは、問題として数えない
        cfg = ROOT / "config" / "linkcheck.json"
        refusing = set(json.loads(cfg.read_text(encoding="utf-8")).get("refusing_hosts", [])) if cfg.exists() else set()
        skipped = 0
        with ThreadPoolExecutor(8) as ex:
            for url, st in ex.map(check_url, urls):
                if st == 200:
                    continue
                if urllib.parse.urlparse(url).hostname in refusing and st in (403, 503):
                    skipped += 1
                    continue
                problems.append(f"リンク {st}: {url}")
        print(f"リンク {len(urls)}件を点検（自動のアクセスを断るサイト {skipped}件は除外）")

    print(f"{len(words)}語を点検")
    for x in problems:
        print(" -", x)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
