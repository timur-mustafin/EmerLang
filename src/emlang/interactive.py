def main():
    from .cli import interactive
    import typer
    typer.run(interactive)
