#!/usr/bin/env python3
"""「あなたはどの意味派？」の回答数を GoatCounter から集めて data/poll.json に書く。

使い方: GOATCOUNTER_TOKEN=... python3 tools/fetch_poll.py
GitHub Actions（.github/workflows/poll.yml）が週1回動かす。標準ライブラリだけで動く。
site.js は回答のたびに「poll/words/<slug>/<番号>」というイベントを送っている（番号は意味の順、知らなかった は n）。
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://aimaijiten.goatcounter.com"
START = "2026-11-01T00:00:00Z"  # 計測を始めた日より前


def api(path, params):
    token = os.environ["GOATCOUNTER_TOKEN"]
    url = f"{SITE}/api/v0/{path}?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                time.sleep(0.3)  # 1秒に4回まで
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                time.sleep(2 + attempt * 2)
                continue
            raise


def main():
    if not os.environ.get("GOATCOUNTER_TOKEN"):
        print("GOATCOUNTER_TOKEN がありません", file=sys.stderr)
        sys.exit(1)
    # 1. イベントのうち poll/ で始まるものの ID を集める
    ids, after = {}, None
    while True:
        params = {"limit": 200}
        if after:
            params["after"] = after
        d = api("paths", params)
        for p in d.get("paths", []):
            name = p.get("path", "").lstrip("/")
            if p.get("event") and name.startswith("poll/words/"):
                ids[str(p["id"])] = name
        if not d.get("more") or not d.get("paths"):
            break
        after = d["paths"][-1]["id"]

    # 2. その ID の回答数を、計測開始から今までで数える
    end = dt.datetime.now(dt.timezone.utc).replace(minute=0, second=0, microsecond=0) + dt.timedelta(hours=1)
    counts = {}
    id_list = list(ids)
    for k in range(0, len(id_list), 50):
        chunk = id_list[k:k + 50]
        d = api("stats/hits", {"start": START, "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"), "limit": 100,
                               "include_paths": chunk})
        for h in d.get("hits", []):
            name = ids.get(str(h.get("path_id"))) or h.get("path", "").lstrip("/")
            parts = name.split("/")  # poll / words / <slug> / <番号>
            if len(parts) != 4:
                continue
            slug, i = parts[2], parts[3]
            counts.setdefault(slug, {})
            counts[slug][i] = counts[slug].get(i, 0) + int(h.get("count", 0))

    out = {"updated": dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d"), "words": counts}
    (ROOT / "data" / "poll.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(counts)}語の回答を集計（イベント {len(ids)}種類）")


if __name__ == "__main__":
    main()
