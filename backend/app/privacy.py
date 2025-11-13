"""
Privacy filters for sensitive information detection.
"""

import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class PrivacyFilter:
    """Detect and filter sensitive information from memories."""
    
    # Patterns for sensitive information
    SENSITIVE_PATTERNS = [
        (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'credit_card'),  # Credit card numbers
        (r'\b\d{3}-\d{2}-\d{4}\b', 'ssn'),  # SSN
        (r'\b\d{9}\b', 'ssn_alt'),  # SSN without dashes
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'email'),  # Email addresses
        (r'\b\d{10,11}\b', 'phone'),  # Phone numbers
        (r'\b[A-Z]{2}\d{6,9}\b', 'passport'),  # Passport numbers
    ]
    
    def detect_sensitive_info(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect sensitive information in text.
        
        Args:
            text: Text to scan
        
        Returns:
            List of detected sensitive information with types
        """
        detected = []
        
        for pattern, info_type in self.SENSITIVE_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                detected.append({
                    "type": info_type,
                    "value": match.group(),
                    "position": match.start()
                })
        
        return detected
    
    def filter_sensitive_info(self, text: str, replacement: str = "[REDACTED]") -> str:
        """
        Filter sensitive information from text.
        
        Args:
            text: Text to filter
            replacement: Replacement string for sensitive info
        
        Returns:
            Filtered text with sensitive information replaced
        """
        filtered_text = text
        
        for pattern, info_type in self.SENSITIVE_PATTERNS:
            filtered_text = re.sub(pattern, replacement, filtered_text)
        
        return filtered_text
    
    def should_redact_memory(self, memory: Dict[str, Any]) -> bool:
        """
        Determine if a memory should be redacted due to sensitive information.
        
        Args:
            memory: Memory object
        
        Returns:
            True if memory contains sensitive information
        """
        content = memory.get("content", "")
        detected = self.detect_sensitive_info(content)
        
        if detected:
            logger.warning(
                f"Memory contains sensitive information: {len(detected)} items detected"
            )
            return True
        
        return False


def get_privacy_filter() -> PrivacyFilter:
    """Get privacy filter instance."""
    return PrivacyFilter()

