# Blog Writing App

Pascal SEOツールからエクスポートされたHTMLレポートを解析し、記事構成案や独自性の提案などの情報を抽出し、記事執筆用のプロンプトとディレクトリ構造を自動生成するアプリケーションです。

## 機能

- Pascal HTMLレポートから「AIによる記事構成案」セクションを抽出
- H1タイトル候補の抽出
- パターンA/Bから選択したパターンの情報を抽出
  - H2見出し（全8つ）
  - 各H2に含まれるH3見出し
  - 各H3の「執筆のアドバイス」
  - 各H3の「記事内で使用したいキーワード」
- 「独自性の提案」セクションから選択した提案を抽出
- 抽出結果をJSON形式で出力
- JSONデータからプロンプトテンプレートを生成（各フェーズごとに）
- 記事執筆用のディレクトリ構造を自動生成（ハイブリッド構造）

## セットアップ

### 必要な環境

- Python 3.8以上

### インストール

```bash
# 仮想環境を作成（推奨）
python3 -m venv venv

# 仮想環境を有効化
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt
```

## 完全なワークフロー

このアプリケーションは、以下の3ステップで記事執筆の準備を自動化します：

### ステップ1: HTMLからデータ抽出

Pascal HTMLレポートから必要な情報を抽出し、JSON形式で保存します。

```bash
python -m src.cli <HTMLファイルのパス> --pattern A --proposals 0 -o output/data.json
```

**オプション:**
- `html_file`: 解析するPascal HTMLファイルのパス（必須）
- `-o, --output`: 出力ファイルのパス（デフォルト: `output/extracted_data.json`）
- `--pattern`: パターンを直接指定（A/B）。指定しない場合は対話的に選択
- `--proposals`: 独自性の提案のインデックス（カンマ区切り、例: `0,1,2`）

**抽出される情報:**
- H1タイトル候補（複数）
- 選択したパターン（A/B）の記事構成
- 各H2見出しとその配下のH3見出し
- 各H3の執筆アドバイスとキーワード
- 選択した独自性の提案

### ステップ2: プロンプト生成

抽出したJSONデータから、記事執筆用のプロンプトを自動生成します。

```bash
python -m src.prompt_cli output/data.json
```

**オプション:**
- `json_file`: 抽出されたJSONデータファイルのパス（必須）
- `-t, --template`: プロンプトテンプレートファイルのパス（デフォルト: `templates/prompts.md`）
- `-o, --output`: 出力ディレクトリのパス（デフォルト: `output/prompts/`）
- `--phases`: 生成するフェーズを指定（カンマ区切り、例: `1,2,3`）。指定しない場合はすべて生成

**生成されるプロンプト:**

プロンプトはパターン別・フェーズ別に整理されます：

```
output/prompts/
├── pattern_A/
│   ├── phase1/          # FACT_ソース集め（各H2ごと）
│   ├── phase2/          # FACT_アウトプット（各H3ごと）
│   ├── phase3/          # Experience_アウトプット（各H2ごと）
│   ├── phase4/          # 記事執筆
│   ├── phase5/          # 画像生成
│   └── phase6/          # まとめ
└── pattern_B/
    └── ...
```

- **Phase 1 (FACT_ソース集め)**: 各H2見出しごとに、情報源を検索するプロンプト
- **Phase 2 (FACT_アウトプット)**: 各H3見出しごとに、事実をまとめるプロンプト
- **Phase 3 (Experience_アウトプット)**: 各H2見出しごとに、体験談を抽出するプロンプト
- **Phase 4 (記事執筆)**: 設計図を含む記事執筆用プロンプト
- **Phase 5 (画像生成)**: 画像生成用プロンプトテンプレート
- **Phase 6 (まとめ)**: 記事の最終編集用プロンプトテンプレート

### ステップ3: 記事ディレクトリ構造生成

記事執筆用のディレクトリ構造を自動生成します。ハイブリッド構造（日付+連番+タイトル）で整理されます。

```bash
python -m src.article_cli output/data.json \
  --source-html "input/report.html" \
  --copy-prompts \
  --cleanup
```

**オプション:**
- `json_file`: 抽出されたJSONデータファイルのパス（必須）
- `-o, --output`: 出力ディレクトリのパス（デフォルト: `output/articles`）
- `--h1-title`: 使用するH1タイトル（指定しない場合は最初の候補を使用）
- `--list-h1`: H1タイトル候補のリストを表示して終了
- `--source-html`: 元のHTMLファイルのパス（メタデータ用）
- `--copy-prompts`: プロンプトも記事ディレクトリにコピーする
- `--prompts-dir`: プロンプトのディレクトリ（デフォルト: `output/prompts`）
- `--cleanup`: 記事生成後、使用したJSONとプロンプトを削除する
- `--archive`: 記事生成後、使用したJSONとプロンプトをアーカイブに移動する

**生成されるディレクトリ構造:**

```
output/articles/
└── 20251128_001_ダイビング後に飛行機搭乗は危険？知っておくべき理由/
    ├── .article.json          # メタデータ（記事ID、作成日、パターンなど）
    ├── source.json            # 元のJSONデータ（コピー）
    ├── content/               # 記事コンテンツ
    │   ├── h1_[タイトル].md
    │   ├── h2-1_[H2タイトル]/
    │   │   ├── h2-1_[タイトル].md
    │   │   ├── pascal_h2-1.md      # Pascal設計図（自動生成済み）
    │   │   ├── experience_h2-1.md
    │   │   ├── h3-1_[タイトル].md
    │   │   ├── h3-2_[タイトル].md
    │   │   └── ...
    │   ├── h2-2_[H2タイトル]/
    │   └── ...
    └── prompts/               # この記事用のプロンプト
        └── pattern_A/
            ├── phase1/
            ├── phase2/
            └── ...
```

