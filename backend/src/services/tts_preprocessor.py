"""
TTS Preprocessor Service
Prepares text for text-to-speech conversion
"""

import re
from typing import Dict, List, Tuple, Optional
from src.utils.loggers import get_logger

logger = get_logger(__name__)


class TTSPreprocessor:
    """Preprocess text for optimal TTS output"""
    
    def __init__(self):
        """Initialize TTS preprocessor with conversion rules"""
        
        # Number conversion patterns
        self.number_patterns = {
            'currency': r'\$(\d+(?:\.\d{2})?)',
            'percentage': r'(\d+(?:\.\d+)?)\%',
            'time_12hr': r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)',
            'time_24hr': r'(\d{1,2}):(\d{2})(?!\s*[ap]m)',
            'decimal': r'(\d+)\.(\d+)',
            'large_number': r'(\d{1,3}(?:,\d{3})+)',
            'ordinal': r'(\d+)(st|nd|rd|th)\b',
        }
        
        # Common abbreviations to expand
        self.abbreviations = {
            # Units
            'km': 'kilometers',
            'mi': 'miles',
            'kg': 'kilograms',
            'lbs': 'pounds',
            'ft': 'feet',
            'hrs': 'hours',
            'mins': 'minutes',
            'secs': 'seconds',
            
            # Common terms
            'vs': 'versus',
            'etc': 'et cetera',
            'ie': 'that is',
            'eg': 'for example',
            'btw': 'by the way',
            'fyi': 'for your information',
            'asap': 'as soon as possible',
            'eta': 'estimated time of arrival',
            'diy': 'do it yourself',
            'faq': 'frequently asked questions',
            
            # Titles
            'mr': 'mister',
            'mrs': 'missus',
            'ms': 'miss',
            'dr': 'doctor',
            'prof': 'professor',
            'st': 'saint',
            
            # Technology
            'api': 'A P I',
            'url': 'U R L',
            'ai': 'A I',
            'ui': 'U I',
            'ux': 'U X',
            'os': 'operating system',
            'pc': 'personal computer',
        }
        
        # Emoji descriptions for TTS
        self.emoji_descriptions = {
            '😀': 'smiling',
            '😂': 'laughing',
            '😍': 'heart eyes',
            '🤔': 'thinking',
            '😭': 'crying',
            '😎': 'cool',
            '👍': 'thumbs up',
            '👎': 'thumbs down',
            '❤️': 'red heart',
            '🔥': 'fire',
            '💯': 'one hundred',
            '🎉': 'party',
        }
        
        logger.info("TTS preprocessor initialized")
    
    def preprocess_for_tts(self, text: str, options: Optional[Dict] = None) -> str:
        """
        Preprocess text for TTS engine
        
        Args:
            text: Text to preprocess
            options: Optional preprocessing options
            
        Returns:
            TTS-ready text
        """
        if not text:
            return ""
        
        options = options or {}
        processed = text
        
        # Step 1: Expand numbers
        if options.get('expand_numbers', True):
            processed = self._expand_numbers(processed)
        
        # Step 2: Expand abbreviations
        if options.get('expand_abbreviations', True):
            processed = self._expand_abbreviations(processed)
        
        # Step 3: Handle special characters
        processed = self._handle_special_characters(processed)
        
        # Step 4: Add speech markers
        if options.get('add_speech_markers', True):
            processed = self._add_speech_markers(processed)
        
        # Step 5: Handle emphasis
        if options.get('handle_emphasis', True):
            processed = self._handle_emphasis(processed)
        
        # Step 6: Clean up spacing
        processed = self._clean_spacing_for_tts(processed)
        
        # Step 7: Add pauses
        if options.get('add_pauses', True):
            processed = self._add_natural_pauses(processed)
        
        logger.debug(f"Preprocessed text for TTS: {len(text)} -> {len(processed)} chars")
        
        return processed
    
    def _expand_numbers(self, text: str) -> str:
        """Expand numbers for better TTS pronunciation"""
        
        # Currency
        text = re.sub(self.number_patterns['currency'], 
                     lambda m: f"{self._number_to_words(m.group(1))} dollars", text)
        
        # Percentages
        text = re.sub(self.number_patterns['percentage'], 
                     lambda m: f"{self._number_to_words(m.group(1))} percent", text)
        
        # Time (12-hour)
        def expand_time_12hr(match):
            hour = int(match.group(1))
            minute = match.group(2)
            period = match.group(3).lower()
            
            if minute == '00':
                return f"{self._number_to_words(str(hour))} {period}"
            else:
                return f"{self._number_to_words(str(hour))} {self._number_to_words(minute)} {period}"
        
        text = re.sub(self.number_patterns['time_12hr'], expand_time_12hr, text)
        
        # Ordinals
        def expand_ordinal(match):
            number = match.group(1)
            suffix = match.group(2)
            return self._ordinal_to_words(number, suffix)
        
        text = re.sub(self.number_patterns['ordinal'], expand_ordinal, text)
        
        # Large numbers with commas
        text = re.sub(self.number_patterns['large_number'], 
                     lambda m: self._number_to_words(m.group(0).replace(',', '')), text)
        
        return text
    
    def _expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations"""
        
        for abbr, expansion in self.abbreviations.items():
            # Case-sensitive for acronyms
            text = re.sub(r'\b' + abbr + r'\b', expansion, text, flags=re.IGNORECASE)
            # Also handle uppercase versions
            text = re.sub(r'\b' + abbr.upper() + r'\b', expansion.upper(), text)
        
        return text
    
    def _handle_special_characters(self, text: str) -> str:
        """Handle special characters for TTS"""
        
        # Replace symbols with words
        replacements = {
            '&': ' and ',
            '@': ' at ',
            '#': ' hashtag ',
            '*': ' star ',
            '+': ' plus ',
            '=': ' equals ',
            '÷': ' divided by ',
            '×': ' times ',
            '°': ' degrees ',
            '™': ' trademark ',
            '©': ' copyright ',
            '®': ' registered ',
            '…': '... ',
            '—': ', ',
            '–': ' to ',
        }
        
        for symbol, word in replacements.items():
            text = text.replace(symbol, word)
        
        # Remove or replace emojis with descriptions
        for emoji, description in self.emoji_descriptions.items():
            text = text.replace(emoji, f' {description} ')
        
        # Remove any remaining emojis
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        
        return text
    
    def _add_speech_markers(self, text: str) -> str:
        """Add markers to improve TTS flow"""
        
        # Add breaks after sentences
        text = re.sub(r'([.!?])\s+([A-Z])', r'\1 <break time="0.5s"/> \2', text)
        
        # Add breaks before new paragraphs
        text = re.sub(r'\n\n', r' <break time="1s"/> ', text)
        
        # Add breaks around parenthetical statements
        text = re.sub(r'\(([^)]+)\)', r' <break time="0.2s"/> \1 <break time="0.2s"/> ', text)
        
        return text
    
    def _handle_emphasis(self, text: str) -> str:
        """Handle text emphasis for TTS"""
        
        # ALL CAPS words (shouting)
        def replace_caps(match):
            word = match.group(0)
            return f'<emphasis level="strong">{word.lower()}</emphasis>'
        
        text = re.sub(r'\b[A-Z]{2,}\b', replace_caps, text)
        
        # Repeated punctuation for emphasis
        text = re.sub(r'([!?]){2,}', r'\1 <emphasis level="strong">', text)
        
        # Quoted text
        text = re.sub(r'"([^"]+)"', r'<prosody rate="95%">\1</prosody>', text)
        
        return text
    
    def _add_natural_pauses(self, text: str) -> str:
        """Add natural pauses for better flow"""
        
        # Add pause after introductory phrases
        intro_phrases = ['however', 'therefore', 'moreover', 'furthermore', 
                        'nevertheless', 'consequently', 'meanwhile', 'finally']
        
        for phrase in intro_phrases:
            text = re.sub(f'\\b{phrase}\\b', f'{phrase} <break time="0.3s"/>', 
                         text, flags=re.IGNORECASE)
        
        # Add pauses around conjunctions in long sentences
        text = re.sub(r'\b(and|but|or)\b', r' <break time="0.2s"/> \1', text)
        
        # Add pauses after colons and semicolons
        text = re.sub(r'[:;]', r'\g<0> <break time="0.4s"/>', text)
        
        return text
    
    def _clean_spacing_for_tts(self, text: str) -> str:
        """Clean up spacing for TTS"""
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove spaces before punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        # Ensure space after punctuation
        text = re.sub(r'([.,!?;:])([A-Za-z])', r'\1 \2', text)
        
        # Clean up break tags
        text = re.sub(r'(<break[^>]+>)\s*(<break[^>]+>)', r'\1', text)
        
        return text.strip()
    
    def _number_to_words(self, num_str: str) -> str:
        """Convert number to words (simplified version)"""
        
        # Simple conversion for demo - in production use inflect or num2words
        try:
            num = float(num_str)
            
            if num.is_integer():
                num = int(num)
                
            # Simple cases
            if num == 0:
                return "zero"
            elif num == 1:
                return "one"
            elif num == 2:
                return "two"
            elif num < 10:
                return str(num)  # Would expand this in production
            elif num < 100:
                return f"{num}"  # Would convert properly in production
            else:
                # For large numbers, just space out digits for now
                return ' '.join(str(num))
                
        except ValueError:
            return num_str
    
    def _ordinal_to_words(self, num: str, suffix: str) -> str:
        """Convert ordinal number to words"""
        
        ordinals = {
            '1st': 'first', '2nd': 'second', '3rd': 'third',
            '4th': 'fourth', '5th': 'fifth', '6th': 'sixth',
            '7th': 'seventh', '8th': 'eighth', '9th': 'ninth',
            '10th': 'tenth', '11th': 'eleventh', '12th': 'twelfth'
        }
        
        key = num + suffix
        if key in ordinals:
            return ordinals[key]
        
        # Default behavior for other ordinals
        if suffix == 'st':
            return f"{num} first"
        elif suffix == 'nd':
            return f"{num} second"
        elif suffix == 'rd':
            return f"{num} third"
        else:
            return f"{num} {suffix}"
    
    def prepare_for_specific_tts(self, text: str, tts_engine: str = 'gtts') -> str:
        """
        Prepare text for specific TTS engine
        
        Args:
            text: Text to prepare
            tts_engine: Target TTS engine (gtts, pyttsx3, azure, etc.)
            
        Returns:
            Engine-specific formatted text
        """
        if tts_engine == 'gtts':
            # Google TTS doesn't support SSML tags
            text = re.sub(r'<[^>]+>', '', text)
        elif tts_engine == 'azure':
            # Azure supports SSML, enhance it
            text = f'<speak version="1.0" xml:lang="en-US">{text}</speak>'
        elif tts_engine == 'pyttsx3':
            # Remove all XML tags for pyttsx3
            text = re.sub(r'<[^>]+>', ', ', text)
        
        return text


# Singleton instance
_tts_preprocessor = None

def get_tts_preprocessor() -> TTSPreprocessor:
    """Get or create TTS preprocessor instance"""
    global _tts_preprocessor
    if _tts_preprocessor is None:
        _tts_preprocessor = TTSPreprocessor()
    return _tts_preprocessor
