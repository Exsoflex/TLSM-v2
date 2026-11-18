"""Adaptador de cámara para escritorio (OpenCV)."""

from __future__ import annotations

import sys

import cv2

from .config import ConfigCamara


def abrir_camara(cfg: ConfigCamara | None = None) -> cv2.VideoCapture:
    """Abre la cámara con backends razonables en Windows y fallback genérico."""
    cfg = cfg or ConfigCamara()
    backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else 0
    captura = cv2.VideoCapture(cfg.indice, backend) if backend else cv2.VideoCapture(cfg.indice)
    if not captura.isOpened() and backend:
        captura.release()
        captura = cv2.VideoCapture(cfg.indice)
    captura.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.ancho)
    captura.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.alto)
    captura.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return captura


def leer(captura: cv2.VideoCapture, espejo: bool = True):
    """Lee un frame; devuelve (ok, frame) y aplica espejo si se pide."""
    ok, frame = captura.read()
    if ok and espejo:
        frame = cv2.flip(frame, 1)
    return ok, frame


def cerrar(captura: cv2.VideoCapture) -> None:
    if captura is not None:
        captura.release()


__all__ = ["abrir_camara", "cerrar", "leer"]
