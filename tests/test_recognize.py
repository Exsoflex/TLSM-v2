from __future__ import annotations

import numpy as np
from test_features import mano_sintetica

from tlsm.landmarks import FrameLandmarks
from tlsm.model_io import PaqueteModelo
from tlsm.recognize import Reconocedor


class ProbabilidadesFijas:
    def __init__(self, clases: list[str], probs: list[float]) -> None:
        self.classes_ = np.array(clases)
        self._probs = np.array(probs, dtype=float)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return np.tile(self._probs, (len(X), 1))


def _paquete(clases: list[str], probs: list[float], tipo: str) -> PaqueteModelo:
    return PaqueteModelo(
        modelo=ProbabilidadesFijas(clases, probs),
        etiquetas=clases,
        tipo=tipo,
        formato_entrada="vector" if tipo == "estatico" else "secuencia_aplanada",
    )


def _frame(puntos: np.ndarray, ts: int) -> FrameLandmarks:
    return FrameLandmarks(puntos=puntos, mano="Right", confianza=1.0, ts_ms=ts)


def test_estatico_necesita_ventana_completa():
    paquete = _paquete(["A", "B"], [0.95, 0.05], "estatico")
    reconocedor = Reconocedor(estatico=paquete)
    puntos = mano_sintetica()

    eventos = []
    for i in range(9):
        eventos.extend(reconocedor.actualizar(_frame(puntos, 1000 + i * 40)))
    assert eventos == []

    eventos.extend(reconocedor.actualizar(_frame(puntos, 1000 + 9 * 40)))
    assert len(eventos) == 1
    assert eventos[0].etiqueta == "A"
    assert eventos[0].tipo == "static"


def test_sin_mano_reinicia_la_ventana():
    paquete = _paquete(["A", "B"], [0.95, 0.05], "estatico")
    reconocedor = Reconocedor(estatico=paquete)
    puntos = mano_sintetica()

    for i in range(6):
        reconocedor.actualizar(_frame(puntos, 1000 + i * 40))
    reconocedor.actualizar(None, 1300)
    eventos = []
    for i in range(6):
        eventos.extend(reconocedor.actualizar(_frame(puntos, 1400 + i * 40)))
    assert eventos == []


def test_dinamico_detecta_movimiento():
    paquete = _paquete(["J", "A"], [0.9, 0.1], "dinamico")
    reconocedor = Reconocedor(dinamico=paquete)

    base = mano_sintetica()
    eventos = []
    ts = 1000
    for i in range(24):
        puntos = base.copy()
        signo = 1.0 if i % 2 == 0 else -1.0
        puntos[5:9, 0] += signo * 0.5
        puntos[5:9, 1] += signo * 0.4
        eventos.extend(reconocedor.actualizar(_frame(puntos, ts)))
        ts += 70

    assert eventos, "Debe emitirse al menos un evento dinamico"
    assert eventos[0].etiqueta == "J"
    assert eventos[0].tipo == "dynamic"


def test_sin_modelos_no_hay_eventos():
    reconocedor = Reconocedor()
    assert reconocedor.actualizar(_frame(mano_sintetica(), 1000)) == []
