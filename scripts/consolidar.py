"""Consolida las sesiones capturadas en los datasets de entrenamiento.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\consolidar.py
    .\\.venv\\Scripts\\python.exe scripts\\consolidar.py --salida-dir data/processed
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from _path import RAIZ, asegurar_src

asegurar_src()

from tlsm.config import DATA_RAW  # noqa: E402
from tlsm.datasets import (  # noqa: E402
    combinar_dinamicos,
    combinar_estaticos,
    guardar_procesado,
    resumen_etiquetas,
)


def _concatenar(partes: list[dict]) -> dict:
    if not partes:
        raise ValueError("No hay sesiones para consolidar")
    claves = set(partes[0])
    for parte in partes[1:]:
        claves &= set(parte)
    resultado = {}
    for clave in claves:
        if clave == "fps":
            valores = {round(float(p[clave]), 3) for p in partes}
            if len(valores) > 1:
                raise ValueError(f"FPS inconsistentes entre sesiones: {sorted(valores)}")
            resultado[clave] = partes[0][clave]
        else:
            resultado[clave] = np.concatenate([p[clave] for p in partes])
    return resultado


def main() -> int:
    parser = argparse.ArgumentParser(description="Consolida data/raw en data/processed")
    parser.add_argument("--raw", type=Path, default=DATA_RAW)
    parser.add_argument("--salida-dir", type=Path, default=RAIZ / "data" / "processed")
    args = parser.parse_args()

    sesiones = sorted(p for p in args.raw.glob("*") if p.is_dir())
    if not sesiones:
        print(f"No hay sesiones en {args.raw}")
        return 1

    estaticos = [combinar_estaticos(s) for s in sesiones if any(s.glob("static_*.npz"))]
    dinamicos = [combinar_dinamicos(s) for s in sesiones if any(s.glob("dynamic_*.npz"))]

    if not estaticos and not dinamicos:
        print("Las sesiones no contienen datos static_*.npz ni dynamic_*.npz")
        return 1

    args.salida_dir.mkdir(parents=True, exist_ok=True)

    if estaticos:
        datos = _concatenar(estaticos)
        ruta = guardar_procesado(
            args.salida_dir / "static_v2.npz",
            datos["X"],
            datos["y"],
            datos["sesion"],
            datos["firmante"],
            raw=datos["raw"],
        )
        print(f"Estatico: {len(datos['X'])} muestras -> {ruta}")
        print(f"  clases: {resumen_etiquetas(datos['y'])}")
        print(f"  firmantes: {sorted(set(datos['firmante']))}")

    if dinamicos:
        datos = _concatenar(dinamicos)
        ruta = guardar_procesado(
            args.salida_dir / "dynamic_v2.npz",
            datos["X"],
            datos["y"],
            datos["sesion"],
            datos["firmante"],
            raw=datos["raw"],
            fps=datos["fps"],
        )
        print(f"Dinamico: {len(datos['X'])} secuencias -> {ruta}")
        print(f"  clases: {resumen_etiquetas(datos['y'])}")
        print(f"  firmantes: {sorted(set(datos['firmante']))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
