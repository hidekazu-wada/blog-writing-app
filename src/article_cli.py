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
        default='output/articles',
        help='出力ディレクトリのパス（デフォルト: output/articles）'
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
        '--copy-prompts',
        action='store_true',
        help='プロンプトも記事ディレクトリにコピーする'
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
        help='記事生成後、使用したJSONとプロンプトを削除する'
    )
    parser.add_argument(
        '--archive',
        action='store_true',
        help='記事生成後、使用したJSONとプロンプトをアーカイブに移動する'
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
    
    # ディレクトリ構造を生成
    print("\n" + "="*60)
    print("記事ディレクトリ構造を生成中...")
    print("="*60)
    
    try:
        article_path = generator.generate_structure(
            args.output,
            args.h1_title,
            args.source_html
        )
        
        # プロンプトをコピー
        prompts_source_path = None
        json_data = generator.json_data
        pattern = json_data.get('pattern', 'Unknown')
        prompts_source = Path(args.prompts_dir) / f"pattern_{pattern}"
        
        if args.copy_prompts:
            prompts_dest = Path(article_path) / 'prompts' / f"pattern_{pattern}"
            
            if prompts_source.exists():
                import shutil
                if prompts_dest.exists():
                    shutil.rmtree(prompts_dest)
                shutil.copytree(prompts_source, prompts_dest)
                prompts_source_path = prompts_source
                print(f"プロンプトをコピーしました: {prompts_dest}")
            else:
                print(f"警告: プロンプトディレクトリが見つかりません: {prompts_source}")
        else:
            # コピーしない場合でも、クリーンアップ用にパスを保持
            if prompts_source.exists():
                prompts_source_path = prompts_source
        
        # クリーンアップ処理
        if args.cleanup or args.archive:
            import shutil
            json_path = Path(args.json_file)
            
            if args.archive:
                # アーカイブディレクトリを作成
                archive_dir = Path(args.output).parent / 'archive'
                archive_dir.mkdir(exist_ok=True)
                
                # JSONファイルをアーカイブ
                if json_path.exists() and json_path.parent.name == 'output':
                    archive_json = archive_dir / json_path.name
                    if not archive_json.exists():
                        shutil.move(str(json_path), str(archive_json))
                        print(f"JSONファイルをアーカイブしました: {archive_json}")
                
                # プロンプトをアーカイブ
                if prompts_source_path and prompts_source_path.exists():
                    archive_prompts = archive_dir / 'prompts' / prompts_source_path.name
                    archive_prompts.parent.mkdir(parents=True, exist_ok=True)
                    if not archive_prompts.exists():
                        shutil.move(str(prompts_source_path), str(archive_prompts))
                        print(f"プロンプトをアーカイブしました: {archive_prompts}")
                
                # パターンディレクトリが空になったら削除
                if prompts_source_path:
                    pattern_dir = prompts_source_path.parent
                    if pattern_dir.exists() and not any(pattern_dir.iterdir()):
                        pattern_dir.rmdir()
                        print(f"空のパターンディレクトリを削除しました: {pattern_dir}")
                    
                    prompts_base_dir = pattern_dir.parent
                    if prompts_base_dir.exists() and not any(prompts_base_dir.iterdir()):
                        prompts_base_dir.rmdir()
                        print(f"空のプロンプトディレクトリを削除しました: {prompts_base_dir}")
            else:
                # 削除処理
                if json_path.exists() and json_path.parent.name == 'output':
                    json_path.unlink()
                    print(f"JSONファイルを削除しました: {json_path}")
                
                if prompts_source_path and prompts_source_path.exists():
                    shutil.rmtree(prompts_source_path)
                    print(f"プロンプトディレクトリを削除しました: {prompts_source_path}")
                    
                    # パターンディレクトリが空になったら削除
                    pattern_dir = prompts_source_path.parent
                    if pattern_dir.exists() and not any(pattern_dir.iterdir()):
                        pattern_dir.rmdir()
                        print(f"空のパターンディレクトリを削除しました: {pattern_dir}")
                    
                    # プロンプトベースディレクトリが空になったら削除
                    prompts_base_dir = pattern_dir.parent
                    if prompts_base_dir.exists() and not any(prompts_base_dir.iterdir()):
                        prompts_base_dir.rmdir()
                        print(f"空のプロンプトディレクトリを削除しました: {prompts_base_dir}")
        
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
    print(f"\n出力先: {article_path}")
    print("\n完了しました！")


if __name__ == '__main__':
    main()

