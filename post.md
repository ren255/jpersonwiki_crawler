
  1. タイトル: [Self-Made] X件のYデータセット のように [Self-Made]タグ + 件数 + 何のデータか、を簡潔に。
  2. 1〜2文のフック: 何を集めたか、なぜ珍しいか(既存になかった/最大規模など)を最初に。
  3. 収集方法: どこから(API/スクレイピング/公開データ)、どうやって(ツール名)、を簡潔に1〜2文。
  4. 規模・スペック: 行数、列数、ファイルサイズ、フォーマット(CSV/JSON/Parquet)。
  5. カラム一覧 or サンプル行: 主要カラムを箇条書き、または実際の1〜2行のサンプルをコードブロックで貼る(表より実データの方が信頼されやすい)。
  6. 既知の制限・注意点: 欠損値、バイアス、精度、ライセンス上の制約など正直に書く(これがないと質問攻めに遭う)。
  7. ライセンス: 再利用条件を明記(MIT/CC0/CC BY-SAなど)。r/datasetsは特に厳しく聞いてくる。
  8. リンク: GitHub(コード)+ Kaggle/HuggingFace(データ本体)の両方を貼るのが定番。
  9. クロージング: 「フィードバック歓迎」「〇〇用途に使えると思う」という一文で終える投稿が多い。


[Self-Made] 231k Real Japanese People with 37 Attributes. (name, gender , age, occupations ...).

This dataset has all entry from wikidata who has Japanese citizenship and a wiki article, 231k in total. This is the largest structured dataset of real Japanese individuals available. The dataset is on [Kaggle](https://www.kaggle.com/datasets/rentoda/jpersonwiki).

I Queried via SPARQL against the QLever Wikidata endpoint, then cleaned/normalized with Python (name cleaning/splitting, BMI calculation, etc). dataset is in CSV format, 65MB. with multiple entry column separated with "|"

**Sample rows** (two people picked so together they cover every column):

qid: Q160847  
kanji: 東條 英機  
hiragana: とうじょう ひでき  
description: 日本の陸軍軍人、政治家、第40代内閣総理大臣(1884-1948)  
gender: M  
birth_year: 1884  
death_year: 1948  
age: 64  
death_age: 64  
label: 東條英機  
name_en: Hideki Tojo  
is_japanese_name: True  
readings: とうじょう ひでき  
occupations: 士官|政治家|外交官  
birth_places: 麹町区  
alma_maters: 東京陸軍幼年学校|陸軍大学校|陸軍中央幼年学校|陸軍士官学校  
positions_held: 内務大臣|内閣総理大臣|外務大臣|軍需省|陸軍省|文部省|参謀本部|農商務卿  
death_places: 巣鴨拘置所  
death_causes: 縊死  
death_manners: 死刑  
fathers: 東條英教  
mothers: 東條千歳  
spouses: 東條かつ子  
children: 東條敏夫|東條輝雄|東條満喜枝  
awards: 大礼記念章|チュラチョームクラーオ勲章|...(18 total)  
parties: 大政翼賛会  
notable_works: 東條英機の遺言|大詔を拝し奉りて  
military_branches: 大日本帝国陸軍|関東軍  
military_ranks: 陸軍大将  
wiki_url: https://ja.wikipedia.org/wiki/東條英機  
image_url: http://commons.wikimedia.org/wiki/Special:FilePath/Hideki%20Tojo.jpg  

qid: Q11467665  
kanji: 山咲 トオル  
hiragana: やまざき とおる  
description: 日本の漫画家、タレント  
gender: M  
birth_year: 1969  
age: 57  
label: 山咲トオル  
name_en: Tōru Yamazaki  
is_japanese_name: True  
readings: やまざき とおる  
occupations: タレント|日本の漫画家  
birth_places: 東京都  
genres: ホラー漫画  
height_cm: 170.0  
weight_kg: 57.0  
bmi: 19.7  
siblings: 中沢初絵  
wiki_url: https://ja.wikipedia.org/wiki/山咲トオル  

# Potential Use Cases & As a Dataset

|Dataset Angle|Task|Columns|
|:-|:-|:-|
|Japanese Name with Gender|Gender inference from name|kanji, hiragana, gender|
|Kanji, Hiragana Name Pairs|Reading (furigana) prediction|kanji, hiragana, readings|
|Family Relations|Genealogy / kinship network analysis|fathers, mothers, spouses, siblings, children|
|Portrait Images|Gender/age/occupation estimation|image_url, gender, birth_year|
|Athlete / Model Physique|Body-composition trend analysis by occupation|height_cm, weight_kg, bmi, occupations|
|Politicians|Politician attribute & career analysis|parties, positions_held, birth_places, alma_maters|
|Awards|Field/attribute analysis of award recipients|awards, occupations, gender|
|Cause & Manner of Death|Statistical analysis of death cause and age|death_causes, death_manners, death_age|
|Birthplace / Alma Mater|Geographic distribution and education-career correlation|birth_places, alma_maters, occupations|
|Age|Age-based demographic analysis|birth_year, death_year, death_age|
|Writers / Artists Database|Classification of writers/artists by notable works and genre|notable_works, genres, occupations|
|Military|Historical figures database|military_branches, military_ranks, birth_year|

**limitations**: The least-filled column, `military_ranks`, has only ~3k rows filled, while the average filled-column count per row is 15.25 out of 37 (41.2%). No rows are dropped to keep this the full Wiki-derived dataset. But I added `is_japanese_name` column so you can reliably excludes non-Japanese names (virtually no false negatives, ~0.1% false positives). About 1% of rows have a reversed family/given order in the `hiragana` column.

Crawler code : [Kaggle notebook](https://www.kaggle.com/code/rentoda/jpersonwiki-crawler) / [GitHub](https://github.com/ren255/jpersonwiki_crawler). This dataset will be updated automatically with the crawler.
