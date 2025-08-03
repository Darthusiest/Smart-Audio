from deep_translator import GoogleTranslator
from typing import Optional, Dict, List
from utils.logger import get_logger
from config import TRANSLATION_SETTINGS

logger = get_logger("translator")

class Translator:
    """Handles text translation using Google Translate"""
    
    def __init__(self):
        self.settings = TRANSLATION_SETTINGS
        self.supported_languages = self.settings["supported_languages"]
        self.chunk_size = self.settings["chunk_size"]
        self.retry_attempts = self.settings["retry_attempts"]
    
    def translate(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
        """Translate text to target language"""
        
        if not text.strip():
            logger.warning("Empty text provided for translation")
            return ""
        
        # Validate target language
        if target_lang not in self.supported_languages:
            logger.error(f"Unsupported target language: {target_lang}")
            raise ValueError(f"Unsupported language: {target_lang}")
        
        try:
            logger.info(f"Translating text to {target_lang} ({len(text)} characters)")
            
            # Handle long text by chunking
            if len(text) > self.chunk_size:
                return self._translate_chunked(text, target_lang, source_lang)
            
            # Single translation
            return self._translate_chunk(text, target_lang, source_lang)
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise
    
    def _translate_chunk(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
        """Translate a single chunk of text"""
        
        for attempt in range(self.retry_attempts):
            try:
                translator = GoogleTranslator(
                    source=source_lang or 'auto',
                    target=target_lang
                )
                
                translated = translator.translate(text)
                logger.debug(f"Translation successful (attempt {attempt + 1})")
                return translated
                
            except Exception as e:
                logger.warning(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt == self.retry_attempts - 1:
                    raise
                continue
    
    def _translate_chunked(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
        """Translate long text by breaking into chunks"""
        
        logger.info(f"Chunking text for translation ({len(text)} characters)")
        
        # Split text into chunks
        chunks = self._split_text_into_chunks(text)
        
        # Translate each chunk
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Translating chunk {i+1}/{len(chunks)}")
            translated_chunk = self._translate_chunk(chunk, target_lang, source_lang)
            translated_chunks.append(translated_chunk)
        
        # Combine translated chunks
        translated_text = " ".join(translated_chunks)
        
        logger.info(f"Chunked translation completed: {len(translated_text)} characters")
        return translated_text
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks at sentence boundaries"""
        
        import re
        
        # Split by sentence endings
        sentences = re.split(r'([.!?]+)', text)
        
        chunks = []
        current_chunk = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
            
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk + sentence + punctuation) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + punctuation
            else:
                current_chunk += sentence + punctuation
        
        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def detect_language(self, text: str) -> str:
        """Detect the language of text"""
        
        try:
            logger.info("Detecting text language...")
            
            translator = GoogleTranslator(source='auto', target='en')
            detected_lang = translator.detect(text)
            
            logger.info(f"Detected language: {detected_lang}")
            return detected_lang
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "en"  # Default to English
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return self.supported_languages.copy()
    
    def validate_language(self, lang_code: str) -> bool:
        """Validate if language code is supported"""
        return lang_code in self.supported_languages
    
    def translate_with_confidence(self, text: str, target_lang: str, 
                                source_lang: Optional[str] = None) -> Dict[str, any]:
        """Translate text and return with confidence information"""
        
        try:
            # Detect source language if not provided
            if not source_lang:
                source_lang = self.detect_language(text)
            
            # Translate
            translated_text = self.translate(text, target_lang, source_lang)
            
            return {
                "original_text": text,
                "translated_text": translated_text,
                "source_language": source_lang,
                "target_language": target_lang,
                "confidence": "high"  # Google Translate doesn't provide confidence scores
            }
            
        except Exception as e:
            logger.error(f"Translation with confidence failed: {e}")
            raise
    
    def batch_translate(self, texts: List[str], target_lang: str, 
                       source_lang: Optional[str] = None) -> List[str]:
        """Translate multiple texts efficiently"""
        
        logger.info(f"Batch translating {len(texts)} texts to {target_lang}")
        
        translated_texts = []
        for i, text in enumerate(texts):
            try:
                translated = self.translate(text, target_lang, source_lang)
                translated_texts.append(translated)
                logger.debug(f"Translated text {i+1}/{len(texts)}")
            except Exception as e:
                logger.error(f"Failed to translate text {i+1}: {e}")
                translated_texts.append(text)  # Keep original on failure
        
        return translated_texts 