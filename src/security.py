from __future__ import annotations

import re


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"reveal\s+(the\s+)?(system|developer)\s+prompt",
    r"show\s+(me\s+)?(the\s+)?(system|developer)\s+message",
    r"override\s+(the\s+)?instructions",
    r"act\s+as\s+the\s+system",
    r"exfiltrat(e|ion)",
    r"print\s+(all\s+)?secrets",
]


def contains_prompt_injection(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered, re.IGNORECASE) for pattern in INJECTION_PATTERNS)
