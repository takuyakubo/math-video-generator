import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import PyPDF2
import pdfplumber
from PIL import Image
import io

logger = logging.getLogger(__name__)

class PDFProcessor:
    """ピーディーエフ処理ユーティリティ"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def extract_metadata(self, pdf_path: Path) -> Dict:
        """メタデータを抽出"""
        metadata = {
            'title': '',
            'author': '',
            'subject': '',
            'creator': '',
            'producer': '',
            'creation_date': None,
            'modification_date': None,
            'pages': 0
        }
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                metadata['pages'] = len(reader.pages)
                
                if reader.metadata:
                    metadata.update({
                        'title': reader.metadata.get('/Title', ''),
                        'author': reader.metadata.get('/Author', ''),
                        'subject': reader.metadata.get('/Subject', ''),
                        'creator': reader.metadata.get('/Creator', ''),
                        'producer': reader.metadata.get('/Producer', ''),
                        'creation_date': reader.metadata.get('/CreationDate'),
                        'modification_date': reader.metadata.get('/ModDate')
                    })
                    
        except Exception as e:
            logger.error(f"PDF metadata extraction error: {e}")
            
        return metadata
    
    def extract_text(self, pdf_path: Path) -> str:
        """テキストを抽出"""
        text = ""
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        
        except Exception as e:
            logger.error(f"PDF text extraction error: {e}")
            
        return text
    
    def extract_images(self, pdf_path: Path, output_dir: Path) -> List[str]:
        """画像を抽出"""
        output_dir.mkdir(parents=True, exist_ok=True)
        image_paths = []
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(reader.pages):
                    if '/XObject' in page['/Resources']:
                        xObject = page['/Resources']['/XObject'].get_object()
                        
                        for obj in xObject:
                            if xObject[obj]['/Subtype'] == '/Image':
                                try:
                                    # 画像データを抽出
                                    img_data = xObject[obj]._data
                                    img = Image.open(io.BytesIO(img_data))
                                    
                                    # 画像を保存
                                    img_path = output_dir / f"page_{page_num+1}_img_{obj}.png"
                                    img.save(img_path, 'PNG')
                                    image_paths.append(str(img_path))
                                    
                                except Exception as e:
                                    logger.warning(f"Image extraction failed for {obj}: {e}")
                                    
        except Exception as e:
            logger.error(f"PDF image extraction error: {e}")
            
        return image_paths
    
    def extract_tables(self, pdf_path: Path) -> List[List[List[str]]]:
        """表を抽出"""
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
                        
        except Exception as e:
            logger.error(f"PDF table extraction error: {e}")
            
        return tables
    
    def detect_columns(self, pdf_path: Path) -> List[Dict]:
        """カラムレイアウトを検出"""
        column_info = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # テキストのX座標を分析
                    chars = page.chars
                    if not chars:
                        continue
                    
                    # X座標でグループ化
                    x_positions = sorted(set(char['x0'] for char in chars))
                    
                    # カラムの閾値を決定
                    tolerance = 20  # ピクセル
                    columns = []
                    current_column = [x_positions[0]]
                    
                    for x in x_positions[1:]:
                        if x - current_column[-1] < tolerance:
                            current_column.append(x)
                        else:
                            columns.append({
                                'start': min(current_column),
                                'end': max(current_column)
                            })
                            current_column = [x]
                    
                    if current_column:
                        columns.append({
                            'start': min(current_column),
                            'end': max(current_column)
                        })
                    
                    column_info.append({
                        'page': page_num + 1,
                        'columns': columns,
                        'column_count': len(columns)
                    })
                    
        except Exception as e:
            logger.error(f"PDF column detection error: {e}")
            
        return column_info
    
    def extract_fonts(self, pdf_path: Path) -> List[Dict]:
        """フォント情報を抽出"""
        font_info = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    chars = page.chars
                    if not chars:
                        continue
                    
                    # フォント情報を集計
                    fonts = {}
                    for char in chars:
                        font_name = char.get('fontname', 'Unknown')
                        font_size = char.get('size', 0)
                        font_key = f"{font_name}_{font_size}"
                        
                        if font_key not in fonts:
                            fonts[font_key] = {
                                'name': font_name,
                                'size': font_size,
                                'count': 0,
                                'chars': []
                            }
                        
                        fonts[font_key]['count'] += 1
                        fonts[font_key]['chars'].append(char['text'])
                    
                    font_info.append({
                        'page': page_num + 1,
                        'fonts': list(fonts.values())
                    })
                    
        except Exception as e:
            logger.error(f"PDF font extraction error: {e}")
            
        return font_info
    
    def split_by_pages(self, pdf_path: Path, output_dir: Path) -> List[str]:
        """ページごとにPDFを分割"""
        output_dir.mkdir(parents=True, exist_ok=True)
        split_files = []
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(reader.pages):
                    writer = PyPDF2.PdfWriter()
                    writer.add_page(page)
                    
                    output_path = output_dir / f"page_{page_num+1:03d}.pdf"
                    
                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)
                    
                    split_files.append(str(output_path))
                    
        except Exception as e:
            logger.error(f"PDF splitting error: {e}")
            
        return split_files
    
    def merge_pdfs(self, pdf_paths: List[Path], output_path: Path) -> bool:
        """複数のPDFを結合"""
        try:
            writer = PyPDF2.PdfWriter()
            
            for pdf_path in pdf_paths:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        writer.add_page(page)
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return True
            
        except Exception as e:
            logger.error(f"PDF merging error: {e}")
            return False
    
    def extract_bookmarks(self, pdf_path: Path) -> List[Dict]:
        """ブックマーク（目次）を抽出"""
        bookmarks = []
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                def extract_outline(outline, level=0):
                    for item in outline:
                        if isinstance(item, list):
                            extract_outline(item, level + 1)
                        else:
                            page_num = None
                            if hasattr(item, 'page') and item.page:
                                page_num = reader.pages.index(item.page.get_object()) + 1
                            
                            bookmarks.append({
                                'title': item.title,
                                'level': level,
                                'page': page_num
                            })
                
                if reader.outline:
                    extract_outline(reader.outline)
                    
        except Exception as e:
            logger.error(f"PDF bookmark extraction error: {e}")
            
        return bookmarks
    
    def get_page_dimensions(self, pdf_path: Path) -> List[Dict]:
        """ページの寸法情報を取得"""
        dimensions = []
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(reader.pages):
                    mediabox = page.mediabox
                    dimensions.append({
                        'page': page_num + 1,
                        'width': float(mediabox.width),
                        'height': float(mediabox.height),
                        'orientation': 'landscape' if mediabox.width > mediabox.height else 'portrait'
                    })
                    
        except Exception as e:
            logger.error(f"PDF dimension extraction error: {e}")
            
        return dimensions