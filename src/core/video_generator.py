import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import json
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
from moviepy.video.fx import resize
from PIL import Image, ImageDraw, ImageFont
import tempfile

from ..config.settings import settings

logger = logging.getLogger(__name__)

class VideoGenerator:
    """動画生成クラス"""
    
    def __init__(self):
        self.ffmpeg_path = settings.ffmpeg_path
    
    async def generate_video(
        self, 
        job_id: str, 
        slides_path: str, 
        audio_path: str,
        quality: str = "1080p",
        chapters: bool = True
    ) -> str:
        """
        最終的な動画を生成
        
        Args:
            job_id: ジョブID
            slides_path: スライドPDFのパス
            audio_path: 音声ファイルのパス
            quality: 動画品質
            chapters: チャプター情報を含めるか
            
        Returns:
            生成された動画ファイルのパス
        """
        try:
            video_path = Path(settings.output_dir) / f"{job_id}.mp4"
            video_path.parent.mkdir(parents=True, exist_ok=True)
            
            # PDFを画像に変換
            slide_images = await self._pdf_to_images(slides_path)
            
            # 音声の長さを取得
            audio_duration = await self._get_audio_duration(audio_path)
            
            # 各スライドの表示時間を計算
            slide_durations = self._calculate_slide_durations(
                len(slide_images), audio_duration
            )
            
            # 動画品質設定
            video_config = self._get_video_config(quality)
            
            # MoviePyを使用して動画を作成
            video_clip = await self._create_video_with_moviepy(
                slide_images, slide_durations, audio_path, video_config
            )
            
            # チャプター情報を追加
            if chapters:
                chapter_data = await self._get_chapter_data(job_id)
                await self._add_chapters_to_video(video_clip, video_path, chapter_data)
            else:
                video_clip.write_videofile(
                    str(video_path),
                    fps=video_config['fps'],
                    codec='libx264',
                    audio_codec='aac'
                )
            
            # リソースのクリーンアップ
            video_clip.close()
            
            logger.info(f"Video generated successfully: {video_path}")
            return str(video_path)
            
        except Exception as e:
            logger.error(f"Video generation error: {e}")
            raise
    
    async def _pdf_to_images(self, pdf_path: str) -> List[str]:
        """PDFを画像に変換"""
        try:
            from pdf2image import convert_from_path
            
            # PDFを画像に変換
            images = convert_from_path(pdf_path, dpi=300)
            
            image_paths = []
            temp_dir = Path(settings.temp_dir) / "slides"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            for i, image in enumerate(images):
                image_path = temp_dir / f"slide_{i+1:03d}.png"
                image.save(image_path, 'PNG')
                image_paths.append(str(image_path))
            
            logger.info(f"Converted {len(image_paths)} slides to images")
            return image_paths
            
        except ImportError:
            raise RuntimeError("pdf2image library not available")
        except Exception as e:
            raise RuntimeError(f"PDF to image conversion failed: {e}")
    
    async def _get_audio_duration(self, audio_path: str) -> float:
        """音声ファイルの長さを取得"""
        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            audio_clip.close()
            return duration
        except Exception as e:
            raise RuntimeError(f"Failed to get audio duration: {e}")
    
    def _calculate_slide_durations(self, num_slides: int, total_duration: float) -> List[float]:
        """各スライドの表示時間を計算"""
        if num_slides == 0:
            return []
        
        # 均等に分割（実際にはチャプター情報に基づいて調整）
        base_duration = total_duration / num_slides
        return [base_duration] * num_slides
    
    def _get_video_config(self, quality: str) -> Dict:
        """動画品質設定を取得"""
        configs = {
            "720p": {"width": 1280, "height": 720, "fps": 30, "bitrate": "2M"},
            "1080p": {"width": 1920, "height": 1080, "fps": 30, "bitrate": "5M"},
            "4k": {"width": 3840, "height": 2160, "fps": 30, "bitrate": "20M"}
        }
        return configs.get(quality, configs["1080p"])
    
    async def _create_video_with_moviepy(
        self, 
        slide_images: List[str], 
        slide_durations: List[float],
        audio_path: str,
        video_config: Dict
    ) -> CompositeVideoClip:
        """MoviePyを使用して動画を作成"""
        try:
            clips = []
            current_time = 0
            
            for i, (image_path, duration) in enumerate(zip(slide_images, slide_durations)):
                # 画像クリップを作成
                img_clip = ImageClip(image_path)
                img_clip = img_clip.set_duration(duration)
                img_clip = img_clip.set_start(current_time)
                
                # リサイズ
                img_clip = img_clip.resize((video_config['width'], video_config['height']))
                
                clips.append(img_clip)
                current_time += duration
            
            # 動画を合成
            video = CompositeVideoClip(clips)
            
            # 音声を追加
            audio = AudioFileClip(audio_path)
            video = video.set_audio(audio)
            
            return video
            
        except Exception as e:
            raise RuntimeError(f"Video creation with MoviePy failed: {e}")
    
    async def _get_chapter_data(self, job_id: str) -> List[Dict]:
        """チャプターデータを取得"""
        # 実際の実装ではデータベースから取得
        return [
            {
                "title": "微分積分学の基礎",
                "start_time": 0.0,
                "end_time": 120.0
            },
            {
                "title": "線形代数の基礎", 
                "start_time": 120.0,
                "end_time": 240.0
            }
        ]
    
    async def _add_chapters_to_video(self, video_clip: CompositeVideoClip, output_path: Path, chapters: List[Dict]):
        """動画にチャプター情報を追加"""
        try:
            # 一時的にビデオファイルを保存
            temp_video = output_path.with_suffix('.temp.mp4')
            video_clip.write_videofile(
                str(temp_video),
                fps=30,
                codec='libx264',
                audio_codec='aac'
            )
            
            # チャプター情報をJSON形式で準備
            chapter_file = output_path.with_suffix('.chapters')
            with open(chapter_file, 'w', encoding='utf-8') as f:
                json.dump(chapters, f, ensure_ascii=False, indent=2)
            
            # FFmpegでチャプター情報を埋め込み
            await self._embed_chapters_with_ffmpeg(temp_video, output_path, chapter_file)
            
            # 一時ファイルを削除
            temp_video.unlink()
            chapter_file.unlink()
            
        except Exception as e:
            logger.warning(f"Failed to add chapters: {e}")
            # チャプター追加に失敗した場合は通常の動画として保存
            video_clip.write_videofile(
                str(output_path),
                fps=30,
                codec='libx264',
                audio_codec='aac'
            )
    
    async def _embed_chapters_with_ffmpeg(self, input_path: Path, output_path: Path, chapter_file: Path):
        """FFmpegを使用してチャプター情報を埋め込み"""
        try:
            # チャプターファイルをFFmpeg形式に変換
            ffmpeg_chapters = self._convert_chapters_to_ffmpeg_format(chapter_file)
            
            ffmpeg_chapter_file = chapter_file.with_suffix('.txt')
            with open(ffmpeg_chapter_file, 'w', encoding='utf-8') as f:
                f.write(ffmpeg_chapters)
            
            # FFmpegコマンドを実行
            cmd = [
                self.ffmpeg_path,
                '-i', str(input_path),
                '-i', str(ffmpeg_chapter_file),
                '-map', '0',
                '-map_metadata', '1',
                '-c', 'copy',
                str(output_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg chapter embedding failed: {stderr.decode()}")
            
            ffmpeg_chapter_file.unlink()
            
        except Exception as e:
            raise RuntimeError(f"Chapter embedding error: {e}")
    
    def _convert_chapters_to_ffmpeg_format(self, chapter_file: Path) -> str:
        """チャプター情報をFFmpeg形式に変換"""
        with open(chapter_file, 'r', encoding='utf-8') as f:
            chapters = json.load(f)
        
        ffmpeg_format = ";FFMETADATA1\n"
        
        for chapter in chapters:
            start_time = int(chapter['start_time'] * 1000)  # ミリ秒に変換
            end_time = int(chapter['end_time'] * 1000)
            
            ffmpeg_format += f"[CHAPTER]\n"
            ffmpeg_format += f"TIMEBASE=1/1000\n"
            ffmpeg_format += f"START={start_time}\n"
            ffmpeg_format += f"END={end_time}\n"
            ffmpeg_format += f"title={chapter['title']}\n"
        
        return ffmpeg_format