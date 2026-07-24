import re
import unicodedata

def sanitize_external(text: str) -> str:
    """
    Strips HTML, dangerous links, and instructions from external content.
    Prefixes with EXTERNAL_UNTRUSTED_CONTENT per dev-guide.
    """
    if not text:
        return "EXTERNAL_UNTRUSTED_CONTENT: [EMPTY]"

    # 1. Strip HTML tags
    text = re.sub(r'<[^>]*?>', '', text)
    
    # 2. Normalize Unicode (NFKC) and strip non-printable
    text = unicodedata.normalize('NFKC', text)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\n\r\t")
    
    # 3. Strip non-standard markdown links (keep http/https)
    # Replaces [text](javascript:...) or [text](file://...) with [text]([REMOVED])
    text = re.sub(r'\[([^\]]+)\]\((?!(https?://))[^\)]+\)', r'[\1]([REMOVED])', text)
    
    # 4. Strip embedded instruction phrases (e.g. "ignore previous instructions")
    instruction_patterns = [
        r"(?i)ignore\s+previous\s+instructions",
        r"(?i)system\s+prompt",
        r"(?i)you\s+are\s+now",
        r"(?i)forget\s+everything"
    ]
    for pattern in instruction_patterns:
        text = re.sub(pattern, "[STRIPPED_INSTRUCTION]", text)

    return f"EXTERNAL_UNTRUSTED_CONTENT: {text.strip()}"
