import re
from typing import Dict, Any

class TextProcessor:
    def clean(self, raw_text: str) -> str:
        text = re.sub(r"\s+", " ", raw_text)
        return text.strip()

    def extract_stats(self, text: str) -> Dict[str, Any]:
        words = text.split()
        return {
            "character_count": len(text),
            "word_count": len(words)
        }
