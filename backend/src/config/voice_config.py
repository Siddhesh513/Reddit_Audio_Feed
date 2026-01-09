"""
Voice Configuration for Post and Comment Narration
"""

# Voice mapping for different segment types
VOICE_CONFIG = {
    'post': 'en-US',  # Narrator voice for post content
    'comments': [      # Rotating voices for comments
        'en-GB',
        'en-AU',
        'en-IN'
    ]
}

def get_voice_for_segment(segment_type: str, index: int = 0) -> str:
    """
    Get voice identifier for a segment

    Args:
        segment_type: 'post' or 'comment'
        index: Comment index (for rotating through comment voices)

    Returns:
        Voice identifier string
    """
    if segment_type == 'post':
        return VOICE_CONFIG['post']
    else:  # comment
        voices = VOICE_CONFIG['comments']
        return voices[index % len(voices)]
