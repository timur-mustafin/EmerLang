import zlib, re

def crc8(data: bytes) -> int:
    return zlib.adler32(data) & 0xFF

_PUNCT_CLOSE = r"[.,!?;:)\]\}%»]"
_PUNCT_OPEN  = r"[(\[\{%«]"

def smart_join(tokens):
    out = []
    prev = ""
    for tok in tokens:
        add_space = False
        if re.match(r"^\w|^⟦|^[Α-Ωα-ω]", tok):
            add_space = True
        if re.match(f"^{_PUNCT_CLOSE}$", tok):
            add_space = False
        if prev and re.match(f"^{_PUNCT_OPEN}$", prev):
            add_space = False
        if add_space and out and not out[-1].endswith(" "):
            out.append(" ")
        out.append(tok)
        prev = tok
    s = "".join(out)
    s = re.sub(r"\s+(" + _PUNCT_CLOSE + r")", r"\1", s)
    return s.strip()
