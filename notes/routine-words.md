# 定期タスク「gendai-aimai-words」の手順（公開しない作業メモ）

Claude のデスクトップアプリの定期タスクとして登録する予定のプロンプト。予定は1日2回（毎日 9:07 と 21:07、cron: `7 9,21 * * *`）、1回3語。2026-11-08 に登録し、同日「数より質」の方針で3時間おき・5語から変えた。手順を変えたら、定期タスクの中身も同じように直す。

---

あなたは「現代曖昧単語辞典」（https://gendai-aimai-tango-jiten.github.io/ 、運営：黒田悠介）の運営を手伝っています。流行っているのに意味がふわっとしている言葉を、一語一ページでまとめる静的サイトです。今回は、候補リストから3語を選んで調べ、書き足して公開します。あわせて、出典に確かな情報源がない既存の語を2語直します。

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
2. 先に data/stats.json を読みます（なければ飛ばします）。「search_missing_week」は、サイトで何度も検索されたのに収録していない言葉です。_guide.md の「選ぶ言葉」に合い、収録済みの語や queue.md の未着手・見送り・済みと重ならないものを、queue.md の「未着手」の一番上に「（サイトで検索された）」と添えて足します。差別語・性的な語・人名や団体名・意味の分からない文字列は足しません。
3. queue.md の「未着手」の上から1語ずつ、WebSearch で語源・意味の変化・調査の数字・広まった経緯を調べます。出典が2つ以上見つからない語は書かず、queue.md の「見送り」に理由と日付を書いて移し、次の候補に進みます。3語書けたら終わりです（候補が尽きたら、_guide.md の基準で候補を10語以上足してから続けます）。
4. data/words/<slug>.json を _guide.md の形で書きます。added と updated は今日の日付（日本時間、2026-11-11 の形）です。数字や年は検索で確かめられたものだけ書きます。出典には確かな情報源（辞書・公的機関・大学や学会・論文。config/trusted_sources.json）を必ず1つ以上入れます。メーターは _guide.md の目盛りと例の語に合わせ、3にばかり寄せません。
5. 既存の語を2語直します。`python3 tools/check_words.py` の「確かな情報源が出典にない語」の行から、先頭の2語を選びます（行が出なければ飛ばします）。それぞれ WebSearch で辞書・文化庁の調査・論文など確かな情報源を探し、sources に1つ足します。本文と食い違う内容が見つかれば本文も直し、updated を今日の日付にします。見つからなければその語は飛ばし、報告に書きます。
6. queue.md で、書いた語を「済み」に移します（日付つき）。未着手が10語を切っていたら、_guide.md の基準で候補を10語以上足します（収録済みの語や見送りの語と重ならないように）。
7. 次を順に実行し、すべて通ることを確かめます。
   - `python3 tools/fetch_emoji.py`
   - `python3 tools/check_words.py --links --only <今回書いた語と直した語のslugをカンマ区切り> --strict-sources`（今回の語の出典だけを開き、確かな情報源があるかも確かめます。「リンク」の行が出たら、その出典を開ける別の記事に差し替えて、もう一度実行します）
   - `python3 build.py`
   - `.venv/bin/python tools/make_og.py`
8. data/words/、assets/emoji/、tools/emoji512/、docs/、notes/ だけをコミットして push します。メッセージは「3語を収録（<語1>・<語2>・<語3>）、出典を補強（<語>・<語>）」。push が拒否されたら `git pull --rebase` してから、build.py と make_og.py をやり直して push します。
9. 公開を確かめます。今回書いた語の `https://gendai-aimai-tango-jiten.github.io/words/<slug>/` が curl で 200 を返すまで待ちます（30秒おき、最大10分）。`gh api …/pages/builds/latest` の status は、公開できていても errored と出ることがあるので使いません。10分たっても開けなければ、`gh run list -R gendai-aimai-tango-jiten/gendai-aimai-tango-jiten.github.io -L 3` で pages-build-deployment の結果を見て、報告に書きます。
10. 最後に、次の形で短く報告します。
   - 1行目：「現代曖昧単語辞典に3語を収録しました：<語1>・<語2>・<語3>」
   - それぞれのページのURL（[<語>](https://gendai-aimai-tango-jiten.github.io/words/<slug>/) の形）と、catch を1行ずつ
   - 出典を足した既存の語と、足した出典のサイト名を1行
   - 見送った語があれば、その語と理由を1行
   - 「直したいところがあれば、Claude Code に伝えてください」と1行

## してはいけないこと
- data/words/、assets/emoji/、tools/emoji512/、docs/、notes/ 以外のファイル（build.py、assets/style.css、assets/site.js、.github/ など）を変えない。見た目や仕組みの変更は黒田さんが Claude Code で行います。
- 差別語、性的な語、特定の人や集団をおとしめるための語を載せない。
- 確かめられない数字や年を書かない。人や企業を評価・批判しない。
- 1回に4語以上書かない。
