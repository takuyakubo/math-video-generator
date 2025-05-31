import logging
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FileManager:
    """ファイル管理ユーティリティ"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.upload_dir = self.base_dir / "uploads"
        self.output_dir = self.base_dir / "outputs"
        self.temp_dir = self.base_dir / "temp"
        
        # ディレクトリを作成
        for directory in [self.upload_dir, self.output_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_uploaded_file(self, file_content: bytes, filename: str, job_id: str) -> Path:
        """アップロードされたファイルを保存"""
        # ファイルの拡張子を取得
        suffix = Path(filename).suffix
        
        # 保存パスを生成
        safe_filename = f"{job_id}{suffix}"
        file_path = self.upload_dir / safe_filename
        
        # ファイルを保存
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"File saved: {file_path}")
        return file_path
    
    def get_file_hash(self, file_path: Path) -> str:
        """ファイルのSHA256ハッシュを計算"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def create_temp_directory(self, job_id: str) -> Path:
        """ジョブ用の一時ディレクトリを作成"""
        temp_job_dir = self.temp_dir / job_id
        temp_job_dir.mkdir(parents=True, exist_ok=True)
        return temp_job_dir
    
    def cleanup_temp_files(self, job_id: str) -> bool:
        """ジョブの一時ファイルを清掃"""
        try:
            temp_job_dir = self.temp_dir / job_id
            if temp_job_dir.exists():
                shutil.rmtree(temp_job_dir)
                logger.info(f"Cleaned up temp files for job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup temp files for {job_id}: {e}")
            return False
    
    def cleanup_old_files(self, max_age_days: int = 7) -> Dict[str, int]:
        """古いファイルを清掃"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        cleaned_counts = {
            'uploads': 0,
            'outputs': 0,
            'temp': 0
        }
        
        for dir_name, directory in [
            ('uploads', self.upload_dir),
            ('outputs', self.output_dir),
            ('temp', self.temp_dir)
        ]:
            try:
                for file_path in directory.rglob('*'):
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_date:
                            file_path.unlink()
                            cleaned_counts[dir_name] += 1
                            logger.debug(f"Removed old file: {file_path}")
                    elif file_path.is_dir() and not any(file_path.iterdir()):
                        # 空のディレクトリを削除
                        file_path.rmdir()
                        logger.debug(f"Removed empty directory: {file_path}")
            except Exception as e:
                logger.error(f"Error cleaning {dir_name}: {e}")
        
        logger.info(f"Cleanup completed: {cleaned_counts}")
        return cleaned_counts
    
    def get_disk_usage(self) -> Dict[str, Dict[str, int]]:
        """ディスク使用量を取得"""
        def get_directory_size(path: Path) -> Tuple[int, int]:
            """bytes, file_count"""
            total_size = 0
            file_count = 0
            
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return total_size, file_count
        
        usage = {}
        
        for dir_name, directory in [
            ('uploads', self.upload_dir),
            ('outputs', self.output_dir),
            ('temp', self.temp_dir)
        ]:
            size, count = get_directory_size(directory)
            usage[dir_name] = {
                'size_bytes': size,
                'size_mb': round(size / (1024 * 1024), 2),
                'file_count': count
            }
        
        return usage
    
    def validate_file_type(self, file_path: Path, allowed_extensions: List[str]) -> bool:
        """ファイルタイプを検証"""
        return file_path.suffix.lower() in [ext.lower() for ext in allowed_extensions]
    
    def validate_file_size(self, file_path: Path, max_size_bytes: int) -> bool:
        """ファイルサイズを検証"""
        return file_path.stat().st_size <= max_size_bytes
    
    def backup_file(self, source_path: Path, backup_dir: Optional[Path] = None) -> Path:
        """ファイルをバックアップ"""
        if backup_dir is None:
            backup_dir = self.base_dir / "backups"
        
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # タイムスタンプ付きファイル名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
        backup_path = backup_dir / backup_filename
        
        shutil.copy2(source_path, backup_path)
        logger.info(f"File backed up: {source_path} -> {backup_path}")
        
        return backup_path
    
    def restore_file(self, backup_path: Path, restore_path: Path) -> bool:
        """ファイルを復元"""
        try:
            shutil.copy2(backup_path, restore_path)
            logger.info(f"File restored: {backup_path} -> {restore_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore file: {e}")
            return False
    
    def create_file_manifest(self, job_id: str) -> Dict:
        """ジョブのファイルマニフェストを作成"""
        manifest = {
            'job_id': job_id,
            'created_at': datetime.now().isoformat(),
            'files': {}
        }
        
        # 各ディレクトリでジョブ関連ファイルを検索
        for dir_name, directory in [
            ('uploads', self.upload_dir),
            ('outputs', self.output_dir),
            ('temp', self.temp_dir)
        ]:
            job_files = list(directory.glob(f"{job_id}*"))
            
            manifest['files'][dir_name] = []
            for file_path in job_files:
                if file_path.is_file():
                    manifest['files'][dir_name].append({
                        'filename': file_path.name,
                        'size_bytes': file_path.stat().st_size,
                        'modified_at': datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                        'hash': self.get_file_hash(file_path)
                    })
        
        # マニフェストを保存
        manifest_path = self.base_dir / f"{job_id}_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        return manifest
    
    def verify_file_integrity(self, file_path: Path, expected_hash: str) -> bool:
        """ファイルの整合性を検証"""
        if not file_path.exists():
            return False
        
        actual_hash = self.get_file_hash(file_path)
        return actual_hash == expected_hash
    
    def get_file_info(self, file_path: Path) -> Dict:
        """ファイル情報を取得"""
        if not file_path.exists():
            return {}
        
        stat = file_path.stat()
        
        return {
            'name': file_path.name,
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'extension': file_path.suffix,
            'is_readable': file_path.exists() and file_path.is_file(),
            'hash': self.get_file_hash(file_path) if file_path.is_file() else None
        }
    
    def archive_job_files(self, job_id: str, archive_path: Optional[Path] = None) -> Path:
        """ジョブのファイルをアーカイブ"""
        import zipfile
        
        if archive_path is None:
            archive_path = self.base_dir / f"{job_id}_archive.zip"
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 各ディレクトリからジョブ関連ファイルを集める
            for dir_name, directory in [
                ('uploads', self.upload_dir),
                ('outputs', self.output_dir)
            ]:
                job_files = list(directory.glob(f"{job_id}*"))
                
                for file_path in job_files:
                    if file_path.is_file():
                        # アーカイブ内のパス
                        arcname = f"{dir_name}/{file_path.name}"
                        zipf.write(file_path, arcname)
            
            # マニフェストも含める
            manifest = self.create_file_manifest(job_id)
            manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
            zipf.writestr(f"{job_id}_manifest.json", manifest_json)
        
        logger.info(f"Job files archived: {archive_path}")
        return archive_path