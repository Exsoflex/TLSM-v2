"""Reconocimiento en tiempo real de letras estáticas y dinámicas.

El módulo no conoce la cámara ni la ventana: recibe landmarks y devuelve eventos.
Esa separación es la que permite reutilizarlo en la versión web.

Estático:
    Se suaviza la predicción con una ventana de votos. Solo se emite un evento
    cuando hay suficientes votos, confianza mínima y margen sobre la segunda clase.

Dinámico:
    Se muestrea a una tasa fija (por defecto 15 fps), igual que en el entrenamiento.
    Se mantiene una ventana deslizante de T frames y se emite un evento cuando hay
    movimiento suficiente en la ventana y el clasificador está seguro.
"""

from __future__ import annotations

import time
from collections import Counter, deque
from dataclasses import dataclass

import numpy as np

from .config import ConfigFeatures, ConfigReconocimiento
from .features import FEATURES_POR_MANO, features
from .landmarks import FrameLandmarks
from .model_io import PaqueteModelo


@dataclass(frozen=True)
class Evento:
    etiqueta: str
    confianza: float
    tipo: str  # "static" | "dynamic"
    ts_ms: int


def _ahora_ms() -> int:
    return int(time.monotonic() * 1000)


class Reconocedor:
    def __init__(
        self,
        estatico: PaqueteModelo | None = None,
        dinamico: PaqueteModelo | None = None,
        cfg: ConfigReconocimiento | None = None,
        cfg_features: ConfigFeatures | None = None,
    ) -> None:
        self.estatico = estatico
        self.dinamico = dinamico
        self.cfg = cfg or ConfigReconocimiento()
        self.cfg_features = cfg_features or ConfigFeatures()

        self._historial: deque[tuple[str, float]] = deque(maxlen=self.cfg.ventana_estatica)
        self._buffer: deque[np.ndarray] = deque(maxlen=self.cfg.ventana_movimiento)
        self._ultimo_muestreo_ms = 0
        self._movimiento_previo = 0.0
        self._frames_con_movimiento = 0
        self._ultimo_evento_ms = -(10**9)
        self._suprimir_estatico_hasta_ms = -(10**9)
        self._mano_previa = False

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def reiniciar(self) -> None:
        self._historial.clear()
        self._buffer.clear()
        self._frames_con_movimiento = 0
        self._mano_previa = False

    def actualizar(
        self,
        deteccion: FrameLandmarks | None,
        ts_ms: int | None = None,
    ) -> list[Evento]:
        if ts_ms is not None:
            ahora = int(ts_ms)
        elif deteccion is not None:
            ahora = int(deteccion.ts_ms)
        else:
            ahora = _ahora_ms()

        if deteccion is None:
            if self._mano_previa:
                self.reiniciar()
                self._mano_previa = False
            return []

        self._mano_previa = True
        vector = features(deteccion.puntos, deteccion.mano, self.cfg_features)

        eventos: list[Evento] = []
        evento_dinamico = self._actualizar_dinamico(vector, ahora)
        if evento_dinamico is not None:
            eventos.append(evento_dinamico)
            self._historial.clear()
            self._suprimir_estatico_hasta_ms = ahora + int(self.cfg.cooldown_gesto_s * 1000)
        elif ahora >= self._suprimir_estatico_hasta_ms:
            evento_estatico = self._actualizar_estatico(vector, ahora)
            if evento_estatico is not None:
                eventos.append(evento_estatico)
        return eventos

    # ------------------------------------------------------------------
    # Estático
    # ------------------------------------------------------------------

    def _actualizar_estatico(self, vector: np.ndarray, ahora: int) -> Evento | None:
        if self.estatico is None:
            return None

        etiqueta, confianza, _ = self.estatico.predecir(vector[None, :])
        self._historial.append((etiqueta, confianza))
        if len(self._historial) < self._historial.maxlen:
            return None

        conteo = Counter(e for e, _ in self._historial)
        ganadora, votos = conteo.most_common(1)[0]
        if votos < self.cfg.votos_minimos:
            return None

        confianzas = [c for e, c in self._historial if e == ganadora]
        confianza_media = float(np.mean(confianzas))
        if confianza_media < self.cfg.confianza_minima:
            return None

        # Margen contra la segunda clase más votada.
        segunda = conteo.most_common(2)
        margen = (votos - segunda[1][1]) / len(self._historial) if len(segunda) > 1 else 1.0
        if margen < self.cfg.margen_minimo:
            return None

        if ahora - self._ultimo_evento_ms < self.cfg.cooldown_letra_s * 1000:
            return None

        self._historial.clear()
        self._ultimo_evento_ms = ahora
        return Evento(ganadora, confianza_media, "static", ahora)

    # ------------------------------------------------------------------
    # Dinámico
    # ------------------------------------------------------------------

    def _actualizar_dinamico(self, vector: np.ndarray, ahora: int) -> Evento | None:
        if self.dinamico is None or self.cfg.ventana_movimiento <= 1:
            return None

        paso_ms = 1000.0 / self.cfg.fps_movimiento
        if self._ultimo_muestreo_ms and ahora - self._ultimo_muestreo_ms < paso_ms:
            return None

        if self._buffer:
            diferencia = float(np.mean(np.abs(vector[:42] - self._buffer[-1][:42])))
        else:
            diferencia = 0.0

        self._ultimo_muestreo_ms = ahora
        self._buffer.append(vector.astype(np.float32))

        if diferencia > self.cfg.umbral_inicio:
            self._frames_con_movimiento += 1
        else:
            self._frames_con_movimiento = 0
        self._movimiento_previo = diferencia

        if len(self._buffer) < self.cfg.ventana_movimiento:
            return None
        if self._frames_con_movimiento < self.cfg.frames_para_iniciar:
            return None

        secuencia = np.stack(self._buffer)
        movimiento_total = float(np.mean(np.abs(np.diff(secuencia[:, :42], axis=0))))
        if movimiento_total < self.cfg.umbral_movimiento_total:
            return None
        if ahora - self._ultimo_evento_ms < self.cfg.cooldown_gesto_s * 1000:
            return None

        etiqueta, confianza, _ = self.dinamico.predecir(secuencia[None, ...])
        if confianza < self.cfg.confianza_movimiento:
            return None

        self._buffer.clear()
        self._frames_con_movimiento = 0
        self._ultimo_evento_ms = ahora
        return Evento(etiqueta, confianza, "dynamic", ahora)


__all__ = ["Evento", "Reconocedor", "FEATURES_POR_MANO"]
