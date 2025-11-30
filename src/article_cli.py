"""
記事ディレクトリ構造生成のコマンドラインインターフェース
"""
import argparse
import sys
from pathlib import Path

# 相対インポートと絶対インポートの両方に対応
try:
    from .article_structure_generator import ArticleStructureGenerator
except ImportError:
    from article_structure_generator import ArticleStructureGenerator


def main():
    parser = argparse.ArgumentParser(
        description='JSONデータから記事ディレクトリ構造を生成します'
    )
    parser.add_argument(
        'json_file',
        type=str,
        help='抽出されたJSONデータファイルのパス'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='output',
        help='出力ディレクトリのパス（デフォルト: output）'
    )
    parser.add_argument(
        '--h1-title',
        type=str,
        default=None,
        help='使用するH1タイトル（指定しない場合は最初の候補を使用）'
    )
    parser.add_argument(
        '--list-h1',
        action='store_true',
        help='H1タイトル候補のリストを表示して終了'
    )
    parser.add_argument(
        '--source-html',
        type=str,
        default=None,
        help='元のHTMLファイルのパス（メタデータ用）'
    )
    parser.add_argument(
        '--prompts-dir',
        type=str,
        default='output/prompts',
        help='プロンプトのディレクトリ（デフォルト: output/prompts）'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='記事生成後、使用したJSONファイルを削除する'
    )
    
    args = parser.parse_args()
    
    # JSONファイルの存在確認
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"エラー: JSONファイルが見つかりません: {json_path}")
        sys.exit(1)
    
    # ジェネレーターを初期化
    try:
        generator = ArticleStructureGenerator(str(json_path))
    except Exception as e:
        print(f"エラー: 初期化に失敗しました: {e}")
        sys.exit(1)
    
    # H1タイトル候補のリストを表示
    if args.list_h1:
        h1_candidates = generator.list_h1_candidates()
        if not h1_candidates:
            print("H1タイトル候補が見つかりませんでした。")
            sys.exit(1)
        
        print("\n利用可能なH1タイトル候補:")
        print("="*60)
        for i, title in enumerate(h1_candidates, start=1):
            print(f"  [{i}] {title}")
        print("="*60)
        print(f"\n使用する場合は --h1-title オプションで指定してください。")
        print(f"例: --h1-title \"{h1_candidates[0]}\"")
        sys.exit(0)
    
    # 同じHTMLファイルから生成された既存のcontentとpromptsを削除
    if args.source_html:
        import json
        import shutil
        output_path = Path(args.output)
        source_html_path = Path(args.source_html).resolve()
        
        if output_path.exists():
            metadata_file = output_path / '.article.json'
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    existing_source_html = metadata.get('source_html')
                    if existing_source_html:
                        existing_path = Path(existing_source_html).resolve()
                        if existing_path == source_html_path:
                            # 既存のcontentのみ削除
                            # 一時的なプロンプト（output/prompts/pattern_*）は削除しない
                            content_path = output_path / 'content'
                            if content_path.exists():
                                shutil.rmtree(content_path)
                                print(f"既存のcontentディレクトリを削除しました")
                            # 記事用のpromptsディレクトリ（output/prompts）は削除しない
                            # 一時的なプロンプト（output/prompts/pattern_*）と同じ場所にあるため
                except (json.JSONDecodeError, Exception) as e:
                    # メタデータファイルの読み込みに失敗した場合はスキップ
                    pass
    
    # ディレクトリ構造を生成
    print("\n" + "="*60)
    print("記事ディレクトリ構造を生成中...")
    print("="*60)
    
    try:
        generated_output_path = generator.generate_structure(
            args.output,
            args.h1_title,
            args.source_html
        )
        
        # プロンプトは既に output/prompts/pattern_A に生成されているので、コピー不要
        # 記事ディレクトリ内のpromptsディレクトリは作成しない（output/prompts/pattern_Aを直接使用）
        
        # クリーンアップ処理（JSONファイルのみ削除）
        if args.cleanup:
            json_path = Path(args.json_file)
            if json_path.exists() and json_path.parent.name == 'output':
                json_path.unlink()
                print(f"JSONファイルを削除しました: {json_path}")
        
    except Exception as e:
        print(f"エラー: ディレクトリ構造の生成に失敗しました: {e}")
        sys.exit(1)
    
    # 結果を表示
    json_data = generator.json_data
    pattern = json_data.get('pattern', 'Unknown')
    h1_title = args.h1_title or json_data.get('h1_title_candidates', [None])[0]
    h2_count = len(json_data.get('article_structure', []))
    
    print(f"\n**パターン:** {pattern}")
    print(f"**H1タイトル:** {h1_title}")
    print(f"**H2の数:** {h2_count}")
    print(f"\n出力先: {generated_output_path}")
    print("\n完了しました！")


if __name__ == '__main__':
    main()

