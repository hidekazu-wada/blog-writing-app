# クイックスタートガイド

このガイドでは、HTMLファイルから記事執筆用のディレクトリ構造を生成するまでの完全な手順を説明します。

## 準備：既存ファイルの削除

まず、既存の出力ファイルを削除してクリーンな状態にします。

```bash
# outputディレクトリ内の既存ファイルを削除
rm -rf output/articles output/prompts output/*.json output/archive
```

または、outputディレクトリ全体を削除して再作成：

```bash
rm -rf output
mkdir output
```

## 完全なワークフロー

### ステップ1: HTMLファイルを配置

Pascal SEOツールからエクスポートしたHTMLファイルを `input/` ディレクトリに配置します。

```bash
# 例: HTMLファイルをinputディレクトリにコピー
cp /path/to/your/report.html input/記事作成レポート.html
```

### ステップ2: HTMLからデータ抽出

HTMLファイルから必要な情報を抽出し、JSON形式で保存します。

```bash
# 仮想環境を有効化（まだの場合）
source venv/bin/activate

# データ抽出（対話形式）
python -m src.cli input/記事作成レポート.html

# または、オプションを指定して非対話的に実行
python -m src.cli input/記事作成レポート.html \
  --pattern A \
  --proposals 0 \
  -o output/extracted_data.json
```

**実行内容:**
- パターンA/Bから選択（`--pattern`で指定可能）
- 独自性の提案から選択（`--proposals`で指定可能、カンマ区切り）
- JSONファイルに保存（`-o`で出力先を指定可能）

**出力:** `output/extracted_data.json`

### ステップ3: プロンプト生成

抽出したJSONデータから、記事執筆用のプロンプトを自動生成します。

```bash
python -m src.prompt_cli output/extracted_data.json
```

**実行内容:**
- JSONデータを読み込み
- 各フェーズ（phase1〜phase6）のプロンプトを生成
- パターン別・フェーズ別にディレクトリを整理

**出力:** `output/prompts/pattern_A/` または `output/prompts/pattern_B/`

### ステップ4: H1タイトル候補の確認（オプション）

使用するH1タイトルを確認します。

```bash
python -m src.article_cli output/extracted_data.json --list-h1
```

**出力例:**
```
利用可能なH1タイトル候補:
============================================================
  [1] ダイビング後に飛行機搭乗は危険？知っておくべき理由
  [2] 沖縄でダイビング後の飛行機搭乗時間を徹底解説！
  [3] ダイビング直後に飛行機搭乗が禁止な理由と待機時間
  [4] スキューバダイビング後の飛行機搭乗、絶対知っておくべきこと
============================================================
```

### ステップ5: 記事ディレクトリ構造生成

記事執筆用のディレクトリ構造を自動生成します。

```bash
# 基本的な使い方（最初のH1タイトル候補を使用）
python -m src.article_cli output/extracted_data.json \
  --source-html "input/記事作成レポート.html" \
  --copy-prompts \
  --cleanup
```

**オプション説明:**
- `--source-html`: 元のHTMLファイルのパス（メタデータに記録されます）
- `--copy-prompts`: プロンプトも記事ディレクトリにコピーします
- `--cleanup`: 記事生成後、使用したJSONとプロンプトを削除します（作業領域を整理）

**特定のH1タイトルを指定する場合:**
```bash
python -m src.article_cli output/extracted_data.json \
  --h1-title "沖縄でダイビング後の飛行機搭乗時間を徹底解説！" \
  --source-html "input/記事作成レポート.html" \
  --copy-prompts \
  --cleanup
```

**出力:** `output/articles/YYYYMMDD_NNN_タイトル/`

## 生成されるディレクトリ構造

```
output/articles/
└── 20251128_001_記事タイトル/
    ├── .article.json          # メタデータ
    ├── source.json            # 元のJSONデータ
    ├── content/               # 記事コンテンツ
    │   ├── h1_[タイトル].md
    │   ├── h2-1_[H2タイトル]/
    │   │   ├── h2-1_[タイトル].md
    │   │   ├── pascal_h2-1.md      # Pascal設計図（自動生成済み）
    │   │   ├── experience_h2-1.md
    │   │   ├── h3-1_[タイトル].md
    │   │   ├── h3-2_[タイトル].md
    │   │   └── images/             # 画像用ディレクトリ（空）
    │   └── ...
    └── prompts/               # この記事用のプロンプト
        └── pattern_A/
            ├── phase1/
            ├── phase2/
            └── ...
```

## 完全な実行例

```bash
# 1. 既存ファイルを削除
rm -rf output/articles output/prompts output/*.json

# 2. HTMLファイルを配置（input/ディレクトリに配置済みと仮定）
# input/記事作成レポート.html

# 3. データ抽出
python -m src.cli input/記事作成レポート.html \
  --pattern A \
  --proposals 0 \
  -o output/extracted_data.json

# 4. プロンプト生成
python -m src.prompt_cli output/extracted_data.json

# 5. H1タイトル候補を確認
python -m src.article_cli output/extracted_data.json --list-h1

# 6. 記事ディレクトリ生成（クリーンアップ付き）
python -m src.article_cli output/extracted_data.json \
  --source-html "input/記事作成レポート.html" \
  --copy-prompts \
  --cleanup
```

## トラブルシューティング

### エラー: ファイルが見つかりません
- HTMLファイルのパスが正しいか確認
- 仮想環境が有効化されているか確認

### エラー: パターンが見つかりません
- HTMLファイルが正しいPascalレポートか確認
- `--pattern`オプションでAまたはBを指定

### プロンプトが生成されない
- JSONファイルが正しく生成されているか確認
- `output/extracted_data.json`の内容を確認

## 次のステップ

記事ディレクトリが生成されたら：
1. `content/`ディレクトリ内のファイルにコンテンツを記入
2. `images/`ディレクトリに画像を追加
3. `prompts/`ディレクトリ内のプロンプトをLLMに渡して作業を進める

