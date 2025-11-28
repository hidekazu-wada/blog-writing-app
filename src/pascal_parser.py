"""
Pascal SEOツールのHTMLレポートを解析するモジュール
"""
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import re


class PascalParser:
    """Pascal HTMLレポートを解析するクラス"""
    
    def __init__(self, html_file_path: str):
        """
        Args:
            html_file_path: Pascal HTMLファイルのパス
        """
        self.html_file_path = html_file_path
        with open(html_file_path, 'r', encoding='utf-8') as f:
            self.soup = BeautifulSoup(f.read(), 'lxml')
    
    def find_ai_article_section(self) -> Optional:
        """AIによる記事構成案セクションを検索"""
        # 「AIによる記事構成案」というH2を探す
        h2_title = self.soup.find('h2', class_='title', string=re.compile('AIによる記事構成案'))
        if not h2_title:
            return None
        
        # 親のsectionContentsを取得
        section = h2_title.find_parent('div', class_='sectionContents')
        return section
    
    def extract_patterns(self) -> Dict[str, any]:
        """パターンAとパターンBを抽出"""
        section = self.find_ai_article_section()
        if not section:
            return {}
        
        patterns = {}
        
        # パターンAを探す
        pattern_a_title = section.find('div', class_='section-draft-title', string=re.compile('記事構成案 パターンA'))
        if pattern_a_title:
            pattern_a_container = pattern_a_title.find_parent('div', class_='section-draft-inn')
            patterns['A'] = self._extract_pattern_structure(pattern_a_container)
        
        # パターンBを探す
        pattern_b_title = section.find('div', class_='section-draft-title', string=re.compile('記事構成案 パターンB'))
        if pattern_b_title:
            pattern_b_container = pattern_b_title.find_parent('div', class_='section-draft-inn')
            patterns['B'] = self._extract_pattern_structure(pattern_b_container)
        
        return patterns
    
    def _extract_pattern_structure(self, container) -> List[Dict]:
        """パターンの構造を抽出（H2、H3、アドバイス、キーワード）"""
        structure = []
        current_h2 = None
        current_h3_list = []
        
        # コンテナ内のすべての要素を順番に処理
        for element in container.find_all(['div'], recursive=False):
            # H2の検出
            if element.get('class') and 'h2' in element.get('class', []):
                # 前のH2を保存
                if current_h2:
                    structure.append({
                        'h2': current_h2,
                        'h3_sections': current_h3_list
                    })
                
                # 新しいH2を取得
                h2_text_elem = element.find('div', class_='block-tag-text')
                if h2_text_elem:
                    current_h2 = h2_text_elem.get_text(strip=True)
                    current_h3_list = []
            
            # H3の検出
            elif element.get('class') and 'h3' in element.get('class', []):
                h3_data = self._extract_h3_data(element)
                if h3_data:
                    current_h3_list.append(h3_data)
        
        # 最後のH2を保存
        if current_h2:
            structure.append({
                'h2': current_h2,
                'h3_sections': current_h3_list
            })
        
        return structure
    
    def _extract_h3_data(self, h3_element) -> Optional[Dict]:
        """H3要素からデータを抽出"""
        # H3見出しを取得
        h3_title_elem = h3_element.find('div', class_='h3-left')
        if not h3_title_elem:
            return None
        
        h3_title = h3_title_elem.get_text(strip=True)
        
        # 執筆のアドバイスを取得
        advice_elem = h3_element.find('div', class_='block-advice-text')
        advice = advice_elem.get_text(strip=True) if advice_elem else ""
        
        # キーワードを取得
        keyword_elem = h3_element.find('div', class_='block-keyword-text')
        keywords = []
        if keyword_elem:
            keyword_spans = keyword_elem.find_all('span')
            keywords = [span.get_text(strip=True) for span in keyword_spans if span.get_text(strip=True)]
        
        return {
            'h3': h3_title,
            'advice': advice,
            'keywords': keywords
        }
    
    def extract_h1_title_candidates(self) -> List[str]:
        """記事タイトルの候補（H1）を抽出"""
        section = self.find_ai_article_section()
        if not section:
            return []
        
        # 「記事タイトルの候補」というH4を探す
        h4_title = section.find('h4', class_='title', string=re.compile('記事タイトルの候補'))
        if not h4_title:
            return []
        
        # 親のsectionBlockを取得
        section_block = h4_title.find_parent('div', class_='sectionBlock')
        if not section_block:
            return []
        
        # section-title要素を探す
        section_title = section_block.find('div', class_='section-title')
        if not section_title:
            return []
        
        titles = []
        
        # 各title要素を取得
        title_elements = section_title.find_all('div', class_='title')
        for title_elem in title_elements:
            # check-iconを削除してテキストを取得
            for icon in title_elem.find_all('span', class_='check-icon'):
                icon.decompose()
            title = title_elem.get_text(strip=True)
            if title:
                titles.append(title)
        
        return titles
    
    def extract_originality_proposals(self) -> List[Dict]:
        """独自性の提案セクションを抽出"""
        section = self.find_ai_article_section()
        if not section:
            return []
        
        # 「独自性の提案」というH4を探す
        h4_title = section.find('h4', class_='title', string=re.compile('独自性の提案'))
        if not h4_title:
            return []
        
        # 親のsectionBlockを取得
        section_block = h4_title.find_parent('div', class_='sectionBlock')
        if not section_block:
            return []
        
        proposals = []
        
        # block-original要素を探す
        original_blocks = section_block.find_all('div', class_='block-original')
        for block in original_blocks:
            # 見出しを取得（check-iconを除く）
            title_elem = block.find('div', class_='block-title')
            if title_elem:
                # check-iconを削除してテキストを取得
                for icon in title_elem.find_all('span', class_='check-icon'):
                    icon.decompose()
                title = title_elem.get_text(strip=True)
            else:
                title = ""
            
            # 執筆のアドバイスを取得
            advice_elem = block.find('div', class_='block-text')
            advice = advice_elem.get_text(strip=True) if advice_elem else ""
            
            if title:  # タイトルがある場合のみ追加
                proposals.append({
                    'title': title,
                    'advice': advice
                })
        
        return proposals
    
    def extract_selected_pattern(self, pattern: str) -> Dict:
        """選択したパターンのデータを抽出"""
        patterns = self.extract_patterns()
        if pattern not in patterns:
            raise ValueError(f"パターン{pattern}が見つかりません。利用可能なパターン: {list(patterns.keys())}")
        
        return {
            'pattern': pattern,
            'article_structure': patterns[pattern]
        }
    
    def extract_selected_proposals(self, selected_indices: List[int]) -> List[Dict]:
        """選択した独自性の提案を抽出"""
        all_proposals = self.extract_originality_proposals()
        selected = []
        
        for idx in selected_indices:
            if 0 <= idx < len(all_proposals):
                selected.append(all_proposals[idx])
        
        return selected
    
    def extract_all(self, pattern: str, proposal_indices: List[int] = None) -> Dict:
        """すべての情報を抽出して統合"""
        result = self.extract_selected_pattern(pattern)
        
        # H1タイトル候補を追加
        result['h1_title_candidates'] = self.extract_h1_title_candidates()
        
        if proposal_indices is not None:
            result['originality_proposals'] = self.extract_selected_proposals(proposal_indices)
        else:
            result['originality_proposals'] = []
        
        return result

