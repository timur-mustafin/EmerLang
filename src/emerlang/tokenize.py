import re, unicodedata
from typing import List

# Words, numbers, or standalone punctuation
WORD_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*|[0-9]+|[^\w\s]", re.UNICODE)

def normalize(text: str, form: str = "NFKC") -> str:
    return unicodedata.normalize(form, text)

def tokenize_basic(text: str) -> List[str]:
    return WORD_RE.findall(text)

def is_word(tok: str) -> bool:
    return bool(re.match(r"^[^\W\d_]+$", tok, re.UNICODE)) or bool(re.match(r"^[0-9]+$", tok))
