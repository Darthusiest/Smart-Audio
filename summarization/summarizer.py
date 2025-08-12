from typing import Optional
import os

from openai import OpenAI, APIError, RateLimitError, APIStatusError
from utils.logger import get_logger
from config import SUMMARIZATION_SETTINGS

logger = get_logger("summarizer")

# Flip to True when you want to try OpenAI first
USE_OPENAI_SUMMARY = True

LOCAL_SUMMARY_MODEL = "sshleifer/distilbart-cnn-12-6"


class Summarizer:
    """Summarize with OpenAI when available, otherwise local/extractive."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.settings = SUMMARIZATION_SETTINGS
        self.model = model

        self.use_openai = USE_OPENAI_SUMMARY  # runtime switch
        self.client = None

        if self.use_openai:
            try:
                self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
            except Exception as e:
                logger.warning(f"OpenAI client init failed ({e}); using local/extractive.")
                self.use_openai = False

    def summarize(self, text: str, max_length: Optional[int] = None, style: str = "concise") -> str:
        if not text.strip():
            logger.warning("Empty text provided for summarization")
            return ""

        max_len = max_length or self.settings["max_length"]

        # Try OpenAI first if enabled, otherwise local/extractive
        if self.use_openai and self.client:
            try:
                logger.info(f"Summarizing via OpenAI ({len(text)} chars)")
                prompt = self._create_summary_prompt(text, style)
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You create concise, accurate summaries."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=max_len,
                    temperature=self.settings.get("temperature", 0.7),
                    top_p=self.settings.get("top_p", 1.0),
                )
                summary = (resp.choices[0].message.content or "").strip()
                logger.info(f"Summary created via OpenAI: {len(summary)} chars")
                return summary

            except RateLimitError as e:
                # 429 — turn off OpenAI for this process and fall back
                logger.warning(f"OpenAI rate/credit error (429): {e}. Falling back to local/extractive for this run.")
                self.use_openai = False
            except APIStatusError as e:
                # HTTP errors (e.g., 5xx)
                logger.warning(f"OpenAI HTTP error {e.status_code}: {e}. Falling back to local/extractive.")
                self.use_openai = False
            except APIError as e:
                logger.warning(f"OpenAI API error: {e}. Falling back to local/extractive.")
                self.use_openai = False
            except Exception as e:
                logger.warning(f"OpenAI failed unexpectedly: {e}. Falling back to local/extractive.")
                self.use_openai = False

        # Local abstractive (HF) or extractive fallback
        return self._local_or_extractive(text, max_len, style)

    def _create_summary_prompt(self, text: str, style: str) -> str:
        if style == "concise":
            return f"Provide a concise 2–3 sentence summary of the following:\n\n{text}\n\nSummary:"
        if style == "detailed":
            return f"Provide a detailed summary covering the main points and key details:\n\n{text}\n\nSummary:"
        if style == "bullet":
            return f"Provide bullet points with the key ideas:\n\n{text}\n\nKey Points:"
        if style == "academic":
            return f"Provide an academic-style summary suitable for research notes:\n\n{text}\n\nSummary:"
        return f"Summarize the following text:\n\n{text}\n\nSummary:"

    def _local_or_extractive(self, text: str, max_length: int, style: str) -> str:
        """Try a local HF summarizer; if unavailable, use extractive fallback."""
        try:
            from transformers import pipeline
            logger.info("Summarizing via local HF model")
            pipe = pipeline("summarization", model=LOCAL_SUMMARY_MODEL)
            result = pipe(
                text,
                max_length=min(max_length, 256),
                min_length=min(60, max(10, int((max_length or 150) * 0.3))),
                do_sample=False,
            )[0]["summary_text"]
            return result.strip()
        except Exception as e:
            logger.info(f"Local summarizer unavailable ({e}); using extractive fallback.")
            return self._extractive_summarize(text, max_length)

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

    def chunk_and_summarize(self, text: str, chunk_size: int = 1000, style: str = "concise") -> str:
        """
        Split long text into chunks, summarize each with self.summarize(), then combine.
        Matches app.py call: chunk_and_summarize(original_text, chunk_size=..., style=...).
        """
        if not text.strip():
            logger.warning("Empty text provided for chunked summarization")
            return ""

        # Make chunks roughly `chunk_size` characters, prefer sentence boundaries
        chunks = []
        start = 0
        n = len(text)
        while start < n:
            end = min(start + chunk_size, n)
            # try to cut on a sentence end within the last 25% of the window
            cut = text.rfind('.', start + int(chunk_size * 0.75), end)
            if cut == -1:
                cut = text.rfind('!', start + int(chunk_size * 0.75), end)
            if cut == -1:
                cut = text.rfind('?', start + int(chunk_size * 0.75), end)
            if cut != -1:
                end = cut + 1  # include punctuation

            chunks.append(text[start:end].strip())
            start = end

        logger.info(f"Text split into {len(chunks)} chunks for summarization")

        partials = []
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Summarizing chunk {i}/{len(chunks)}...")
            partials.append(self.summarize(chunk, style=style))

        combined = "\n".join(s for s in partials if s).strip()

        # Optional: one more short pass to tighten the combined summary
        if len(combined) > (self.settings.get("max_length", 150) * 2):
            logger.info("Doing a final pass to tighten combined summary")
            combined = self.summarize(combined, max_length=self.settings.get("max_length", 150), style=style)

        return combined
