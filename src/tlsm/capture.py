"""Lógica de captura guiada.

Los scripts solo dibujan y pasan frames; aquí vive la máquina de estados para que
la captura sea idéntica desde cualquier interfaz (escritorio hoy, web después).
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np

from .config import ConfigCaptura, ConfigFeatures
from .features import features


@dataclass(frozen=True)
class EstadoCaptura:
    fase: str  # "espera" | "cuenta" | "capturando" | "listo" | "abortado"
    mensaje: str
    cuenta: int = 0
    muestras: int = 0
    total: int = 0
    omitidas: int = 0
    progreso: float = 0.0

    @property
    def terminado(self) -> bool:
        return self.fase == "listo"


def _ahora(ahora: float | None) -> float:
    return time.monotonic() if ahora is None else ahora


class CapturadorEstatico:
    """Cuenta regresiva y captura de una letra estática."""

    def __init__(
        self,
        etiqueta: str,
        cfg: ConfigCaptura | None = None,
        cfg_features: ConfigFeatures | None = None,
        muestras: int | None = None,
    ) -> None:
        self.etiqueta = etiqueta
        self.cfg = cfg or ConfigCaptura()
        self.cfg_features = cfg_features or ConfigFeatures()
        self.total = int(muestras or self.cfg.muestras_estaticas)
        self._X: list[np.ndarray] = []
        self._raw: list[np.ndarray] = []
        self._inicio_cuenta = 0.0
        self._ultima_muestra = 0.0
        self._ultimo_vector: np.ndarray | None = None

    def iniciar(self, ahora: float | None = None) -> None:
        self._inicio_cuenta = _ahora(ahora)
        self._ultima_muestra = 0.0
        self._X.clear()
        self._raw.clear()
        self._ultimo_vector = None

    def reiniciar(self, ahora: float | None = None) -> None:
        self.iniciar(ahora)

    def actualizar(
        self,
        puntos: np.ndarray | None,
        mano: str = "Right",
        ahora: float | None = None,
    ) -> EstadoCaptura:
        ahora = _ahora(ahora)

        if self._inicio_cuenta == 0.0:
            return EstadoCaptura("espera", "SPACE para iniciar", total=self.total)

        if puntos is None:
            return EstadoCaptura(
                "cuenta",
                "Muestra la mano para continuar",
                cuenta=max(1, math.ceil(self.cfg.cuenta_regresiva_s)),
                muestras=len(self._X),
                total=self.total,
            )

        transcurrido = ahora - self._inicio_cuenta
        if transcurrido < self.cfg.cuenta_regresiva_s:
            restante = max(1, math.ceil(self.cfg.cuenta_regresiva_s - transcurrido))
            return EstadoCaptura(
                "cuenta",
                f"Preparate... {restante}",
                cuenta=restante,
                total=self.total,
            )

        if len(self._X) >= self.total:
            return EstadoCaptura(
                "listo",
                "Listo. R para repetir o Q para salir",
                muestras=len(self._X),
                total=self.total,
                progreso=1.0,
            )

        vector = features(puntos, mano, self.cfg_features)
        movimiento = (
            float(np.mean(np.abs(vector - self._ultimo_vector)))
            if self._ultimo_vector is not None
            else 0.0
        )
        estable = movimiento <= self.cfg.movimiento_maximo_estatico
        self._ultimo_vector = vector

        intervalo = self.cfg.intervalo_estatico_ms / 1000.0
        if ahora - self._ultima_muestra < intervalo:
            return self._estado_actual("Capturando...")

        self._ultima_muestra = ahora
        if estable:
            self._X.append(vector)
            self._raw.append(np.asarray(puntos, dtype=np.float32).copy())
        return self._estado_actual("Capturando..." if estable else "Manten la mano quieta")

    def _estado_actual(self, mensaje: str) -> EstadoCaptura:
        return EstadoCaptura(
            "capturando" if len(self._X) < self.total else "listo",
            mensaje if len(self._X) < self.total else "Listo. R para repetir o Q para salir",
            muestras=len(self._X),
            total=self.total,
            progreso=min(1.0, len(self._X) / max(1, self.total)),
        )

    @property
    def listo(self) -> bool:
        return len(self._X) >= self.total

    def resultado(self) -> tuple[np.ndarray, np.ndarray]:
        if not self.listo:
            raise RuntimeError("La captura aún no está completa")
        return np.stack(self._X), np.stack(self._raw)


class CapturadorDinamico:
    """Graba T frames a una tasa fija. Se usa para J, K, Ñ, Q, X y Z."""

    def __init__(
        self,
        etiqueta: str,
        cfg: ConfigCaptura | None = None,
        cfg_features: ConfigFeatures | None = None,
        frames: int | None = None,
        fps: float | None = None,
    ) -> None:
        self.etiqueta = etiqueta
        self.cfg = cfg or ConfigCaptura()
        self.cfg_features = cfg_features or ConfigFeatures()
        self.frames = int(frames or self.cfg.frames_dinamicos)
        self.fps = float(fps or self.cfg.fps_dinamicos)
        self._X: list[np.ndarray] = []
        self._raw: list[np.ndarray] = []
        self._activo = False
        self._inicio = 0.0
        self._ultimo_muestreo = 0.0

    def iniciar(self, ahora: float | None = None) -> None:
        ahora = _ahora(ahora)
        self._X.clear()
        self._raw.clear()
        self._activo = True
        self._inicio = ahora
        self._ultimo_muestreo = 0.0

    def abortar(self) -> None:
        self._activo = False

    def actualizar(
        self,
        puntos: np.ndarray | None,
        mano: str = "Right",
        ahora: float | None = None,
    ) -> EstadoCaptura:
        ahora = _ahora(ahora)
        if not self._activo:
            return EstadoCaptura("espera", "SPACE para grabar el movimiento", total=self.frames)

        if puntos is None:
            return EstadoCaptura(
                "capturando",
                "Mano perdida: acerca la mano a la camara",
                muestras=len(self._X),
                total=self.frames,
                progreso=len(self._X) / self.frames,
            )

        paso = 1.0 / self.fps
        if self._ultimo_muestreo and ahora - self._ultimo_muestreo < paso:
            return self._estado()
        self._ultimo_muestreo = ahora

        self._X.append(features(puntos, mano, self.cfg_features))
        self._raw.append(np.asarray(puntos, dtype=np.float32).copy())

        if len(self._X) >= self.frames:
            self._activo = False
            return EstadoCaptura(
                "listo",
                "Listo. R para repetir o Q para salir",
                muestras=len(self._X),
                total=self.frames,
                progreso=1.0,
            )
        return self._estado()

    def _estado(self) -> EstadoCaptura:
        return EstadoCaptura(
            "capturando",
            "Grabando movimiento...",
            muestras=len(self._X),
            total=self.frames,
            progreso=len(self._X) / self.frames,
        )

    @property
    def listo(self) -> bool:
        return len(self._X) >= self.frames

    def resultado(self) -> tuple[np.ndarray, np.ndarray, float]:
        if not self.listo:
            raise RuntimeError("La captura aún no está completa")
        return np.stack(self._X), np.stack(self._raw), self.fps


__all__ = [
    "CapturadorDinamico",
    "CapturadorEstatico",
    "EstadoCaptura",
]
