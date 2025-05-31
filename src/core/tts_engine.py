import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
import tempfile
from abc import ABC, abstractmethod

# TTS provider imports (these would be installed as needed)
try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

try:
    from google.cloud import texttospeech
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from ..config.settings import settings

logger = logging.getLogger(__name__)

class TTSProvider(ABC):
    """TTS プロバイダーの抽象基底クラス"""
    
    @abstractmethod
    async def synthesize_text(self, text: str, output_path: Path, voice: str = None) -> None:
        pass

class AzureTTSProvider(TTSProvider):
    """Azure Cognitive Services TTS プロバイダー"""
    
    def __init__(self):
        if not AZURE_AVAILABLE:
            raise ImportError("Azure SDK not available")
        if not settings.azure_speech_key or not settings.azure_speech_region:
            raise ValueError("Azure Speech credentials not configured")
        
        self.speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key,
            region=settings.azure_speech_region
        )
    
    async def synthesize_text(self, text: str, output_path: Path, voice: str = "ja-JP-NanamiNeural") -> None:
        """テキストを音声に変換"""
        try:
            self.speech_config.speech_synthesis_voice_name = voice
            
            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # 非同期実行のため、スレッドプールで実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: synthesizer.speak_text_async(text).get()
            )
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"Audio synthesized successfully: {output_path}")
            else:
                raise RuntimeError(f"Speech synthesis failed: {result.reason}")
                
        except Exception as e:
            logger.error(f"Azure TTS error: {e}")
            raise

class GoogleTTSProvider(TTSProvider):
    """Google Cloud Text-to-Speech プロバイダー"""
    
    def __init__(self):
        if not GOOGLE_AVAILABLE:
            raise ImportError("Google Cloud TTS SDK not available")
        
        self.client = texttospeech.TextToSpeechClient()
    
    async def synthesize_text(self, text: str, output_path: Path, voice: str = "ja-JP-Wavenet-A") -> None:
        """テキストを音声に変換"""
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # 音声設定
            voice_params = texttospeech.VoiceSelectionParams(
                language_code="ja-JP" if "ja-JP" in voice else "en-US",
                name=voice
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16
            )
            
            # 非同期実行
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice_params,
                    audio_config=audio_config
                )
            )
            
            # 音声ファイルを保存
            with open(output_path, 'wb') as audio_file:
                audio_file.write(response.audio_content)
            
            logger.info(f"Audio synthesized successfully: {output_path}")
            
        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            raise

class TTSEngine:
    """TTS エンジンメインクラス"""
    
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """利用可能なTTSプロバイダーを初期化"""
        if AZURE_AVAILABLE and settings.azure_speech_key:
            try:
                self.providers['azure'] = AzureTTSProvider()
                logger.info("Azure TTS provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Azure TTS: {e}")
        
        if GOOGLE_AVAILABLE and settings.google_tts_credentials:
            try:
                self.providers['google'] = GoogleTTSProvider()
                logger.info("Google TTS provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google TTS: {e}")
        
        if not self.providers:
            logger.warning("No TTS providers available")
    
    async def generate_audio(self, job_id: str, voice: str = "ja-JP-NanamiNeural", language: str = "ja") -> str:
        """
        音声を生成
        
        Args:
            job_id: ジョブID
            voice: 使用する音声
            language: 言語
            
        Returns:
            生成された音声ファイルのパス
        """
        try:
            # 文書データを取得
            document_data = await self._get_document_data(job_id)
            
            # テキストを準備
            full_text = self._prepare_text_for_tts(document_data)
            
            # 出力ファイルパス
            audio_path = Path(settings.output_dir) / f"{job_id}_audio.wav"
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            
            # プロバイダーを選択して音声生成
            provider = self._select_provider(voice)
            await provider.synthesize_text(full_text, audio_path, voice)
            
            logger.info(f"Audio generated successfully: {audio_path}")
            return str(audio_path)
            
        except Exception as e:
            logger.error(f"Audio generation error: {e}")
            raise
    
    def _select_provider(self, voice: str) -> TTSProvider:
        """音声に基づいてプロバイダーを選択"""
        if voice.startswith('ja-JP') and 'azure' in self.providers:
            return self.providers['azure']
        elif 'google' in self.providers:
            return self.providers['google']
        elif 'azure' in self.providers:
            return self.providers['azure']
        else:
            raise RuntimeError("No suitable TTS provider available")
    
    async def _get_document_data(self, job_id: str) -> Dict:
        """文書データを取得（実際の実装ではデータベースから）"""
        # ダミーデータ
        return {
            'title': '数学解析の基礎',
            'chapters': [
                {
                    'title': '微分積分学の基礎',
                    'content': '微分積分学は、変化率と累積を扱う数学の分野です。導関数は関数の変化率を表し、積分は累積量を計算します。',
                    'math_expressions': ['f prime of x equals the limit as h approaches 0 of f of x plus h minus f of x, all over h']
                }
            ]
        }
    
    def _prepare_text_for_tts(self, document_data: Dict) -> str:
        """TTS用のテキストを準備"""
        text_parts = []
        
        # タイトル
        if document_data.get('title'):
            text_parts.append(f"タイトル: {document_data['title']}")
            text_parts.append("")
        
        # 各章の内容
        for i, chapter in enumerate(document_data.get('chapters', []), 1):
            text_parts.append(f"第{i}章: {chapter['title']}")
            
            if chapter.get('content'):
                text_parts.append(chapter['content'])
            
            # 数式の読み上げテキスト
            for math_expr in chapter.get('math_expressions', []):
                math_text = self._convert_math_to_speech(math_expr)
                text_parts.append(f"数式: {math_text}")
            
            text_parts.append("")  # 章間の区切り
        
        return "\n".join(text_parts)
    
    def _convert_math_to_speech(self, math_expr: str) -> str:
        """数式を読み上げ用テキストに変換"""
        # 簡単な変換ルール（実際にはもっと複雑な処理が必要）
        replacements = {
            r'\frac{': '分数 ',
            r'}{': ' 分の ',
            r'}': '',
            r'\lim_{': 'リミット ',
            r'\to': 'が近づくとき',
            r'\sum': '総和',
            r'\int': '積分',
            r'\sqrt{': 'ルート ',
            r'^{': 'の',
            r'_{': 'サブ',
            r'\alpha': 'アルファ',
            r'\beta': 'ベータ',
            r'\gamma': 'ガンマ'
        }
        
        result = math_expr
        for pattern, replacement in replacements.items():
            result = result.replace(pattern, replacement)
        
        return result