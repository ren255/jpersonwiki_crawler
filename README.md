# jpersondata_crawler

Wikidata(SPARQL/QLever経由)から「日本国籍かつ日本語版Wikipediaに記事がある人物」を抽出し、クリーニングした上でCSV化するデータパイプライン(`jpersonwiki`)、およびそれを他の辞書データと統合して姓名+性別データセットを作る2本目のパイプライン(`jnamegender`)を含むリポジトリ。`jpersonwiki`は236,507件規模で、公開データセットとしては日本人限定では最大級。

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 使い方

### `jpersonwiki_crawler.ipynb` — Wikidata人物データ

1. セル単位(Jupyter/VS Code interactive window)で実行、または一括実行:
   ```bash
   jupyter nbconvert --to notebook --execute --inplace jpersonwiki_crawler.ipynb
   ```
   QLeverへSPARQLクエリを送信 → `jpersonwiki/intermidiate/jawikidata.csv` にキャッシュ → クリーニング → `jpersonwiki/jpersonwiki.csv` を出力する。
2. Kaggle認証情報(`.env`参照)が設定されていれば、続けて`rentoda/jpersonwiki`としてKaggleへアップロードする。

### `jnamegender_clawler.ipynb` — 姓名+性別統合データセット

1. セル単位で実行、または一括実行:
   ```bash
   jupyter nbconvert --to notebook --execute --inplace jnamegender_clawler.ipynb
   ```
   ENAMDICT由来の`enamdict`、頻度調査由来の`name_origin`をDL・パースし、`jpersonwiki`(ローカルでは`kagglehub`経由、Kaggle上では`/kaggle/input`経由)の実在人物データ(`is_japanese_name == True`のみ)と統合して`jnamegender/jnamegender.csv`を出力する。
2. 中間ファイルは`jnamegender/intermidiate/`に、単体データセットは`jnamegender/enamdict.csv` / `jnamegender/name_origin.csv` / `jpersonwiki/jpersonwiki.csv`に出力される。

## 出力カラム(jpersonwiki)

主なもの: `qid`, `kanji`(姓名スペース区切り), `hiragana`(読み仮名、姓名スペース区切り), `label`, `name_en`, `is_japanese_name`, `gender`, `birth_year`/`death_year`, `age`, `occupations`, `height_cm`/`weight_kg`/`bmi` など。全カラムは`jpersonwiki_crawler.ipynb`内の`main_columns`を参照。

## 出力カラム(jnamegender)

`dataset`(jpersonwiki/enamdict/name_origin), `sex`(M/F), `given_kanji`, `given_hiragana`, `family_kanji`, `family_hiragana`(jpersonwiki由来の行のみ、他はNaN), `birth_year`(jpersonwiki由来の行のみ)。

## `is_japanese_name` の判定条件

以下のいずれかに当てはまると `False`(日本人名でないと判定)、すべて満たせば `True`:

- 表記名(kanji)に半角/全角の英数字が含まれる
- 表記名(kanji)に記号・絵文字・ローマ数字・combining mark・ギリシャ文字などの特殊文字が含まれる
- 表記名(kanji)が漢字・ひらがな・カタカナ以外の文字を含む
- 英語名(name_en)が「姓 名」のちょうど2語に分割できない(称号付き、ミドルネームあり、1語のみ、3語以上など)
- 英語名やWikidataの読み(P1814)から生成した読み仮名(hiragana)が日本語表記でない、または「姓 名」の2語に分割できない

実際に`False`に分類される代表的なケース:

- 英語の称号・敬称が付いた名前(例: `Prince Kan'in Haruhito`)
- ミドルネーム/洋風の追加の名が入っている(例: `Raymond Ken'ichi Tanaka`)
- 半角英字1文字が混じる芸名(例: 佐藤B作の「B」)
- 英語名が1語のみで姓が無い(例: `Mizuki`)
- 西洋名順・外国風芸名でカタカナに「・」区切りが入る(例: イトー・ターリ)
- ニックネーム的な英語表記(例: `NoB`)
- ハイフンで結合された称号・肩書き付き名前(例: `Manta-shinnō`)
- 複合姓の中に"no"を含む古い人名(例: 大伴坂上郎女 = `Ōtomo no Sakanoue no Iratsume`、姓自体に"no"が含まれるため判別不可)
- 英語名・Wikidataの読みのどちらも存在せず、かつ表記名に漢字が一切ない(判定材料が無い)

## 既知の限界

`is_japanese_name` は `False` 側に誤判定はほぼ無いが、`True` 側には約0.1%の誤判定が残る。また英語名(name_en)が「姓 名」の順になっていないケースが約3k件(全体の約1%)あり、この場合hiraganaの姓名分割が逆になっていることがある。

## 他の日本人名データセットとの比較

日本人名+属性(性別など)を持つ既存の大規模公開データセットの多くは、辞書・頻度調査・合成データに基づくものであり、実在の人物起点ではない。本データセットはWikidata上の実在の日本国籍の人物236,507件から構築されており、この規模で実在人物ベースのものとしては最大級と考えられる。

| データセット | 件数 | 出典 | 備考 |
|---|---|---|---|
| philipperemy/name-dataset | 150k | Facebook 530M件流出データ | 漢字またはひらがなのみ(両方は無い) |
| rgamici/japanese-names | 116k | ENAMDICT/JMnedict | 辞書ベース、重複無し |
| shuheilocale/japanese-personal-name-dataset | 90k | 名前由来 | 頻度調査、重複無し |
| tarudesu/gendec-dataset | 64k | 上記データセットの派生 | 合成フルネーム、研究用途限定 |
| rentoda/Japanese Names with Gender | 69k | 日本語版Wikipedia(性別カテゴリ) | 実在人物、性別ラベル付き |
| **jpersonwiki(本リポジトリ)** | **236,507** | **Wikidata** | **実在人物、属性が豊富(生年・職業・身長体重・受賞歴など)** |
| **jnamegender(本リポジトリ)** | **約409,328** | **jpersonwiki + ENAMDICT + 頻度調査** | **上記jpersonwikiの実在人物データとENAMDICT/頻度調査辞書を統合、Facebook流出データは使用していない** |

`philipperemy/name-dataset`はFacebookの533M件流出データが出典のため、`jnamegender`データセットの構築には使用していない(過去に一時的に名前統計の補助データとして組み込んでいたが削除済み)。

## 想定用途

- 名前からの性別推定(LLM/BERT規模のモデルに頼らない軽量な推定)
- 日本語NLP: 固有表現抽出、読み予測、姓名分割
- 日本語の姓名パーサー/トークナイザーの学習・評価
- 他のWikipedia/Wikidata由来データセットとの突合

## データソース

- `jpersonwiki`: Wikidata(CC0)
- `jnamegender`: 上記`jpersonwiki` + `rgamici/japanese-names`(ENAMDICT/JMnedict) + `shuheilocale/japanese-personal-name-dataset`(頻度調査)

`*.csv` / `*.json` / `jpersonwiki/` / `jnamegender/` / `local/` はgitignore対象のため、新規checkoutでは各クローラーnotebook(`jpersonwiki_crawler.ipynb` / `jnamegender_clawler.ipynb`)の実行で再生成する必要がある。
