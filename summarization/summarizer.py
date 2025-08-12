from typing import Optional
from datetime import datetime
import os

from openai import OpenAI
from utils.logger import get_logger
from config import SUMMARIZATION_SETTINGS

logger = get_logger("summarizer")

class Summarizer:
    """Handles text summarization using OpenAI GPT models (OpenAI Python >= 1.0)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.settings = SUMMARIZATION_SETTINGS
        self.model = model
        # Prefer explicit key if provided; otherwise the SDK will read OPENAI_API_KEY from env
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()

    def summarize(self, text: str, max_length: Optional[int] = None, style: str = "concise") -> str:
        """Summarize text using OpenAI chat completions."""
        if not text.strip():
            logger.warning("Empty text provided for summarization")
            return ""

        try:
            logger.info(f"Summarizing text ({len(text)} characters)")
            prompt = self._create_summary_prompt(text, style)
            max_len = max_length or self.settings["max_length"]

            resp = self.client.chat.completions.create(
                model=self.model,  # e.g., "gpt-4o-mini"
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates concise, accurate summaries.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_len,
                temperature=self.settings.get("temperature", 0.7),
                # top_p is optional in the new SDK; do_sample is not a param anymore
                top_p=self.settings.get("top_p", 1.0),
            )

            summary = (resp.choices[0].message.content or "").strip()
            logger.info(f"Summary created: {len(summary)} characters")
            return summary

        except Exception as e:
            logger.error(f"Failed to summarize text: {e}")
            return self._extractive_summarize(text, max_length)

    def _create_summary_prompt(self, text: str, style: str) -> str:
        if style == "concise":
            return f"Please provide a concise summary of the following text in 2-3 sentences:\n\n{text}\n\nSummary:"
        elif style == "detailed":
            return f"Please provide a detailed summary of the following text, covering the main points and key details:\n\n{text}\n\nSummary:"
        elif style == "bullet":
            return f"Please provide a bullet-point summary of the following text, highlighting the key points:\n\n{text}\n\nKey Points:"
        elif style == "academic":
            return f"Please provide an academic-style summary of the following text, suitable for research or academic purposes:\n\n{text}\n\nSummary:"
        else:
            return f"Please summarize the following text:\n\n{text}\n\nSummary:"

    def _extractive_summarize(self, text: str, max_length: Optional[int] = None) -> str:
        try:
            logger.info("Using extractive summarization fallback")
            import re

            sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
            if not sentences:
                return text

            words = text.lower().split()
            word_freq = {}
            for w in words:
                if len(w) > 3:
                    word_freq[w] = word_freq.get(w, 0) + 1

            scored = []
            for s in sentences:
                score = sum(word_freq.get(w.lower(), 0) for w in s.split())
                scored.append((score, s))
            scored.sort(reverse=True)

            max_len = max_length or self.settings["max_length"]
            out, cur = [], 0
            for _, s in scored:
                if cur + len(s) <= max_len:
                    out.append(s)
                    cur += len(s)
                else:
                    break

            return (". ".join(out) + ".") if out else text[:max_len]
        except Exception:
            return text[:max_length] if max_length else text

    # chunk_and_summarize stays the same; it calls self.summarize() which now uses the new API.
