from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pathlib import Path
import uuid
import shutil
from typing import Dict, Any

from ...config.settings import settings
from ...core.document_parser import DocumentParser
from ...models.document import Document, DocumentType, ProcessingStatus

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    ファイルをアップロードして解析を開始
    """
    # ファイルサイズチェック
    if file.size > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
        )
    
    # ファイル形式チェック
    allowed_extensions = [".pdf", ".tex", ".md"]
    file_suffix = Path(file.filename).suffix.lower()
    if file_suffix not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed: {allowed_extensions}"
        )
    
    # ユニークなファイル名生成
    job_id = str(uuid.uuid4())
    filename = f"{job_id}{file_suffix}"
    file_path = Path(settings.upload_dir) / filename
    
    # ディレクトリ作成
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # ファイル保存
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # 文書タイプ判定
    document_type_map = {
        ".pdf": DocumentType.PDF,
        ".tex": DocumentType.LATEX,
        ".md": DocumentType.MARKDOWN
    }
    document_type = document_type_map[file_suffix]
    
    # 文書解析開始
    parser = DocumentParser()
    try:
        parsed_data = await parser.parse_document(file_path)
        
        # データベースに保存（実際の実装ではSQLAlchemyセッションを使用）
        document_data = {
            "id": job_id,
            "filename": filename,
            "original_filename": file.filename,
            "file_path": str(file_path),
            "document_type": document_type,
            "title": parsed_data.get("title", ""),
            "author": parsed_data.get("author", ""),
            "abstract": parsed_data.get("abstract", ""),
            "chapters": parsed_data.get("chapters", []),
            "total_pages": parsed_data.get("total_pages", 0),
            "status": ProcessingStatus.UPLOADED
        }
        
        return {
            "job_id": job_id,
            "status": "uploaded",
            "filename": file.filename,
            "document_info": {
                "title": parsed_data.get("title", ""),
                "author": parsed_data.get("author", ""),
                "chapters": len(parsed_data.get("chapters", [])),
                "pages": parsed_data.get("total_pages", 0)
            }
        }
        
    except Exception as e:
        # ファイル削除
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")

@router.get("/upload/status/{job_id}")
async def get_upload_status(job_id: str) -> Dict[str, Any]:
    """
    アップロード状況の確認
    """
    # 実際の実装ではデータベースから取得
    # ここでは簡単な例を示す
    return {
        "job_id": job_id,
        "status": "uploaded",
        "message": "File uploaded and parsed successfully"
    }