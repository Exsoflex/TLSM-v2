"""Interfaz de escritorio del traductor (OpenCV).

Es un adaptador: toda la lógica vive en el núcleo. La versión web reutilizará los
mismos módulos y solo cambiará esta capa.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2
import numpy as np

from .camera import abrir_camara, cerrar, leer
from .config import (
    CONFIG,
    MODELO_DINAMICO,
    MODELO_ESTATICO,
    ConfigCamara,
    display_ascii,
)
from .landmarks import CONEXIONES_MANOS, FrameLandmarks, FuenteManos
from .model_io import cargar_modelo
from .recognize import Evento, Reconocedor
from .text import CompositorTexto
from .voice import VozNula, VozPyttsx3

FONDO = (32, 32, 38)
TEXTO = (240, 240, 240)
TEXTO_SUAVE = (170, 170, 180)
VERDE = (80, 220, 120)
AMARILLO = (60, 210, 240)
ROJO = (80, 80, 230)
AZUL = (230, 170, 60)

FUENTE = cv2.FONT_HERSHEY_SIMPLEX


# ---------------------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------------------


def _envolver(texto: str, ancho: int, escala: float = 0.75, grosor: int = 2) -> list[str]:
    def cabe(cadena: str) -> bool:
        return cv2.getTextSize(cadena, FUENTE, escala, grosor)[0][0] <= ancho

    if not texto:
        return [""]

    lineas: list[str] = []
    actual = ""
    for palabra in texto.split(" "):
        prueba = f"{actual} {palabra}" if actual else palabra
        if cabe(prueba):
            actual = prueba
            continue
        if actual:
            lineas.append(actual)
        resto = palabra
        while not cabe(resto):
            corte = len(resto)
            while corte > 1 and not cabe(resto[:corte]):
                corte -= 1
            lineas.append(resto[:corte])
            resto = resto[corte:]
        actual = resto
    if actual or not lineas:
        lineas.append(actual)
    return lineas


def _dibujar_mano(
    frame: np.ndarray, deteccion: FrameLandmarks, color: tuple[int, int, int]
) -> None:
    alto, ancho = frame.shape[:2]
    puntos = [
        (int(np.clip(x, 0.0, 1.0) * ancho), int(np.clip(y, 0.0, 1.0) * alto))
        for x, y, _ in deteccion.puntos
    ]
    for a, b in CONEXIONES_MANOS:
        cv2.line(frame, puntos[a], puntos[b], color, 2, cv2.LINE_AA)
    for x, y in puntos:
        cv2.circle(frame, (x, y), 4, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (x, y), 4, color, 1, cv2.LINE_AA)


def _dibujar_panel(
    alto: int,
    texto: str,
    prediccion: str,
    confianza: float,
    fps: float,
    mano: bool,
    estado_modelos: str,
    aviso: str,
) -> np.ndarray:
    ancho = CONFIG.ui.ancho_panel
    panel = np.full((alto, ancho, 3), FONDO, dtype=np.uint8)

    cv2.putText(panel, "TLSM", (18, 40), FUENTE, 1.1, TEXTO, 2, cv2.LINE_AA)
    cv2.putText(
        panel,
        "Lengua de Senas Mexicanas",
        (18, 66),
        FUENTE,
        0.52,
        TEXTO_SUAVE,
        1,
        cv2.LINE_AA,
    )
    cv2.line(panel, (18, 80), (ancho - 18, 80), (70, 70, 80), 1)

    # Texto reconocido
    cv2.putText(panel, "TEXTO", (18, 112), FUENTE, 0.55, TEXTO_SUAVE, 1, cv2.LINE_AA)
    lineas = _envolver(texto, ancho - 40, escala=0.78, grosor=2)
    for i, linea in enumerate(lineas[-4:]):
        cv2.putText(
            panel,
            linea,
            (18, 150 + i * 34),
            FUENTE,
            0.78,
            TEXTO,
            2,
            cv2.LINE_AA,
        )
    if not texto:
        cv2.putText(
            panel,
            "Haz una senal...",
            (18, 150),
            FUENTE,
            0.6,
            (110, 110, 120),
            1,
            cv2.LINE_AA,
        )

    # Predicción actual
    y = 320
    cv2.line(panel, (18, y - 28), (ancho - 18, y - 28), (70, 70, 80), 1)
    cv2.putText(panel, "SENAL ACTUAL", (18, y), FUENTE, 0.55, TEXTO_SUAVE, 1, cv2.LINE_AA)
    if prediccion:
        cv2.putText(
            panel, display_ascii(prediccion), (18, y + 52), FUENTE, 1.6, VERDE, 3, cv2.LINE_AA
        )
        cv2.putText(
            panel,
            f"{confianza * 100:5.1f}%",
            (130, y + 52),
            FUENTE,
            0.9,
            VERDE,
            2,
            cv2.LINE_AA,
        )
    else:
        cv2.putText(panel, "--", (18, y + 52), FUENTE, 1.4, (100, 100, 110), 2, cv2.LINE_AA)

    # Estado
    color_mano = VERDE if mano else ROJO
    cv2.circle(panel, (26, y + 92), 6, color_mano, -1, cv2.LINE_AA)
    cv2.putText(
        panel,
        "mano detectada" if mano else "sin mano",
        (40, y + 98),
        FUENTE,
        0.55,
        TEXTO_SUAVE,
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        panel,
        f"{fps:4.1f} FPS",
        (ancho - 120, y + 98),
        FUENTE,
        0.55,
        TEXTO_SUAVE,
        1,
        cv2.LINE_AA,
    )

    cv2.putText(panel, estado_modelos, (18, alto - 74), FUENTE, 0.45, TEXTO_SUAVE, 1, cv2.LINE_AA)
    if aviso:
        cv2.putText(panel, aviso, (18, alto - 52), FUENTE, 0.45, AMARILLO, 1, cv2.LINE_AA)

    cv2.putText(
        panel,
        "ESPACIO  B borrar  C limpiar  V hablar  L puntos  Q salir",
        (18, alto - 20),
        FUENTE,
        0.42,
        (150, 150, 160),
        1,
        cv2.LINE_AA,
    )
    return panel


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


def ejecutar(args: argparse.Namespace) -> int:
    cfg_camara = ConfigCamara(
        indice=args.camara,
        ancho=args.ancho,
        alto=args.alto,
        espejo=not args.sin_espejo,
    )
    captura = abrir_camara(cfg_camara)
    if not captura.isOpened():
        print(f"No se pudo abrir la camara {args.camara}.")
        return 1

    estado_modelos = []
    paquete_estatico = None
    paquete_dinamico = None
    if not args.sin_modelo:
        try:
            paquete_estatico = cargar_modelo(args.modelo)
            estado_modelos.append(f"estatico: {len(paquete_estatico.etiquetas)} clases")
        except FileNotFoundError:
            estado_modelos.append("estatico: sin modelo")
        try:
            paquete_dinamico = cargar_modelo(args.modelo_dinamico)
            estado_modelos.append(f"dinamico: {len(paquete_dinamico.etiquetas)} clases")
        except FileNotFoundError:
            estado_modelos.append("dinamico: sin modelo")

    reconocedor = Reconocedor(
        paquete_estatico, paquete_dinamico, CONFIG.reconocimiento, CONFIG.features
    )
    compositor = CompositorTexto(CONFIG.reconocimiento)

    voz = VozNula() if args.sin_voz else VozPyttsx3(CONFIG.voz)
    aviso = "" if voz.disponible or args.sin_voz else "Voz no disponible"

    mostrar_puntos = CONFIG.ui.mostrar_landmarks
    ultima: Evento | None = None
    ultima_ts = 0.0
    fps = 0.0
    anterior = time.perf_counter()
    aviso_hasta = time.monotonic() + 4.0

    try:
        with FuenteManos(modelo=args.modelo_manos, max_manos=args.max_manos) as fuente:
            while True:
                ok, frame = leer(captura, espejo=not args.sin_espejo)
                if not ok:
                    print("No se pudo leer un frame de la camara.")
                    break

                detecciones = fuente.detectar_bgr(frame)
                deteccion = detecciones[0] if detecciones else None

                if deteccion is not None and mostrar_puntos:
                    color = AZUL if deteccion.mano == "Left" else VERDE
                    _dibujar_mano(frame, deteccion, color)

                for evento in reconocedor.actualizar(deteccion):
                    if compositor.agregar_evento(evento.etiqueta):
                        ultima = evento
                        ultima_ts = time.monotonic()
                    else:
                        ultima = evento
                        ultima_ts = time.monotonic()

                compositor.actualizar_mano(deteccion is not None)

                ahora = time.perf_counter()
                delta = max(ahora - anterior, 1e-6)
                fps = 0.9 * fps + 0.1 * (1.0 / delta) if fps else 1.0 / delta
                anterior = ahora

                prediccion = ""
                confianza = 0.0
                if ultima is not None and time.monotonic() - ultima_ts < 1.2:
                    prediccion = ultima.etiqueta
                    confianza = ultima.confianza

                frame = cv2.resize(frame, (CONFIG.ui.alto * 4 // 3, CONFIG.ui.alto))
                panel = _dibujar_panel(
                    CONFIG.ui.alto,
                    compositor.texto,
                    prediccion,
                    confianza,
                    fps,
                    deteccion is not None,
                    " | ".join(estado_modelos) or "sin modelos",
                    aviso if time.monotonic() < aviso_hasta else "",
                )
                cv2.imshow("TLSM", np.hstack([frame, panel]))

                tecla = cv2.waitKey(1) & 0xFF
                if tecla in (27, ord("q")):
                    break
                if tecla == ord(" "):
                    compositor.espacio()
                elif tecla in (8, 127):
                    compositor.borrar()
                elif tecla == ord("c"):
                    compositor.limpiar()
                elif tecla == ord("v"):
                    voz.decir(compositor.texto)
                elif tecla == ord("l"):
                    mostrar_puntos = not mostrar_puntos
                elif tecla == ord("r"):
                    reconocedor.reiniciar()
    finally:
        cerrar(captura)
        cv2.destroyAllWindows()
        voz.cerrar()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TLSM - traductor de Lengua de Senas Mexicanas")
    parser.add_argument("--camara", type=int, default=CONFIG.camara.indice)
    parser.add_argument("--ancho", type=int, default=CONFIG.camara.ancho)
    parser.add_argument("--alto", type=int, default=CONFIG.camara.alto)
    parser.add_argument("--max-manos", type=int, default=1)
    parser.add_argument("--modelo", type=Path, default=MODELO_ESTATICO)
    parser.add_argument("--modelo-dinamico", type=Path, default=MODELO_DINAMICO)
    parser.add_argument("--modelo-manos", type=Path, default=None)
    parser.add_argument("--sin-voz", action="store_true")
    parser.add_argument("--sin-espejo", action="store_true")
    parser.add_argument(
        "--sin-modelo", action="store_true", help="Solo detectar manos, sin clasificar"
    )
    args = parser.parse_args(argv)

    if args.modelo_manos is None:
        from .config import MODELO_MANOS

        args.modelo_manos = MODELO_MANOS
    return ejecutar(args)


if __name__ == "__main__":
    raise SystemExit(main())
