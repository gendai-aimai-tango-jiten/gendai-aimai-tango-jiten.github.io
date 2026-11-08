#!/usr/bin/env python3
"""data/words/*.json の emoji に使う Noto Emoji の画像のうち、手元にないものを取ってくる。

使い方: python3 tools/fetch_emoji.py
128px は assets/emoji/、512px は tools/emoji512/ に置く。
"""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/2D/png/{size}/emoji_u{cp}.png"


def fetch(cp, size, dest):
    if dest.exists():
        return True
    try:
        with urllib.request.urlopen(URL.format(size=size, cp=cp), timeout=20) as r:
            dest.write_bytes(r.read())
        return True
    except Exception as e:  # noqa: BLE001
        print(f"取得できません: {cp} ({size}px) {e}", file=sys.stderr)
        return False


def main():
    bad = []
    # 語と曖昧ノートの絵文字
    files = sorted((ROOT / "data" / "words").glob("*.json")) + sorted((ROOT / "data" / "notes").glob("*.json"))
    for p in files:
        cp = json.loads(p.read_text(encoding="utf-8"))["emoji"]
        ok = fetch(cp, 128, ROOT / "assets" / "emoji" / f"{cp}.png")
        ok = fetch(cp, 512, ROOT / "tools" / "emoji512" / f"{cp}.png") and ok
        if not ok:
            bad.append(p.stem)
    if bad:
        print("絵文字がない語:", ", ".join(bad), file=sys.stderr)
        sys.exit(1)
    print("ok")


if __name__ == "__main__":
    main()
