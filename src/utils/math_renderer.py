import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import re
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.mathtext as mathtext

logger = logging.getLogger(__name__)

class MathRenderer:
    """数式レンダリングユーティリティ"""
    
    def __init__(self):
        self.default_dpi = 300
        self.default_font_size = 14
        
        # 数式レンダリングの設定
        plt.rcParams['mathtext.fontset'] = 'stix'
        plt.rcParams['font.family'] = 'STIXGeneral'
    
    def render_latex_to_image(self, latex_expr: str, output_path: Path, 
                             dpi: int = 300, font_size: int = 14) -> bool:
        """ラテックス数式を画像にレンダリング"""
        try:
            # 数式をクリーンアップ
            clean_expr = self._clean_latex_expression(latex_expr)
            
            # matplotlibでレンダリング
            fig, ax = plt.subplots(figsize=(10, 2))
            ax.text(0.5, 0.5, f'${clean_expr}$', 
                   horizontalalignment='center',
                   verticalalignment='center',
                   fontsize=font_size,
                   transform=ax.transAxes)
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            # 余白を最小化
            plt.tight_layout()
            plt.savefig(output_path, dpi=dpi, bbox_inches='tight', 
                       pad_inches=0.1, facecolor='white')
            plt.close()
            
            return True
            
        except Exception as e:
            logger.error(f"LaTeX rendering error: {e}")
            return False
    
    def render_multiple_expressions(self, expressions: List[str], 
                                  output_dir: Path, **kwargs) -> List[str]:
        """複数の数式を一括レンダリング"""
        output_dir.mkdir(parents=True, exist_ok=True)
        rendered_paths = []
        
        for i, expr in enumerate(expressions):
            output_path = output_dir / f"math_{i+1:03d}.png"
            
            if self.render_latex_to_image(expr, output_path, **kwargs):
                rendered_paths.append(str(output_path))
            else:
                logger.warning(f"Failed to render expression {i+1}: {expr}")
        
        return rendered_paths
    
    def create_equation_slide(self, expressions: List[str], 
                            title: str, output_path: Path,
                            slide_width: int = 1920, slide_height: int = 1080) -> bool:
        """数式スライドを作成"""
        try:
            # スライド背景を作成
            img = Image.new('RGB', (slide_width, slide_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # フォントの設定を試行
            try:
                title_font = ImageFont.truetype("arial.ttf", 48)
                text_font = ImageFont.truetype("arial.ttf", 24)
            except OSError:
                # デフォルトフォントを使用
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
            
            # タイトルを描画
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (slide_width - title_width) // 2
            draw.text((title_x, 50), title, fill='black', font=title_font)
            
            # 数式をレンダリングして配置
            y_offset = 150
            spacing = 100
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                for i, expr in enumerate(expressions):
                    math_img_path = temp_path / f"math_{i}.png"
                    
                    if self.render_latex_to_image(expr, math_img_path, dpi=200, font_size=20):
                        # 数式画像をスライドに貼り付け
                        math_img = Image.open(math_img_path)
                        
                        # 中央揃え
                        math_x = (slide_width - math_img.width) // 2
                        math_y = y_offset + i * spacing
                        
                        img.paste(math_img, (math_x, math_y))
            
            # スライドを保存
            img.save(output_path, 'PNG')
            return True
            
        except Exception as e:
            logger.error(f"Equation slide creation error: {e}")
            return False
    
    def _clean_latex_expression(self, expr: str) -> str:
        """ラテックス数式をクリーンアップ"""
        # 不要な空白を除去
        expr = re.sub(r'\s+', ' ', expr.strip())
        
        # ドルマークを除去
        expr = expr.replace('$', '')
        
        # エスケープシーケンスを修正
        expr = expr.replace('\\\\', '\\\\')
        
        return expr
    
    def validate_latex_syntax(self, expr: str) -> Dict[str, any]:
        """ラテックス数式の文法を検証"""
        errors = []
        warnings = []
        
        # ブレースのバランスチェック
        brace_count = expr.count('{') - expr.count('}')
        if brace_count != 0:
            errors.append(f"ブレースのバランスエラー: {brace_count}")
        
        # パレンのバランスチェック
        paren_count = expr.count('(') - expr.count(')')
        if paren_count != 0:
            errors.append(f"括弧のバランスエラー: {paren_count}")
        
        # 角括弧のバランスチェック
        bracket_count = expr.count('[') - expr.count(']')
        if bracket_count != 0:
            errors.append(f"角括弧のバランスエラー: {bracket_count}")
        
        # 未完成のコマンドをチェック
        incomplete_commands = re.findall(r'\\[a-zA-Z]*\{[^}]*$', expr)
        if incomplete_commands:
            errors.append(f"未完成のコマンド: {incomplete_commands}")
        
        # 未定義コマンドの検出
        commands = re.findall(r'\\([a-zA-Z]+)', expr)
        known_commands = {
            'frac', 'sqrt', 'sum', 'int', 'prod', 'lim',
            'sin', 'cos', 'tan', 'log', 'ln', 'exp',
            'alpha', 'beta', 'gamma', 'delta', 'epsilon',
            'theta', 'lambda', 'mu', 'pi', 'sigma', 'phi',
            'left', 'right', 'begin', 'end', 'text',
            'mathbf', 'mathit', 'mathrm', 'mathcal',
            'partial', 'nabla', 'infty', 'pm', 'cdot',
            'times', 'div', 'leq', 'geq', 'neq', 'approx'
        }
        
        unknown_commands = set(commands) - known_commands
        if unknown_commands:
            warnings.append(f"未知のコマンド: {list(unknown_commands)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def extract_math_from_text(self, text: str) -> List[str]:
        """テキストから数式を抽出"""
        patterns = [
            r'\$\$([^$]+)\$\$',  # Display math
            r'\$([^$]+)\$',      # Inline math
            r'\\\[([^\]]+)\\\]',  # Display math alternative
            r'\\\(([^\)]+)\\\)',  # Inline math alternative
            r'\\begin\{equation\}(.*?)\\end\{equation\}',
            r'\\begin\{align\}(.*?)\\end\{align\}',
            r'\\begin\{eqnarray\}(.*?)\\end\{eqnarray\}'
        ]
        
        math_expressions = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            math_expressions.extend(matches)
        
        # 重複を除去して返す
        return list(set(math_expressions))
    
    def create_math_animation_frames(self, expr: str, steps: int, 
                                   output_dir: Path) -> List[str]:
        """数式アニメーションのフレームを作成"""
        output_dir.mkdir(parents=True, exist_ok=True)
        frame_paths = []
        
        # 数式を部分ごとに分割
        parts = self._split_expression_into_parts(expr)
        
        for i in range(steps):
            # ステップに応じて表示する部分を決定
            visible_parts = parts[:int((i + 1) * len(parts) / steps)]
            partial_expr = ' '.join(visible_parts)
            
            frame_path = output_dir / f"frame_{i+1:03d}.png"
            
            if self.render_latex_to_image(partial_expr, frame_path):
                frame_paths.append(str(frame_path))
            else:
                logger.warning(f"Failed to render frame {i+1}")
        
        return frame_paths
    
    def _split_expression_into_parts(self, expr: str) -> List[str]:
        """数式をアニメーション用に分割"""
        # 簡単な分割ロジック（実際の実装ではもっと複雑な処理が必要）
        
        # 等号、演算子で分割
        separators = ['=', '+', '-', '\\cdot', '\\times', '\\to']
        
        parts = [expr]
        for sep in separators:
            new_parts = []
            for part in parts:
                if sep in part:
                    split_parts = part.split(sep)
                    for i, split_part in enumerate(split_parts):
                        new_parts.append(split_part.strip())
                        if i < len(split_parts) - 1:
                            new_parts.append(sep)
                else:
                    new_parts.append(part)
            parts = new_parts
        
        # 空の部分を除去
        return [part for part in parts if part.strip()]
    
    def test_render_capability(self) -> Dict[str, bool]:
        """レンダリング機能のテスト"""
        test_expressions = {
            'simple': 'x + y = z',
            'fraction': '\\frac{a}{b}',
            'integral': '\\int_0^1 x dx',
            'greek': '\\alpha + \\beta = \\gamma',
            'complex': '\\sum_{i=1}^n \\frac{1}{i^2} = \\frac{\\pi^2}{6}'
        }
        
        results = {}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            for name, expr in test_expressions.items():
                test_file = temp_path / f"test_{name}.png"
                results[name] = self.render_latex_to_image(expr, test_file)
        
        return results