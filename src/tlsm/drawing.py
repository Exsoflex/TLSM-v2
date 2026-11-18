"""Utilidades de dibujo compartidas por las interfaces OpenCV.

Es parte de la capa de presentación: el núcleo de reconocimiento no importa este
módulo. Se separó de `ui.py` para reutilizarlo en la interfaz de captura.
"""

from __future__ import annotations

import cv2
import numpy as np

from .landmarks import CONEXIONES_MANOS

FUENTE = cv2.FONT_HERSHEY_SIMPLEX


def envolver_texto(texto: str, ancho: int, escala: float = 0.75, grosor: int = 2) -> list[str]:
    """Divide el texto en líneas que caben en `ancho` píxeles."""

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


def dibujar_mano(
    frame: np.ndarray,
    puntos: np.ndarray,
    color: tuple[int, int, int],
    grosor: int = 2,
    radio: int = 4,
) -> None:
    """Dibuja los 21 landmarks y sus conexiones sobre un frame BGR."""
    alto, ancho = frame.shape[:2]
    coords = [
        (int(np.clip(x, 0.0, 1.0) * ancho), int(np.clip(y, 0.0, 1.0) * alto))
        for x, y, _ in np.asarray(puntos)
    ]
    for a, b in CONEXIONES_MANOS:
        cv2.line(frame, coords[a], coords[b], color, grosor, cv2.LINE_AA)
    for x, y in coords:
        cv2.circle(frame, (x, y), radio, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (x, y), radio, color, 1, cv2.LINE_AA)


def barra_progreso(
    frame: np.ndarray,
    x: int,
    y: int,
    ancho: int,
    alto: int,
    progreso: float,
    color: tuple[int, int, int],
    fondo: tuple[int, int, int] = (60, 60, 70),
) -> None:
    progreso = float(np.clip(progreso, 0.0, 1.0))
    cv2.rectangle(frame, (x, y), (x + ancho, y + alto), fondo, -1)
    if progreso > 0:
        cv2.rectangle(
            frame,
            (x, y),
            (x + int(ancho * progreso), y + alto),
            color,
            -1,
        )


__all__ = ["FUENTE", "barra_progreso", "dibujar_mano", "envolver_texto"]
