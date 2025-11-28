"""
プロンプト生成のコマンドラインインターフェース
"""
import argparse
import sys
from pathlib import Path

# 相対インポートと絶対インポートの両方に対応
try:
    from .prompt_generator import PromptGenerator
except ImportError:
    from prompt_generator import PromptGenerator


def main():
    parser = argparse.ArgumentParser(
        description='JSONデータからプロンプトを生成します'
    )
    parser.add_argument(
        'json_file',
        type=str,
        help='抽出されたJSONデータファイルのパス'
    )
    parser.add_argument(
        '-t', '--template',
        type=str,
        default='templates/prompts.md',
        help='プロンプトテンプレートファイルのパス（デフォルト: templates/prompts.md）'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='出力ディレクトリのパス（デフォルト: output/prompts/）'
    )
    parser.add_argument(
        '--phases',
        type=str,
        default=None,
        help='生成するフェーズを指定（カンマ区切り、例: 1,2,3）。指定しない場合はすべて生成'
    )
    
    args = parser.parse_args()
    
    # JSONファイルの存在確認
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"エラー: JSONファイルが見つかりません: {json_path}")
        sys.exit(1)
    
    # テンプレートファイルの存在確認
    template_path = Path(args.template)
    if not template_path.exists():
        print(f"エラー: テンプレートファイルが見つかりません: {template_path}")
        sys.exit(1)
    
    # プロンプトジェネレーターを初期化
    try:
        generator = PromptGenerator(str(template_path))
    except Exception as e:
        print(f"エラー: テンプレートファイルの読み込みに失敗しました: {e}")
        sys.exit(1)
    
    # JSONデータを読み込む
    try:
        json_data = generator.load_json_data(str(json_path))
    except Exception as e:
        print(f"エラー: JSONファイルの読み込みに失敗しました: {e}")
        sys.exit(1)
    
    # 出力ディレクトリを決定
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path('output') / 'prompts'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成するフェーズを決定
    if args.phases:
        try:
            phase_numbers = [int(x.strip()) for x in args.phases.split(',')]
            phases_to_generate = [f'phase{num}' for num in phase_numbers]
        except ValueError:
            print("エラー: フェーズ番号は数値でカンマ区切りで指定してください。")
            sys.exit(1)
    else:
        phases_to_generate = ['phase1', 'phase2', 'phase3', 'phase4', 'phase5', 'phase6']
    
    # プロンプトを生成
    print("\n" + "="*60)
    print("プロンプト生成中...")
    print("="*60)
    
    all_prompts = generator.generate_all(json_data)
    
    # 指定されたフェーズのみを保存
    prompts_to_save = {}
    for phase in phases_to_generate:
        if phase in all_prompts:
            prompts_to_save[phase] = all_prompts[phase]
        else:
            print(f"警告: {phase}が見つかりませんでした。")
    
    # プロンプトを保存
    try:
        generator.save_prompts(prompts_to_save, str(output_dir), json_data)
    except Exception as e:
        print(f"エラー: プロンプトの保存に失敗しました: {e}")
        sys.exit(1)
    
    # 結果を表示
    pattern = json_data.get('pattern', 'Unknown')
    pattern_dir = Path(output_dir) / f"pattern_{pattern}"
    
    print("\n" + "="*60)
    print("生成結果のサマリー")
    print("="*60)
    print(f"**パターン:** {pattern}")
    
    phase1_count = len(prompts_to_save.get('phase1', []))
    phase2_count = len(prompts_to_save.get('phase2', []))
    phase3_count = len(prompts_to_save.get('phase3', []))
    
    if phase1_count > 0:
        print(f"Phase 1: {phase1_count}件のプロンプトを生成（各H2ごと）")
    if phase2_count > 0:
        print(f"Phase 2: {phase2_count}件のプロンプトを生成（各H3ごと）")
    if phase3_count > 0:
        print(f"Phase 3: {phase3_count}件のプロンプトを生成（各H2ごと）")
    if 'phase4' in prompts_to_save:
        print("Phase 4: 記事執筆プロンプトを生成")
    if 'phase5' in prompts_to_save:
        print("Phase 5: 画像生成プロンプトを生成")
    if 'phase6' in prompts_to_save:
        print("Phase 6: まとめプロンプトを生成")
    
    print(f"\n出力先: {pattern_dir}")
    print("\n完了しました！")


if __name__ == '__main__':
    main()

