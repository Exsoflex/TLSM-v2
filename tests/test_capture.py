from __future__ import annotations

import numpy as np
from test_features import mano_sintetica

from tlsm.capture import CapturadorDinamico, CapturadorEstatico
from tlsm.config import ConfigCaptura


def _cfg() -> ConfigCaptura:
    return ConfigCaptura(
        cuenta_regresiva_s=0.0,
        intervalo_estatico_ms=0,
        movimiento_maximo_estatico=10.0,
        muestras_estaticas=3,
        frames_dinamicos=3,
        fps_dinamicos=15.0,
    )


def test_captura_estatica_completa():
    capturador = CapturadorEstatico("A", _cfg(), muestras=3)
    capturador.iniciar(1.0)
    puntos = mano_sintetica()

    estados = [capturador.actualizar(puntos, "Right", ahora=1.0 + i * 0.05) for i in range(3)]

    assert estados[-1].fase == "listo"
    assert estados[-1].muestras == 3
    X, raw = capturador.resultado()
    assert X.shape == (3, 63)
    assert raw.shape == (3, 21, 3)


def test_captura_estatica_espera_la_mano():
    capturador = CapturadorEstatico("A", _cfg(), muestras=3)
    capturador.iniciar(1.0)
    estado = capturador.actualizar(None, ahora=2.0)
    assert estado.fase == "cuenta"
    assert not capturador.listo


def test_captura_dinamica_muestrea_a_tasa_fija():
    capturador = CapturadorDinamico("J", _cfg(), frames=3, fps=15.0)
    capturador.iniciar(1.0)
    puntos = mano_sintetica()

    capturador.actualizar(puntos, "Right", ahora=1.0)
    # 20 ms después no debe muestrear todavía.
    capturador.actualizar(puntos, "Right", ahora=1.02)
    assert len(capturador._X) == 1

    capturador.actualizar(puntos, "Right", ahora=1.10)
    estado = capturador.actualizar(puntos, "Right", ahora=1.20)

    assert estado.fase == "listo"
    X, raw, fps = capturador.resultado()
    assert X.shape == (3, 63)
    assert raw.shape == (3, 21, 3)
    assert fps == 15.0
    assert np.isfinite(X).all()


def test_captura_dinamica_abortar():
    capturador = CapturadorDinamico("J", _cfg())
    capturador.iniciar(1.0)
    capturador.abortar()
    estado = capturador.actualizar(mano_sintetica(), ahora=1.1)
    assert estado.fase == "espera"
