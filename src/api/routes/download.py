from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Dict, Any

from ...config.settings import settings

router = APIRouter()

@router.get("/download/{job_id}/video")
async def download_video(job_id: str) -> FileResponse:
    """
    生成された動画をダウンロード
    """
    video_path = Path(settings.output_dir) / f"{job_id}.mp4"
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found or not ready")
    
    return FileResponse(
        path=video_path,
        filename=f"math_video_{job_id}.mp4",
        media_type="video/mp4"
    )

@router.get("/download/{job_id}/slides")
async def download_slides(job_id: str) -> FileResponse:
    """
    生成されたスライド（PDF）をダウンロード
    """
    slides_path = Path(settings.output_dir) / f"{job_id}_slides.pdf"
    
    if not slides_path.exists():
        raise HTTPException(status_code=404, detail="Slides not found")
    
    return FileResponse(
        path=slides_path,
        filename=f"slides_{job_id}.pdf",
        media_type="application/pdf"
    )

@router.get("/download/{job_id}/info")
async def get_download_info(job_id: str) -> Dict[str, Any]:
    """
    ダウンロード可能なファイル情報を取得
    """
    output_dir = Path(settings.output_dir)
    
    files = {
        "video": (output_dir / f"{job_id}.mp4").exists(),
        "slides": (output_dir / f"{job_id}_slides.pdf").exists(),
        "audio": (output_dir / f"{job_id}_audio.wav").exists()
    }
    
    return {
        "job_id": job_id,
        "available_files": files,
        "download_urls": {
            "video": f"/api/download/{job_id}/video" if files["video"] else None,
            "slides": f"/api/download/{job_id}/slides" if files["slides"] else None
        }
    }