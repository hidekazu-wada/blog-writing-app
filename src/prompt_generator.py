"""
プロンプトテンプレートからJSONデータを埋め込んでプロンプトを生成するモジュール
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


class PromptGenerator:
    """プロンプトテンプレートにJSONデータを埋め込んで生成するクラス"""
    
    def __init__(self, template_file: str):
        """
        Args:
            template_file: プロンプトテンプレートファイルのパス
        """
        self.template_file = Path(template_file)
        if not self.template_file.exists():
            raise FileNotFoundError(f"テンプレートファイルが見つかりません: {template_file}")
        
        with open(self.template_file, 'r', encoding='utf-8') as f:
            self.template_content = f.read()
    
    def load_json_data(self, json_file: str) -> Dict:
        """JSONファイルを読み込む"""
        json_path = Path(json_file)
        if not json_path.exists():
            raise FileNotFoundError(f"JSONファイルが見つかりません: {json_file}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_phase(self, phase_name: str) -> Optional[str]:
        """テンプレートから特定のフェーズを抽出"""
        # フェーズの開始パターンを検索
        pattern = rf'## {re.escape(phase_name)}.*?\n(.*?)(?=\n## |\Z)'
        match = re.search(pattern, self.template_content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def generate_phase1(self, json_data: Dict) -> List[Dict[str, str]]:
        """phase1プロンプトを生成（各H2ごとに）"""
        prompts = []
        phase_template = self.extract_phase('phase1（FACT_ソース集め）')
        if not phase_template:
            return prompts
        
        for h2_index, h2_section in enumerate(json_data.get('article_structure', []), start=1):
            h2_title = h2_section.get('h2', '')
            if not h2_title:
                continue
            
            prompt = phase_template.replace(
                '[ここにH2または記事の主要テーマを入力]',
                h2_title
            )
            
            prompts.append({
                'phase': 'phase1',
                'h2_index': h2_index,
                'h2': h2_title,
                'prompt': prompt
            })
        
        return prompts
    
    def generate_phase2(self, json_data: Dict) -> List[Dict[str, str]]:
        """phase2プロンプトを生成（各H3ごとに）"""
        prompts = []
        phase_template = self.extract_phase('phase2（FACT_アウトプット）')
        if not phase_template:
            return prompts
        
        for h2_index, h2_section in enumerate(json_data.get('article_structure', []), start=1):
            h2_title = h2_section.get('h2', '')
            h3_sections = h2_section.get('h3_sections', [])
            
            for h3_index, h3_section in enumerate(h3_sections, start=1):
                h3_title = h3_section.get('h3', '')
                if not h3_title:
                    continue
                
                prompt = phase_template.replace(
                    '[ここにH3を入力]',
                    h3_title
                )
                
                prompts.append({
                    'phase': 'phase2',
                    'h2_index': h2_index,
                    'h3_index': h3_index,
                    'h2': h2_title,
                    'h3': h3_title,
                    'prompt': prompt
                })
        
        return prompts
    
    def generate_phase3(self, json_data: Dict) -> List[Dict[str, str]]:
        """phase3プロンプトを生成（各H2ごとに）"""
        prompts = []
        phase_template = self.extract_phase('phase3（Experience_アウトプット）')
        if not phase_template:
            return prompts
        
        for h2_index, h2_section in enumerate(json_data.get('article_structure', []), start=1):
            h2_title = h2_section.get('h2', '')
            h3_sections = h2_section.get('h3_sections', [])
            
            if not h2_title or not h3_sections:
                continue
            
            # H3のリストを作成
            h3_list = '\n'.join([f"- {h3.get('h3', '')}" for h3 in h3_sections if h3.get('h3')])
            
            prompt = phase_template.replace(
                '[ここにH2を入力]',
                h2_title
            ).replace(
                '[ここにH3のリストをすべて貼り付け]',
                h3_list
            )
            
            prompts.append({
                'phase': 'phase3',
                'h2_index': h2_index,
                'h2': h2_title,
                'prompt': prompt
            })
        
        return prompts
    
    def generate_phase4(self, json_data: Dict) -> Dict[str, str]:
        """phase4プロンプトを生成（設計図全体）"""
        phase_template = self.extract_phase('phase4（記事執筆）')
        if not phase_template:
            return {}
        
        # 設計図を構造化して表示
        blueprint = self._format_blueprint(json_data)
        
        # テンプレートに設計図を追加（適切な場所に挿入）
        # phase4は設計図を参照する形式なので、そのまま返す
        # 実際の使用時には設計図を別途提供する想定
        
        return {
            'phase': 'phase4',
            'prompt': phase_template,
            'blueprint': blueprint
        }
    
    def generate_phase5(self) -> Dict[str, str]:
        """phase5プロンプトを生成（テンプレートのみ）"""
        phase_template = self.extract_phase('phase5（画像生成）')
        if not phase_template:
            return {}
        
        return {
            'phase': 'phase5',
            'prompt': phase_template
        }
    
    def generate_phase6(self) -> Dict[str, str]:
        """phase6プロンプトを生成（テンプレートのみ）"""
        phase_template = self.extract_phase('phase6（まとめ）')
        if not phase_template:
            return {}
        
        return {
            'phase': 'phase6',
            'prompt': phase_template
        }
    
    def _format_blueprint(self, json_data: Dict) -> str:
        """設計図を読みやすい形式でフォーマット"""
        lines = []
        lines.append(f"# 設計図（パターン{json_data.get('pattern', '')}）\n")
        
        for h2_section in json_data.get('article_structure', []):
            h2_title = h2_section.get('h2', '')
            h3_sections = h2_section.get('h3_sections', [])
            
            lines.append(f"## {h2_title}\n")
            
            for h3_section in h3_sections:
                h3_title = h3_section.get('h3', '')
                advice = h3_section.get('advice', '')
                keywords = h3_section.get('keywords', [])
                
                lines.append(f"### {h3_title}\n")
                lines.append(f"**執筆アドバイス:** {advice}\n")
                if keywords:
                    keywords_str = ', '.join(keywords)
                    lines.append(f"**キーワード:** {keywords_str}\n")
                lines.append("\n")
        
        # 独自性の提案
        proposals = json_data.get('originality_proposals', [])
        if proposals:
            lines.append("## 独自性の提案\n")
            for proposal in proposals:
                title = proposal.get('title', '')
                advice = proposal.get('advice', '')
                lines.append(f"### {title}\n")
                lines.append(f"{advice}\n\n")
        
        return '\n'.join(lines)
    
    def generate_all(self, json_data: Dict) -> Dict[str, any]:
        """すべてのフェーズのプロンプトを生成"""
        return {
            'phase1': self.generate_phase1(json_data),
            'phase2': self.generate_phase2(json_data),
            'phase3': self.generate_phase3(json_data),
            'phase4': self.generate_phase4(json_data),
            'phase5': self.generate_phase5(),
            'phase6': self.generate_phase6()
        }
    
    def save_prompts(self, prompts: Dict[str, any], output_dir: str, json_data: Dict):
        """生成されたプロンプトをファイルに保存"""
        # パターン情報を取得
        pattern = json_data.get('pattern', 'Unknown')
        
        # パターン別のベースディレクトリを作成
        base_path = Path(output_dir) / f"pattern_{pattern}"
        base_path.mkdir(parents=True, exist_ok=True)
        
        # phase1: 各H2ごとに保存
        phase1_dir = base_path / "phase1"
        phase1_dir.mkdir(exist_ok=True)
        for prompt_data in prompts.get('phase1', []):
            h2_index = prompt_data.get('h2_index', 0)
            h2_safe = self._sanitize_filename(prompt_data['h2'])
            file_path = phase1_dir / f"{h2_index:02d}_{h2_safe}.md"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Phase 1: FACT_ソース集め\n\n")
                f.write(f"**パターン:** {pattern}\n")
                f.write(f"**H2番号:** {h2_index}\n")
                f.write(f"**対象H2:** {prompt_data['h2']}\n\n")
                f.write("---\n\n")
                f.write(prompt_data['prompt'])
        
        # phase2: 各H3ごとに保存
        phase2_dir = base_path / "phase2"
        phase2_dir.mkdir(exist_ok=True)
        for prompt_data in prompts.get('phase2', []):
            h2_index = prompt_data.get('h2_index', 0)
            h3_index = prompt_data.get('h3_index', 0)
            h2_safe = self._sanitize_filename(prompt_data['h2'])
            h3_safe = self._sanitize_filename(prompt_data['h3'])
            file_path = phase2_dir / f"{h2_index:02d}_{h3_index:02d}_{h3_safe}.md"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Phase 2: FACT_アウトプット\n\n")
                f.write(f"**パターン:** {pattern}\n")
                f.write(f"**H2番号:** {h2_index}\n")
                f.write(f"**H3番号:** {h3_index}\n")
                f.write(f"**対象H2:** {prompt_data['h2']}\n")
                f.write(f"**対象H3:** {prompt_data['h3']}\n\n")
                f.write("---\n\n")
                f.write(prompt_data['prompt'])
        
        # phase3: 各H2ごとに保存
        phase3_dir = base_path / "phase3"
        phase3_dir.mkdir(exist_ok=True)
        for prompt_data in prompts.get('phase3', []):
            h2_index = prompt_data.get('h2_index', 0)
            h2_safe = self._sanitize_filename(prompt_data['h2'])
            file_path = phase3_dir / f"{h2_index:02d}_{h2_safe}.md"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Phase 3: Experience_アウトプット\n\n")
                f.write(f"**パターン:** {pattern}\n")
                f.write(f"**H2番号:** {h2_index}\n")
                f.write(f"**対象H2:** {prompt_data['h2']}\n\n")
                f.write("---\n\n")
                f.write(prompt_data['prompt'])
        
        # phase4: 設計図とプロンプトを保存
        phase4_dir = base_path / "phase4"
        phase4_dir.mkdir(exist_ok=True)
        phase4_data = prompts.get('phase4', {})
        if phase4_data:
            file_path = phase4_dir / "記事執筆.md"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Phase 4: 記事執筆\n\n")
                f.write(f"**パターン:** {pattern}\n\n")
                f.write("---\n\n")
                f.write(phase4_data['prompt'])
                f.write("\n\n---\n\n")
                f.write("## 設計図（Pascal_Blueprint）\n\n")
                f.write(phase4_data.get('blueprint', ''))
        
        # phase5: テンプレートを保存
        phase5_dir = base_path / "phase5"
        phase5_dir.mkdir(exist_ok=True)
        phase5_data = prompts.get('phase5', {})
        if phase5_data:
            file_path = phase5_dir / "画像生成.md"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Phase 5: 画像生成\n\n")
                f.write(f"**パターン:** {pattern}\n\n")
                f.write("---\n\n")
                f.write(phase5_data['prompt'])
        
        # phase6: テンプレートを保存
        phase6_dir = base_path / "phase6"
        phase6_dir.mkdir(exist_ok=True)
        phase6_data = prompts.get('phase6', {})
        if phase6_data:
            file_path = phase6_dir / "まとめ.md"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Phase 6: まとめ\n\n")
                f.write(f"**パターン:** {pattern}\n\n")
                f.write("---\n\n")
                f.write(phase6_data['prompt'])
    
    def _sanitize_filename(self, filename: str) -> str:
        """ファイル名に使えない文字を置換"""
        # ファイル名に使えない文字を置換
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        # 長すぎる場合は切り詰め
        if len(filename) > 100:
            filename = filename[:100]
        return filename

