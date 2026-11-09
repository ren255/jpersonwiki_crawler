# AGENTS.md

このファイルは、このリポジトリで作業するClaude Code (claude.ai/code) への指示を記載する。

## これは何か

日本人の名前・属性データセットを構築するリポジトリ。独立した2つのクローラー(notebook)が存在する:

1. **`jpersonwiki_crawler.ipynb`** — Wikidata(SPARQL/QLever経由)から実在の日本人人物データを収集・クリーニングし、`jpersonwiki`データセットを構築する。
2. **`jnamegender_clawler.ipynb`** — 上記`jpersonwiki`(Kaggle経由)、ENAMDICT由来の辞書(`enamdict`)、頻度調査由来の辞書(`name_origin`)の3つを統合し、姓名+性別の`jnamegender`データセットを構築する。

パッケージ/ビルドシステムは存在せず、Jupyter notebookと`#%%`区切りのスクリプト群で構成されており、通常のスクリプトとして最初から最後まで実行するのではなく、セル単位(VS Code / Jupyter interactive window形式)で実行することを前提としている。

## 環境

- Pythonのvenvは`.venv/`にある。依存関係は`requirements.txt`に記載(romkan2, namedivider-python, pandas, requests, ipykernel, matplotlib, kagglehub, python-dotenv) — `pip install -r requirements.txt`でインストールする。
- テストスイート、リンター、ビルドステップはこのリポジトリには存在しない。
- `jnamegender_clawler.ipynb`はKaggle上とローカルの両方で実行できるよう、`IS_KAGGLE = os.path.exists("/kaggle/input")`で分岐している。Kaggle上では`/kaggle/input/datasets/rentoda/jpersonwiki/jpersonwiki.csv`を直接参照し、ローカルでは`kagglehub.dataset_download("rentoda/jpersonwiki")`経由で取得する。

## フォルダ構成

各クローラーの中間生成物・最終データセットは、クローラーごとの専用フォルダに入る(いずれもgitignore対象):

```
jpersonwiki/
├── intermidiate/      SPARQL生データキャッシュ(jawikidata.csv, parts/)
└── jpersonwiki.csv     最終データセット(jpersonwiki_crawler.ipynbの出力)

jnamegender/
├── intermidiate/       DL中間ファイル(enumdict_*.txt/csv, name_origin_*.txt/csv)
├── jnamegender.csv      最終統合データセット
├── enamdict.csv         enamdict由来(given nameのみ)
└── name_origin.csv      name_origin由来(given nameのみ)

local/                  上記2クローラーに直接紐づかない雑多なファイル(image/, output/, source/, stat.py, plan.md)。gitignore対象で、新規checkoutには存在しない。
```

## パイプライン / データフロー

### 1. `jpersonwiki_crawler.ipynb` — Wikidata人物データパイプライン

- QLeverのWikidataエンドポイント(`https://qlever.cs.uni-freiburg.de/api/wikidata`)にSPARQLクエリを送信し、職業・出身地・家族・受賞歴・軍歴など幅広いプロパティを持つ日本人全員を取得、生の結果を`jpersonwiki/intermidiate/jawikidata.json` / `jpersonwiki/intermidiate/jawikidata.csv`にキャッシュする。
- SPARQLの生の変数名をsnake_caseのカラム名にリネーム(`rename_map`)して`wikidata_raw`に格納。
- `wikidata_raw`から`wikidata`を導出する: QID URLから`qid`を抽出、`label`から`kanji`名を分離、`romkan2`と`namedivider-python`でローマ字化・名前の検証を行い、英字や特殊文字・非日本語表記を含むエントリを除外して`is_japanese_name`をフラグ付けする(ファイル全体で繰り返される`mask = ...; wikidata.loc[mask, ...] = ...; endL(...)`というパターンに注目 — 各ブロックが1種類の不正データをフィルタ/null化し、影響を受けた行数をログ出力している)。
- 年齢、現在の年齢、身長/体重のメートル法換算など、派生する数値フィールドを計算。
- 最終的な出力カラムは`main_columns` / `common_columns`に列挙されている — これがクリーニング済みデータセットの正規スキーマである。
- 最後にクリーニング済みデータセットを`jpersonwiki/jpersonwiki.csv`へ書き出す。
- 続けて、Kaggle認証情報(`.env`のKAGGLE_USERNAME/KAGGLE_KEY/KAGGLE_DATASET_NAME、またはKaggle上ではUserSecretsClient)があれば`kagglehub.dataset_upload`で`jpersonwiki/jpersonwiki.csv`をKaggleデータセット(`rentoda/jpersonwiki`)として公開する。認証情報が無い場合はアップロードをスキップする。
- 複数値を持つフィールド(職業、出身校、受賞歴、家族など)はリストではなく`"|"`区切りの文字列として格納されている — カテゴリ/マルチラベルデータとして扱う前に`"|"`で分割すること。
- データ中の性別の値は日本語の文字列(`"男性"`, `"女性"`)。

### 2. `jnamegender_clawler.ipynb` — 姓名+性別統合データセットパイプライン

- `enamdict`: `rgamici/japanese-names`のmale/femaleリスト(ENAMDICT由来)をDL・パースし、given name + sex(M/F)の辞書を作る。
- `name_origin`: `shuheilocale/japanese-personal-name-dataset`のfirst_name_man/woman_orgをDL・パースし、given name + sex(M/F)の辞書を作る。
- `jpersonwiki`: 上記`get_jpersonwiki_path()`で取得した`jpersonwiki.csv`から`is_japanese_name == True`の行のみ残し、`gender`列をM/F以外(トランス女性等)除外した上で、`BasicNameDivider`でフルネームを姓・名に分割する。
- 3つを`sex`(M/F)・`given_kanji`・`given_hiragana`・`family_kanji`・`family_hiragana`(enamdict/name_originは姓を持たないためNaN)・`birth_year`のスキーマに揃えて`pd.concat`し、`jnamegender/jnamegender.csv`として出力する。各ソースの単体CSVも`jnamegender/enamdict.csv`、`jnamegender/name_origin.csv`、`jpersonwiki/jpersonwiki.csv`として個別に書き出す。
- 以前`names-dataset`(Philippe Remy作、Facebookの533M件流出データが出典)を使って名前ごとの性別比・ランク統計(`name_stats.csv`)を生成していたが、流出データ由来のため削除済み。再度名前統計を追加する場合は出典に注意すること。

### 3. `local/stat.py` — 探索的分析・プロット

- クリーニング済み`wikidata`データフレームに対する分析・プロット。現在`local/`配下にあり、パス参照が最新のフォルダ構成(`jpersonwiki/jpersonwiki.csv`)に追従していない可能性があるため、使う前にパスを確認すること。

## このリポジトリ固有の慣習

- `*.csv`、`*.json`、`jpersonwiki/`、`jnamegender/`、`local/`はgitignoreされている — 新規checkoutにデータファイルが存在すると仮定しないこと。各クローラーのnotebookを実行して再生成するか、ローカルに既に存在している必要がある。
- enamdict/name_originの元データは「姓」を持たないファーストネーム専用データセットのため、`family_kanji`/`family_hiragana`は常にNaN。姓データを持つのは`jpersonwiki`由来の行のみ。
