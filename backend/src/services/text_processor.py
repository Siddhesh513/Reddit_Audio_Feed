"""
Text Processing Service
Handles cleaning and formatting of Reddit post text for TTS
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from src.utils.loggers import get_logger

logger = get_logger(__name__)


class TextProcessor:
    """Main text processing service for Reddit posts"""

    def __init__(self):
        """Initialize text processor with regex patterns"""

        # Reddit-specific patterns
        self.patterns = {
            # User and subreddit mentions
            'user_mention': r'/u/[\w-]+|u/[\w-]+',
            'subreddit_mention': r'/r/[\w-]+|r/[\w-]+',

            # Reddit formatting
            'strikethrough': r'~~([^~]+)~~',
            'spoiler': r'>!([^!]+)!<',
            'quote': r'^>+\s*(.+)$',

            # Links and URLs
            'reddit_link': r'\[([^\]]+)\]\(([^\)]+)\)',
            'url': r'https?://[^\s\)]+',
            'www_url': r'www\.[^\s\)]+',

            # Edit markers
            'edit_marker': r'(EDIT|Edit|UPDATE|Update)[\s\d]*:',
            'tldr': r'(TL;?DR|tl;?dr)[\s:]*',

            # Special Reddit phrases
            'gold_thanks': r'(Thanks for the gold|Thank you for the gold|Thanks kind stranger)[^.!]*[.!]?',
            'rip_inbox': r'(RIP (my )?inbox|inbox (is )?dead)[^.!]*[.!]?',
            'this_blew_up': r'(This blew up|This got big|Wow this blew up)[^.!]*[.!]?',
            'throwaway': r'(Throwaway account|Throwaway for obvious reasons)[^.!]*[.!]?',

            # Metadata in brackets
            'age_gender': r'\[(\d+)\s*([MFmf])\]',
            'metadata_brackets': r'\[([^\]]+)\]',

            # Multiple spaces and newlines
            'multiple_spaces': r'\s+',
            'multiple_newlines': r'\n{3,}',

            # Emojis (basic removal)
            'emoji': r'[😀-🙏🌀-🗿🚀-🛿🤠-🤯🤰-🤿🥀-🥿🦀-🪿🫀-🫿☀-⛿✀-➿🀀-🿿]',

            # Common abbreviations
            'abbreviations': {
                'AITA': 'Am I the asshole',
                'YTA': 'You\'re the asshole',
                'NTA': 'Not the asshole',
                'ESH': 'Everyone sucks here',
                'NAH': 'No assholes here',
                'TIFU': 'Today I fucked up',
                'TIL': 'Today I learned',
                'ELI5': 'Explain like I\'m five',
                'AMA': 'Ask me anything',
                'IAMA': 'I am a',
                'DAE': 'Does anyone else',
                'TBH': 'To be honest',
                'IMO': 'In my opinion',
                'IMHO': 'In my humble opinion',
                'AFAIK': 'As far as I know',
                'IIRC': 'If I recall correctly',
                'FTFY': 'Fixed that for you',
                'ETA': 'Edited to add',
                'IANAL': 'I am not a lawyer',
                'SO': 'Significant other',
                'OP': 'Original poster',
                'OC': 'Original content',
            }
        }

        logger.info("Text processor initialized with Reddit-specific patterns")

    def process_post(self, post: Dict[str, Any], options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a complete Reddit post for TTS

        Args:
            post: Reddit post dictionary
            options: Processing options

        Returns:
            Processed post with clean text
        """
        options = options or {}

        # Extract title and body
        title = post.get('title', '')
        body = post.get('selftext', '')

        # Process title
        clean_title = self.clean_text(title, is_title=True)

        # Process body if it exists
        clean_body = ""
        if body and body.strip() and body not in ['[removed]', '[deleted]']:
            clean_body = self.clean_text(body, is_title=False)

        # Combine for TTS
        if clean_body:
            tts_text = f"{clean_title}.\n\n{clean_body}"
        else:
            tts_text = clean_title

        # Add processing metadata
        result = post.copy()
        result['processed_title'] = clean_title
        result['processed_body'] = clean_body
        result['tts_text'] = tts_text
        result['text_length'] = len(tts_text)
        result['processing_notes'] = self._generate_processing_notes(
            title, body, clean_title, clean_body)

        logger.debug(
            f"Processed post {post.get('id', 'unknown')}: {len(tts_text)} chars")

        return result

    def clean_text(self, text: str, is_title: bool = False) -> str:
        """
        Clean Reddit text for TTS

        Args:
            text: Raw text to clean
            is_title: Whether this is a title (different rules apply)

        Returns:
            Cleaned text ready for TTS
        """
        if not text:
            return ""

        original = text

        # Step 1: Remove Reddit-specific annoyances
        text = self._remove_reddit_cliches(text)

        # Step 2: Handle Reddit markdown
        text = self._process_markdown(text)

        # Step 3: Process user and subreddit mentions
        text = self._process_mentions(text)

        # Step 4: Handle links and URLs
        text = self._process_links(text)

        # Step 5: Expand abbreviations
        text = self._expand_abbreviations(text)

        # Step 6: Process age/gender markers
        text = self._process_metadata(text)

        # Step 7: Clean up spacing and punctuation
        text = self._clean_spacing(text)

        # Step 8: Title-specific processing
        if is_title:
            text = self._process_title(text)

        # Step 9: Final cleanup
        text = self._final_cleanup(text)

        if text != original:
            logger.debug(f"Text cleaned: {len(original)} -> {len(text)} chars")

        return text

    def _remove_reddit_cliches(self, text: str) -> str:
        """Remove common Reddit cliches and phrases"""
        # Remove "Thanks for the gold" type phrases
        text = re.sub(self.patterns['gold_thanks'],
                      '', text, flags=re.IGNORECASE)
        text = re.sub(self.patterns['rip_inbox'],
                      '', text, flags=re.IGNORECASE)
        text = re.sub(self.patterns['this_blew_up'],
                      '', text, flags=re.IGNORECASE)
        text = re.sub(self.patterns['throwaway'],
                      '', text, flags=re.IGNORECASE)

        return text

    def _process_markdown(self, text: str) -> str:
        """Process Reddit markdown formatting"""
        # Remove strikethrough
        text = re.sub(self.patterns['strikethrough'], r'\1', text)

        # Reveal spoilers
        text = re.sub(self.patterns['spoiler'], r'\1', text)

        # Process quotes (remove > marker)
        lines = text.split('\n')
        processed_lines = []
        for line in lines:
            if line.strip().startswith('>'):
                # Remove quote marker but keep the text
                processed_lines.append(re.sub(r'^>+\s*', '', line))
            else:
                processed_lines.append(line)
        text = '\n'.join(processed_lines)

        # Bold and italic markers
        text = re.sub(r'\*{2,}([^\*]+)\*{2,}', r'\1', text)  # Bold
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)  # Italic
        text = re.sub(r'_{2,}([^_]+)_{2,}', r'\1', text)  # Bold
        text = re.sub(r'_([^_]+)_', r'\1', text)  # Italic

        return text

    def _process_mentions(self, text: str) -> str:
        """Process user and subreddit mentions"""
        # Convert /u/username to "user username"
        text = re.sub(r'/u/([\w-]+)', r'user \1', text, flags=re.IGNORECASE)
        text = re.sub(r'u/([\w-]+)', r'user \1', text, flags=re.IGNORECASE)

        # Convert /r/subreddit to "subreddit r/subreddit"
        text = re.sub(r'/r/([\w-]+)', r'subreddit \1',
                      text, flags=re.IGNORECASE)
        text = re.sub(r'(?<!\/)r\/([\w-]+)',
                      r'subreddit \1', text, flags=re.IGNORECASE)

        return text

    def _process_links(self, text: str) -> str:
        """Process links and URLs"""
        # Reddit-style links [text](url) - keep just the text
        text = re.sub(self.patterns['reddit_link'], r'\1', text)

        # Remove standalone URLs
        text = re.sub(self.patterns['url'], 'link removed', text)
        text = re.sub(self.patterns['www_url'], 'link removed', text)

        return text

    def _expand_abbreviations(self, text: str) -> str:
        """Expand common Reddit abbreviations"""
        for abbr, expansion in self.patterns['abbreviations'].items():
            # Case-sensitive replacement for acronyms
            text = re.sub(r'\b' + abbr + r'\b', expansion, text)
            # Also handle lowercase versions
            text = re.sub(r'\b' + abbr.lower() + r'\b',
                          expansion.lower(), text)

        return text

    def _process_metadata(self, text: str) -> str:
        """Process age/gender and other metadata markers"""
        # Convert [28M] to "28 year old male"
        def age_gender_replacement(match):
            age = match.group(1)
            gender = match.group(2).upper()
            gender_full = "male" if gender == 'M' else "female"
            return f"{age} year old {gender_full}"

        text = re.sub(self.patterns['age_gender'],
                      age_gender_replacement, text)

        # Remove other brackets that might contain metadata
        text = re.sub(r'\[removed\]', '', text)
        text = re.sub(r'\[deleted\]', '', text)
        text = re.sub(r'\[removed by moderator\]', '', text)

        return text

    def _process_title(self, text: str) -> str:
        """Special processing for titles"""
        # Remove trailing punctuation if it's just for emphasis
        text = re.sub(r'[!?]{2,}$', '?', text)

        # Ensure title ends with appropriate punctuation
        if text and text[-1] not in '.!?':
            text += '.'

        return text

    def _clean_spacing(self, text: str) -> str:
        """Clean up spacing and newlines"""
        # Remove emojis
        text = re.sub(self.patterns['emoji'], '', text)

        # Clean up EDIT markers
        text = re.sub(self.patterns['edit_marker'], '\n\nEdit: ', text)

        # Clean up TL;DR
        text = re.sub(
            self.patterns['tldr'], '\n\nToo long, didn\'t read: ', text, flags=re.IGNORECASE)

        # Replace multiple spaces with single space
        text = re.sub(self.patterns['multiple_spaces'], ' ', text)

        # Replace multiple newlines with double newline
        text = re.sub(self.patterns['multiple_newlines'], '\n\n', text)

        return text

    def _final_cleanup(self, text: str) -> str:
        """Final cleanup pass"""
        # Strip leading/trailing whitespace
        text = text.strip()

        # Remove any remaining special characters that might cause issues
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]',
                      '', text)  # Zero-width spaces

        # Ensure sentences are properly spaced
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)

        return text

    def _generate_processing_notes(self, original_title: str, original_body: str,
                                   clean_title: str, clean_body: str) -> str:
        """Generate notes about what was processed"""
        notes = []

        if len(original_title) != len(clean_title):
            notes.append(
                f"Title cleaned ({len(original_title)} -> {len(clean_title)} chars)")

        if original_body and len(original_body) != len(clean_body):
            notes.append(
                f"Body cleaned ({len(original_body)} -> {len(clean_body)} chars)")

        if '[removed]' in original_body or '[deleted]' in original_body:
            notes.append("Removed/deleted content filtered")

        return "; ".join(notes) if notes else "No significant changes"


# Singleton instance
_text_processor = None


def get_text_processor() -> TextProcessor:
    """Get or create text processor instance"""
    global _text_processor
    if _text_processor is None:
        _text_processor = TextProcessor()
    return _text_processor
