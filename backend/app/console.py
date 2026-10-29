import io
import sys


def use_utf8_output() -> None:
    """En Windows, la salida redirigida (tuberías, Git Bash) no usa UTF-8 por defecto."""
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
