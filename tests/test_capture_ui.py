from __future__ import annotations

import numpy as np

from tlsm import capture_ui
from tlsm.capture_ui import ALTO_CAMARA, ALTO_GRILLA, ANCHO_PANEL, ANCHO_TOTAL, AppCaptura, Opciones
from tlsm.config import LETRAS
from tlsm.datasets import Metadatos, contar_sesion, guardar_dinamico, guardar_estatico
from tlsm.landmarks import FrameLandmarks


def _opciones(**cambios) -> Opciones:
    base = dict(
        firmante="S01",
        sesion="prueba",
        camara=0,
        rondas=1,
        muestras_ronda=2,
        secuencias_ronda=1,
        letras=("A", "B"),
        auto_avanzar=True,
        notas="",
        espejo=True,
    )
    base.update(cambios)
    return Opciones(**base)


def _app(opciones: Opciones) -> AppCaptura:
    return AppCaptura(opciones, fuente=object(), camara=object())


def _deteccion() -> FrameLandmarks:
    puntos = np.tile(np.array([[0.5, 0.5, 0.0]], dtype=np.float32), (21, 1))
    return FrameLandmarks(puntos=puntos, mano="Right", confianza=1.0, ts_ms=0)


def test_contar_sesion(tmp_path):
    meta = Metadatos("prueba", "S01", "camara_0")
    rng = np.random.default_rng(0)
    guardar_estatico(tmp_path, "A", rng.random((3, 63)), rng.random((3, 21, 3)), meta)
    guardar_estatico(tmp_path, "A", rng.random((2, 63)), rng.random((2, 21, 3)), meta)
    guardar_dinamico(
        tmp_path,
        "J",
        rng.random((1, 20, 63)),
        rng.random((1, 20, 21, 3)),
        15.0,
        meta,
    )

    assert contar_sesion(tmp_path) == {"A": 5, "J": 1}
    assert contar_sesion(tmp_path / "no_existe") == {}


def test_grilla_y_panel(tmp_path, monkeypatch):
    monkeypatch.setattr(capture_ui, "DATA_RAW", tmp_path)
    app = _app(_opciones(letras=LETRAS))

    grilla = app._grilla()
    panel = app._panel()

    assert grilla.shape == (ALTO_GRILLA, ANCHO_TOTAL, 3)
    assert panel.shape == (ALTO_CAMARA, ANCHO_PANEL, 3)
    assert grilla.dtype.name == "uint8"
    assert panel.dtype.name == "uint8"


def test_ronda_estatica_guarda_y_avanza(tmp_path, monkeypatch):
    monkeypatch.setattr(capture_ui, "DATA_RAW", tmp_path)
    app = _app(_opciones())
    deteccion = _deteccion()

    app._iniciar_ronda(1000.0)
    assert app.fase == "grabando"

    ahora = 1003.1  # pasa la cuenta regresiva de 3 s
    app._actualizar(deteccion, ahora)
    for _ in range(2):
        ahora += 0.05
        app._actualizar(deteccion, ahora)

    assert app.fase == "inactivo"
    assert app.muestras("A") == 2
    assert (tmp_path / "prueba" / "static_A.npz").exists()
    assert app.letra == "B"  # auto-avance a la siguiente pendiente


def test_ronda_dinamica_guarda_secuencia(tmp_path, monkeypatch):
    monkeypatch.setattr(capture_ui, "DATA_RAW", tmp_path)
    app = _app(_opciones(letras=("J",), secuencias_ronda=1, rondas=1))
    deteccion = _deteccion()

    app._iniciar_ronda(2000.0)
    assert app.fase == "preparando"

    app._actualizar(None, 2000.5)
    assert app.fase == "preparando"

    ahora = 2002.5
    app._actualizar(deteccion, ahora)  # termina la preparacion
    assert app.fase == "grabando"

    frames = app.capturador.frames
    for _ in range(frames):
        ahora += 0.07
        app._actualizar(deteccion, ahora)

    assert app.fase == "ronda_lista"
    assert app.muestras("J") == 1
    assert (tmp_path / "prueba" / "dynamic_J.npz").exists()


def test_descartar_y_navegar(tmp_path, monkeypatch):
    monkeypatch.setattr(capture_ui, "DATA_RAW", tmp_path)
    app = _app(_opciones())

    app._iniciar_ronda(1000.0)
    assert app._tecla(ord("r"), 1001.0) is True
    assert app.fase == "inactivo"

    app._tecla(ord("d"), 1001.0)
    assert app.letra == "B"
    app._tecla(ord("a"), 1001.0)
    assert app.letra == "A"

    app.ayuda = True
    app._tecla(ord("d"), 1001.0)
    assert app.letra == "A"  # la ayuda bloquea la navegacion
    app._tecla(ord("h"), 1001.0)
    assert app.ayuda is False

    assert app._tecla(ord("q"), 1001.0) is False
