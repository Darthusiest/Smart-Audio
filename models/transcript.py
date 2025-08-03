from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class TranscriptSegment:
    """Data model for a transcript segment with timing"""
    
    start_time: float
    end_time: float
    text: str
    confidence: Optional[float] = None
    speaker: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "text": self.text,
            "confidence": self.confidence,
            "speaker": self.speaker
        }

@dataclass
class Transcript:
    """Data model for complete transcript"""
    
    segments: List[TranscriptSegment]
    full_text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    confidence: Optional[float] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "segments": [seg.to_dict() for seg in self.segments],
            "full_text": self.full_text,
            "language": self.language,
            "duration": self.duration,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def get_text_with_timestamps(self) -> str:
        """Get formatted text with timestamps"""
        lines = []
        for segment in self.segments:
            start_min = int(segment.start_time // 60)
            start_sec = int(segment.start_time % 60)
            end_min = int(segment.end_time // 60)
            end_sec = int(segment.end_time % 60)
            
            timestamp = f"[{start_min:02d}:{start_sec:02d}-{end_min:02d}:{end_sec:02d}]"
            lines.append(f"{timestamp} {segment.text}")
        
        return "\n".join(lines) 