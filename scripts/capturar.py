"""Captura guiada de letras estáticas y dinámicas.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\capturar.py --letra A
    .\\.venv\\Scripts\\python.exe scripts\\capturar.py --letra J
    .\\.venv\\Scripts\\python.exe scripts\\capturar.py --letra N_TILDE --firmante S02

Teclas:
    ESPACIO   iniciar / repetir la captura
    Q / ESC   salir
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from _path import asegurar_src

asegurar_src()

from tlsm.camera import abrir_camara, cerrar, leer  # noqa: E402
from tlsm.capture import CapturadorDinamico, CapturadorEstatico, EstadoCaptura  # noqa: E402
from tlsm.config import (  # noqa: E402
    CONFIG,
    DATA_RAW,
    LETRAS,
    MODELO_MANOS,
    ConfigCamara,
    es_dinamica,
)
from tlsm.datasets import Metadatos, guardar_dinamico, guardar_estatico  # noqa: E402
from tlsm.landmarks import CONEXIONES_MANOS, FuenteManos  # noqa: E402

FUENTE = cv2.FONT_HERSHEY_SIMPLEX
VERDE = (80, 220, 120)
AMARILLO = (60, 210, 240)
ROJO = (80, 80, 230)


def etiqueta_canonica(texto: str) -> str:
    limpio = texto.strip().upper().replace("Ñ", "N_TILDE")
    if limpio in LETRAS:
        return limpio
    raise SystemExit(f"Letra invalida: {texto}. Opciones: {', '.join(LETRAS)}")


def dibujar_mano(frame: np.ndarray, puntos: np.ndarray) -> None:
    alto, ancho = frame.shape[:2]
    coords = [(int(np.clip(x, 0, 1) * ancho), int(np.clip(y, 0, 1) * alto)) for x, y, _ in puntos]
    for a, b in CONEXIONES_MANOS:
        cv2.line(frame, coords[a], coords[b], VERDE, 2, cv2.LINE_AA)
    for x, y in coords:
        cv2.circle(frame, (x, y), 4, (255, 255, 255), -1, cv2.LINE_AA)


def barra(frame: np.ndarray, progreso: float, color) -> None:
    alto, ancho = frame.shape[:2]
    x0, x1 = 40, ancho - 40
    y = alto - 46
    cv2.rectangle(frame, (x0, y), (x1, y + 16), (60, 60, 60), -1)
    cv2.rectangle(frame, (x0, y), (x0 + int((x1 - x0) * progreso), y + 16), color, -1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Captura guiada de letras LSM")
    parser.add_argument("--letra", required=True)
    parser.add_argument("--sesion", default=datetime.now().strftime("%Y-%m-%d_%H%M"))
    parser.add_argument("--firmante", default="S01")
    parser.add_argument("--camara", type=int, default=CONFIG.camara.indice)
    parser.add_argument("--muestras", type=int, default=None, help="Solo captura estatica")
    parser.add_argument("--frames", type=int, default=None, help="Solo captura dinamica")
    parser.add_argument("--fps", type=float, default=None, help="Solo captura dinamica")
    parser.add_argument("--notas", default="")
    args = parser.parse_args()

    etiqueta = etiqueta_canonica(args.letra)
    dinamica = es_dinamica(etiqueta)

    cfg_camara = ConfigCamara(indice=args.camara)
    captura = abrir_camara(cfg_camara)
    if not captura.isOpened():
        print(f"No se pudo abrir la camara {args.camara}.")
        return 1

    if dinamica:
        capturador = CapturadorDinamico(
            etiqueta, CONFIG.captura, CONFIG.features, frames=args.frames, fps=args.fps
        )
    else:
        capturador = CapturadorEstatico(
            etiqueta, CONFIG.captura, CONFIG.features, muestras=args.muestras
        )

    meta = Metadatos(
        sesion=args.sesion,
        firmante=args.firmante,
        camara=f"camara_{args.camara}",
        notas=args.notas,
    )
    directorio = DATA_RAW / args.sesion

    iniciado = False
    pendiente_dinamica: float | None = None
    guardado: Path | None = None

    print(f"Letra: {etiqueta} ({'dinamica' if dinamica else 'estatica'})")
    print(f"Sesion: {args.sesion}  Firmante: {args.firmante}")
    print("ESPACIO inicia. Q sale.")

    try:
        with FuenteManos(modelo=MODELO_MANOS, max_manos=1) as fuente:
            while True:
                ok, frame = leer(captura, espejo=cfg_camara.espejo)
                if not ok:
                    print("No se pudo leer un frame.")
                    break

                detecciones = fuente.detectar_bgr(frame)
                deteccion = detecciones[0] if detecciones else None
                if deteccion is not None:
                    dibujar_mano(frame, deteccion.puntos)

                ahora = time.monotonic()
                estado: EstadoCaptura | None = None

                if iniciado and pendiente_dinamica is not None:
                    restante = pendiente_dinamica - ahora
                    if deteccion is None:
                        pendiente_dinamica = ahora + CONFIG.captura.cuenta_regresiva_s
                        estado = EstadoCaptura(
                            "cuenta",
                            "Muestra la mano para continuar",
                            cuenta=max(1, int(np.ceil(CONFIG.captura.cuenta_regresiva_s))),
                            total=capturador.frames,
                        )
                    elif restante <= 0:
                        capturador.iniciar(ahora)
                        pendiente_dinamica = None
                    else:
                        cuenta = max(1, int(np.ceil(restante)))
                        estado = EstadoCaptura(
                            "cuenta",
                            f"Preparate... {cuenta}",
                            cuenta=cuenta,
                            total=capturador.frames,
                        )

                if iniciado and estado is None:
                    if deteccion is None:
                        estado = capturador.actualizar(None, ahora=ahora)
                    else:
                        estado = capturador.actualizar(
                            deteccion.puntos, deteccion.mano, ahora=ahora
                        )

                # Guardar una sola vez al terminar.
                if estado is not None and estado.fase == "listo" and guardado is None:
                    if isinstance(capturador, CapturadorDinamico):
                        X, raw, fps = capturador.resultado()
                        guardado = guardar_dinamico(directorio, etiqueta, X, raw, fps, meta)
                    else:
                        X, raw = capturador.resultado()
                        guardado = guardar_estatico(directorio, etiqueta, X, raw, meta)
                    print(f"Guardado: {guardado}")

                # HUD
                cv2.rectangle(frame, (0, 0), (frame.shape[1], 92), (20, 20, 24), -1)
                cv2.putText(
                    frame,
                    f"Letra: {etiqueta}",
                    (24, 36),
                    FUENTE,
                    0.9,
                    VERDE,
                    2,
                    cv2.LINE_AA,
                )
                if not iniciado:
                    cv2.putText(
                        frame,
                        "ESPACIO para iniciar  |  Q salir",
                        (24, 72),
                        FUENTE,
                        0.65,
                        (220, 220, 220),
                        2,
                        cv2.LINE_AA,
                    )
                elif estado is not None:
                    color = AMARILLO if guardado is None else VERDE
                    cv2.putText(
                        frame,
                        estado.mensaje,
                        (24, 72),
                        FUENTE,
                        0.65,
                        color,
                        2,
                        cv2.LINE_AA,
                    )
                    barra(frame, estado.progreso, color)
                    cv2.putText(
                        frame,
                        f"{estado.muestras}/{estado.total}",
                        (40, frame.shape[0] - 58),
                        FUENTE,
                        0.55,
                        (200, 200, 200),
                        1,
                        cv2.LINE_AA,
                    )
                if guardado is not None:
                    cv2.putText(
                        frame,
                        "Guardado. ESPACIO para otra ronda, Q para salir",
                        (24, frame.shape[0] - 80),
                        FUENTE,
                        0.6,
                        VERDE,
                        2,
                        cv2.LINE_AA,
                    )

                cv2.imshow(f"TLSM captura - {etiqueta}", frame)
                tecla = cv2.waitKey(1) & 0xFF
                if tecla in (27, ord("q")):
                    break
                if tecla == ord(" "):
                    guardado = None
                    iniciado = True
                    if isinstance(capturador, CapturadorDinamico):
                        pendiente_dinamica = time.monotonic() + CONFIG.captura.cuenta_regresiva_s
                    else:
                        pendiente_dinamica = None
                        capturador.iniciar(time.monotonic())
    finally:
        cerrar(captura)
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
