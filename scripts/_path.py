"""Utilidad compartida por los scripts: permite ejecutarlos sin instalar el paquete."""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def asegurar_src() -> Path:
    src = str(RAIZ / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    return RAIZ
