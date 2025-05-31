import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.document_parser import DocumentParser

class TestDocumentParser:
    """DocumentParser のテストクラス"""
    
    def setup_method(self):
        self.parser = DocumentParser()
    
    def test_supported_formats(self):
        """サポートされているファイル形式をテスト"""
        expected_formats = ['.pdf', '.tex', '.md']
        assert self.parser.supported_formats == expected_formats
    
    @pytest.mark.asyncio
    async def test_parse_unsupported_format(self):
        """サポートされていないファイル形式のテスト"""
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp:
            tmp_path = Path(tmp.name)
            
            with pytest.raises(ValueError, match="Unsupported file format"):
                await self.parser.parse_document(tmp_path)
    
    def test_detect_chapters_japanese(self):
        """日本語の章構造検出をテスト"""
        text = """
        第1章 微分積分学の基礎
        
        関数の概念について説明します。
        
        第2章 線形代数
        
        ベクトルと行列について学びます。
        """
        
        chapters = self.parser._detect_chapters(text)
        
        assert len(chapters) == 2
        assert chapters[0]['title'] == '微分積分学の基礎'
        assert chapters[1]['title'] == '線形代数'
    
    def test_detect_chapters_english(self):
        """英語の章構造検出をテスト"""
        text = """
        Chapter 1: Introduction to Calculus
        
        This chapter covers basic concepts.
        
        Chapter 2: Linear Algebra
        
        We will study vectors and matrices.
        """
        
        chapters = self.parser._detect_chapters(text)
        
        assert len(chapters) == 2
        assert chapters[0]['title'] == 'Introduction to Calculus'
        assert chapters[1]['title'] == 'Linear Algebra'
    
    def test_extract_math_expressions(self):
        """数式抽出をテスト"""
        text = """
        導関数の定義は以下の通りです：
        $$f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}$$
        
        また、インライン数式 $x^2 + y^2 = r^2$ もあります。
        
        \begin{equation}
        \int_a^b f(x) dx = F(b) - F(a)
        \end{equation}
        """
        
        math_expressions = self.parser._extract_math_expressions(text)
        
        assert len(math_expressions) >= 3
        assert any("lim" in expr for expr in math_expressions)
        assert any("int" in expr for expr in math_expressions)
    
    def test_extract_latex_command(self):
        """LaTeXコマンド抽出をテスト"""
        content = r"\title{数学解析の基礎}\author{山田太郎}"
        
        title = self.parser._extract_latex_command(content, 'title')
        author = self.parser._extract_latex_command(content, 'author')
        
        assert title == '数学解析の基礎'
        assert author == '山田太郎'
    
    def test_extract_latex_environment(self):
        """LaTeX環境抽出をテスト"""
        content = r"""
        \begin{abstract}
        この論文では微分積分学の基礎について述べる。
        \end{abstract}
        """
        
        abstract = self.parser._extract_latex_environment(content, 'abstract')
        
        assert 'この論文では微分積分学の基礎について述べる。' in abstract
    
    def test_extract_latex_structure(self):
        """LaTeX構造抽出をテスト"""
        content = r"""
        \chapter{微分積分学}
        \section{導関数}
        \subsection{定義}
        \section{積分}
        \subsection{基本定理}
        """
        
        chapters = self.parser._extract_latex_structure(content)
        
        assert len(chapters) == 5
        assert chapters[0]['type'] == 'chapter'
        assert chapters[1]['type'] == 'section'
        assert chapters[2]['type'] == 'subsection'
    
    @pytest.mark.asyncio 
    async def test_parse_markdown(self):
        """Markdown解析をテスト"""
        content = """
# 数学の基礎

## 微分積分

導関数の定義: $f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}$

## 線形代数

ベクトルの内積について。
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        try:
            result = await self.parser._parse_markdown(tmp_path)
            
            assert result['title'] == '数学の基礎'
            assert len(result['chapters']) >= 2
            assert len(result['math_expressions']) >= 1
            
        finally:
            tmp_path.unlink()