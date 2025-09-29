"""
TTS Engine Service
Abstract TTS engine that can swap between different providers
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import os
from pathlib import Path
from gtts import gTTS
import tempfile
import uuid
from src.utils.loggers import get_logger

logger = get_logger(__name__)


class TTSEngine(ABC):
    """Abstract base class for TTS engines"""
    
    @abstractmethod
    def generate_audio(
        self, 
        text: str, 
        output_path: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate audio from text
        
        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            voice: Voice identifier
            speed: Speech speed multiplier
            **kwargs: Engine-specific parameters
            
        Returns:
            Dictionary with audio metadata
        """
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available voices"""
        pass
    
    @abstractmethod
    def estimate_duration(self, text: str, speed: float = 1.0) -> float:
        """Estimate audio duration in seconds"""
        pass
    
    @abstractmethod
    def validate_text(self, text: str) -> bool:
        """Check if text is valid for TTS"""
        pass


class GTTSEngine(TTSEngine):
    """Google Text-to-Speech engine implementation"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize gTTS engine"""
        self.config = config or {}
        self.language = self.config.get('language', 'en')
        self.tld = self.config.get('tld', 'com')  # com, co.uk, com.au for accents
        
        # Voice mapping for gTTS (via different TLDs)
        self.voice_map = {
            'en-US': 'com',
            'en-GB': 'co.uk',
            'en-AU': 'com.au',
            'en-IN': 'co.in',
            'en-CA': 'ca'
        }
        
        logger.info(f"gTTS engine initialized with language={self.language}, tld={self.tld}")
    
    def generate_audio(
        self, 
        text: str, 
        output_path: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate audio using gTTS"""
        
        if not self.validate_text(text):
            raise ValueError("Invalid text for TTS conversion")
        
        try:
            # Determine TLD for voice variant
            tld = self.voice_map.get(voice, self.tld) if voice else self.tld
            
            # gTTS doesn't support speed directly, but we can mention it in metadata
            slow = speed < 0.9
            
            # Create gTTS instance
            tts = gTTS(
                text=text,
                lang=self.language,
                slow=slow,
                tld=tld
            )
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save audio file
            tts.save(output_path)
            
            # Calculate metadata
            file_size = os.path.getsize(output_path)
            duration = self.estimate_duration(text, speed)
            
            metadata = {
                'engine': 'gtts',
                'voice': voice or f'{self.language}-{tld}',
                'language': self.language,
                'speed': speed,
                'file_path': output_path,
                'file_size_bytes': file_size,
                'duration_seconds': duration,
                'text_length': len(text),
                'success': True
            }
            
            logger.success(f"Audio generated: {output_path} ({duration:.1f}s, {file_size/1024:.1f}KB)")
            return metadata
            
        except Exception as e:
            logger.error(f"gTTS generation failed: {e}")
            return {
                'engine': 'gtts',
                'success': False,
                'error': str(e)
            }
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get available gTTS voices (via TLD variants)"""
        voices = []
        for voice_id, tld in self.voice_map.items():
            voices.append({
                'id': voice_id,
                'name': f'Google {voice_id}',
                'language': voice_id.split('-')[0],
                'region': voice_id.split('-')[1],
                'gender': 'neutral',  # gTTS doesn't specify gender
                'tld': tld
            })
        return voices
    
    def estimate_duration(self, text: str, speed: float = 1.0) -> float:
        """Estimate audio duration based on text length"""
        # Rough estimate: 150 words per minute at normal speed
        word_count = len(text.split())
        words_per_second = (150 / 60) * speed
        duration = word_count / words_per_second
        return max(duration, 0.5)  # Minimum 0.5 seconds
    
    def validate_text(self, text: str) -> bool:
        """Validate text for gTTS"""
        if not text or not text.strip():
            return False
        
        # gTTS has a limit of about 5000 characters
        if len(text) > 5000:
            logger.warning(f"Text too long for gTTS: {len(text)} characters")
            return False
        
        return True


class ReplicateKokoroEngine(TTSEngine):
    """
    Kokoro engine via Replicate API (for future cloud deployment)
    This will be implemented when deploying to cloud
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize Replicate Kokoro engine"""
        self.config = config or {}
        self.api_token = self.config.get('replicate_api_token')
        
        # Kokoro voice options
        self.voices = {
            'af_bella': {'name': 'Bella', 'gender': 'female', 'style': 'neutral'},
            'af_nicole': {'name': 'Nicole', 'gender': 'female', 'style': 'warm'},
            'af_sarah': {'name': 'Sarah', 'gender': 'female', 'style': 'professional'},
            'am_adam': {'name': 'Adam', 'gender': 'male', 'style': 'neutral'},
            'am_michael': {'name': 'Michael', 'gender': 'male', 'style': 'friendly'},
        }
        
        logger.info("Replicate Kokoro engine initialized (placeholder for cloud deployment)")
    
    def generate_audio(
        self, 
        text: str, 
        output_path: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate audio using Kokoro via Replicate
        This is a placeholder for future implementation
        """
        logger.info("Kokoro via Replicate will be implemented during cloud deployment")
        
        # For now, return mock metadata
        return {
            'engine': 'kokoro_replicate',
            'voice': voice or 'af_bella',
            'success': False,
            'error': 'Not implemented yet - will be available in cloud deployment'
        }
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get available Kokoro voices"""
        voices = []
        for voice_id, info in self.voices.items():
            voices.append({
                'id': voice_id,
                'name': info['name'],
                'gender': info['gender'],
                'style': info['style'],
                'engine': 'kokoro'
            })
        return voices
    
    def estimate_duration(self, text: str, speed: float = 1.0) -> float:
        """Estimate audio duration for Kokoro"""
        # Similar estimation to gTTS
        word_count = len(text.split())
        words_per_second = (150 / 60) * speed
        return word_count / words_per_second
    
    def validate_text(self, text: str) -> bool:
        """Validate text for Kokoro"""
        if not text or not text.strip():
            return False
        
        # Kokoro can handle longer texts
        if len(text) > 10000:
            logger.warning(f"Text very long for Kokoro: {len(text)} characters")
        
        return True


class MockTTSEngine(TTSEngine):
    """Mock TTS engine for testing without generating actual audio"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize mock engine"""
        self.config = config or {}
        logger.info("Mock TTS engine initialized (for testing)")
    
    def generate_audio(
        self, 
        text: str, 
        output_path: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock audio generation"""
        
        # Create a tiny empty file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).touch()
        
        return {
            'engine': 'mock',
            'voice': voice or 'mock_voice',
            'file_path': output_path,
            'duration_seconds': self.estimate_duration(text, speed),
            'text_length': len(text),
            'success': True,
            'mock': True
        }
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get mock voices"""
        return [
            {'id': 'mock_voice', 'name': 'Mock Voice', 'gender': 'neutral'}
        ]
    
    def estimate_duration(self, text: str, speed: float = 1.0) -> float:
        """Estimate duration for mock"""
        word_count = len(text.split())
        return word_count / (2.5 * speed)
    
    def validate_text(self, text: str) -> bool:
        """Validate for mock"""
        return bool(text and text.strip())


class TTSEngineFactory:
    """Factory to create appropriate TTS engine"""
    
    @staticmethod
    def create_engine(engine_type: str = 'gtts', config: Optional[Dict] = None) -> TTSEngine:
        """
        Create a TTS engine instance
        
        Args:
            engine_type: Type of engine ('gtts', 'kokoro', 'mock')
            config: Engine configuration
            
        Returns:
            TTSEngine instance
        """
        engines = {
            'gtts': GTTSEngine,
            'kokoro': ReplicateKokoroEngine,
            'mock': MockTTSEngine
        }
        
        engine_class = engines.get(engine_type.lower())
        if not engine_class:
            logger.warning(f"Unknown engine type: {engine_type}, falling back to gTTS")
            engine_class = GTTSEngine
        
        return engine_class(config)


# Singleton instance management
_tts_engine = None

def get_tts_engine(engine_type: Optional[str] = None, config: Optional[Dict] = None) -> TTSEngine:
    """Get or create TTS engine instance"""
    global _tts_engine
    
    # If requesting specific engine type or config, create new instance
    if engine_type is not None or config is not None:
        engine_type = engine_type or 'gtts'
        _tts_engine = TTSEngineFactory.create_engine(engine_type, config)
    
    # If no instance exists, create default
    if _tts_engine is None:
        _tts_engine = TTSEngineFactory.create_engine('gtts')
    
    return _tts_engine
