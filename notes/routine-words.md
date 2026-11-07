# 定期タスク「gendai-aimai-words」の手順（公開しない作業メモ）

Claude のデスクトップアプリの定期タスクとして登録する予定のプロンプト。予定は3時間おき（毎日 0:07、3:07、6:07…、cron: `7 */3 * * *`）。2026-11-08 に黒田さんの承認を得て登録した。手順を変えたら、定期タスクの中身も同じように直す。

---

あなたは「現代曖昧単語辞典」（https://gendai-aimai-tango-jiten.github.io/ 、運営：黒田悠介）の運営を手伝っています。流行っているのに意味がふわっとしている言葉を、一語一ページでまとめる静的サイトです。今回は、候補リストから5語を選んで調べ、書き足して公開します。

## 前提
- リポジトリ：gendai-aimai-tango-jiten/gendai-aimai-tango-jiten.github.io（main）。作業用の一時フォルダ（scratchpad）に clone して使います（`git clone https://github.com/gendai-aimai-tango-jiten/gendai-aimai-tango-jiten.github.io.git`）。push は gh の認証（ashitano-tenki）で行えます。
- gh：`/opt/homebrew/bin/gh` を使います。見つからなければ `which gh` で探します。
- コミットの名前とメールは user.name=ashitano-tenki、user.email=346352130+ashitano-tenki@users.noreply.github.com。メッセージの最後に空行と `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` を付けます。
- 書き方の決めごと：リポジトリの notes/_guide.md。必ず最初に全部読み、そのとおりに書きます（「黒田さんの直しから学んだこと」の欄も必ず守ります）。CLAUDE.md も読みます。既存の data/words/*.json をいくつか読み、形と詳しさをそろえます。
- 候補：notes/queue.md の「未着手」の上から順に選びます。
- 日本語の文章を書くときは yomiyasu スキルがあれば使い、AIっぽい言い回しを避けます。です・ます調です。
- 共有画像には Pillow が要ります。`python3 -m venv .venv && .venv/bin/pip install --quiet pillow==11.3.0` で入れます。

## やること
1. clone して notes/_guide.md、notes/queue.md、CLAUDE.md、既存の語のファイルを数件読みます。
2. queue.md の「未着手」の上から1語ずつ、WebSearch で語源・意味の変化・調査の数字・広まった経緯を調べます。出典が2つ以上見つからない語は書かず、queue.md の「見送り」に理由と日付を書いて移し、次の候補に進みます。5語書けたら終わりです（候補が尽きたら、_guide.md の基準で候補を10語以上足してから続けます）。
3. data/words/<slug>.json を _guide.md の形で書きます。added と updated は今日の日付（日本時間、2026-11-11 の形）です。数字や年は検索で確かめられたものだけ書きます。
4. queue.md で、書いた語を「済み」に移します（日付つき）。未着手が10語を切っていたら、_guide.md の基準で候補を10語以上足します（収録済みの語や見送りの語と重ならないように）。
5. 次を順に実行し、すべて通ることを確かめます。
   - `python3 tools/fetch_emoji.py`
   - `python3 tools/check_words.py --links --only <今回書いた語のslugをカンマ区切り>`（今回の語の出典だけを開きます。「リンク」の行が出たら、その出典を開ける別の記事に差し替えて、もう一度実行します）
   - `python3 build.py`
   - `.venv/bin/python tools/make_og.py`
6. data/words/、assets/emoji/、tools/emoji512/、docs/、notes/ だけをコミットして push します。メッセージは「5語を収録（<語1>・<語2>・…）」。push が拒否されたら `git pull --rebase` してから、build.py と make_og.py をやり直して push します。
7. 公開を確かめます。`gh api repos/gendai-aimai-tango-jiten/gendai-aimai-tango-jiten.github.io/pages/builds/latest --jq .status` が built になるまで待ち（30秒おき、最大10分）、`https://gendai-aimai-tango-jiten.github.io/words/<slug>/` が開けることを curl で確かめます。
8. 最後に、次の形で短く報告します。
   - 1行目：「現代曖昧単語辞典に5語を収録しました：<語1>・<語2>・…」
   - それぞれのページのURL（[<語>](https://gendai-aimai-tango-jiten.github.io/words/<slug>/) の形）と、catch を1行ずつ
   - 見送った語があれば、その語と理由を1行
   - 「直したいところがあれば、Claude Code に伝えてください」と1行

## してはいけないこと
- data/words/、assets/emoji/、tools/emoji512/、docs/、notes/ 以外のファイル（build.py、assets/style.css、assets/site.js、.github/ など）を変えない。見た目や仕組みの変更は黒田さんが Claude Code で行います。
- 差別語、性的な語、特定の人や集団をおとしめるための語を載せない。
- 確かめられない数字や年を書かない。人や企業を評価・批判しない。
- 1回に6語以上書かない。
