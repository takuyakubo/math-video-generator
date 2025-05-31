import re
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class ChapterDetector:
    """文書のチャプター構造を自動検出するクラス"""
    
    def __init__(self):
        # 章検出のためのパターン定義
        self.chapter_patterns = [
            # 日本語パターン
            (r'^第\s*([0-9０-９一二三四五六七八九十]+)\s*章\s*(.+)', 'chapter', 1),
            (r'^第\s*([0-9０-９一二三四五六七八九十]+)\s*節\s*(.+)', 'section', 2),
            (r'^([0-9０-９]+)\.([0-9０-９]+)\s+(.+)', 'subsection', 3),
            
            # 英語パターン
            (r'^Chapter\s+([0-9]+)[\.:]\ *(.+)', 'chapter', 1),
            (r'^Section\s+([0-9]+)[\.:]\ *(.+)', 'section', 2),
            (r'^([0-9]+)\.([0-9]+)\.([0-9]+)\s+(.+)', 'subsubsection', 4),
            (r'^([0-9]+)\.([0-9]+)\s+(.+)', 'subsection', 3),
            (r'^([0-9]+)\.\s+(.+)', 'section', 2),
            
            # 数学特有のパターン
            (r'^定理\s*([0-9]+)[\.:]\ *(.+)', 'theorem', 3),
            (r'^補題\s*([0-9]+)[\.:]\ *(.+)', 'lemma', 3),
            (r'^証明[\.:]\ *(.+)', 'proof', 3),
            (r'^例\s*([0-9]+)[\.:]\ *(.+)', 'example', 3),
            
            # LaTeX特有のパターン
            (r'^\\chapter\{(.+)\}', 'chapter', 1),
            (r'^\\section\{(.+)\}', 'section', 2),
            (r'^\\subsection\{(.+)\}', 'subsection', 3),
            (r'^\\subsubsection\{(.+)\}', 'subsubsection', 4),
        ]
    
    def detect_chapters(self, text: str, source_type: str = 'text') -> List[Dict]:
        """
        テキストからチャプター構造を検出
        
        Args:
            text: 解析するテキスト
            source_type: ソースの種類 ('text', 'latex', 'pdf')
            
        Returns:
            チャプター情報のリスト
        """
        chapters = []
        lines = text.split('\n')
        
        for line_no, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            chapter_info = self._match_chapter_pattern(line, line_no)
            if chapter_info:
                chapters.append(chapter_info)
        
        # チャプターの階層構造を整理
        chapters = self._organize_hierarchy(chapters)
        
        # ビデオ用のタイムスタンプを推定
        chapters = self._estimate_timestamps(chapters, len(lines))
        
        logger.info(f"Detected {len(chapters)} chapters/sections")
        return chapters
    
    def _match_chapter_pattern(self, line: str, line_no: int) -> Dict:
        """行がチャプターパターンにマッチするかチェック"""
        for pattern, chapter_type, level in self.chapter_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                title = self._extract_title(match, chapter_type)
                number = self._extract_number(match, chapter_type)
                
                return {
                    'title': title,
                    'type': chapter_type,
                    'level': level,
                    'number': number,
                    'line_number': line_no,
                    'original_text': line
                }
        
        return None
    
    def _extract_title(self, match, chapter_type: str) -> str:
        """マッチオブジェクトからタイトルを抽出"""
        groups = match.groups()
        if not groups:
            return ""
        
        # 最後のグループがタイトルであることが多い
        if len(groups) >= 2:
            return groups[-1].strip()
        else:
            return groups[0].strip()
    
    def _extract_number(self, match, chapter_type: str) -> str:
        """マッチオブジェクトから番号を抽出"""
        groups = match.groups()
        if not groups:
            return ""
        
        # 最初のグループが番号であることが多い
        return groups[0].strip()
    
    def _organize_hierarchy(self, chapters: List[Dict]) -> List[Dict]:
        """チャプターの階層構造を整理"""
        organized = []
        current_chapter = None
        current_section = None
        
        for chapter in chapters:
            chapter_copy = chapter.copy()
            
            if chapter['type'] == 'chapter':
                current_chapter = chapter_copy
                current_section = None
                chapter_copy['children'] = []
                organized.append(chapter_copy)
                
            elif chapter['type'] in ['section', 'theorem', 'lemma', 'example']:
                if current_chapter:
                    current_chapter['children'].append(chapter_copy)
                    current_section = chapter_copy
                    chapter_copy['parent'] = current_chapter['title']
                else:
                    organized.append(chapter_copy)
                    
            elif chapter['type'] in ['subsection', 'proof']:
                if current_section:
                    if 'children' not in current_section:
                        current_section['children'] = []
                    current_section['children'].append(chapter_copy)
                    chapter_copy['parent'] = current_section['title']
                elif current_chapter:
                    current_chapter['children'].append(chapter_copy)
                    chapter_copy['parent'] = current_chapter['title']
                else:
                    organized.append(chapter_copy)
        
        return organized
    
    def _estimate_timestamps(self, chapters: List[Dict], total_lines: int) -> List[Dict]:
        """各チャプターの推定タイムスタンプを計算"""
        if not chapters:
            return chapters
        
        # 1行あたりの平均時間を推定（読み上げ速度から）
        # 平均的な読み上げ速度: 150-200 words/minute
        # 日本語: 約300-400文字/minute
        estimated_duration_per_line = 2.0  # 秒
        
        for i, chapter in enumerate(chapters):
            line_no = chapter.get('line_number', 0)
            
            # 開始時間
            start_time = line_no * estimated_duration_per_line
            
            # 終了時間（次のチャプターの開始時間、または文書の終わり）
            if i + 1 < len(chapters):
                next_line = chapters[i + 1].get('line_number', total_lines)
            else:
                next_line = total_lines
            
            end_time = next_line * estimated_duration_per_line
            
            chapter['start_time'] = start_time
            chapter['end_time'] = end_time
            chapter['duration'] = end_time - start_time
        
        return chapters