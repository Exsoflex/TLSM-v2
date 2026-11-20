"""Convierte los datasets de la v1 al esquema v2.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\importar_v1.py
    .\\.venv\\Scripts\\python.exe scripts\\importar_v1.py --sin-dinamico
"""

from __future__ import annotations

import argparse
from pathlib import Path

from _path import RAIZ, asegurar_src

asegurar_src()

from tlsm.datasets import (  # noqa: E402
    cargar_procesado,
    guardar_procesado,
    importar_v1_dinamico,
    importar_v1_estatico,
    mezclar_procesado,
    resumen_etiquetas,
)


def _importar_y_mezclar(ruta, importar, *args, **kwargs) -> dict:
    """Importa la v1 conservando las sesiones que no sean de la v1."""
    previo = cargar_procesado(ruta) if ruta.exists() else None
    importar(*args, **kwargs)
    nuevo = cargar_procesado(ruta)
    datos = mezclar_procesado(previo, nuevo)
    guardar_procesado(
        ruta,
        datos["X"],
        datos["y"],
        datos["sesion"],
        datos["firmante"],
        raw=datos.get("raw"),
        fps=datos.get("fps"),
    )
    return datos


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa los datos v1 al esquema v2")
    parser.add_argument(
        "--estatico",
        type=Path,
        default=RAIZ / "legacy" / "v1" / "modelos" / "dataset_senas.csv",
    )
    parser.add_argument(
        "--dinamico",
        type=Path,
        default=RAIZ / "legacy" / "v1" / "modelos" / "dataset_movimiento.pkl",
    )
    parser.add_argument("--salida-dir", type=Path, default=RAIZ / "data" / "processed")
    parser.add_argument("--sin-dinamico", action="store_true")
    args = parser.parse_args()

    args.salida_dir.mkdir(parents=True, exist_ok=True)

    if not args.estatico.exists():
        print(f"No existe el CSV estatico: {args.estatico}")
        return 1
    salida_estatica = args.salida_dir / "static_v2.npz"
    datos = _importar_y_mezclar(
        salida_estatica, importar_v1_estatico, args.estatico, salida_estatica
    )
    print(f"Estatico: {len(datos['X'])} muestras -> {salida_estatica}")
    print(f"  features: {datos['X'].shape[1]}  clases: {resumen_etiquetas(datos['y'])}")

    if not args.sin_dinamico:
        if not args.dinamico.exists():
            print(f"No existe el PKL de movimiento: {args.dinamico}")
            return 1
        salida_dinamica = args.salida_dir / "dynamic_v2.npz"
        datos_din = _importar_y_mezclar(
            salida_dinamica, importar_v1_dinamico, args.dinamico, salida_dinamica
        )
        print(
            f"Dinamico: {len(datos_din['X'])} secuencias "
            f"{datos_din['X'].shape[1:]} -> {salida_dinamica}"
        )
        print(f"  clases: {resumen_etiquetas(datos_din['y'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
