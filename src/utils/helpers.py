"""General helper utilities."""
from datetime import datetime

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "2m 34s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def generate_session_id() -> str:
    """Generate a unique session ID.
    
    Returns:
        Session ID string
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"sess_{timestamp}"

async def extract_tokens(response):    
    u = response.context_wrapper.usage
    return {
        "input_tokens": u.input_tokens,
        "output_tokens": u.output_tokens,
        "total_tokens": u.input_tokens + u.output_tokens,
        "cached_tokens": u.input_tokens_details.cached_tokens,
        "reasoning_tokens": u.output_tokens_details.reasoning_tokens,
    }

