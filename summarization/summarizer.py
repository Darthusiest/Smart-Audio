import openai
from typing import List, Optional, Dict, Any
from datetime import datetime
from utils.logger import get_logger
from config import SUMMARIZATION_SETTINGS

logger = get_logger("summarizer")

class Summarizer:
    """Handles text summarization using OpenAI GPT models"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.settings = SUMMARIZATION_SETTINGS
        self._setup_openai()
    
    def _setup_openai(self):
        """Setup OpenAI API"""
        if self.api_key:
            openai.api_key = self.api_key
        else:
            # Try to get from environment
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                openai.api_key = api_key
            else:
                logger.warning("No OpenAI API key provided. Summarization may fail.")
    
    def summarize(self, text: str, max_length: Optional[int] = None, 
                 style: str = "concise") -> str:
        """Summarize text using OpenAI GPT"""
        
        if not text.strip():
            logger.warning("Empty text provided for summarization")
            return ""
        
        try:
            logger.info(f"Summarizing text ({len(text)} characters)")
            
            # Prepare prompt based on style
            prompt = self._create_summary_prompt(text, style)
            
            # Get max length
            max_len = max_length or self.settings["max_length"]
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", 
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise, accurate summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_len,
                temperature=self.settings["temperature"],
                top_p=self.settings["top_p"],
                do_sample=self.settings["do_sample"]
            )
            
            summary = response.choices[0].message.content.strip()
            
            logger.info(f"Summary created: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to summarize text: {e}")
            # Fallback to extractive summarization
            return self._extractive_summarize(text, max_length)
    
    def _create_summary_prompt(self, text: str, style: str) -> str:
        """Create appropriate prompt for summarization style"""
        
        if style == "concise":
            return f"""Please provide a concise summary of the following text in 2-3 sentences:

{text}

Summary:"""
        
        elif style == "detailed":
            return f"""Please provide a detailed summary of the following text, covering the main points and key details:

{text}

Summary:"""
        
        elif style == "bullet":
            return f"""Please provide a bullet-point summary of the following text, highlighting the key points:

{text}

Key Points:"""
        
        elif style == "academic":
            return f"""Please provide an academic-style summary of the following text, suitable for research or academic purposes:

{text}

Summary:"""
        
        else:
            return f"""Please summarize the following text:

{text}

Summary:"""
    
    def _extractive_summarize(self, text: str, max_length: Optional[int] = None) -> str:
        """Fallback extractive summarization using simple heuristics"""
        
        try:
            logger.info("Using extractive summarization fallback")
            
            # Split into sentences
            import re
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                return text
            
            # Simple scoring based on word frequency
            words = text.lower().split()
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Score sentences
            sentence_scores = []
            for sentence in sentences:
                score = sum(word_freq.get(word.lower(), 0) for word in sentence.split())
                sentence_scores.append((score, sentence))
            
            # Sort by score and take top sentences
            sentence_scores.sort(reverse=True)
            
            max_len = max_length or self.settings["max_length"]
            selected_sentences = []
            current_length = 0
            
            for score, sentence in sentence_scores:
                if current_length + len(sentence) <= max_len:
                    selected_sentences.append(sentence)
                    current_length += len(sentence)
                else:
                    break
            
            summary = ". ".join(selected_sentences) + "."
            
            logger.info(f"Extractive summary created: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"Extractive summarization failed: {e}")
            return text[:max_length] if max_length else text
    

    # make sure to handle chunks of text without breaking sentences********
    
    def chunk_and_summarize(self, text: str, chunk_size: Optional[int] = None) -> str:
        """Summarize long text by chunking first"""
        
        chunk_size = chunk_size or self.settings["chunk_size"]
        overlap = self.settings["overlap"]
        
        if len(text) <= chunk_size:
            return self.summarize(text)
        
        logger.info(f"Chunking text into {chunk_size} character chunks")
        
        # Split text into overlapping chunks
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_exclamation = chunk.rfind('!')
                last_question = chunk.rfind('?')
                break_point = max(last_period, last_exclamation, last_question)
                
                if break_point > start + chunk_size * 0.5:  # Only break if it's not too early
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk)
            start = end - overlap
        
        # Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Summarizing chunk {i+1}/{len(chunks)}")
            summary = self.summarize(chunk)
            chunk_summaries.append(summary)
        
        # Combine chunk summaries
        combined_summary = " ".join(chunk_summaries)
        
        # Final summary of combined summaries
        final_summary = self.summarize(combined_summary)
        
        logger.info(f"Chunk summarization completed: {len(final_summary)} characters")
        return final_summary 