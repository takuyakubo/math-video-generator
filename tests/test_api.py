import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import tempfile
from pathlib import Path

from src.main import app

class TestAPI:
    """API エンドポイントのテストクラス"""
    
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_health_check(self):
        """ヘルスチェックエンドポイントをテスト"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    @patch('src.api.routes.upload.DocumentParser')
    def test_upload_file_success(self, mock_parser):
        """ファイルアップロード成功をテスト"""
        # モックの設定
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        mock_parser_instance.parse_document = AsyncMock(return_value={
            'title': 'テスト文書',
            'author': 'テスト著者',
            'chapters': [],
            'total_pages': 5,
            'text_content': 'テスト内容',
            'math_expressions': []
        })
        
        # テストファイルを作成
        test_content = b"Test PDF content"
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open_func(test_content)), \
             patch('shutil.copyfileobj'):
            
            response = self.client.post(
                "/api/upload",
                files={"file": ("test.pdf", test_content, "application/pdf")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "uploaded"
        assert data["filename"] == "test.pdf"
    
    def test_upload_file_unsupported_format(self):
        """サポートされていないファイル形式のテスト"""
        test_content = b"Test content"
        
        response = self.client.post(
            "/api/upload",
            files={"file": ("test.txt", test_content, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]
    
    def test_upload_file_too_large(self):
        """ファイルサイズ制限のテスト"""
        # 設定されたサイズ制限を超える大きなファイル
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB
        
        # ファイルサイズをモック
        with patch('fastapi.UploadFile.size', 101 * 1024 * 1024):
            response = self.client.post(
                "/api/upload",
                files={"file": ("large.pdf", large_content, "application/pdf")}
            )
        
        assert response.status_code == 413
        assert "File too large" in response.json()["detail"]
    
    def test_start_processing(self):
        """処理開始エンドポイントをテスト"""
        job_id = "test-job-123"
        config = {
            "template": "academic",
            "voice": "ja-JP-Wavenet-A",
            "language": "ja",
            "chapters": True,
            "video_quality": "1080p",
            "animation_speed": 1.0
        }
        
        response = self.client.post(f"/api/process/{job_id}", json=config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "processing_started"
        assert "config" in data
    
    def test_get_processing_status(self):
        """処理状況確認エンドポイントをテスト"""
        job_id = "test-job-123"
        
        response = self.client.get(f"/api/process/{job_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "progress" in data
    
    def test_get_download_info(self):
        """ダウンロード情報取得をテスト"""
        job_id = "test-job-123"
        
        with patch('pathlib.Path.exists', return_value=False):
            response = self.client.get(f"/api/download/{job_id}/info")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "available_files" in data
        assert "download_urls" in data
    
    def test_download_video_not_found(self):
        """存在しない動画のダウンロードをテスト"""
        job_id = "nonexistent-job"
        
        with patch('pathlib.Path.exists', return_value=False):
            response = self.client.get(f"/api/download/{job_id}/video")
        
        assert response.status_code == 404
        assert "Video not found" in response.json()["detail"]

def mock_open_func(content):
    """ファイルオープンのモック関数"""
    from unittest.mock import mock_open
    return mock_open(read_data=content)

# 統合テスト用のフィクスチャ
@pytest.fixture
def sample_pdf_file():
    """テスト用のサンプルPDFファイルを作成"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
        return Path(tmp.name)

@pytest.fixture
def sample_tex_file():
    """テスト用のサンプルLaTeXファイルを作成"""
    content = r"""
    \documentclass{article}
    \title{Test Document}
    \author{Test Author}
    \begin{document}
    \maketitle
    \section{Introduction}
    This is a test document.
    \end{document}
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False, encoding='utf-8') as tmp:
        tmp.write(content)
        return Path(tmp.name)