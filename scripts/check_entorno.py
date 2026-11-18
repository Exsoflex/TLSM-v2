"""Verifica que el entorno del proyecto esté completo.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\check_entorno.py
    .\\.venv\\Scripts\\python.exe scripts\\check_entorno.py --sin-camara
"""

from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MODELO_MANOS = RAIZ / "assets" / "mediapipe" / "hand_landmarker.task"

FALLOS: list[str] = []
AVISOS: list[str] = []


def titulo(texto: str) -> None:
    print(f"\n== {texto} " + "=" * max(0, 58 - len(texto)))


def revisar_import(nombre: str, modulo: str) -> object | None:
    try:
        import importlib

        paquete = importlib.import_module(modulo)
        version = getattr(paquete, "__version__", "?")
        print(f"  [OK]   {nombre:<12} {version}")
        return paquete
    except Exception as exc:  # noqa: BLE001 - reportamos cualquier fallo
        print(f"  [FALLA] {nombre:<12} {type(exc).__name__}: {exc}")
        FALLOS.append(f"{nombre}: {exc}")
        return None


def revisar_modelos(cv2_mod: object | None, mp_mod: object | None) -> None:
    titulo("Modelo de MediaPipe")
    if not MODELO_MANOS.exists():
        print(f"  [FALLA] No existe {MODELO_MANOS}")
        FALLOS.append("falta hand_landmarker.task")
        return

    print(f"  [OK]   {MODELO_MANOS.name} ({MODELO_MANOS.stat().st_size / 1_048_576:.1f} MB)")

    if cv2_mod is None or mp_mod is None:
        return

    try:
        import numpy as np
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        opciones = vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(MODELO_MANOS)),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=1,
        )
        with vision.HandLandmarker.create_from_options(opciones) as detector:
            imagen = mp_mod.Image(
                image_format=mp_mod.ImageFormat.SRGB,
                data=np.zeros((64, 64, 3), dtype=np.uint8),
            )
            resultado = detector.detect(imagen)
        print(f"  [OK]   Modelo cargado (manos en imagen vacía: {len(resultado.hand_landmarks)})")
    except Exception as exc:  # noqa: BLE001
        print(f"  [FALLA] No se pudo cargar el modelo: {type(exc).__name__}: {exc}")
        FALLOS.append(f"modelo: {exc}")


def revisar_camaras(cv2_mod: object | None, maximo: int = 4) -> None:
    titulo("Cámaras")
    if cv2_mod is None:
        return

    encontradas = 0
    for indice in range(maximo):
        captura = None
        try:
            backend = cv2_mod.CAP_DSHOW if sys.platform.startswith("win") else 0
            captura = cv2_mod.VideoCapture(indice, backend) if backend else cv2_mod.VideoCapture(indice)
            if not captura.isOpened():
                continue
            ok, frame = captura.read()
            if ok and frame is not None:
                alto, ancho = frame.shape[:2]
                print(f"  [OK]   Cámara {indice}: {ancho}x{alto}")
                encontradas += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  [AVISO] Cámara {indice}: {type(exc).__name__}: {exc}")
        finally:
            if captura is not None:
                captura.release()

    if encontradas == 0:
        print("  [AVISO] No se detectó ninguna cámara (puede estar en uso por otra app).")
        AVISOS.append("sin cámaras detectadas")
    else:
        print(f"  Cámaras disponibles: {encontradas}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Revisa el entorno de TLSM")
    parser.add_argument("--sin-camara", action="store_true", help="No probar las cámaras")
    args = parser.parse_args()

    titulo("Sistema")
    print(f"  Python   {sys.version.split()[0]}")
    print(f"  Sistema  {platform.platform()}")
    print(f"  Proyecto {RAIZ}")

    titulo("Dependencias")
    cv2_mod = revisar_import("opencv", "cv2")
    mp_mod = revisar_import("mediapipe", "mediapipe")
    revisar_import("numpy", "numpy")
    revisar_import("pandas", "pandas")
    revisar_import("sklearn", "sklearn")
    revisar_import("joblib", "joblib")
    revisar_import("pyttsx3", "pyttsx3")

    if mp_mod is not None and not hasattr(mp_mod, "solutions"):
        print("  [INFO] API legacy 'mp.solutions' no disponible (MediaPipe >= 1.0).")
        print("         El código nuevo debe usar 'mediapipe.tasks'.")

    revisar_modelos(cv2_mod, mp_mod)

    if not args.sin_camara:
        revisar_camaras(cv2_mod)

    titulo("Resultado")
    if FALLOS:
        print(f"  {len(FALLOS)} fallo(s): el entorno NO está listo.")
        for fallo in FALLOS:
            print(f"   - {fallo}")
        return 1

    if AVISOS:
        print(f"  Entorno listo con {len(AVISOS)} aviso(s).")
        for aviso in AVISOS:
            print(f"   - {aviso}")
        return 0

    print("  Entorno listo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
