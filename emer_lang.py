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
import random
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List

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
        # fallback if somehow exhausted
        k = f"Ω{len(used)}"
        used.add(k)
        return k
    return make_token

# ---------- Codebook building ----------
def build_codebook(corpus_text: str, vocab_size: int = 500, seed: int = 1337) -> Dict:
    tokens = [t.lower() for t in tokenize(corpus_text) if is_word(t)]
    freq = Counter(tokens)
    most_common = [w for w,_ in freq.most_common(vocab_size)]
    make_token = _token_factory(seed=seed)

    # word -> emergent_token mapping
    w2e, e2w = {}, {}
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
    Path(path).write_text(json.dumps(cb, ensure_ascii=False, indent=2), encoding="utf-8")

def load_codebook(path: str) -> Dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

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
            # keep punctuation as-is (for a readable "protocol noise")
            out.append(t)
    if structure and structure > 0.0:
        out = maybe_insert_structure(out, strength=structure, seed=seed)
    # join: add space before word-like/glyph tokens, tighten before punctuation
    buf = []
    for i, tok in enumerate(out):
        if i > 0 and re.match(r"^\w|⟦|[Α-Ωα-ω]", tok):
            buf.append(" ")
        if buf and buf[-1].endswith(" ") and re.match(r"^[.,!?;:)]$", tok):
            buf[-1] = buf[-1][:-1]
        buf.append(tok)
    return "".join(buf).strip()

# ---------- Decode ----------
GLYPH_BLOCK_RE = re.compile(r"⟦([{}]+)⟧".format("".join(map(re.escape, HEX_DIGIT_TO_GLYPH.values()))))

def decode_text(encoded: str, codebook: Dict) -> str:
    # 1) replace fallback glyph blocks first
    def replace_block(m):
        inner = m.group(1)
        return fallback_decode_word(inner, codebook)
    encoded = GLYPH_BLOCK_RE.sub(lambda m: replace_block(m), encoded)

    # 2) tokenize and map emergent tokens back
    tokens = tokenize(encoded)
    em2w = codebook.get("em2word", {})
    out = []
    for t in tokens:
        if t in em2w:
            out.append(em2w[t])
        elif t in {"::","∴","⇔"}:
            out.append(" ")
        else:
            out.append(t)

    # 3) naive spacing
    text = ""
    for i, tok in enumerate(out):
        if i > 0 and re.match(r"^\w", tok):
            text += " "
        if text.endswith(" ") and re.match(r"^[.,!?;:)]$", tok):
            text = text[:-1]
        text += tok
    return text.strip()

# ---------- Interactive helpers ----------
def prompt_nonempty(prompt: str) -> str:
    s = input(prompt).strip()
    while not s:
        s = input(prompt).strip()
    return s

def interactive_build():
    print("\n[BUILD] Train a codebook from text you paste here.")
    codebook_path = input("Path to save codebook.json (default: codebook.json): ").strip() or "codebook.json"
    vocab = input("Vocab size (default 500): ").strip() or "500"
    seed = input("Seed (default 1337): ").strip() or "1337"

    print("\nPaste your corpus text. Finish with an empty line (press Enter twice):")
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    corpus_text = "\n".join(lines)

    cb = build_codebook(corpus_text, vocab_size=int(vocab), seed=int(seed))
    save_codebook(cb, codebook_path)
    print(f"\n[OK] Codebook saved to {codebook_path} (vocab={vocab}, seed={seed})")

