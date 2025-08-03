from pathlib import Path
from typing import Optional, Dict, Any
from tqdm import tqdm
import time

# Import
from audio_utils.converter import AudioConverter
from audio_utils.cleaner import AudioCleaner
from transcription.whisper_transcriber import WhisperTranscriber
from summarization.summarizer import Summarizer
from translation.translator import Translator
from output.writer import OutputWriter
from utils.logger import get_logger
from config import AUDIO_SETTINGS, OUTPUT_SETTINGS

logger = get_logger("main_app")

class AudioProcessor:
    """Main audio processing pipeline"""
    
    def __init__(self):
        self.converter = AudioConverter() # Converts audio formats
        self.cleaner = AudioCleaner() # Cleans audio files
        self.transcriber = WhisperTranscriber() # Transcribes audio to text
        self.summarizer = Summarizer() # Summarizes text
        self.translator = Translator() # Translates text
        self.writer = OutputWriter() # Writes output files
        
        self.temp_files = []
    
    def process_audio_file(self, audio_path: Path, target_language: str = "en",
                          output_format: str = "txt", summary_style: str = "concise") -> Path:
        """Main processing pipeline"""
        
        logger.info("=== Starting Audio Processing Pipeline ===")
        
        try:
            # Step 1: Validate and convert audio
            logger.info("Step 1: Validating and converting audio...")
            if not self.converter.validate_audio_file(audio_path):
                raise ValueError(f"Invalid audio file: {audio_path}")
            
            converted_path = self.converter.convert_to_wav(audio_path)
            self.temp_files.append(converted_path)
            
            # Step 2: Clean audio
            logger.info("Step 2: Cleaning audio...")
            cleaned_path = self.cleaner.clean_audio(converted_path)
            self.temp_files.append(cleaned_path)
            
            # Step 3: Transcribe audio
            logger.info("Step 3: Transcribing audio...")
            transcript = self.transcriber.transcribe(cleaned_path)
            
            if not transcript.full_text.strip():
                raise ValueError("No speech detected in audio")
            
            # Step 4: Summarize transcript
            logger.info("Step 4: Summarizing transcript...")
            summary = self.summarizer.summarize(
                transcript.full_text, 
                style=summary_style
            )
            
            # Step 5: Translate summary
            logger.info(f"Step 5: Translating summary to {target_language}...")
            translated_summary = self.translator.translate(summary, target_language)
            
            # Step 6: Save results
            logger.info("Step 6: Saving results...")
            output_path = self.writer.save_summary(
                original_text=transcript.full_text,
                summary=summary,
                translated_summary=translated_summary,
                target_language=target_language,
                audio_path=audio_path,
                output_format=output_format
            )
            
            # Step 7: Cleanup
            logger.info("Step 7: Cleaning up temporary files...")
            self._cleanup_temp_files()
            
            logger.info("=== Processing Pipeline Completed ===")
            return output_path
            
        except Exception as e:
            logger.error(f"Processing pipeline failed: {e}")
            self._cleanup_temp_files()
            raise
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        self.writer.cleanup_temp_files(self.temp_files)
        self.temp_files.clear()

def process_audio_file(audio_path: Path, target_language: str = "en",
                      output_format: str = "txt", summary_style: str = "concise") -> Path:
    """Convenience function to process audio file"""
    
    processor = AudioProcessor()
    return processor.process_audio_file(
        audio_path=audio_path,
        target_language=target_language,
        output_format=output_format,
        summary_style=summary_style
    )

def main():
    """Main entry point for the application"""
    
    print("=== Smart Audio Summarizer & Translator ===\n")
    
    # Get user input
    audio_path = input("Enter path to audio file: ").strip()
    target_language = input("Enter target language (e.g., en, es, fr): ").strip() or "en"
    output_format = input("Enter output format (txt/pdf/json): ").strip() or "txt"
    summary_style = input("Enter summary style (concise/detailed/bullet/academic): ").strip() or "concise"
    
    # Validate audio file
    audio_file = Path(audio_path)
    if not audio_file.exists():
        print(f"Error: Audio file not found: {audio_path}")
        return
    
    try:
        # Process the audio
        output_path = process_audio_file(
            audio_path=audio_file,
            target_language=target_language,
            output_format=output_format,
            summary_style=summary_style
        )
        
        print(f"\n✅ Processing completed!")
        print(f"📄 Output saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Error processing audio: {e}")
        logger.exception("Processing failed")

if __name__ == "__main__":
    main()
