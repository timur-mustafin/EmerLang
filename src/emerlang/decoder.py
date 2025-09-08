import re
from .tokenize import tokenize_basic
from .utils import smart_join, crc8

GLYPH_BLOCK_RE = re.compile(r"⟦([^\]~]+)~([0-9a-fA-F]{2})⟧")
_EMERG_OPS = "ΔΨΩΛΣΦΘΞζδπµ∑∴⊕⊗⊡⟦⟧⟨⟩⇔⇒⇐↔→←∵≈≡∝∞∇"
EMERG_TOKEN_RE = re.compile(r"([Α-Ωα-ω])([" + _EMERG_OPS + r"α-ω]?)(\d{1,2})")

def _fallback_decode(glyphs: str, csum_hex: str, codebook) -> str:
    hex_map = codebook.glyph2hex
    hex_str = "".join(hex_map.get(ch, "") for ch in glyphs)
    try:
        raw = bytes.fromhex(hex_str)
        if f"{crc8(raw):02x}" != csum_hex.lower():
            return "[UNK]"
        return raw.decode("utf-8")
    except Exception:
        return "[UNK]"

def _decode_emergent_tokens(text: str, em2word: dict) -> str:
    def repl(m: re.Match) -> str:
        token = "".join(m.groups())
        return em2word.get(token, token)
    return EMERG_TOKEN_RE.sub(repl, text)

def decode(encoded: str, codebook) -> str:
    def repl_block(m):
        return _fallback_decode(m.group(1), m.group(2), codebook)
    s = GLYPH_BLOCK_RE.sub(lambda m: repl_block(m), encoded)
    for marker in ("::", "∴", "⇔"):
        s = s.replace(marker, " ")
    s = _decode_emergent_tokens(s, codebook.em2word)
    toks = tokenize_basic(s)
    return smart_join(toks)
