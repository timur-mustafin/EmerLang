from typing import List
import re, random
from .tokenize import tokenize_basic, is_word, normalize
from .utils import crc8, smart_join

def _encode_fallback(word: str, codebook) -> str:
    data = word.encode("utf-8")
    hex_str = data.hex()
    glyphs = "".join(codebook.hex2glyph.get(ch, "α") for ch in hex_str)
    cc = crc8(data)
    return f"⟦{glyphs}~{cc:02x}⟧"

def encode(text: str, codebook, structure: float = 0.2, seed: int = 42) -> str:
    text = normalize(text, "NFKC")
    toks = tokenize_basic(text)
    out: List[str] = []
    for t in toks:
        if is_word(t):
            key = t.lower()
            if key in codebook.word2em:
                out.append(codebook.word2em[key])
            else:
                out.append(_encode_fallback(key, codebook))
        else:
            out.append(t)
    if structure and structure > 0:
        rnd = random.Random(seed)
        salted = []
        for tok in out:
            salted.append(tok)
            if rnd.random() < structure:
                salted.append(rnd.choice(["::","∴","⇔"]))
        out = salted
    return smart_join(out)
