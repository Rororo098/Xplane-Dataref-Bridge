"""Utility functions for the X-Plane Dataref Bridge."""

import re
from typing import Optional


def format_dataref_description(name: str) -> str:
    """
    Format a dataref name into a human-readable description.
    
    Args:
        name: The dataref name (e.g., 'sim/cockpit2/radios/nav_frequency_hz')
        
    Returns:
        A formatted description (e.g., 'Sim Cockpit2 Radios Nav Frequency Hz')
    """
    if not name:
        return "Unknown Dataref"
    
    # Normalize path-like names: / and _ to spaces, then title-case each word
    clean = name.replace('/', ' ').replace('_', ' ').replace('\\', ' ')
    
    # Clean up extra spaces
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    # Split into words and capitalize each word
    words = [word.capitalize() for word in clean.split() if word]
    
    # Join back together
    result = ' '.join(words)
    
    # Special handling for common abbreviations
    result = re.sub(r'\bHz\b', 'Hz', result, flags=re.IGNORECASE)
    result = re.sub(r'\bKts\b', 'Kts', result, flags=re.IGNORECASE)
    result = re.sub(r'\bFt\b', 'Ft', result, flags=re.IGNORECASE)
    result = re.sub(r'\bM\b', 'M', result, flags=re.IGNORECASE)  # meters
    
    return result


def get_display_description(dataref_name: str, db_description: Optional[str]) -> str:
    """
    Get the appropriate description for a dataref, using fallback if needed.
    
    Args:
        dataref_name: The name of the dataref
        db_description: The description from the database (may be None or empty)
        
    Returns:
        A display-ready description
    """
    # Use database description if it exists and is not empty/whitespace
    if db_description and db_description.strip():
        return db_description.strip()
    
    # Fall back to formatted name
    return format_dataref_description(dataref_name)
