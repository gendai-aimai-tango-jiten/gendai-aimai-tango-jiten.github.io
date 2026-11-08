#!/usr/bin/env python3
"""GoatCounter から辞典の数字を集めて、まとめたものを data/ に書く。

使い方: GOATCOUNTER_TOKEN=... python3 tools/fetch_stats.py
GitHub Actions（.github/workflows/stats.yml）が週1回動かす。標準ライブラリだけで動く。
トークンは GitHub の Secret にだけ置く。ここで書くファイルは公開されるので、まとめた数字だけを書く。

書くもの
- data/poll.json  「あなたはどの意味派？」の回答数（計測開始から）
- data/stats.json 語ごとの閲覧数・シェア数（直近7日と計測開始から）、全体の閲覧数、流入元の上位、
                  何度も検索されたのに収録していない言葉（個人の情報が混ざらないよう絞り込む）

site.js が送るイベント名
- poll/words/<slug>/<番号>   意味派（番号は意味の順、知らなかった は n）
- share/<x|facebook|threads|copy>/words/<slug>/  シェアボタン
- search/<入力した言葉>       検索欄（入力が1.5秒止まったとき、2文字以上）
"""
import datetime as dt
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://aimaijiten.goatcounter.com"
START = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)  # 計測を始めた日より前
JST = dt.timezone(dt.timedelta(hours=9))


def api(path, params=None):
    token = os.environ["GOATCOUNTER_TOKEN"]
    url = f"{SITE}/api/v0/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
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
            body = e.read().decode("utf-8", "replace")[:300]
            raise RuntimeError(f"{path}: HTTP {e.code} {body}") from None


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def hits(start, end):
    """期間内のページとイベントの数を、すべて取る。id → (名前, イベントか, 数)
    /stats/hits は1回に100件まで。取った id を exclude_paths に入れて続きを取る"""
    out, seen = {}, []
    for _ in range(100):
        params = {"start": iso(start), "end": iso(end), "limit": 100}
        if seen:
            params["exclude_paths"] = seen
        d = api("stats/hits", params)
        got = d.get("hits", []) or []
        for h in got:
            pid = str(h.get("path_id"))
            if pid in out:
                continue
            out[pid] = (h.get("path", ""), bool(h.get("event")), int(h.get("count", 0)))
            seen.append(pid)
        if not d.get("more") or not got:
            break
    return out


def norm(s):
    s = unicodedata.normalize("NFKC", s).lower().strip()
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def looks_private(term):
    """個人の情報が混ざっていそうな検索語は書かない"""
    if len(term) > 20 or len(term) < 2:
        return True
    if re.search(r"[@＠]|https?:|www\.|\d{4,}", term):
        return True
    return False


def main():
    if not os.environ.get("GOATCOUNTER_TOKEN"):
        print("GOATCOUNTER_TOKEN がありません", file=sys.stderr)
        sys.exit(1)
    now = dt.datetime.now(dt.timezone.utc).replace(minute=0, second=0, microsecond=0) + dt.timedelta(hours=1)
    week = now - dt.timedelta(days=7)
    words = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "data" / "words").glob("*.json")}

    h_all = hits(START, now)
    h_week = hits(week, now)
    paths = {pid: (v[0], v[1]) for pid, v in h_all.items()}
    for pid, v in h_week.items():
        paths.setdefault(pid, (v[0], v[1]))
    c_all = {pid: v[2] for pid, v in h_all.items()}
    c_week = {pid: v[2] for pid, v in h_week.items()}

    poll, per_word, searches = {}, {}, {}
    page_week = page_all = 0
    for pid, (name, event) in paths.items():
        a, w = c_all.get(pid, 0), c_week.get(pid, 0)
        name = name.strip()
        if not event:
            page_all += a
            page_week += w
            m = re.fullmatch(r"/?words/([a-z0-9-]+)/?", name)  # 末尾の / はない形で記録される
            if m and m.group(1) in words:
                s = per_word.setdefault(m.group(1), {"views7": 0, "viewsAll": 0, "shares7": 0, "sharesAll": 0})
                s["views7"] += w
                s["viewsAll"] += a
            continue
        name = name.lstrip("/")
        parts = [x for x in name.split("/") if x != ""] if not name.startswith("search/") else name.split("/")
        if parts[0] == "poll" and len(parts) == 4 and parts[2] in words:
            poll.setdefault(parts[2], {})
            poll[parts[2]][parts[3]] = poll[parts[2]].get(parts[3], 0) + a
        elif parts[0] == "share" and len(parts) >= 4 and parts[2] == "words" and parts[3] in words:
            s = per_word.setdefault(parts[3], {"views7": 0, "viewsAll": 0, "shares7": 0, "sharesAll": 0})
            s["shares7"] += w
            s["sharesAll"] += a
        elif parts[0] == "search" and len(parts) >= 2:
            term = urllib.parse.unquote("/".join(parts[1:])).strip()
            if w:
                searches[term] = searches.get(term, 0) + w

    # 収録している語・読み・タグに当たらない検索語だけを、候補として残す
    known = set()
    for d in words.values():
        known.update([norm(d["word"]), norm(d["reading"])] + [norm(t) for t in d["tags"]])
    missing = {}
    for term, n in searches.items():
        t = norm(term)
        if looks_private(term) or any(t in k or k in t for k in known if len(k) >= 2):
            continue
        missing[t] = missing.get(t, 0) + n
    missing = sorted(([t, n] for t, n in missing.items() if n >= 2), key=lambda x: -x[1])[:30]

    refs = []
    try:
        d = api("stats/toprefs", {"start": iso(week), "end": iso(now), "limit": 10})
        for r in d.get("stats", d.get("refs", [])) or []:
            name = r.get("name") or r.get("ref") or "（直接・不明）"
            if name.startswith("gendai-aimai-tango-jiten.github.io"):
                continue  # サイトの中の移動は流入元に数えない
            refs.append([name, int(r.get("count", 0))])
    except Exception as e:  # noqa: BLE001
        print("流入元は取れませんでした:", e, file=sys.stderr)

    today = dt.datetime.now(JST).strftime("%Y-%m-%d")
    (ROOT / "data" / "poll.json").write_text(
        json.dumps({"updated": today, "words": poll}, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    stats = {
        "updated": today,
        "week": {"start": week.astimezone(JST).strftime("%Y-%m-%d"), "end": now.astimezone(JST).strftime("%Y-%m-%d")},
        "views": {"week": page_week, "all": page_all},
        "words": per_word,
        "refs_week": refs,
        "search_missing_week": missing,
    }
    (ROOT / "data" / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"閲覧 直近7日 {page_week}・累計 {page_all}／意味派 {len(poll)}語／収録していない検索語 {len(missing)}件")


if __name__ == "__main__":
    main()
