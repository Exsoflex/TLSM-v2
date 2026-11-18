"""Fuente de landmarks de manos con MediaPipe Tasks.

Este es el único módulo que conoce MediaPipe para la parte de detección.
El resto del núcleo trabaja con arreglos de NumPy, lo que permite sustituir la
fuente (por ejemplo, MediaPipe WASM en la web o un archivo de video) sin tocar
la lógica de reconocimiento.
"""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from .config import MODELO_MANOS

CONEXIONES_MANOS: tuple[tuple[int, int], ...] = tuple(
    (c.start, c.end) for c in vision.HandLandmarksConnections.HAND_CONNECTIONS
)


@dataclass(frozen=True)
class FrameLandmarks:
    puntos: np.ndarray  # (21, 3), float32
    mano: str  # "Left", "Right" o "Unknown"
    confianza: float
    ts_ms: int


class FuenteManos:
    """Detector de manos con la API moderna de MediaPipe Tasks."""

    def __init__(
        self,
        modelo: Path | str = MODELO_MANOS,
        max_manos: int = 1,
        modo: str = "video",
        deteccion: float = 0.5,
        presencia: float = 0.5,
        seguimiento: float = 0.5,
    ) -> None:
        if modo not in {"video", "imagen"}:
            raise ValueError("modo debe ser 'video' o 'imagen'")
        modelo = Path(modelo)
        if not modelo.exists():
            raise FileNotFoundError(f"No existe el modelo de manos: {modelo}")

        self.modo = modo
        opciones = vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(modelo)),
            running_mode=vision.RunningMode.VIDEO if modo == "video" else vision.RunningMode.IMAGE,
            num_hands=max_manos,
            min_hand_detection_confidence=deteccion,
            min_hand_presence_confidence=presencia,
            min_tracking_confidence=seguimiento,
        )
        self._detector = vision.HandLandmarker.create_from_options(opciones)
        self._ultimo_ts = -1

    def detectar_bgr(self, frame_bgr: np.ndarray, ts_ms: int | None = None) -> list[FrameLandmarks]:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return self.detectar_rgb(rgb, ts_ms)

    def detectar_rgb(self, rgb: np.ndarray, ts_ms: int | None = None) -> list[FrameLandmarks]:
        imagen = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=np.ascontiguousarray(rgb, dtype=np.uint8),
        )
        if self.modo == "video":
            ts = int(ts_ms if ts_ms is not None else time.perf_counter() * 1000)
            if ts <= self._ultimo_ts:
                ts = self._ultimo_ts + 1
            self._ultimo_ts = ts
            resultado = self._detector.detect_for_video(imagen, ts)
        else:
            ts = int(ts_ms if ts_ms is not None else time.perf_counter() * 1000)
            resultado = self._detector.detect(imagen)

        salida: list[FrameLandmarks] = []
        for indice, landmarks in enumerate(resultado.hand_landmarks):
            puntos = np.array([[p.x, p.y, p.z] for p in landmarks], dtype=np.float32)
            mano = "Unknown"
            confianza = 0.0
            if indice < len(resultado.handedness) and resultado.handedness[indice]:
                categoria = resultado.handedness[indice][0]
                mano = categoria.category_name
                confianza = float(categoria.score)
            salida.append(FrameLandmarks(puntos=puntos, mano=mano, confianza=confianza, ts_ms=ts))
        return salida

    def cerrar(self) -> None:
        with contextlib.suppress(Exception):
            self._detector.close()

    def __enter__(self) -> FuenteManos:
        return self

    def __exit__(self, *_: object) -> None:
        self.cerrar()


__all__ = ["CONEXIONES_MANOS", "FrameLandmarks", "FuenteManos"]
