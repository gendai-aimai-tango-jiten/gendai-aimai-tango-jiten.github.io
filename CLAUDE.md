# 現代曖昧単語辞典：Claude Code 向けの引き継ぎ

流行っているのに意味がふわっとしている言葉を、一語一ページでまとめる静的サイトです。
https://gendai-aimai-tango-jiten.github.io/

運営者は黒田悠介さん（GitHub アカウント ashitano-tenki、組織 gendai-aimai-tango-jiten）。お手本は同じ運営者の「コミュニティ図鑑」と「あしたの転機観測所」で、見た目はデザインシステム「黒田悠介」（明るい地、空色、黄色の円と面、Noto Emoji の絵）に合わせています。

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
| tools/fetch_emoji.py | 語と曖昧ノートの emoji に使う Noto Emoji の画像（128px と 512px）を取ってくる |
| tools/check_words.py | 語のデータの点検。`--links` で出典のURLも開く（`--only slug1,slug2` でその語の出典だけ）。自動のアクセスを断るサイトは config/linkcheck.json の refusing_hosts に入れて除外する。確かな情報源（config/trusted_sources.json）がない語を知らせ、`--strict-sources` で問題として数える。曖昧ノートが収録済みの語だけを使っているかも見る |
| tools/make_og.py | 共有画像を作る。語ごと（docs/og/<slug>.png）、意味派の結果（docs/og/r/、名前が変わったものだけ作り直す）、曖昧ノート（docs/og/notes/） |
| tools/fetch_stats.py | GoatCounter の API から辞典の数字を集め、data/poll.json（意味派の回答数）と data/stats.json（語ごとの閲覧数・シェア数、全体の閲覧数、流入元の上位、収録していない検索語）に書く。GitHub の Secret「GOATCOUNTER_TOKEN」が要る。トークンはこの Secret にだけ置く（黒田さんの判断で、Mac のキーチェーンには置かない）。リポジトリは公開なので、書くのはまとめた数字だけ。検索語は2回以上・20字以内で、メールアドレスや長い数字を含まないものに絞る |
| .github/workflows/stats.yml | 毎週月曜 6:00 に fetch_stats.py を動かし、変わっていればサイトを作り直して push する |
| tools/pick_share.py | 次にシェアする語の候補を出す。推奨度と直近7日の読まれ方を半分ずつ |
| .github/workflows/check-links.yml | 毎週月曜 7:00 に出典のリンクを点検し、問題があれば Issue を作る |
| 定期タスク「gendai-aimai-words」 | 1日2回（9:07と21:07ごろ）に、notes/queue.md から3語を選んで書き、公開する（2026-11-08 に3時間おき・5語から変更）。2026-11-08 登録、Auto モード。手順は notes/routine-words.md（変えたら定期タスクの中身も直す）。アプリが閉じていると、次に開いたときに動く |
| 定期タスク「gendai-aimai-note」 | 毎日10:20ごろに（2026-11-08 に毎週火曜から変更）、notes/note-ideas.md から1つ選んで曖昧ノートを書き、公開する。2026-11-08 登録（権限の設定は保存されなかったので、最初の実行で確認が出ることがある） |
| 定期タスク「gendai-aimai-report」 | 毎週月曜8:30ごろに、data/stats.json と data/poll.json と1週間の更新をまとめて黒田さんに報告する。ファイルは変えない |
| 定期タスク「gendai-aimai-share」 | 毎週水曜9:00ごろに、tools/pick_share.py でまだシェアしていない語を1つ選び、notes/share-log.md に記録して、Asana のタスク「現代曖昧単語辞典をシェア」の説明欄の一番上に書く。黒田さんは翌日の木曜にシェアする。2026-11-08 登録、Auto モード |

## 計測と公開の設定（2026-11-08 黒田さんが採用）

