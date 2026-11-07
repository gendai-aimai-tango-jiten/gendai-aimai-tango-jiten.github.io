# 現代曖昧単語辞典：Claude Code 向けの引き継ぎ

流行っているのに意味がふわっとしている言葉を、一語一ページでまとめる静的サイトです。
https://gendai-aimai-tango-jiten.github.io/

運営者は黒田悠介さん（GitHub アカウント ashitano-tenki、組織 gendai-aimai-tango-jiten）。お手本は同じ運営者の「コミュニティ図鑑」と「あしたの転機観測所」で、見た目はデザインシステム「黒田悠介」（明るい地、空色、黄色の蛍光ペン、Noto Emoji の絵）に合わせています。

## 目的

SNSで「面白いサイトだ」と広まり、多くの人に読まれること（2026-11-07 黒田さんの方針）。

## 仕組み

1. 1語＝1ファイル（data/words/<slug>.json）。書き方は notes/_guide.md、次に書く候補は notes/queue.md。
2. `python3 build.py` で docs/ に静的HTMLを作る（標準ライブラリだけ）。CSSとJSのURLには中身のハッシュを付け、古いファイルが残らないようにしている。
3. `python3 tools/make_og.py` で共有画像（docs/og/*.png）を作る（Pillow と macOS のヒラギノ角ゴシックが必要）。
4. docs/ をコミットして push すると、GitHub Pages（main の /docs）が公開する。ビルドは GitHub 側では行わない。

## 道具

| ファイル | 中身 |
|---|---|
| tools/fetch_emoji.py | 語の emoji に使う Noto Emoji の画像（128px と 512px）を取ってくる |
| tools/check_words.py | 語のデータの点検。`--links` で出典のURLも開く。自動のアクセスを断るサイトは config/linkcheck.json の refusing_hosts に入れて除外する |
| .github/workflows/check-links.yml | 毎週月曜 7:00 に出典のリンクを点検し、問題があれば Issue を作る |
| 定期タスク「gendai-aimai-words」 | Claude のデスクトップアプリの定期タスク。毎週火曜と金曜の10:00ごろに、notes/queue.md から2語を選んで書き、公開する。手順は ~/.claude/scheduled-tasks/gendai-aimai-words/SKILL.md |

## ページ

| URL | 中身 |
|---|---|
| / | トップ。収録語の一覧（新着順・曖昧度順・五十音順、検索、タグの絞り込み、24語ずつ「もっと見る」）、この辞典の読み方 |
| /words/{slug}/ | 単語ページ。30秒でわかる、曖昧メーター、どういう意味？、あなたはどの意味派？、意味の変遷、語源・成り立ち、広まった経緯、ズレのポイント、多様な観点（タブ）、使用シーン、関連語、出典、シェア、タグの近い6語 |
| /about/ | この辞典について |

## 守ること（黒田さんの判断）

- クイズは作らない（2026-11-08 に外した）。
- シェアは X・Facebook・Threads・リンクのコピー。LINE は使わない。
- カードや箱の端に色の帯（左や上の線）を付けない。区別は箱全体の薄い色か札の色で。
- 出典の下に補足文を付けない。GitHub のリンクや Issue の案内を画面に出さない。
- メーターは曖昧度・誤用度・通用度の3つ。説明文は build.py の METERS。
- 見た目を大きく変えるときは、先に黒田さんに見せて選んでもらう。
- 黒田さんへの返答・報告は日本語で。日本語の文章は yomiyasu スキルの方針で書く。
