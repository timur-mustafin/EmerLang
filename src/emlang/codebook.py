from __future__ import annotations
import json, random, time
from dataclasses import dataclass, field
from typing import Dict
from collections import Counter
from .tokenize import tokenize_basic, is_word

GREEK_LOWER = list("αβγδεζηθικλμνξοπρστυφχψω")
GREEK_UPPER = list("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ")
OPS = ["Δ","Ψ","Ω","Λ","Σ","Φ","Θ","Ξ","ζ","δ","π","µ","∑","∴","⊕","⊗","⊡","⟦","⟧","⟨","⟩","⇔","⇒","⇐","↔","→","←","∵","≈","≡","∝","∞","∇"]
RESERVED = set(["⟦","⟧","⟨","⟩","::","∴"])

HEX_DIGIT_TO_GLYPH = {
    "0":"α","1":"β","2":"γ","3":"δ","4":"ε","5":"ζ","6":"η","7":"θ",
    "8":"ι","9":"κ","a":"λ","b":"μ","c":"ν","d":"ξ","e":"ο","f":"π",
}
GLYPH_TO_HEX = {v:k for k,v in HEX_DIGIT_TO_GLYPH.items()}

def _token_factory(seed: int = 1337):
    rnd = random.Random(seed)
    used = set()
    def make_token() -> str:
        for _ in range(10000):
            a = rnd.choice(GREEK_UPPER + GREEK_LOWER)
            b = rnd.choice(["", rnd.choice(OPS), rnd.choice(GREEK_LOWER)])
            c = str(rnd.randint(0, 99))
            t = f"{a}{b}{c}"
            if (t not in used) and (t not in RESERVED):
                used.add(t); return t
        k = f"Ω{len(used)}"; used.add(k); return k
    return make_token

@dataclass
class Codebook:
    format: int = 3
    created: float = field(default_factory=lambda: time.time())
    seed: int = 42
    vocab_size: int = 500
    ngram_max: int = 1
    tokenizer: str = "basic"
    word2em: Dict[str, str] = field(default_factory=dict)
    em2word: Dict[str, str] = field(default_factory=dict)
    hex2glyph: Dict[str, str] = field(default_factory=lambda: HEX_DIGIT_TO_GLYPH)
    glyph2hex: Dict[str, str] = field(default_factory=lambda: GLYPH_TO_HEX)

    @classmethod
    def train(cls, corpus_path: str, vocab_size: int = 500, seed: int = 42, tokenizer: str = "basic", ngram_max: int = 1):
        text = open(corpus_path, "r", encoding="utf-8").read()
        toks = tokenize_basic(text)
        words = [t.lower() for t in toks if is_word(t)]
        from collections import Counter
        freq = Counter(words)
        most_common = [w for w,_ in freq.most_common(vocab_size)]
        make_token = _token_factory(seed)
        word2em, em2word = {}, {}
        for w in most_common:
            et = make_token()
            word2em[w] = et; em2word[et] = w
        return cls(seed=seed, vocab_size=vocab_size, ngram_max=ngram_max, tokenizer=tokenizer,
                   word2em=word2em, em2word=em2word)

    def save(self, path: str):
        data = {
            "format": self.format, "created": self.created, "seed": self.seed,
            "vocab_size": self.vocab_size, "ngram_max": self.ngram_max, "tokenizer": self.tokenizer,
            "word2em": self.word2em, "em2word": self.em2word,
            "hex2glyph": self.hex2glyph, "glyph2hex": self.glyph2hex,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "Codebook":
        data = json.load(open(path, "r", encoding="utf-8"))
        return cls(**data)
