import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from src.core.slide_generator import SlideGenerator
from src.core.tts_engine import TTSEngine
from src.core.video_generator import VideoGenerator

class TestSlideGenerator:
    """SlideGenerator のテストクラス"""
    
    def setup_method(self):
        self.generator = SlideGenerator()
    
    def test_templates_available(self):
        """利用可能なテンプレートをテスト"""
        expected_templates = ['academic', 'modern', 'default']
        for template in expected_templates:
            assert template in self.generator.templates
    
    @pytest.mark.asyncio
    @patch('src.core.slide_generator.SlideGenerator._get_document_data')
    @patch('src.core.slide_generator.SlideGenerator._compile_latex')
    async def test_generate_slides(self, mock_compile, mock_get_data):
        """スライド生成をテスト"""
        # モックデータの設定
        mock_get_data.return_value = {
            'title': 'テスト文書',
            'author': 'テスト著者',
            'chapters': [
                {
                    'title': '第1章',
                    'type': 'chapter',
                    'content': 'テスト内容',
                    'math_expressions': ['x^2 + y^2 = r^2']
                }
            ]
        }
        mock_compile.return_value = None
        
        with patch('pathlib.Path.mkdir'), \
             patch('src.core.slide_generator.Document') as mock_doc:
            
            mock_doc_instance = Mock()
            mock_doc.return_value = mock_doc_instance
            
            result = await self.generator.generate_slides('test_job_id')
            
            assert result is not None
            mock_get_data.assert_called_once_with('test_job_id')
            mock_compile.assert_called_once()

class TestTTSEngine:
    """TTSEngine のテストクラス"""
    
    def setup_method(self):
        self.engine = TTSEngine()
    
    def test_convert_math_to_speech(self):
        """数式の音声テキスト変換をテスト"""
        math_expr = r"\frac{f(x+h) - f(x)}{h}"
        result = self.engine._convert_math_to_speech(math_expr)
        
        assert '分数' in result or 'frac' not in result
    
    def test_prepare_text_for_tts(self):
        """TTS用テキスト準備をテスト"""
        document_data = {
            'title': 'テスト文書',
            'chapters': [
                {
                    'title': '第1章',
                    'content': 'テスト内容です。',
                    'math_expressions': ['x^2']
                }
            ]
        }
        
        result = self.engine._prepare_text_for_tts(document_data)
        
        assert 'テスト文書' in result
        assert '第1章' in result
        assert 'テスト内容です。' in result
    
    def test_select_provider_no_providers(self):
        """プロバイダーが利用できない場合のテスト"""
        engine = TTSEngine()
        engine.providers = {}
        
        with pytest.raises(RuntimeError, match="No suitable TTS provider"):
            engine._select_provider('ja-JP-test')

class TestVideoGenerator:
    """VideoGenerator のテストクラス"""
    
    def setup_method(self):
        self.generator = VideoGenerator()
    
    def test_calculate_slide_durations(self):
        """スライド表示時間計算をテスト"""
        num_slides = 4
        total_duration = 120.0  # 2分
        
        durations = self.generator._calculate_slide_durations(num_slides, total_duration)
        
        assert len(durations) == num_slides
        assert all(d == 30.0 for d in durations)  # 各スライド30秒
    
    def test_get_video_config(self):
        """動画設定取得をテスト"""
        config_720p = self.generator._get_video_config('720p')
        config_1080p = self.generator._get_video_config('1080p')
        config_unknown = self.generator._get_video_config('unknown')
        
        assert config_720p['width'] == 1280
        assert config_720p['height'] == 720
        
        assert config_1080p['width'] == 1920
        assert config_1080p['height'] == 1080
        
        # 不明な品質はデフォルト（1080p）になる
        assert config_unknown == config_1080p
    
    def test_convert_chapters_to_ffmpeg_format(self):
        """FFmpeg章形式変換をテスト"""
        chapters = [
            {'title': '第1章', 'start_time': 0.0, 'end_time': 60.0},
            {'title': '第2章', 'start_time': 60.0, 'end_time': 120.0}
        ]
        
        # 一時ファイルを作成してテスト
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json.dump(chapters, tmp, ensure_ascii=False)
            tmp_path = Path(tmp.name)
        
        try:
            result = self.generator._convert_chapters_to_ffmpeg_format(tmp_path)
            
            assert ';FFMETADATA1' in result
            assert '[CHAPTER]' in result
            assert '第1章' in result
            assert '第2章' in result
            assert 'START=0' in result
            assert 'END=60000' in result  # ミリ秒
            
        finally:
            tmp_path.unlink()