def interactive_encode():
    print("\n[ENCODE] Transform plain text into emergent-looking output.")
    codebook_path = prompt_nonempty("Path to existing codebook.json: ")
    structure = input("Structure strength (0..1, default 0.2): ").strip() or "0.2"
    seed = input("Seed (default 1337): ").strip() or "1337"

    # choose text source
    mode = (input("Input source: [1] paste text  [2] read file (default 1): ").strip() or "1")
    if mode == "2":
        infile = prompt_nonempty("Path to input text file: ")
        text = Path(infile).read_text(encoding="utf-8")
    else:
        print("\nPaste your text. Finish with an empty line (press Enter twice):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        text = "\n".join(lines)

    cb = load_codebook(codebook_path)
    emergent = encode_text(text, cb, structure=float(structure), seed=int(seed))
    print("\n----- Emergent output -----\n")
    print(emergent)
    print("\n---------------------------\n")

    outpath = input("Save to file? Enter path or leave empty to skip: ").strip()
    if outpath:
        Path(outpath).write_text(emergent, encoding="utf-8")
        print(f"[OK] Saved to {outpath}")

def interactive_decode():
    print("\n[DECODE] Attempt to recover text from emergent output.")
    codebook_path = prompt_nonempty("Path to existing codebook.json: ")

    mode = (input("Input source: [1] paste emergent text  [2] read file (default 1): ").strip() or "1")
    if mode == "2":
        infile = prompt_nonempty("Path to emergent input file: ")
        emergent = Path(infile).read_text(encoding="utf-8")
    else:
        print("\nPaste emergent text. Finish with an empty line (press Enter twice):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        emergent = "\n".join(lines)

    cb = load_codebook(codebook_path)
    plain = decode_text(emergent, cb)
    print("\n----- Decoded text -----\n")
    print(plain)
    print("\n------------------------\n")

    outpath = input("Save to file? Enter path or leave empty to skip: ").strip()
    if outpath:
        Path(outpath).write_text(plain, encoding="utf-8")
        print(f"[OK] Saved to {outpath}")

def interactive_main():
    print("🛰️ EmerLang (interactive mode) — not cryptography; art/edu demo.\n")
    print("Choose a command:")
    print("  [1] build   — train a codebook from pasted text")
    print("  [2] encode  — paste text or read file, get emergent output")
    print("  [3] decode  — paste emergent text or read file, get plain text")
    print("  [q] quit")
    while True:
        choice = input("\nYour choice [1/2/3/q]: ").strip().lower()
        if choice in ("q", "quit", "exit"):
            print("Bye.")
            return
        if choice == "1":
            interactive_build()
        elif choice == "2":
            interactive_encode()
        elif choice == "3":
            interactive_decode()
        else:
            print("Please enter 1, 2, 3, or q.")

# ---------- CLI ----------
def main():
    p = argparse.ArgumentParser(
        description="emlang — educational emergent-language codec (art/edu; NOT crypto)."
    )
    sub = p.add_subparsers(dest="cmd", required=False)  # <- allow interactive if omitted

    # build
    p_build = sub.add_parser("build", help="Build a codebook from a corpus file")
    p_build.add_argument("codebook_path", nargs="?", help="Where to save codebook.json")
    p_build.add_argument("corpus", nargs="?", help="Path to a corpus text file")
    p_build.add_argument("--vocab", type=int, default=500, help="Vocabulary size (most frequent words)")
    p_build.add_argument("--seed", type=int, default=1337, help="Seed for determinism")

    # encode
    p_encode = sub.add_parser("encode", help="Encode text to emergent-looking form")
    p_encode.add_argument("codebook_path", nargs="?", help="Path to codebook.json")
    p_encode.add_argument("--infile", help="Input plain text file (if omitted, will prompt)")
    p_encode.add_argument("--outfile", help="Where to write emergent output (if omitted, prints to stdout)")
    p_encode.add_argument("--structure", type=float, default=0.2, help="Structural marker ratio (0..1)")
    p_encode.add_argument("--seed", type=int, default=1337, help="Seed for markers")

    # decode
    p_decode = sub.add_parser("decode", help="Decode emergent text back to plain text")
    p_decode.add_argument("codebook_path", nargs="?", help="Path to codebook.json")
    p_decode.add_argument("--infile", help="Input emergent text file (if omitted, will prompt)")
    p_decode.add_argument("--outfile", help="Where to write recovered text (if omitted, prints to stdout)")

    args = p.parse_args()

    # No subcommand → interactive menu
    if not args.cmd:
        interactive_main()
        return

    # Subcommand paths
    if args.cmd == "build":
        # If positional args are missing, fall back to interactive build
        if not args.codebook_path or not args.corpus:
            interactive_build()
            return
        corpus_text = Path(args.corpus).read_text(encoding="utf-8")
        cb = build_codebook(corpus_text, vocab_size=args.vocab, seed=args.seed)
        save_codebook(cb, args.codebook_path)
        print(f"[OK] Codebook saved to {args.codebook_path} (vocab={args.vocab}, seed={args.seed})")

    elif args.cmd == "encode":
        # If any required info missing, go interactive
        if not args.codebook_path or (not args.infile and not args.outfile):
            interactive_encode()
            return
        cb = load_codebook(args.codebook_path)
        if args.infile:
            text = Path(args.infile).read_text(encoding="utf-8")
        else:
            # stdin-like: read from console
            text = input().strip()
        emergent = encode_text(text, cb, structure=args.structure, seed=args.seed)
        if args.outfile:
            Path(args.outfile).write_text(emergent, encoding="utf-8")
            print(f"[OK] Encoded to {args.outfile} (structure={args.structure})")
        else:
            print(emergent)

    elif args.cmd == "decode":
        if not args.codebook_path or (not args.infile and not args.outfile):
            interactive_decode()
            return
        cb = load_codebook(args.codebook_path)
        if args.infile:
            enc = Path(args.infile).read_text(encoding="utf-8")
        else:
            enc = input().strip()
        dec = decode_text(enc, cb)
        if args.outfile:
            Path(args.outfile).write_text(dec, encoding="utf-8")
            print(f"[OK] Decoded to {args.outfile}")
        else:
            print(dec)

if __name__ == "__main__":
    main()
