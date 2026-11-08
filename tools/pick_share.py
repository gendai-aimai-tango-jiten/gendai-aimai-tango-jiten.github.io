#!/usr/bin/env python3
"""次にシェアする語の候補を、よい順に出す（毎週水曜の定期タスク「gendai-aimai-share」が使う）。

使い方: python3 tools/pick_share.py [件数]
notes/share-log.md にまだない語を、次の点数の高い順に並べる。
- 推奨度（build.py の recommend_scores）を半分
- 直近7日の読まれ方（閲覧数と、シェア数を閲覧5回分として数えたもの。data/stats.json）を半分
data/stats.json がない、または数字がまだない週は、推奨度だけで並ぶ。
出力：slug、語、catch、点数（タブ区切り）
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    words = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "data" / "words").glob("*.json"))]
    log = (ROOT / "notes" / "share-log.md")
    shared = set(re.findall(r"/words/([a-z0-9-]+)/", log.read_text(encoding="utf-8"))) if log.exists() else set()
    rec = build.recommend_scores(words)
    stats = build.STATS.get("words", {})
    recent = {w["slug"]: math.log1p(stats.get(w["slug"], {}).get("views7", 0) + 5 * stats.get(w["slug"], {}).get("shares7", 0))
              for w in words}
    hi = max(recent.values()) or 1
    rows = []
    for w in words:
        if w["slug"] in shared:
            continue
        score = 0.5 * rec[w["slug"]] + 0.5 * recent[w["slug"]] / hi
        rows.append((score, w))
    rows.sort(key=lambda x: (-x[0], x[1]["reading"]))
    for score, w in rows[:n]:
        print(w["slug"], w["word"], w["catch"], f"{score:.3f}", sep="\t")


if __name__ == "__main__":
    main()
