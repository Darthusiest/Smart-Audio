"""
from audio_utils.converter import convert_audio_to_wav
from audio_utils.cleaner import clean_audio
from transcription.whisper_transcriber import transcribe_audio
from summarization.summarizer import summarize_text
from translation.translator import translate_text
from output.writer import save_output
from interface.cli import prompt_user_input
import os

def main():
    print("=== Smart Audio Summarizer & Translator ===\n")

    # Step 1: Get audio path and target language
    audio_path = prompt_user_input("Enter path to audio file (e.g., .mp3 or .wav): ")
    target_lang = prompt_user_input("Enter target language code (e.g., en, es, auto): ")

    if not os.path.exists(audio_path):
        print(f"[ERROR] File not found: {audio_path}")
        return

    # Step 2: Convert to .wav if needed
    print("[INFO] Converting audio to .wav format...")
    wav_path = convert_audio_to_wav(audio_path)

    # Step 3: Clean/normalize audio
    print("[INFO] Cleaning audio for better transcription...")
    cleaned_path = clean_audio(wav_path)

    # Step 4: Transcribe audio
    print("[INFO] Transcribing audio to text...")
    transcript = transcribe_audio(cleaned_path)

    if not transcript.strip():
        print("[ERROR] No speech detected in audio.")
        return

    # Step 5: Summarize text
    print("[INFO] Summarizing transcript...")
    summary = summarize_text(transcript)

    # Step 6: Translate summary
    print(f"[INFO] Translating summary to '{target_lang}'...")
    translated = translate_text(summary, target_lang)

    # Step 7: Save output
    print("[INFO] Saving final output...")
    save_output(summary, translated, target_lang)

    print("\nDone! Your translated summary is ready.")

if __name__ == "__main__":
    main()
"""
# -------------------------------------------------------------------------------------

from pathlib import Path
from typing import Optional

from utils.logger import get_logger
from config import OUTPUT_SETTINGS, SUMMARIZATION_SETTINGS, TEMP_DIR

from audio_utils import AudioConverter, AudioCleaner
from transcription import WhisperTranscriber
from summarization import Summarizer
from translation.translator import Translator
from output import OutputWriter

logger = get_logger("app")

def process_audio_file(audio_path: Path, target_language: str = "en", output_format: str = "txt", summary_style: str = "concise") -> Path:
    """
    creates the pipeline convert -> clean -> transcribe -> summarize -> translate -> save
    """

    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    #inialization
    converter = AudioConverter()
    cleaner = AudioCleaner()
    transcriber = WhisperTranscriber()
    summarizer = Summarizer()
    translator = Translator()
    writer = OutputWriter()

    temp_files = []

    #convert audio 
    logger.info(f"Converting audio: {audio_path}")
    converted_path = converter.convert_to_wav(audio_path)
    temp_files.append(converted_path)

    #clean audio
    logger.info(f"Cleaning audio: {converted_path}")
    cleaned_path = cleaner.clean_audio(converted_path)
    temp_files.append(cleaned_path)

    #transcribe audio
    logger.info(f"Transcribing audio: {cleaned_path}")
    transcript = transcriber.transcribe(cleaned_path)
    original_text = transcript.full_text or ""

    #timestamps for transcript
    if OUTPUT_SETTINGS.get("include_timestamps", True):
        try:
            writer.save_transcript_with_timestamps(transcript)
        except Exception as e:
            logger.warning(f"Failed to save transcript with timestamps: {e}")
        
    #summarize text
    logger.info("Summarizing transcript...")
    chunk_size = SUMMARIZATION_SETTINGS.get("chunk_size", 1000)
    if len(original_text) > chunk_size:
        summary = summarizer.chunk_and_summarize(original_text, chunk_size = chunk_size)
    else:
        summary = summarizer.summarize(original_text, style = summary_style)
    
    #translate summary
    logger.info(f"Translating summary to {target_language}")
    translated_summary = translator.translate(summary, target_language)

    #write output
    logger.info(f"Writing output as {output_format}")
    output_path = writer.save_summary(original_text = original_text, summary = summary, translated_summary = translated_summary, target_language = target_language, audio_path = cleaned_path, output_format = output_format)

    #clean temp files
    try:
        #remove files in TEMP_DIR
        safe_temp = []
        for p in temp_files:
            p = Path(p)
            if TEMP_DIR in p.parents or p.parent == TEMP_DIR:
                safe_temp.append(p)
        
        writer.cleanup_temp_files([str(p) for p in safe_temp])
    except Exception as e:
        logger.warning(f"Failed to clean temp files: {e}")
    
    logger.info(f"Completed. Output at: {output_path}")
    
    return output_path

if __name__ == "__main__":
    from interface.cli import prompt_user_input

    ap = Path(prompt_user_input("Enter path to audio file: "))
    lang = prompt_user_input("Target language (e.g., en, es, fr): ", default = 'en')
    fmt = prompt_user_input("Output format (txt/pdf/json): ", default = "txt")
    style = prompt_user_input("Summary style (concise/detailed/bullet/academic): ", default = "concise")

    result = process_audio_file(ap, target_language= lang, output_format=fmt, summary_style=style)

    print(f"\nSaved to: {result}")
