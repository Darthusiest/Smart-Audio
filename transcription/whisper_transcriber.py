import whisper
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from utils.logger import get_logger
from config import WHISPER_SETTINGS
from models.transcript import Transcript, TranscriptSegment

logger = get_logger("whisper_transcriber")

class WhisperTranscriber:
    """Handles audio transcription using OpenAI Whisper"""
    
    def __init__(self, model_size: str = None):
        self.model_size = model_size or WHISPER_SETTINGS["model_size"]
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> Transcript:
        """Transcribe audio file using Whisper"""
        
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            logger.info(f"Transcribing audio: {audio_path}")
            
            # Set language if provided, otherwise auto-detect
            if language:
                logger.info(f"Using specified language: {language}")
            else:
                logger.info("Auto-detecting language")
            
            # Transcribe with Whisper
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                task=WHISPER_SETTINGS["task"],
                temperature=WHISPER_SETTINGS["temperature"],
                best_of=WHISPER_SETTINGS["best_of"],
                beam_size=WHISPER_SETTINGS["beam_size"],
                verbose=False
            )
            
            # Extract segments
            segments = []
            for segment in result["segments"]:
                transcript_segment = TranscriptSegment(
                    start_time=segment["start"],
                    end_time=segment["end"],
                    text=segment["text"].strip(),
                    confidence=segment.get("avg_logprob", None)
                )
                segments.append(transcript_segment)
            
            # Create transcript object
            transcript = Transcript(
                segments=segments,
                full_text=result["text"].strip(),
                language=result.get("language", language),
                duration=result.get("duration", None),
                confidence=result.get("avg_logprob", None),
                created_at=datetime.now()
            )
            
            logger.info(f"Transcription completed: {len(segments)} segments, {len(transcript.full_text)} characters")
            return transcript
            
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            raise
    
    def transcribe_chunk(self, audio_path: Path, start_time: float, end_time: float, 
                        language: Optional[str] = None) -> Transcript:
        """Transcribe a specific time chunk of audio"""
        
        try:
            logger.info(f"Transcribing chunk {start_time:.2f}s - {end_time:.2f}s")
            
            # Load audio and extract chunk
            import librosa
            audio, sr = librosa.load(str(audio_path), sr=None)
            
            # Convert times to sample indices
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            
            # Extract chunk
            chunk_audio = audio[start_sample:end_sample]
            
            # Save temporary chunk file
            import soundfile as sf
            from config import TEMP_DIR
            chunk_path = TEMP_DIR / f"chunk_{start_time:.2f}_{end_time:.2f}.wav"
            sf.write(str(chunk_path), chunk_audio, sr)
            
            # Transcribe chunk
            transcript = self.transcribe(chunk_path, language)
            
            # Clean up temporary file
            chunk_path.unlink(missing_ok=True)
            
            return transcript
            
        except Exception as e:
            logger.error(f"Failed to transcribe chunk: {e}")
            raise
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
            "hi": "Hindi",
            "auto": "Auto-detect"
        }
    
    def detect_language(self, audio_path: Path) -> str:
        """Detect the language of audio"""
        
        try:
            logger.info("Detecting language...")
            
            # Load audio
            audio, sr = librosa.load(str(audio_path), sr=16000)
            
            # Detect language using Whisper
            result = self.model.detect_language(audio)
            detected_lang = result["language"]
            
            logger.info(f"Detected language: {detected_lang}")
            return detected_lang
            
        except Exception as e:
            logger.error(f"Failed to detect language: {e}")
            return "en"  # Default to English 