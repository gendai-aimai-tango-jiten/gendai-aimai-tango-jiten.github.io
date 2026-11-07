# 現代曖昧単語辞典

流行っているのに意味がふわっとしている言葉を、一語一ページでまとめる静的サイトです。
https://gendai-aimai-tango-jiten.github.io/

見た目はデザインシステム「黒田悠介」（コミュニティ図鑑・あしたの転機観測所と共通）をもとにしています。

## 構成

```
data/words/*.json   1単語＝1ファイルのデータ
assets/             CSS・JavaScript・絵文字（Noto Emoji 128px）
tools/make_og.py    共有画像（1200×630）を docs/og/ に作る（Pillow が必要）
tools/emoji512/     共有画像に使う Noto Emoji 512px とライセンス
build.py            データから docs/ を作る（Python 3 標準ライブラリのみ）
docs/               生成物（GitHub Pages の公開フォルダ）
```

## ページ

| URL | 中身 |
|---|---|
| / | トップ。曖昧度ランキング、この辞典の読み方 |
| /words/{slug}/ | 単語ページ。30秒でわかる要点、曖昧メーター、あなたはどの意味派？、意味の地図、アリ？ナシ？、語源、経緯、ズレやすいポイント、観点別の解説、言い換え、関連語、出典 |
| /about/ | この辞典について |

## 言葉を追加する

1. `data/words/` の既存のJSONをコピーし、`slug`（URLになる英数字）と中身を書き換える
2. 絵文字を決め、Noto Emoji の画像を2つ置く（コードポイントが `1f438` なら）
   - `assets/emoji/1f438.png` ← `https://raw.githubusercontent.com/googlefonts/noto-emoji/main/2D/png/128/emoji_u1f438.png`
   - `tools/emoji512/1f438.png` ← 同じ場所の `512` の画像
3. `python3 build.py` で docs/ を作り、`python3 tools/make_og.py` で共有画像を作る
4. コミットして push する

本文は空行（`\n\n`）で段落が分かれます。`**語**` で太字になります。

### 各項目

| キー | 内容 |
|---|---|
| word / reading / pos | 見出し語・読み・品詞 |
| emoji | Noto Emoji のコードポイント |
| catch | ひとことのキャッチ（カード・共有画像・ページ冒頭に出る） |
| oneliner | 説明文（検索結果やシェアの説明に使う） |
| tldr | 30秒でわかる要点（3つ） |
| tags | タグ |
| origin_date / peak / updated | 初出・流行のピーク・最終更新日 |
| meters | 曖昧度・誤用度・通用度（1〜5） |
| definition | どういう意味？ |
| usages | 意味の地図と「どの意味派？」の選択肢（type は 原義／拡張／誤用寄り） |
| etymology | 語源・成り立ち |
| timeline | 広まった経緯 |
| misuses | ズレやすいポイント |
| examples | アリ？ナシ？（verdict は ok／warn／ng） |
| perspectives | いろんな観点から見る（タブで切り替え） |
| who_where | 誰が・どこで使う？ |
| paraphrase | 言い換え |
| related | 関連語（収録済みの語なら自動でリンク） |
| sources | 出典 |

## ローカルで見る

```
python3 build.py
python3 -m http.server -d docs 8000
```
