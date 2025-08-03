from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class AudioMetadata:
    """Data model for audio file metadata"""
    
    file_path: Path
    file_size: int
    duration: float  # in seconds
    sample_rate: int
    channels: int
    format: str
    bit_rate: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "file_path": str(self.file_path),
            "file_size": self.file_size,
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "format": self.format,
            "bit_rate": self.bit_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

@dataclass
class AudioChunk:
    """Data model for audio chunks"""
    
    chunk_id: int
    start_time: float
    end_time: float
    duration: float
    file_path: Path
    metadata: AudioMetadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "chunk_id": self.chunk_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "file_path": str(self.file_path),
            "metadata": self.metadata.to_dict()
        } 