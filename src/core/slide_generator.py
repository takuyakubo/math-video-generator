import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
from pylatex import Document, Command, Section, Subsection, Math, NoEscape
from pylatex.base_classes import Environment
from pylatex.package import Package
import subprocess

from ..config.settings import settings

logger = logging.getLogger(__name__)

class SlideGenerator:
    """スライド生成クラス（Beamer使用）"""
    
    def __init__(self):
        self.templates = {
            'academic': self._academic_template,
            'modern': self._modern_template,
            'default': self._default_template
        }
    
    async def generate_slides(self, job_id: str, template: str = 'academic') -> str:
        """
        スライドを生成
        
        Args:
            job_id: ジョブID
            template: テンプレート名
            
        Returns:
            生成されたスライドのPDFパス
        """
        try:
            # 文書データを取得（実際の実装ではデータベースから）
            document_data = await self._get_document_data(job_id)
            
            # テンプレート関数を取得
            template_func = self.templates.get(template, self.templates['default'])
            
            # LaTeX文書を作成
            doc = template_func(document_data)
            
            # ファイル名とパスを設定
            tex_filename = f"{job_id}_slides"
            tex_path = Path(settings.temp_dir) / f"{tex_filename}.tex"
            pdf_path = Path(settings.output_dir) / f"{tex_filename}.pdf"
            
            # ディレクトリ作成
            tex_path.parent.mkdir(parents=True, exist_ok=True)
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            
            # LaTeXファイルを生成
            doc.generate_tex(str(tex_path.with_suffix('')))
            
            # PDFにコンパイル
            await self._compile_latex(tex_path, pdf_path)
            
            logger.info(f"Slides generated successfully: {pdf_path}")
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"Slide generation error: {e}")
            raise
    
    async def _get_document_data(self, job_id: str) -> Dict:
        """文書データを取得（ダミーデータ）"""
        # 実際の実装ではデータベースから取得
        return {
            'title': '数学解析の基礎',
            'author': '著者名',
            'chapters': [
                {
                    'title': '微分積分学の基礎',
                    'type': 'chapter',
                    'content': '微分積分学の導入と基本概念',
                    'math_expressions': [r'f\'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}']
                },
                {
                    'title': '線形代数の基礎',
                    'type': 'chapter', 
                    'content': 'ベクトル、行列、連立方程式',
                    'math_expressions': [r'A\mathbf{x} = \mathbf{b}']
                }
            ]
        }
    
    def _academic_template(self, document_data: Dict) -> Document:
        """アカデミックテンプレート"""
        # Beamerドキュメントの作成
        doc = Document(
            documentclass='beamer',
            document_options=['aspectratio=169'],  # 16:9 アスペクト比
            fontenc=None,
            inputenc=None,
            lmodern=False
        )
        
        # パッケージの追加
        doc.packages.append(Package('amsmath'))
        doc.packages.append(Package('amssymb'))
        doc.packages.append(Package('amsfonts'))
        doc.packages.append(Package('mathtools'))
        doc.packages.append(Package('graphicx'))
        doc.packages.append(Package('xcolor'))
        doc.packages.append(Package('tikz'))
        
        # テーマの設定
        doc.append(Command('usetheme', 'Madrid'))
        doc.append(Command('usecolortheme', 'default'))
        
        # タイトル情報
        doc.append(Command('title', document_data.get('title', '')))
        doc.append(Command('author', document_data.get('author', '')))
        doc.append(Command('date', NoEscape(r'\today')))
        
        # ドキュメント開始
        with doc.create(Environment(name='document')):
            # タイトルスライド
            doc.append(Command('titlepage'))
            
            # 目次スライド
            with doc.create(Environment(name='frame')):
                doc.append(Command('frametitle', '目次'))
                doc.append(Command('tableofcontents'))
            
            # 各章のスライド生成
            for chapter in document_data.get('chapters', []):
                self._add_chapter_slides(doc, chapter)
        
        return doc
    
    def _modern_template(self, document_data: Dict) -> Document:
        """モダンテンプレート"""
        doc = Document(
            documentclass='beamer',
            document_options=['aspectratio=169']
        )
        
        # モダンなパッケージとテーマ
        doc.packages.append(Package('amsmath'))
        doc.packages.append(Package('mathtools'))
        doc.packages.append(Package('tikz'))
        doc.packages.append(Package('tcolorbox'))
        
        doc.append(Command('usetheme', 'metropolis'))
        
        # 同様の構造で実装
        return self._academic_template(document_data)
    
    def _default_template(self, document_data: Dict) -> Document:
        """デフォルトテンプレート"""
        return self._academic_template(document_data)
    
    def _add_chapter_slides(self, doc: Document, chapter: Dict):
        """章のスライドを追加"""
        # セクションスライド
        with doc.create(Environment(name='frame')):
            doc.append(Command('frametitle', chapter['title']))
            
            # 章の内容
            if chapter.get('content'):
                doc.append(NoEscape(chapter['content']))
            
            # 数式の追加
            for math_expr in chapter.get('math_expressions', []):
                with doc.create(Math()) as math:
                    math.append(NoEscape(math_expr))
    
    async def _compile_latex(self, tex_path: Path, pdf_path: Path):
        """LaTeXをPDFにコンパイル"""
        try:
            # pdflatexコマンドを実行
            process = await asyncio.create_subprocess_exec(
                settings.pdflatex_path,
                '-interaction=nonstopmode',
                '-output-directory=' + str(tex_path.parent),
                str(tex_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=settings.latex_timeout
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else 'Unknown LaTeX error'
                raise RuntimeError(f"LaTeX compilation failed: {error_msg}")
            
            # 生成されたPDFを出力ディレクトリに移動
            generated_pdf = tex_path.with_suffix('.pdf')
            if generated_pdf.exists():
                generated_pdf.rename(pdf_path)
            else:
                raise FileNotFoundError("PDF was not generated")
                
        except asyncio.TimeoutError:
            raise RuntimeError(f"LaTeX compilation timed out after {settings.latex_timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"LaTeX compilation error: {str(e)}")