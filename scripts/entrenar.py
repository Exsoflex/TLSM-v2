"""Entrena y evalúa el clasificador estático o dinámico.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\entrenar.py --tipo estatico
    .\\.venv\\Scripts\\python.exe scripts\\entrenar.py --tipo dinamico --split bloque

Antes hay que convertir los datos v1:
    .\\.venv\\Scripts\\python.exe scripts\\importar_v1.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from _path import RAIZ, asegurar_src

asegurar_src()

from tlsm.config import MODELO_DINAMICO, MODELO_ESTATICO  # noqa: E402
from tlsm.datasets import cargar_procesado, resumen_etiquetas  # noqa: E402
from tlsm.model_io import guardar_modelo  # noqa: E402
from tlsm.train import MODOS_SPLIT, entrenar, guardar_reporte, resumen_texto  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Entrena un modelo TLSM")
    parser.add_argument("--tipo", choices=("estatico", "dinamico"), default="estatico")
    parser.add_argument("--datos", type=Path, default=None)
    parser.add_argument("--salida", type=Path, default=None)
    parser.add_argument("--split", choices=MODOS_SPLIT, default="auto")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sin-reporte", action="store_true")
    args = parser.parse_args()

    datos = args.datos or (
        RAIZ
        / "data"
        / "processed"
        / ("static_v2.npz" if args.tipo == "estatico" else "dynamic_v2.npz")
    )
    if not datos.exists():
        print(f"No existe el dataset: {datos}")
        print(
            "Ejecuta primero: python scripts/consolidar.py "
            "(o scripts/importar_v1.py si aún no importaste la v1)"
        )
        return 1

    datos_npz = cargar_procesado(datos)
    print(f"Dataset: {datos}")
    print(f"  muestras: {len(datos_npz['X'])}  clases: {resumen_etiquetas(datos_npz['y'])}")
    print(f"  sesiones: {sorted(set(datos_npz['sesion']))}")

    if args.split == "aleatorio":
        print("ADVERTENCIA: el split aleatorio mezcla frames consecutivos y da metricas falsas.")

    paquete, metricas = entrenar(
        datos_npz["X"],
        datos_npz["y"],
        datos_npz["sesion"],
        tipo=args.tipo,
        modo_split=args.split,
        test_size=args.test_size,
        seed=args.seed,
    )

    salida = args.salida or (MODELO_ESTATICO if args.tipo == "estatico" else MODELO_DINAMICO)
    guardar_modelo(salida, paquete)
    print()
    print(resumen_texto(metricas))
    print(f"\nModelo guardado en: {salida}")

    if not args.sin_reporte:
        json_path, png_path = guardar_reporte(metricas, args.tipo)
        print(f"Reporte: {json_path}")
        print(f"Matriz:  {png_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
