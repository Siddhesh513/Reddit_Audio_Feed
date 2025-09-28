"""
Text Processing Helper Utilities
Common functions for text manipulation and analysis
"""

import re
import unicodedata
from typing import List, Tuple, Optional
from src.utils.loggers import get_logger

logger = get_logger(__name__)


class TextHelpers:
    """Helper functions for text processing"""

    @staticmethod
    def estimate_reading_time(text: str, words_per_minute: int = 150) -> float:
        """
        Estimate reading time in seconds

        Args:
            text: Text to estimate
            words_per_minute: Reading speed (default 150 for TTS)

        Returns:
            Estimated time in seconds
        """
        word_count = len(text.split())
        minutes = word_count / words_per_minute
        return minutes * 60

    @staticmethod
    def split_into_chunks(text: str, max_chars: int = 5000) -> List[str]:
        """
        Split text into chunks for processing

        Args:
            text: Text to split
            max_chars: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        if len(text) <= max_chars:
            return [text]

        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""

        for paragraph in paragraphs:
            # If single paragraph is too long, split by sentences
            if len(paragraph) > max_chars:
                sentences = TextHelpers.split_into_sentences(paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 2 <= max_chars:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + " "
            else:
                # Add paragraph to current chunk if it fits
                if len(current_chunk) + len(paragraph) + 2 <= max_chars:
                    current_chunk += paragraph + "\n\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph + "\n\n"

        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """
        Split text into sentences

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved)
        sentence_enders = re.compile(r'([.!?])\s+')
        sentences = sentence_enders.split(text)

        # Recombine the sentence enders with their sentences
        result = []
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                result.append(sentences[i] + sentences[i + 1])
            else:
                if sentences[i].strip():
                    result.append(sentences[i])

        return [s.strip() for s in result if s.strip()]

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """
        Normalize Unicode characters

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Normalize to NFC form (canonical composition)
        normalized = unicodedata.normalize('NFC', text)

        # Replace special quotes and dashes
        replacements = {
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',
            '—': '-',
            '…': '...',
            '\u00a0': ' ',  # Non-breaking space
        }

        for old, new in replacements.items():
            normalized = normalized.replace(old, new)

        return normalized

    @staticmethod
    def extract_statistics(text: str) -> dict:
        """
        Extract statistics about the text

        Args:
            text: Text to analyze

        Returns:
            Dictionary of statistics
        """
        words = text.split()
        sentences = TextHelpers.split_into_sentences(text)

        return {
            'character_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'average_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'average_sentence_length': len(words) / len(sentences) if sentences else 0,
            'estimated_reading_time': TextHelpers.estimate_reading_time(text),
            'paragraph_count': len([p for p in text.split('\n\n') if p.strip()])
        }

    @staticmethod
    def detect_language_hints(text: str) -> List[str]:
        """
        Detect hints about language or special formatting needs

        Args:
            text: Text to analyze

        Returns:
            List of detected hints
        """
        hints = []

        # Check for code blocks
        if '```' in text or '    ' in text:
            hints.append('contains_code')

        # Check for lists
        if re.search(r'^\s*[-*•]\s+', text, re.MULTILINE):
            hints.append('contains_lists')

        # Check for numbered lists
        if re.search(r'^\s*\d+\.\s+', text, re.MULTILINE):
            hints.append('contains_numbered_lists')

        # Check for quotes
        if '>' in text or '"' in text:
            hints.append('contains_quotes')

        # Check for dialogue
        if re.search(r'[""][^""]+[""]', text):
            hints.append('contains_dialogue')

        # Check for all caps (shouting)
        words = text.split()
        caps_words = [w for w in words if w.isupper() and len(w) > 1]
        if len(caps_words) > len(words) * 0.1:  # More than 10% caps
            hints.append('contains_shouting')

        return hints

    @staticmethod
    def clean_for_filename(text: str, max_length: int = 50) -> str:
        """
        Clean text to be used as a filename

        Args:
            text: Text to clean
            max_length: Maximum length for filename

        Returns:
            Filename-safe text
        """
        # Remove special characters
        text = re.sub(r'[^\w\s-]', '', text)
        # Replace spaces with underscores
        text = re.sub(r'[-\s]+', '_', text)
        # Truncate to max length
        if len(text) > max_length:
            text = text[:max_length]
        # Remove trailing underscore
        text = text.rstrip('_')

        return text.lower()

    @staticmethod
    def add_tts_markers(text: str) -> str:
        """
        Add markers for better TTS pronunciation

        Args:
            text: Text to mark up

        Returns:
            Text with TTS markers
        """
        # Add pauses after certain punctuation
        text = re.sub(r'([.!?])\s+', r'\1 <break time="0.5s"/> ', text)

        # Add pauses before "Edit:" and similar markers
        text = re.sub(r'(Edit:|Update:|Note:)', r'<break time="1s"/> \1', text)

        # Add emphasis to quoted text
        text = re.sub(
            r'"([^"]+)"', r'<emphasis level="moderate">\1</emphasis>', text)

        return text

    @staticmethod
    def remove_tts_unsafe_chars(text: str) -> str:
        """
        Remove characters that might cause TTS issues

        Args:
            text: Text to clean

        Returns:
            TTS-safe text
        """
        # Remove or replace problematic characters
        replacements = {
            '&': 'and',
            '@': 'at',
            '#': 'number',
            '$': 'dollars',
            '%': 'percent',
            '^': '',
            '*': '',
            '~': '',
            '`': '',
            '|': '',
            '\\': '',
            '<': 'less than',
            '>': 'greater than',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text


# Create helper functions at module level for convenience
def estimate_reading_time(text: str, wpm: int = 150) -> float:
    """Convenience function for estimating reading time"""
    return TextHelpers.estimate_reading_time(text, wpm)


def split_into_chunks(text: str, max_chars: int = 5000) -> List[str]:
    """Convenience function for splitting text"""
    return TextHelpers.split_into_chunks(text, max_chars)


def clean_for_filename(text: str, max_length: int = 50) -> str:
    """Convenience function for cleaning filenames"""
    return TextHelpers.clean_for_filename(text, max_length)


def extract_statistics(text: str) -> dict:
    """Convenience function for extracting statistics"""
    return TextHelpers.extract_statistics(text)
