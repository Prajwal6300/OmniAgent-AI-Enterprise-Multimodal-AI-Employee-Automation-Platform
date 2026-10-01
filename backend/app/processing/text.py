"""
OmniAgent AI — Text Normalization and Cleaning
"""

import re


class TextProcessor:
    """Provides whitespace normalization, Unicode sanitization, and text chunking."""

    @staticmethod
    def clean(text: str) -> str:
        """Normalizes irregular whitespace and cleans leading/trailing characters."""
        if not text:
            return ""
        # Collapse multi-spaces and newlines into standard clean spacing
        cleaned = re.sub(r"\s+", " ", text)
        return cleaned.strip()
