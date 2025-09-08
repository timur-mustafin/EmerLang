# 🛰️ EmerLang (unified v3) — emergent-looking codec

**Not cryptography.** Educational art-tool that makes text look like an alien protocol.

## What’s unified
- v1 single-file style **interactive mode** (now via `emlang interactive`).
- v2 package with **CLI** (`emlang build|encode|decode`), clean API.
- Stdin/Stdout friendly encode/decode; **checksum** in fallback blocks `⟦…~cc⟧`; improved spacing.

## Quickstart (CLI)
```bash
python -m venv venv
pip install -e .
emlang build codebook.json  examples/corpora/mini_en.txt --vocab 300 --seed 42
emlang encode codebook.json --in examples/corpora/mini_en.txt --out out.em --structure 0.2
emlang decode codebook.json --in out.em --out roundtrip.txt
```

### Stdin/Stdout
```bash
echo "Hello emergent world" | emlang encode codebook.json > out.em
type out.em | emlang decode codebook.json   # Windows
```

## Interactive (v1-style)
```bash
emlang interactive
# choose 1/2/3 and paste text
```

## GUI with demo
```bash
python -m emlang.gui.emerlang_gui
```

## Python API
```python
from emlang import Codebook, encode, decode
cb = Codebook.train("examples/corpora/mini_en.txt", vocab_size=300, seed=42)
em = encode("Hello world!", cb, structure=0.2, seed=42)
print(decode(em, cb))
```

## Security notice
Not encryption / not obfuscation. For real security use vetted cryptography.
