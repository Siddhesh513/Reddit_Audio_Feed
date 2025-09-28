"""
Content Filter Service
Handles filtering of inappropriate or sensitive content
"""

import re
from typing import Dict, Any, List, Set, Optional
from src.utils.loggers import get_logger

logger = get_logger(__name__)


class ContentFilter:
    """Filter inappropriate or sensitive content from Reddit posts"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize content filter with configuration
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Default filter settings
        self.filter_profanity = self.config.get('filter_profanity', True)
        self.filter_nsfw = self.config.get('filter_nsfw', True)
        self.censor_style = self.config.get('censor_style', 'asterisk')  # asterisk, remove, or beep
        
        # Common profanity list (simplified for example)
        # In production, you'd load this from a comprehensive file
        self.profanity_patterns = self._load_profanity_patterns()
        
        # Sensitive topics that might need warnings
        self.sensitive_topics = {
            'violence': ['murder', 'kill', 'assault', 'attack', 'violent'],
            'self_harm': ['suicide', 'self harm', 'self-harm', 'cutting'],
            'substance': ['drug', 'alcohol', 'drunk', 'high', 'overdose'],
            'medical': ['cancer', 'disease', 'terminal', 'diagnosis'],
            'trauma': ['abuse', 'trauma', 'ptsd', 'rape', 'assault']
        }
        
        logger.info(f"Content filter initialized with settings: NSFW={self.filter_nsfw}, Profanity={self.filter_profanity}")
    
    def _load_profanity_patterns(self) -> List[re.Pattern]:
        """
        Load profanity patterns for filtering
        
        Returns:
            List of compiled regex patterns
        """
        # Simplified list - in production, load from comprehensive database
        # Using patterns to catch variations
        profanity_words = [
            r'\bf+u+c+k+\w*\b',
            r'\bs+h+i+t+\w*\b',
            r'\ba+s+s+h+o+l+e+\w*\b',
            r'\bb+i+t+c+h+\w*\b',
            r'\bd+a+m+n+\w*\b',
            r'\bh+e+l+l+\b',
            r'\bc+r+a+p+\w*\b',
        ]
        
        # Compile patterns with case-insensitive flag
        patterns = []
        for word in profanity_words:
            try:
                patterns.append(re.compile(word, re.IGNORECASE))
            except re.error as e:
                logger.error(f"Invalid regex pattern: {word} - {e}")
        
        return patterns
    
    def filter_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter a Reddit post for inappropriate content
        
        Args:
            post: Post dictionary with text content
            
        Returns:
            Filtered post dictionary
        """
        filtered_post = post.copy()
        
        # Check NSFW flag
        if self.filter_nsfw and post.get('over_18', False):
            logger.info(f"Post {post.get('id')} marked as NSFW")
            filtered_post['content_warning'] = 'NSFW content'
            
            if self.config.get('skip_nsfw', False):
                filtered_post['skip_reason'] = 'NSFW content filtered'
                filtered_post['should_skip'] = True
                return filtered_post
        
        # Filter title
        if 'processed_title' in filtered_post:
            filtered_title = self.filter_text(filtered_post['processed_title'])
            filtered_post['processed_title'] = filtered_title
        
        # Filter body
        if 'processed_body' in filtered_post:
            filtered_body = self.filter_text(filtered_post['processed_body'])
            filtered_post['processed_body'] = filtered_body
        
        # Filter combined TTS text
        if 'tts_text' in filtered_post:
            filtered_tts = self.filter_text(filtered_post['tts_text'])
            filtered_post['tts_text'] = filtered_tts
        
        # Add content warnings
        warnings = self.detect_sensitive_content(filtered_post.get('tts_text', ''))
        if warnings:
            filtered_post['content_warnings'] = warnings
        
        # Add filter statistics
        filtered_post['filter_stats'] = self._get_filter_stats(post, filtered_post)
        
        return filtered_post
    
    def filter_text(self, text: str) -> str:
        """
        Filter inappropriate content from text
        
        Args:
            text: Text to filter
            
        Returns:
            Filtered text
        """
        if not text or not self.filter_profanity:
            return text
        
        filtered = text
        replacements_made = 0
        
        # Apply profanity filters
        for pattern in self.profanity_patterns:
            matches = pattern.finditer(filtered)
            for match in reversed(list(matches)):
                original_word = match.group()
                replacement = self._get_replacement(original_word)
                
                # Replace the word
                start, end = match.span()
                filtered = filtered[:start] + replacement + filtered[end:]
                replacements_made += 1
        
        if replacements_made > 0:
            logger.debug(f"Made {replacements_made} profanity replacements")
        
        return filtered
    
    def _get_replacement(self, word: str) -> str:
        """
        Get replacement for filtered word based on censor style
        
        Args:
            word: Word to replace
            
        Returns:
            Replacement string
        """
        if self.censor_style == 'remove':
            return ''
        elif self.censor_style == 'beep':
            return '[beep]'
        else:  # asterisk style
            if len(word) <= 2:
                return '*' * len(word)
            else:
                # Keep first and last letter
                return word[0] + '*' * (len(word) - 2) + word[-1]
    
    def detect_sensitive_content(self, text: str) -> List[str]:
        """
        Detect sensitive topics in text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected sensitive topics
        """
        if not text:
            return []
        
        warnings = []
        text_lower = text.lower()
        
        for topic, keywords in self.sensitive_topics.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if topic not in warnings:
                        warnings.append(topic)
                    break
        
        if warnings:
            logger.debug(f"Detected sensitive topics: {warnings}")
        
        return warnings
    
    def is_safe_for_tts(self, post: Dict[str, Any]) -> bool:
        """
        Check if post is safe for TTS conversion
        
        Args:
            post: Post to check
            
        Returns:
            True if safe for TTS
        """
        # Skip if explicitly marked
        if post.get('should_skip', False):
            return False
        
        # Check for removed/deleted content
        text = post.get('tts_text', '')
        if '[removed]' in text or '[deleted]' in text:
            return False
        
        # Check minimum content length
        if len(text.strip()) < 10:
            return False
        
        # Check if too much content was filtered
        if post.get('filter_stats', {}).get('profanity_ratio', 0) > 0.3:
            logger.warning(f"Post {post.get('id')} has too much profanity (>30%)")
            return False
        
        return True
    
    def _get_filter_stats(self, original: Dict, filtered: Dict) -> Dict:
        """
        Calculate filtering statistics
        
        Args:
            original: Original post
            filtered: Filtered post
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'profanity_found': False,
            'profanity_count': 0,
            'profanity_ratio': 0.0,
            'content_warnings': len(filtered.get('content_warnings', [])),
        }
        
        # Count profanity matches in original text
        original_text = original.get('tts_text', '')
        if original_text:
            for pattern in self.profanity_patterns:
                matches = pattern.findall(original_text)
                stats['profanity_count'] += len(matches)
            
            word_count = len(original_text.split())
            if word_count > 0:
                stats['profanity_ratio'] = stats['profanity_count'] / word_count
            
            stats['profanity_found'] = stats['profanity_count'] > 0
        
        return stats
    
    def get_family_friendly_filter(self) -> 'ContentFilter':
        """
        Get a strict family-friendly version of the filter
        
        Returns:
            ContentFilter configured for family-friendly content
        """
        family_config = {
            'filter_profanity': True,
            'filter_nsfw': True,
            'skip_nsfw': True,
            'censor_style': 'remove',
        }
        return ContentFilter(family_config)


# Singleton instance
_content_filter = None

def get_content_filter(config: Optional[Dict] = None) -> ContentFilter:
    """Get or create content filter instance"""
    global _content_filter
    if _content_filter is None or config is not None:
        _content_filter = ContentFilter(config)
    return _content_filter
