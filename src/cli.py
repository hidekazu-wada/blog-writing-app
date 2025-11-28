"""
Pascal HTML解析のコマンドラインインターフェース
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List

# 相対インポートと絶対インポートの両方に対応
try:
    from .pascal_parser import PascalParser
except ImportError:
    from pascal_parser import PascalParser


def print_pattern_info(patterns: dict):
    """パターン情報を表示"""
    print("\n利用可能なパターン:")
    for pattern_key in patterns.keys():
        h2_count = len(patterns[pattern_key])
        print(f"  パターン{pattern_key}: H2が{h2_count}個")


def print_proposals(proposals: List[dict]):
    """独自性の提案を表示"""
    if not proposals:
        print("\n独自性の提案は見つかりませんでした。")
        return
    
    print(f"\n独自性の提案 ({len(proposals)}件):")
    for i, proposal in enumerate(proposals):
        print(f"\n  [{i}] {proposal['title']}")
        print(f"      アドバイス: {proposal['advice'][:80]}..." if len(proposal['advice']) > 80 else f"      アドバイス: {proposal['advice']}")


def select_pattern(parser: PascalParser) -> str:
    """パターンを選択"""
    patterns = parser.extract_patterns()
    
    if not patterns:
        print("エラー: パターンが見つかりませんでした。")
        sys.exit(1)
    
    print_pattern_info(patterns)
    
    while True:
        choice = input("\nパターンを選択してください (A/B): ").strip().upper()
        if choice in patterns:
            return choice
        print("無効な選択です。AまたはBを入力してください。")


def select_proposals(parser: PascalParser) -> List[int]:
    """独自性の提案を選択"""
    proposals = parser.extract_originality_proposals()
    
    if not proposals:
        print("\n独自性の提案はありません。")
        return []
    
    print_proposals(proposals)
    
    print("\n選択する提案の番号を入力してください（カンマ区切り、例: 0,1,2）。")
    print("何も選択しない場合はEnterキーを押してください。")
    
    while True:
        choice = input("選択: ").strip()
        
        if not choice:
            return []
        
        try:
            indices = [int(x.strip()) for x in choice.split(',')]
            # 有効なインデックスかチェック
            invalid = [idx for idx in indices if idx < 0 or idx >= len(proposals)]
            if invalid:
                print(f"エラー: 無効な番号があります: {invalid}")
                continue
            return indices
        except ValueError:
            print("エラー: 数値を入力してください（カンマ区切り）。")


def save_output(data: dict, output_path: Path):
    """結果をJSONファイルに保存"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n結果を保存しました: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Pascal SEOツールのHTMLレポートを解析して情報を抽出します'
    )
    parser.add_argument(
        'html_file',
        type=str,
        help='解析するPascal HTMLファイルのパス'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='出力ファイルのパス（デフォルト: output/extracted_data.json）'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        choices=['A', 'B'],
        default=None,
        help='パターンを直接指定（指定しない場合は対話的に選択）'
    )
    parser.add_argument(
        '--proposals',
        type=str,
        default=None,
        help='独自性の提案のインデックス（カンマ区切り、例: 0,1,2）'
    )
    
    args = parser.parse_args()
    
    # HTMLファイルの存在確認
    html_path = Path(args.html_file)
    if not html_path.exists():
        print(f"エラー: ファイルが見つかりません: {html_path}")
        sys.exit(1)
    
    # パーサーを初期化
    try:
        pascal_parser = PascalParser(str(html_path))
    except Exception as e:
        print(f"エラー: HTMLファイルの読み込みに失敗しました: {e}")
        sys.exit(1)
    
    # パターンを選択
    if args.pattern:
        pattern = args.pattern
        # パターンの存在確認
        patterns = pascal_parser.extract_patterns()
        if pattern not in patterns:
            print(f"エラー: パターン{pattern}が見つかりません。")
            sys.exit(1)
    else:
        pattern = select_pattern(pascal_parser)
    
    # 独自性の提案を選択
    if args.proposals:
        try:
            proposal_indices = [int(x.strip()) for x in args.proposals.split(',')]
        except ValueError:
            print("エラー: 提案のインデックスは数値でカンマ区切りで指定してください。")
            sys.exit(1)
    else:
        proposal_indices = select_proposals(pascal_parser)
    
    # データを抽出
    try:
        result = pascal_parser.extract_all(pattern, proposal_indices)
    except Exception as e:
        print(f"エラー: データの抽出に失敗しました: {e}")
        sys.exit(1)
    
    # 結果を表示
    print("\n" + "="*60)
    print("抽出結果のサマリー")
    print("="*60)
    print(f"選択したパターン: {result['pattern']}")
    print(f"H2の数: {len(result['article_structure'])}")
    print(f"選択した独自性の提案: {len(result['originality_proposals'])}件")
    
    # 出力ファイルのパスを決定
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / 'extracted_data.json'
    
    # 結果を保存
    save_output(result, output_path)
    
    print("\n完了しました！")


if __name__ == '__main__':
    main()

