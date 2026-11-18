"""Interfaz gráfica de captura guiada del abecedario LSM.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\capturar_ui.py
    .\\.venv\\Scripts\\python.exe scripts\\capturar_ui.py --firmante S01 --sesion 2026-11-18_01
    .\\.venv\\Scripts\\python.exe scripts\\capturar_ui.py --letras A,B,C,J --rondas 3
    .\\.venv\\Scripts\\python.exe scripts\\capturar_ui.py --solo-faltantes

La app guarda automáticamente en data/raw/<sesion>/ y retoma el progreso si
vuelves a abrir la misma sesión.
"""

from __future__ import annotations

from _path import asegurar_src

asegurar_src()

from tlsm.capture_ui import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