- アクセス解析は GoatCounter（サイトコード aimaijiten、https://aimaijiten.goatcounter.com）。build.py の GOATCOUNTER。計測用の assets/count.js はコミュニティ図鑑と同じもの。ページの閲覧のほか、シェア（share/…）、ランダム（random）、タグ（tag/…）、検索（search/…、入力が1.5秒止まったとき）、意味派（poll/…）、ほかのサイトへのリンク（sister/…）を数える。
- Google Search Console は 2026-11-08 に黒田さんのアカウントで確認済み（HTMLタグ、build.py の GSC_VERIFY。消すと確認が外れる）。サイトマップは /sitemap.xml。
- robots.txt は AI の学習用クローラー（build.py の AI_BOTS）を断り、検索エンジンには開く。図鑑と同じ。
- 内容の訂正・ご意見は Google フォーム（黒田さんのアカウント、build.py の FORM_URL）。フッター、「この辞典について」、各単語ページの出典の下にリンクがある。単語ページからは「対象の言葉」の欄に語とURLが入った状態で開く。
- 「この辞典について」の「作り方」に、AI（Claude）が調べて書き、運営者が方針を決めて見直していることを明記している。
- 「あなたはどの意味派？」は、回答が10件以上たまった語だけ「みんなの意味派」の割合を出す（build.py の POLL_MIN）。結果のシェアは /words/<slug>/ha/<番号>/ の専用ページ（「私の〇〇は△△派」の画像つき、人は単語ページへ移す、検索には出さない）。
- 単語ページ・タグのページ・曖昧ノートに構造化データ（JSON-LD）を入れている。
- フッターと「この辞典について」に運営者（黒田悠介、linktr.ee）と、ほかのサイト（あしたの転機観測所、コミュニティ図鑑）を出す。build.py の OPERATOR と SISTER_SITES。

## ページ

| URL | 中身 |
|---|---|
| / | トップ。収録語の一覧（推奨度順・今時度順・曖昧度順・五十音順、検索、タグの絞り込み、24語ずつ「もっと見る」。ページには最初の24語だけを入れ、残りは /cards.json から読み込む）、曖昧ノートの新着3本、この辞典の読み方 |
| /words/{slug}/ | 単語ページ。30秒でわかる、曖昧メーター、どういう意味？、あなたはどの意味派？、意味の変遷、語源・成り立ち、広まった経緯、ズレのポイント、多様な観点（タブ）、使用シーン、関連語、出典、シェア、タグの近い6語 |
| /tags/{slug}/ | タグごとの一覧（検索から来てもらうためのページ）。URLと見出しは build.py の TAG_INFO。新しいタグを作ったら TAG_INFO にも足す |
| /notes/ と /notes/{slug}/ | 曖昧ノート（収録語をテーマごとに読み比べる読み物）。データは data/notes/、ネタ帳は notes/note-ideas.md |
| /about/ | この辞典について |

## 守ること（黒田さんの判断）

- クイズは作らない（2026-11-08 に外した）。
- シェアは X・Facebook・Threads・リンクのコピー。LINE は使わない。
- カードや箱の端に色の帯（左や上の線）を付けない。区別は箱全体の薄い色か札の色で。
- マーカー（蛍光ペン）と、黄色をずらした影は使わない（2026-11-08。AIが作ったように見えるため）。トップのサイト名は原稿用紙のマスに1字ずつ入れる（.masu、線の色は --masu-line。2026-11-08 に5案から選んだ）、見出しは文字だけで中身の数を添える（.h-count。トップの収録語の一覧は見出しを出さず、検索窓と並び順を1行にそろえる）、単語ページの一言は『』でくくる、意味派の結果は「あなたは」を小さく前に置く、共有画像は語の下に空色の短い線。共有画像の見た目を変えたら build.py の OG_STYLE を上げる（意味派の画像の名前が変わり、作り直される）。図鑑・観測所・転機AI・コミュニティAIも同じ日にやめた。
- ほかのサイトへのリンク（target="_blank"）には右上の矢印「↗」が付く（style.css。2026-11-08）。新しいタブで開くリンクは target="_blank" を付ける。
- 出典の下に補足文を付けない。GitHub のリンクや Issue の案内を画面に出さない。
- メーターは曖昧度・誤用度・通用度の3つ。説明文は build.py の METERS。
- 見た目を大きく変えるときは、先に黒田さんに見せて選んでもらう。
- 一覧の並びは推奨度順が基本（2026-11-08）。推奨度は本文の量（35%）・今時度（30%）・曖昧度（20%）・人気（15%、data/stats.json の累計閲覧数とシェア数）の点数で、若者言葉・ネット／ビジネス・心理／誤用の定番を順番に混ぜる。今時度は流行した時期（peak と「〇〇年流行」タグ）の新しさ。計算は build.py の recommend_scores・recommend_order・nowness・popularity。
- 表示はふだんライト。ダークはヘッダーのボタンで選んだ人だけ（端末の設定には合わせない、2026-11-08）。
- 黒田さんへの返答・報告は日本語で。日本語の文章は yomiyasu スキルの方針で書く。
