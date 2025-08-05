import os
from pathlib import Path

# === Base Paths ===
BASE_DIR = Path(__file__).parent.parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# === Audio Settings ===
AUDIO_SETTINGS = {
    "standard_sample_rate": 16000,  # Hz
    "standard_channels": 1,          # Mono
    "max_duration": 3600,           # Max 1 hour
    "supported_formats": [".mp3", ".wav", ".m4a", ".flac", ".ogg"],
    "chunk_duration": 300,          # 5 minutes per chunk
}

# === Whisper Settings ===
WHISPER_SETTINGS = {
    "model_size": "base",           # tiny, base, small, medium, large
    "language": None,               # Auto-detect
    "task": "transcribe",           # transcribe or translate
    "temperature": 0.0,             # Deterministic output
    "best_of": 5,                   # Number of candidates
    "beam_size": 5,                 # Beam search size
}

# === Summarization Settings ===
SUMMARIZATION_SETTINGS = {
    "max_length": 150,              # Max summary length
    "min_length": 30,               # Min summary length
    "do_sample": False,             # Deterministic
    "temperature": 0.7,             # Creativity
    "top_p": 0.9,                   # Nucleus sampling
    "chunk_size": 1000,             # Text chunk size
    "overlap": 200,                 # Overlap between chunks
}

# === Translation Settings ===
TRANSLATION_SETTINGS = {
    "default_source": "auto",       # Auto-detect source language
    "supported_languages": {
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
    },
    "chunk_size": 500,             # Translation chunk size
    "retry_attempts": 3,           # Retry failed translations
}

# === Output Settings ===
OUTPUT_SETTINGS = {
    "default_format": "txt",        # txt, pdf, json
    "include_timestamps": True,     # Include timestamps in output
    "include_confidence": False,    # Include confidence scores
    "clean_output": True,           # Remove artifacts
}

# === Logging Settings ===
LOGGING_SETTINGS = {
    "level": "INFO",
    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    "rotation": "10 MB",
    "retention": "7 days",
    "verbose": True,
}

# === Cache Settings ===
CACHE_SETTINGS = {
    "enable_cache": True,
    "cache_dir": TEMP_DIR / "cache",
    "max_cache_size": "1GB",
    "cache_ttl": 86400,            # 24 hours
}

# === API Settings ===
API_SETTINGS = {
    "timeout": 30,                  # Request timeout
    "max_retries": 3,              # Max retry attempts
    "rate_limit_delay": 1.0,       # Delay between requests
} 