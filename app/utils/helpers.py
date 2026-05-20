"""
Helper utilities module.
"""

from typing import Dict, Any


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries with override taking precedence.
    
    Args:
        base: Base dictionary
        override: Dictionary with overriding values
    
    Returns:
        Merged dictionary
    """
    result = base.copy()
    result.update(override)
    return result
