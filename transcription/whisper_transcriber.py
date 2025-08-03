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
    
    