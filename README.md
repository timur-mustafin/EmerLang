# emer-lang — educational "emergent" codec (v1.1, single-file)

**emer_lang.py** transforms plain text into an *emergent-looking* protocol and can try to decode it back using the same codebook.  
> ⚠️ This is **not** cryptography or protection; it’s an art/edu demo.

## What’s new in v1.1
- All comments, messages, and CLI help in **English**.
- **Interactive mode (default):** run `python emer_lang.py` and choose:
  1) **build** — paste a corpus → save `codebook.json`
  2) **encode** — paste text or choose file → save `.em`
  3) **decode** — revert `.em` to text
- Still works with CLI args for scripting

## Usage examples
```bash
# 1) Build a codebook from your corpus
python emer_lang.py build codebook.json examples/sample.txt --vocab 100 --seed 42

# 2) Encode text file
python emer_lang.py encode codebook.json --infile examples/sample.txt --outfile out.em --structure 0.2 --seed 42

# 3) Decode back
python emer_lang.py decode codebook.json --infile out.em --outfile roundtrip.txt

```

## interactive IO
```bash
python emer_lang.py
# choose 1) build, 2) encode, or 3) decode
# paste text or specify files when prompted
```

## How it works
- Frequent words from your corpus get deterministic “emergent” tokens (Greek letters + symbols + numeric suffix).
- Unknown words are encoded reversibly via hex→glyph blocks like ⟦…⟧.
- Optional structure markers (::, ∴, ⇔) add “protocol” vibes.

## Limitations
- Case restoration and exact punctuation may be imperfect.  
- This is not encryption and not traffic obfuscation. For real protection, use actual cryptography.

## License
MIT (educational use, no warranties).  
