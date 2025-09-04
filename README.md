# emlang — educational "emergent" codec

**Purpose:** demonstrate how text can be stylized into a “neural network language.”  
This is **not cryptography** and **not protection**: the goal is experimentation and visualization.

## Features
- `build`: generate a codebook (by word frequency) from your corpus.  
- `encode`: transform text into an “emergent” stream of glyphs and symbols.  
- `decode`: attempt to restore the original text (works best if words are in the codebook).  
  Unknown words are encoded reversibly through glyphs.

## Installation
Just download `emlang.py` or the example archive.

## Quick start
```bash
# 1) Build a codebook from your corpus
python emlang.py build codebook.json sample.txt --vocab 200 --seed 42

# 2) Encode any text (here: sample.txt)
python emlang.py encode codebook.json --infile sample.txt --outfile sample.em --structure 0.3 --seed 42

# 3) Try to decode it back
python emlang.py decode codebook.json --infile sample.em --outfile sample.dec.txt
```

## How it works (in short)
- Text is tokenized into words/punctuation.  
- The most frequent words in the corpus are assigned “emergent” tokens (Greek letters + symbols + numbers).  
- Unknown words are encoded via hex→glyph mapping and wrapped in `⟦...⟧`, which allows byte-level recovery.  
- Additional structural markers (`::`, `∴`, `⇔`) are inserted to give an “alien protocol” feel.

## Limitations
- Case restoration and exact punctuation may be imperfect.  
- This is not encryption and not traffic obfuscation. For real protection, use actual cryptography.

## License
MIT (educational use, no warranties).  
