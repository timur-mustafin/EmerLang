
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
emlang.py — educational "emergent language" codec (single-file v1)
==================================================================
Purpose: stylize text as an "emergent-looking protocol" using a deterministic
token mapping. This is NOT cryptography and NOT protection; it's an art/edu demo.

Capabilities
------------
- build: train a codebook (word -> emergent token) from a text corpus (by word frequency).
- encode: convert text into an emergent-looking stream.
- decode: attempt to recover text using the same codebook. Unknown words are
          encoded via reversible glyph blocks.

Limitations
-----------
- It's a toy "proto-language" for demonstration.
- Decoding can be lossy re: spacing/case/punctuation.
- Does NOT hide the fact of communication; NOT a cipher.
"""

import argparse
import json
import math
import random
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

# ---------- Symbol sets for emergent look ----------
GREEK_LOWER = list("αβγδεζηθικλμνξοπρστυφχψω")
GREEK_UPPER = list("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ")
OPS = ["Δ","Ψ","Ω","Λ","Σ","Φ","Θ","Ξ","ζ","δ","π","µ","∑","∴","⊕","⊗","⊡","⟦","⟧","⟨","⟩","⇔","⇒","⇐","↔","→","←","∵","≈","≡","∝","∞","∇"]
RESERVED = set(["⟦","⟧","⟨","⟩","::","∴"])

HEX_DIGIT_TO_GLYPH = {
    "0":"α","1":"β","2":"γ","3":"δ","4":"ε","5":"ζ","6":"η","7":"θ",
    "8":"ι","9":"κ","a":"λ","b":"μ","c":"ν","d":"ξ","e":"ο","f":"π",
}
GLYPH_TO_HEX = {v:k for k,v in HEX_DIGIT_TO_GLYPH.items()}

# ---------- Tokenization ----------
WORD_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)

def tokenize(text: str) -> List[str]:
    return WORD_RE.findall(text)

def is_word(tok: str) -> bool:
    return bool(re.match(r"^\w+$", tok, re.UNICODE))

# ---------- Emergent token generator ----------
def _token_factory(seed: int = 1337):
    rnd = random.Random(seed)
    used = set()
    def make_token() -> str:
         # shape: [Greek][optional OPS or Greek][0..99]
        for _ in range(10000):
            a = rnd.choice(GREEK_UPPER + GREEK_LOWER)
            b = rnd.choice(["", rnd.choice(OPS), rnd.choice(GREEK_LOWER)])
            c = str(rnd.randint(0, 99))
            t = f"{a}{b}{c}"
            if (t not in used) and (t not in RESERVED):
                used.add(t)
                return t
        # fallback
        k = f"Ω{len(used)}"
        used.add(k)
        return k
    return make_token

# ---------- Codebook building ----------
def build_codebook(corpus_text: str, vocab_size: int = 500, seed: int = 1337) -> Dict:
    toks = [t.lower() for t in tokenize(corpus_text) if is_word(t)]
    freq = Counter(toks)
    most_common = [w for w,_ in freq.most_common(vocab_size)]
    make_token = _token_factory(seed=seed)

    # word -> emergent_token mapping
    w2e = {}
    e2w = {}
    for w in most_common:
        etok = make_token()
        w2e[w] = etok
        e2w[etok] = w

    codebook = {
        "version": 1,
        "seed": seed,
        "vocab_size": vocab_size,
        "word2em": w2e,
        "em2word": e2w,
        "hex2glyph": HEX_DIGIT_TO_GLYPH,
        "glyph2hex": GLYPH_TO_HEX,
    }
    return codebook

# ---------- Codebook I/O ----------
def save_codebook(cb: Dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cb, f, ensure_ascii=False, indent=2)

def load_codebook(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- Reversible fallback for OOV words ----------
def fallback_encode_word(word: str, codebook: Dict) -> str:
    # Convert to hex, map each hex digit to a glyph, wrap in ⟦...⟧
    data = word.encode("utf-8").hex()
    glyphs = "".join(codebook["hex2glyph"].get(ch, "α") for ch in data)
    return f"⟦{glyphs}⟧"

def fallback_decode_word(glyph_block: str, codebook: Dict) -> str:
    # glyph_block is inner text without ⟦ ⟧
    hex_str = "".join(codebook["glyph2hex"].get(ch, "") for ch in glyph_block)
    try:
        return bytes.fromhex(hex_str).decode("utf-8")
    except Exception:
        return "[UNK]"

# ---------- Optional structural markers ----------
def maybe_insert_structure(encoded_tokens: List[str], strength: float = 0.25, seed: int = 1337) -> List[str]:
    rnd = random.Random(seed)
    out = []
    for tok in encoded_tokens:
        out.append(tok)
        if rnd.random() < strength:
            out.append(rnd.choice(["::","∴","⇔"]))
    return out

# ---------- Encode ----------
def encode_text(text: str, codebook: Dict, structure: float = 0.2, seed: int = 1337) -> str:
    toks = tokenize(text)
    out = []
    for t in toks:
        if is_word(t):
            key = t.lower()
            if key in codebook["word2em"]:
                out.append(codebook["word2em"][key])
            else:
                out.append(fallback_encode_word(key, codebook))
        else:
            # пунктуация остаётся как есть (можно и маппить в глифы, но сохраним читабельный шум)
            out.append(t)
    if structure and structure > 0.0:
        out = maybe_insert_structure(out, strength=structure, seed=seed)
    # join: tighten before punctuation
    buf = []
    for i,t in enumerate(out):
        if i>0 and re.match(r"^\w|⟦|[Α-Ωα-ω]", t):
            # add space before word-like/glyph tokens
            buf.append(" ")
        if buf and len(buf[-1])>0 and buf[-1].endswith(" ") and re.match(r"^[.,!?;:)]$", t):
            buf[-1] = buf[-1][:-1]
        buf.append(t)
    return "".join(buf).strip()

# ---------- Decode ----------
GLYPH_BLOCK_RE = re.compile(r"⟦([{}]+)⟧".format("".join(map(re.escape, HEX_DIGIT_TO_GLYPH.values()))))

def decode_text(encoded: str, codebook: Dict) -> str:
    tokens = tokenize(encoded)
    # replace fallback glyph blocks first
    def replace_block(m):
        inner = m.group(1)
        return fallback_decode_word(inner, codebook)
    encoded = GLYPH_BLOCK_RE.sub(lambda m: replace_block(m), encoded)

    # tokenize and map emergent tokens back
    tokens = tokenize(encoded)

    # codebook use
    em2w = codebook.get("em2word", {})
    out = []
    for t in tokens:
        if t in em2w:
            out.append(em2w[t])
        elif t in {"::","∴","⇔"}:
            # delete structural markers or replace them for space
            out.append(" ")
        else:
            # punctuation as is
            out.append(t)

    # rejoin
    text = ""
    for i,t in enumerate(out):
        if i>0 and re.match(r"^\w", t):
            text += " "
        if text.endswith(" ") and re.match(r"^[.,!?;:)]$", t):
            text = text[:-1]
        text += t
    return text.strip()

# ---------- CLI ----------
def main():
    p = argparse.ArgumentParser(description="emlang — учебный кодек 'эмергентного' языка")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Собрать кодовую книгу из корпуса")
    p_build.add_argument("codebook_path", help="Путь для сохранения codebook.json")
    p_build.add_argument("corpus", help="Путь к текстовому файлу корпуса")
    p_build.add_argument("--vocab", type=int, default=500, help="Размер словаря (по частотам)")
    p_build.add_argument("--seed", type=int, default=1337, help="Seed для детерминированности")

    p_encode = sub.add_parser("encode", help="Закодировать текст в 'эмергентный' вид")
    p_encode.add_argument("codebook_path", help="Путь к codebook.json")
    p_encode.add_argument("--infile", required=True, help="Входной текстовый файл")
    p_encode.add_argument("--outfile", required=True, help="Куда записать результат")
    p_encode.add_argument("--structure", type=float, default=0.2, help="Доля структурных маркеров (0..1)")
    p_encode.add_argument("--seed", type=int, default=1337, help="Seed для маркеров")

    p_decode = sub.add_parser("decode", help="Попытаться декодировать обратно")
    p_decode.add_argument("codebook_path", help="Путь к codebook.json")
    p_decode.add_argument("--infile", required=True, help="Входной файл с 'эмергентным' текстом")
    p_decode.add_argument("--outfile", required=True, help="Куда записать восстановленный текст")

    args = p.parse_args()

    if args.cmd == "build":
        corpus_text = Path(args.corpus).read_text(encoding="utf-8")
        cb = build_codebook(corpus_text, vocab_size=args.vocab, seed=args.seed)
        save_codebook(cb, args.codebook_path)
        print(f"[OK] Codebook saved to {args.codebook_path} (vocab={args.vocab}, seed={args.seed})")

    elif args.cmd == "encode":
        cb = load_codebook(args.codebook_path)
        text = Path(args.infile).read_text(encoding="utf-8")
        enc = encode_text(text, cb, structure=args.structure, seed=args.seed)
        Path(args.outfile).write_text(enc, encoding="utf-8")
        print(f"[OK] Encoded to {args.outfile} (structure={args.structure})")

    elif args.cmd == "decode":
        cb = load_codebook(args.codebook_path)
        enc = Path(args.infile).read_text(encoding="utf-8")
        dec = decode_text(enc, cb)
        Path(args.outfile).write_text(dec, encoding="utf-8")
        print(f"[OK] Decoded to {args.outfile}")
    else:
        p.print_help()

if __name__ == "__main__":
    main()
