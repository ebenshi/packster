"""Security utilities for Packster cloud storage."""

import base64
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional


def generate_secure_url(expiry_hours: int = 168) -> str:
    """Generate a cryptographically secure, unguessable URL identifier.
    
    Args:
        expiry_hours: Number of hours until URL expires (default: 7 days)
        
    Returns:
        Secure URL identifier string
    """
    # Generate cryptographically secure random bytes
    random_bytes = secrets.token_bytes(32)  # 256 bits of entropy
    
    # Add timestamp for expiration tracking
    timestamp = int(time.time())
    expiry_timestamp = int(timestamp + (expiry_hours * 3600))
    
    # Combine random bytes with timestamp
    combined = random_bytes + expiry_timestamp.to_bytes(8, 'big')
    
    # Encode to URL-safe base64
    url_safe = base64.urlsafe_b64encode(combined).decode('ascii')
    
    # Remove padding for cleaner URLs
    url_safe = url_safe.rstrip('=')
    
    return url_safe


def validate_secure_url(url_id: str, current_time: Optional[int] = None) -> bool:
    """Validate if a secure URL is still valid (not expired).
    
    Args:
        url_id: The secure URL identifier to validate
        current_time: Current timestamp (for testing), defaults to current time
        
    Returns:
        True if URL is valid and not expired, False otherwise
    """
    try:
        # Add padding back for base64 decoding
        padding_length = (4 - len(url_id) % 4) % 4
        padded = url_id + '=' * padding_length
        
        # Decode from base64
        decoded = base64.urlsafe_b64decode(padded)
        
        # Extract timestamp (last 8 bytes)
        expiry_timestamp = int.from_bytes(decoded[-8:], 'big')
        
        # Check if expired
        if current_time is None:
            current_time = int(time.time())
            
        return current_time < expiry_timestamp
        
    except (ValueError, IndexError):
        # Invalid URL format
        return False


def extract_timestamp_from_url(url_id: str) -> Optional[datetime]:
    """Extract the expiry timestamp from a secure URL.
    
    Args:
        url_id: The secure URL identifier
        
    Returns:
        Expiry datetime if valid, None otherwise
    """
    try:
        # Add padding back for base64 decoding
        padding_length = (4 - len(url_id) % 4) % 4
        padded = url_id + '=' * padding_length
        
        # Decode from base64
        decoded = base64.urlsafe_b64decode(padded)
        
        # Extract timestamp (last 8 bytes)
        expiry_timestamp = int.from_bytes(decoded[-8:], 'big')
        
        return datetime.fromtimestamp(expiry_timestamp)
        
    except (ValueError, IndexError):
        return None


def generate_readable_id() -> str:
    """Generate a human-readable but still secure identifier.
    
    Returns:
        Readable identifier string (e.g., "abc123-def456-ghi789")
    """
    # Generate 3 groups of 6 characters each
    groups = []
    for _ in range(3):
        # Use alphanumeric characters (no confusing chars like 0/O, 1/l)
        chars = "abcdefghijkmnpqrstuvwxyz23456789"
        group = ''.join(secrets.choice(chars) for _ in range(6))
        groups.append(group)
    
    return '-'.join(groups)


def get_url_info(url_id: str) -> dict:
    """Get information about a secure URL.
    
    Args:
        url_id: The secure URL identifier
        
    Returns:
        Dictionary with URL information
    """
    expiry_time = extract_timestamp_from_url(url_id)
    is_valid = validate_secure_url(url_id)
    
    info = {
        "valid": is_valid,
        "expires_at": expiry_time.isoformat() if expiry_time else None,
        "expires_in_hours": None,
    }
    
    if expiry_time:
        now = datetime.now()
        if expiry_time > now:
            delta = expiry_time - now
            info["expires_in_hours"] = round(delta.total_seconds() / 3600, 1)
        else:
            info["expires_in_hours"] = 0
    
    return info
    