**記事IDの形式:**
- `YYYYMMDD_NNN_タイトル短縮版`
- 例: `20251128_001_ダイビング後に飛行機搭乗は危険？知っておくべき理由`
- 同じ日に複数の記事を作成しても連番で識別可能

**Pascalファイルについて:**
- 各H2ディレクトリ内の`pascal_h2-N.md`には、JSONから取得した情報が自動で書き込まれます
- 内容: H2タイトル、各H3のタイトル、執筆アドバイス、キーワード

## 完全な使用例

### 基本的なワークフロー

```bash
# 1. HTMLからデータを抽出
python -m src.cli input/report.html --pattern A --proposals 0 -o output/data.json

# 2. 抽出したデータからプロンプトを生成
python -m src.prompt_cli output/data.json

# 3. H1タイトル候補を確認
python -m src.article_cli output/data.json --list-h1

# 4. 記事ディレクトリ構造を生成（プロンプトもコピー、不要ファイルは削除）
python -m src.article_cli output/data.json \
  --source-html "input/report.html" \
  --copy-prompts \
  --cleanup
```

### 特定のH1タイトルを指定する場合

```bash
# H1タイトル候補を確認
python -m src.article_cli output/data.json --list-h1

# 特定のH1タイトルを指定して生成
python -m src.article_cli output/data.json \
  --h1-title "沖縄でダイビング後の飛行機搭乗時間を徹底解説！" \
  --source-html "input/report.html" \
  --copy-prompts \
  --cleanup
```

### アーカイブに保存する場合

```bash
# 不要ファイルをアーカイブに移動（削除ではなく保存）
python -m src.article_cli output/data.json \
  --source-html "input/report.html" \
  --copy-prompts \
  --archive
```

## 出力形式

### JSON形式（抽出結果）

```json
{
  "pattern": "A",
  "h1_title_candidates": [
    "ダイビング後に飛行機搭乗は危険？知っておくべき理由",
    "沖縄でダイビング後の飛行機搭乗時間を徹底解説！",
    ...
  ],
  "article_structure": [
    {
      "h2": "ダイビングと飛行機搭乗の基本知識",
      "h3_sections": [
        {
          "h3": "ダイビングの基本とその魅力",
          "advice": "ダイビングの基本的な知識を提供し...",
          "keywords": ["ダイバー", "紹介", "理由", ...]
        }
      ]
    }
  ],
  "originality_proposals": [
    {
      "title": "ダイビング旅行のための航空券予約とスケジュール調整のコツ",
      "advice": "多くの上位ページが..."
    }
  ]
}
```

### メタデータファイル（.article.json）

各記事ディレクトリには、記事のメタデータが含まれます：

```json
{
  "article_id": "20251128_001_ダイビング後に飛行機搭乗は危険？知っておくべき理由",
  "h1_title": "ダイビング後に飛行機搭乗は危険？知っておくべき理由",
  "h1_title_candidates": [...],
  "pattern": "A",
  "created_at": "2025-11-28T13:08:27.921447",
  "source_json": "extracted_data_with_h1.json",
  "source_html": "input/「ダイビング 飛行機」の記事作成レポート20251128111212.html",
  "h2_count": 8,
  "originality_proposals_count": 1
}
```

## プロジェクト構成

```
blog-writing-app/
├── src/
│   ├── __init__.py
│   ├── pascal_parser.py              # Pascal HTML解析ロジック
│   ├── cli.py                         # データ抽出CLI
│   ├── prompt_cli.py                  # プロンプト生成CLI
│   ├── prompt_generator.py            # プロンプト生成ロジック
│   ├── article_cli.py                 # 記事ディレクトリ生成CLI
│   └── article_structure_generator.py # 記事ディレクトリ生成ロジック
├── templates/
│   └── prompts.md                     # プロンプトテンプレート
├── input/                             # 入力HTMLファイル置き場（任意）
├── output/                            # 抽出結果の出力先
│   ├── articles/                      # 生成された記事ディレクトリ
│   │   └── YYYYMMDD_NNN_タイトル/
│   │       ├── .article.json
│   │       ├── source.json
│   │       ├── content/
│   │       └── prompts/
│   ├── prompts/                       # 生成されたプロンプト（一時的）
│   │   └── pattern_A/
│   ├── archive/                       # アーカイブ（--archive使用時）
│   └── *.json                         # 抽出されたJSONデータ（一時的）
├── requirements.txt                   # 依存関係
└── README.md
```

## 開発

### 依存パッケージ

- `beautifulsoup4`: HTML解析
- `lxml`: HTMLパーサー

## 注意事項

- プロンプトやJSONを記事生成前に編集することは想定していません
- 同じJSONデータから複数の記事を生成することは想定していません（1つのHTML → 1つの記事）
- 過去のJSONやプロンプトを参照する必要はありません（各記事ディレクトリに必要な情報が含まれています）
- `--cleanup` または `--archive` オプションを使用することで、作業領域を整理できます

## ライセンス

（必要に応じて追加）
