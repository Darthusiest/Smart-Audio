import os

# === Paths ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Make sure these folders exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

#  Audio Settings 
STANDARD_SAMPLE_RATE = 16000  # Hz

#  Whisper Model 
WHISPER_MODEL_SIZE = "base"  # options: tiny, base, small, medium, large

#  Translation Settings 
DEFAULT_TRANSLATION_LANG = "en"

#  Output File Format 
OUTPUT_FORMAT = "pdf"  # options: txt, pdf

#  Logging 
VERBOSE = True
