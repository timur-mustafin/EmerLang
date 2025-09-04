# emlang — educational "emergent" codec (v1.1, single-file)

**emlang.py** transforms plain text into an *emergent-looking* protocol and can try to decode it back using the same codebook.  
> ⚠️ This is **not** cryptography or protection; it’s an art/edu demo.

## What’s new in v1.1
- All comments, messages, and CLI help in **English**.
- **Interactive mode (default):** run `python emlang.py` and choose:
  1) **build** — paste a corpus → save `codebook.json`
  2) **encode** — paste text or choose a file → emergent output
  3) **decode** — paste emergent text or choose a file → plain text
- **Legacy CLI** remains fully supported (build/encode/decode subcommands).

## Quick start (CLI, legacy style)
```bash
# 1) Build a codebook from your corpus
python emlang.py build codebook.json sample.txt --vocab 200 --seed 42

# 2) Encode any text (here: sample.txt)
python emlang.py encode codebook.json --infile sample.txt --outfile sample.em --structure 0.3 --seed 42

# 3) Try to decode it back
python emlang.py decode codebook.json --infile sample.em --outfile sample.dec.txt
```

## interactive IO
```bash
python emlang.py
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
