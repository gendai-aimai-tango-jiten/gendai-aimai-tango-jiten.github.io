# 現代曖昧単語辞典

流行っているのに意味がはっきりしない言葉を、一語一ページでまとめる静的サイトです。GitHub Pages で公開します。

## 構成

```
data/words/*.json   1単語＝1ファイルのデータ
data/planned.json   トップページの「収録予定」
assets/             CSS と JavaScript
build.py            データから docs/ を生成するスクリプト（Python 3 標準ライブラリのみ）
docs/               生成物（GitHub Pages の公開フォルダ）
```

## 言葉を追加する

1. `data/words/` にある既存のJSONをコピーし、`slug`（URLになる英数字）と中身を書き換える
2. `python3 build.py` を実行する
3. `docs/` をコミットして push する

本文は空行（`\n\n`）で段落が分かれます。`**語**` で太字になります。

### 各項目

| キー | 内容 |
|---|---|
| word / reading / pos | 見出し語・読み・品詞 |
| tags | トップページの絞り込みに使うタグ |
| origin_date / peak / updated | 初出・流行のピーク・最終更新日 |
| meters | 曖昧度・誤用度・トゲ度・定着度（1〜5） |
| oneliner | 一覧に出る一文の説明 |
| definition | ひとことで言うと |
| usages | 意味の地図（type は 原義／拡張／誤用寄り） |
| etymology | 語源・成り立ち |
| timeline | 広まった経緯 |
| misuses | ズレやすいポイント |
| examples | 使用例（verdict は ok／warn／ng） |
| perspectives | 多様な観点から |
| who_where | 誰が・どこで使うか |
| paraphrase | 言い換え |
| related | 関連語（収録済みの語なら自動でリンク） |
| sources | 出典 |

## ローカルで見る

```
python3 build.py
python3 -m http.server -d docs 8000
```

## GitHub Pages の設定

リポジトリの Settings → Pages で、Source を「Deploy from a branch」、Branch を `main` の `/docs` にします。
