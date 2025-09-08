import sys
from pathlib import Path
import typer

# --- Console: best-effort UTF-8 for Windows consoles (prevents cp1252 issues) ---
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from .codebook import Codebook
from .encoder import encode as encode_core
from .decoder import decode as decode_core

app = typer.Typer(no_args_is_help=False, help="EmerLang — emergent-looking codec. Not crypto.")

# --- Robust text reader: auto-detect common BOMs and encodings ---
def _read_text_any(path: str) -> str:
    data = Path(path).read_bytes()
    for enc in ("utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    # Fallback: replace undecodable bytes
    return data.decode("utf-8", errors="replace")

@app.command()
def build(codebook_path: str = typer.Argument(..., help="Path to save codebook.json"),
          corpus: str = typer.Argument(..., help="Path to training corpus"),
          vocab: int = typer.Option(500, "--vocab", help="Vocab size"),
          seed: int = typer.Option(42, "--seed", help="Deterministic seed")):
    cb = Codebook.train(corpus_path=corpus, vocab_size=vocab, seed=seed, tokenizer="basic", ngram_max=1)
    cb.save(codebook_path)
    typer.echo(f"[OK] Codebook saved to {codebook_path} (vocab={vocab}, seed={seed})")

@app.command()
def encode(codebook_path: str = typer.Argument(..., help="Path to codebook.json"),
           infile: str = typer.Option(None, "--in", "--infile", help="Input text (file). If omitted, reads from stdin."),
           outfile: str = typer.Option(None, "--out", "--outfile", help="Output emergent file. If omitted, prints to stdout."),
           structure: float = typer.Option(0.2, "--structure", min=0.0, max=1.0),
           seed: int = typer.Option(42, "--seed")):
    cb = Codebook.load(codebook_path)

    # Input: file > piped stdin > interactive prompt
    if infile:
        text = _read_text_any(infile)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        text = typer.prompt("Paste text")

    emergent = encode_core(text, cb, structure=structure, seed=seed)

    if outfile:
        Path(outfile).write_text(emergent, encoding="utf-8")
        typer.echo(f"[OK] Encoded → {outfile}")
    else:
        # Use print to bypass click/cp1252 encoding edge cases
        print(emergent)

@app.command()
def decode(codebook_path: str = typer.Argument(..., help="Path to codebook.json"),
           infile: str = typer.Option(None, "--in", "--infile", help="Input emergent (file). If omitted, reads from stdin."),
           outfile: str = typer.Option(None, "--out", "--outfile", help="Output plain text file. If omitted, prints to stdout.")):
    cb = Codebook.load(codebook_path)

    # Input: file > piped stdin > interactive prompt
    if infile:
        emergent = _read_text_any(infile)
    elif not sys.stdin.isatty():
        emergent = sys.stdin.read()
    else:
        emergent = typer.prompt("Paste emergent text")

    plain = decode_core(emergent, cb)

    if outfile:
        Path(outfile).write_text(plain, encoding="utf-8")
        typer.echo(f"[OK] Decoded → {outfile}")
    else:
        print(plain)

@app.command()
def interactive():
    """
    Interactive mini-menu (build/encode/decode), useful for trying the codec quickly.
    """
    typer.echo("🛰️ EmerLang interactive — not crypto; art/edu demo.\n")
    typer.echo("Choose: [1] build  [2] encode  [3] decode  [q] quit")
    while True:
        choice = typer.prompt("Your choice", default="q").strip().lower()
        if choice in ("q","quit","exit"):
            raise typer.Exit()
        elif choice == "1":
            codebook_path = typer.prompt("Save codebook to", default="codebook.json")
            vocab = int(typer.prompt("Vocab size", default="500"))
            seed = int(typer.prompt("Seed", default="42"))
            typer.echo("Paste corpus (end with empty line):")
            lines = []
            import sys as _sys
            while True:
                line = _sys.stdin.readline()
                if not line or line.strip() == "":
                    break
                lines.append(line.rstrip("\n"))
            corpus_text = "\n".join(lines) or typer.prompt("Or paste a single-line corpus")
            tmp = Path(".tmp_corpus.txt"); tmp.write_text(corpus_text, encoding="utf-8")
            cb = Codebook.train(str(tmp), vocab_size=vocab, seed=seed)
            cb.save(codebook_path)
            typer.echo(f"[OK] Codebook saved to {codebook_path}")
        elif choice == "2":
            codebook_path = typer.prompt("Path to codebook.json", default="codebook.json")
            structure = float(typer.prompt("Structure (0..1)", default="0.2"))
            seed = int(typer.prompt("Seed", default="42"))
            typer.echo("Paste text (end with empty line):")
            lines = []
            import sys as _sys
            while True:
                line = _sys.stdin.readline()
                if not line or line.strip() == "":
                    break
                lines.append(line.rstrip("\n"))
            text = "\n".join(lines) or typer.prompt("Or paste a single line")
            cb = Codebook.load(codebook_path)
            emergent = encode_core(text, cb, structure=structure, seed=seed)
            print("\n--- emergent ---\n"+emergent+"\n---------------\n")
        elif choice == "3":
            codebook_path = typer.prompt("Path to codebook.json", default="codebook.json")
            typer.echo("Paste emergent text (end with empty line):")
            lines = []
            import sys as _sys
            while True:
                line = _sys.stdin.readline()
                if not line or line.strip() == "":
                    break
                lines.append(line.rstrip("\n"))
            emergent = "\n".join(lines) or typer.prompt("Or paste a single line")
            cb = Codebook.load(codebook_path)
            plain = decode_core(emergent, cb)
            print("\n--- decoded ---\n"+plain+"\n--------------\n")
        else:
            typer.echo("Enter 1/2/3 or q")

if __name__ == "__main__":
    app()
