from __future__ import annotations

from tlsm.drawing import envolver_texto
from tlsm.ui import _dibujar_panel


def test_panel_se_dibuja_sin_errores():
    panel = _dibujar_panel(
        480,
        "HOLA MUNDO",
        "N_TILDE",
        0.93,
        28.5,
        True,
        "estatico: 13 clases | dinamico: 4 clases",
        "Voz no disponible",
    )
    assert panel.shape == (480, 420, 3)
    assert panel.dtype.name == "uint8"


def test_panel_vacio():
    panel = _dibujar_panel(480, "", "", 0.0, 0.0, False, "sin modelos", "")
    assert panel.shape == (480, 420, 3)


def test_envolver_texto_largo():
    lineas = envolver_texto("A" * 200, 300)
    assert len(lineas) > 1
    assert all(linea for linea in lineas)
