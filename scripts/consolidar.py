"""Consolida las sesiones capturadas en los datasets de entrenamiento.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\consolidar.py
    .\\.venv\\Scripts\\python.exe scripts\\consolidar.py --desde-cero

Por defecto **suma** las sesiones de `data/raw` al dataset procesado existente.
Si una sesión ya estaba consolidada, la reemplaza completa (no la duplica), así
que se puede ejecutar varias veces sin miedo. Los datos importados de la v1 se
conservan porque no viven en `data/raw`.

Con `--desde-cero` se ignora el dataset procesado anterior y se reconstruye solo
con lo que haya en `data/raw`. Úsalo únicamente si quieres descartar la v1.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from _path import RAIZ, asegurar_src

asegurar_src()

from tlsm.config import DATA_RAW  # noqa: E402
from tlsm.datasets import (  # noqa: E402
    cargar_procesado,
    combinar_dinamicos,
    combinar_estaticos,
    guardar_procesado,
    mezclar_procesado,
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


def _procesado_previo(ruta: Path, desde_cero: bool) -> dict | None:
    if desde_cero or not ruta.exists():
        return None
    return cargar_procesado(ruta)


def main() -> int:
    parser = argparse.ArgumentParser(description="Consolida data/raw en data/processed")
    parser.add_argument("--raw", type=Path, default=DATA_RAW)
    parser.add_argument("--salida-dir", type=Path, default=RAIZ / "data" / "processed")
    parser.add_argument(
        "--desde-cero",
        action="store_true",
        help="Ignora el dataset procesado previo y reconstruye solo con data/raw",
    )
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
        ruta = args.salida_dir / "static_v2.npz"
        datos = mezclar_procesado(
            _procesado_previo(ruta, args.desde_cero),
            _concatenar(estaticos),
        )
        ruta = guardar_procesado(
            ruta,
            datos["X"],
            datos["y"],
            datos["sesion"],
            datos["firmante"],
            raw=datos.get("raw"),
        )
        print(f"Estatico: {len(datos['X'])} muestras -> {ruta}")
        print(f"  clases: {resumen_etiquetas(datos['y'])}")
        print(f"  firmantes: {sorted(set(datos['firmante']))}")
        print(f"  sesiones: {sorted(set(datos['sesion']))}")

    if dinamicos:
        ruta = args.salida_dir / "dynamic_v2.npz"
        datos = mezclar_procesado(
            _procesado_previo(ruta, args.desde_cero),
            _concatenar(dinamicos),
        )
        ruta = guardar_procesado(
            ruta,
            datos["X"],
            datos["y"],
            datos["sesion"],
            datos["firmante"],
            raw=datos.get("raw"),
            fps=datos.get("fps"),
        )
        print(f"Dinamico: {len(datos['X'])} secuencias -> {ruta}")
        print(f"  clases: {resumen_etiquetas(datos['y'])}")
        print(f"  firmantes: {sorted(set(datos['firmante']))}")
        print(f"  sesiones: {sorted(set(datos['sesion']))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
