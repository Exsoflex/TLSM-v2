"""Abre la aplicación de escritorio.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\app.py
    .\\.venv\\Scripts\\python.exe scripts\\app.py --sin-voz
"""

from __future__ import annotations

from _path import asegurar_src

asegurar_src()

from tlsm.ui import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
