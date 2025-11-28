"""
記事ディレクトリ構造を自動生成するモジュール
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ArticleStructureGenerator:
    """記事ディレクトリ構造を生成するクラス"""
    
    def __init__(self, json_file: str):
        """
        Args:
            json_file: 抽出されたJSONデータファイルのパス
        """
        self.json_file = Path(json_file)
        if not self.json_file.exists():
            raise FileNotFoundError(f"JSONファイルが見つかりません: {json_file}")
        
        with open(self.json_file, 'r', encoding='utf-8') as f:
            self.json_data = json.load(f)
    
    def _sanitize_filename(self, filename: str) -> str:
        """ファイル名に使えない文字を置換"""
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        # 長すぎる場合は切り詰め
        if len(filename) > 100:
            filename = filename[:100]
        return filename
    
    def _generate_article_id(self, output_dir: str, h1_title: str) -> str:
        """記事IDを生成（日付+連番形式）"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 現在の日付を取得
        date_str = datetime.now().strftime('%Y%m%d')
        
        # 同じ日付の記事を検索して連番を決定
        existing_articles = [
            d for d in output_path.iterdir()
            if d.is_dir() and d.name.startswith(date_str)
        ]
        
        # 連番を決定（001, 002, ...）
        sequence = len(existing_articles) + 1
        sequence_str = f"{sequence:03d}"
        
        # タイトルから短い識別子を生成
        title_short = self._sanitize_filename(h1_title)
        # 長すぎる場合は最初の30文字程度に
        if len(title_short) > 30:
            title_short = title_short[:30]
        
        article_id = f"{date_str}_{sequence_str}_{title_short}"
        return article_id
    
    def generate_structure(self, output_dir: str, selected_h1_title: Optional[str] = None, 
                          source_html_file: Optional[str] = None):
        """
        記事ディレクトリ構造を生成（ハイブリッド構造）
        
        Args:
            output_dir: 出力先ディレクトリ
            selected_h1_title: 選択されたH1タイトル（Noneの場合は最初の候補を使用）
            source_html_file: 元のHTMLファイルのパス（メタデータ用）
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # H1タイトルを決定
        h1_candidates = self.json_data.get('h1_title_candidates', [])
        if not h1_candidates:
            raise ValueError("H1タイトル候補が見つかりません。")
        
        if selected_h1_title:
            if selected_h1_title not in h1_candidates:
                raise ValueError(f"指定されたH1タイトルが見つかりません: {selected_h1_title}")
            h1_title = selected_h1_title
        else:
            h1_title = h1_candidates[0]
        
        # 記事IDを生成
        article_id = self._generate_article_id(str(output_path), h1_title)
        article_path = output_path / article_id
        article_path.mkdir(exist_ok=True)
        
        # サブディレクトリを作成
        content_path = article_path / 'content'
        content_path.mkdir(exist_ok=True)
        prompts_path = article_path / 'prompts'
        prompts_path.mkdir(exist_ok=True)
        
        # メタデータファイルを作成
        pattern = self.json_data.get('pattern', 'Unknown')
        metadata = {
            'article_id': article_id,
            'h1_title': h1_title,
            'h1_title_candidates': h1_candidates,
            'pattern': pattern,
            'created_at': datetime.now().isoformat(),
            'source_json': str(self.json_file.name),
            'source_html': source_html_file if source_html_file else None,
            'h2_count': len(self.json_data.get('article_structure', [])),
            'originality_proposals_count': len(self.json_data.get('originality_proposals', []))
        }
        
        metadata_file = article_path / '.article.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 元のJSONデータをコピー
        source_json_file = article_path / 'source.json'
        shutil.copy2(self.json_file, source_json_file)
        
        # H1ファイルを作成（contentディレクトリ内）
        h1_file = content_path / f"h1_{h1_title}.md"
        with open(h1_file, 'w', encoding='utf-8') as f:
            f.write(f"# {h1_title}\n\n")
            f.write("<!-- ここにH1用のコンテンツを記入 -->\n")
        
        # 各H2ごとにディレクトリとファイルを作成（contentディレクトリ内）
        article_structure = self.json_data.get('article_structure', [])
        
        for h2_index, h2_section in enumerate(article_structure, start=1):
            h2_title = h2_section.get('h2', '')
            if not h2_title:
                continue
            
            # H2ディレクトリを作成（contentディレクトリ内）
            h2_dir_name = f"h2-{h2_index}_{self._sanitize_filename(h2_title)}"
            h2_path = content_path / h2_dir_name
            h2_path.mkdir(exist_ok=True)
            
            # H2ファイルを作成
            h2_file = h2_path / f"h2-{h2_index}_{h2_title}.md"
            with open(h2_file, 'w', encoding='utf-8') as f:
                f.write(f"## {h2_title}\n\n")
                f.write("<!-- ここにH2用のコンテンツを記入 -->\n")
            
            # Pascalファイルを作成（H2の設計図・アドバイス）
            pascal_file = h2_path / f"pascal_h2-{h2_index}.md"
            with open(pascal_file, 'w', encoding='utf-8') as f:
                f.write(f"# Pascal設計図: {h2_title}\n\n")
                f.write(f"**パターン:** {pattern}\n")
                f.write(f"**H2番号:** {h2_index}\n\n")
                
                # H3セクションの情報を書き込む
                h3_sections = h2_section.get('h3_sections', [])
                if h3_sections:
                    f.write("## H3一覧\n\n")
                    
                    for h3_index, h3_section in enumerate(h3_sections, start=1):
                        h3_title = h3_section.get('h3', '')
                        if not h3_title:
                            continue
                        
                        f.write(f"### H3-{h3_index}: {h3_title}\n\n")
                        
                        # 執筆アドバイス
                        advice = h3_section.get('advice', '')
                        if advice:
                            f.write(f"**執筆アドバイス:**\n\n")
                            f.write(f"{advice}\n\n")
                        
                        # キーワード
                        keywords = h3_section.get('keywords', [])
                        if keywords:
                            keywords_str = ', '.join(keywords)
                            f.write(f"**キーワード:**\n\n")
                            f.write(f"{keywords_str}\n\n")
                        
                        f.write("---\n\n")
            
            # Experienceファイルを作成
            experience_file = h2_path / f"experience_h2-{h2_index}.md"
            with open(experience_file, 'w', encoding='utf-8') as f:
                f.write(f"# Experience: {h2_title}\n\n")
                f.write("<!-- ここに体験談を記入 -->\n")
            
            # 各H3ファイルを作成
            h3_sections = h2_section.get('h3_sections', [])
            for h3_index, h3_section in enumerate(h3_sections, start=1):
                h3_title = h3_section.get('h3', '')
                if not h3_title:
                    continue
                
                h3_file = h2_path / f"h3-{h3_index}_{h3_title}.md"
                with open(h3_file, 'w', encoding='utf-8') as f:
                    f.write(f"### {h3_title}\n\n")
                    f.write("<!-- ここにH3用のコンテンツを記入 -->\n")
        
        return str(article_path)
    
    def list_h1_candidates(self) -> List[str]:
        """H1タイトル候補のリストを返す"""
        return self.json_data.get('h1_title_candidates', [])

