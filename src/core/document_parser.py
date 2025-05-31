import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import PyPDF2
import pdfplumber
from pylatex import Document as LatexDocument
from pylatex.utils import NoEscape
import re

logger = logging.getLogger(__name__)

class DocumentParser:
    """数学文書（PDF、LaTeX）の解析クラス"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.tex', '.md']
    
    async def parse_document(self, file_path: Path) -> Dict:
        """
        文書を解析してメタデータと構造を抽出
        
        Args:
            file_path: ファイルパス
            
        Returns:
            解析結果の辞書
        """
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            return await self._parse_pdf(file_path)
        elif suffix == '.tex':
            return await self._parse_latex(file_path)
        elif suffix == '.md':
            return await self._parse_markdown(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    async def _parse_pdf(self, file_path: Path) -> Dict:
        """PDF文書の解析"""
        result = {
            'title': '',
            'author': '',
            'abstract': '',
            'chapters': [],
            'total_pages': 0,
            'text_content': '',
            'math_expressions': []
        }
        
        try:
            # PyPDF2でメタデータ取得
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                result['total_pages'] = len(pdf_reader.pages)
                
                if pdf_reader.metadata:
                    result['title'] = pdf_reader.metadata.get('/Title', '')
                    result['author'] = pdf_reader.metadata.get('/Author', '')
            
            # pdfplumberで詳細テキスト抽出
            with pdfplumber.open(file_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                
                result['text_content'] = full_text
                
                # 章構造の検出
                result['chapters'] = self._detect_chapters(full_text)
                
                # 数式の検出（LaTeX形式）
                result['math_expressions'] = self._extract_math_expressions(full_text)
                
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            raise
        
        return result
    
    async def _parse_latex(self, file_path: Path) -> Dict:
        """LaTeX文書の解析"""
        result = {
            'title': '',
            'author': '',
            'abstract': '',
            'chapters': [],
            'total_pages': 0,
            'text_content': '',
            'math_expressions': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            result['text_content'] = content
            
            # メタデータ抽出
            result['title'] = self._extract_latex_command(content, 'title')
            result['author'] = self._extract_latex_command(content, 'author')
            result['abstract'] = self._extract_latex_environment(content, 'abstract')
            
            # 章構造抽出
            result['chapters'] = self._extract_latex_structure(content)
            
            # 数式抽出
            result['math_expressions'] = self._extract_latex_math(content)
            
        except Exception as e:
            logger.error(f"LaTeX parsing error: {e}")
            raise
        
        return result
    
    async def _parse_markdown(self, file_path: Path) -> Dict:
        """Markdown文書の解析"""
        result = {
            'title': '',
            'author': '',
            'abstract': '',
            'chapters': [],
            'total_pages': 0,
            'text_content': '',
            'math_expressions': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            result['text_content'] = content
            result['chapters'] = self._detect_chapters(content)
            result['math_expressions'] = self._extract_math_expressions(content)
            
            # Markdownの場合、最初のH1をタイトルとして扱う
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                result['title'] = title_match.group(1)
                
        except Exception as e:
            logger.error(f"Markdown parsing error: {e}")
            raise
        
        return result
    
    def _detect_chapters(self, text: str) -> List[Dict]:
        """テキストから章構造を検出"""
        chapters = []
        lines = text.split('\n')
        
        chapter_patterns = [
            r'^第\s*\d+\s*章\s+(.+)',  # 第1章 タイトル
            r'^Chapter\s+\d+[\.:]\ *(.+)',  # Chapter 1: Title
            r'^\d+\.\s+(.+)',  # 1. タイトル
            r'^#{1,3}\s+(.+)$',  # Markdown headers
            r'^[A-Z][A-Z\s]+$'  # 全大文字のタイトル
        ]
        
        for i, line in enumerate(lines):
            line = line.strip()
            for pattern in chapter_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    chapters.append({
                        'title': match.group(1) if match.groups() else line,
                        'line_number': i,
                        'type': 'chapter'
                    })
                    break
        
        return chapters
    
    def _extract_math_expressions(self, text: str) -> List[str]:
        """数式を抽出"""
        # LaTeX形式の数式パターン
        patterns = [
            r'\$\$([^$]+)\$\$',  # Display math
            r'\$([^$]+)\$',      # Inline math
            r'\\begin\{equation\}(.*?)\\end\{equation\}',  # equation環境
            r'\\begin\{align\}(.*?)\\end\{align\}'  # align環境
        ]
        
        math_expressions = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            math_expressions.extend(matches)
        
        return math_expressions
    
    def _extract_latex_command(self, content: str, command: str) -> str:
        """LaTeXコマンドの内容を抽出"""
        pattern = rf'\\{command}\{{([^}}]+)\}}'
        match = re.search(pattern, content)
        return match.group(1) if match else ''
    
    def _extract_latex_environment(self, content: str, env: str) -> str:
        """LaTeX環境の内容を抽出"""
        pattern = rf'\\begin\{{{env}\}}(.*?)\\end\{{{env}\}}'
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ''
    
    def _extract_latex_structure(self, content: str) -> List[Dict]:
        """LaTeX文書の構造を抽出"""
        chapters = []
        
        # セクション系コマンドのパターン
        section_patterns = [
            (r'\\chapter\{([^}]+)\}', 'chapter'),
            (r'\\section\{([^}]+)\}', 'section'),
            (r'\\subsection\{([^}]+)\}', 'subsection'),
            (r'\\subsubsection\{([^}]+)\}', 'subsubsection')
        ]
        
        for pattern, section_type in section_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                chapters.append({
                    'title': match.group(1),
                    'type': section_type,
                    'position': match.start()
                })
        
        # 位置順にソート
        chapters.sort(key=lambda x: x['position'])
        
        return chapters
    
    def _extract_latex_math(self, content: str) -> List[str]:
        """LaTeX数式を抽出"""
        math_patterns = [
            r'\\begin\{equation\}(.*?)\\end\{equation\}',
            r'\\begin\{align\}(.*?)\\end\{align\}',
            r'\\begin\{eqnarray\}(.*?)\\end\{eqnarray\}',
            r'\$\$([^$]+)\$\$',
            r'\$([^$]+)\$'
        ]
        
        math_expressions = []
        for pattern in math_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            math_expressions.extend(matches)
        
        return math_expressions