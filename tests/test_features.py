from __future__ import annotations

import numpy as np

from tlsm.features import canonicalizar_lote, escala_mano, features


def mano_sintetica() -> np.ndarray:
    puntos = np.zeros((21, 3), dtype=np.float32)
    puntos[0] = (0.5, 0.7, 0.0)
    for i in range(1, 21):
        angulo = i * 0.31
        radio = 0.05 + 0.012 * (i % 5)
        puntos[i] = (
            0.5 + radio * np.cos(angulo),
            0.7 - radio * np.sin(angulo) - 0.015,
            0.002 * i,
        )
    puntos[9] = (0.55, 0.60, 0.01)
    return puntos


def test_forma_del_vector():
    assert features(mano_sintetica()).shape == (63,)


def test_invarianza_traslacion():
    puntos = mano_sintetica()
    desplazados = puntos + np.array([0.13, -0.08, 0.04], dtype=np.float32)
    assert np.allclose(features(puntos), features(desplazados), atol=1e-5)


def test_invarianza_escala():
    puntos = mano_sintetica()
    escalados = puntos[0] + (puntos - puntos[0]) * 2.7
    assert np.allclose(features(puntos), features(escalados), atol=1e-5)


def test_invarianza_rotacion():
    puntos = mano_sintetica()
    theta = 0.8
    rotacion = np.array(
        [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]],
        dtype=np.float32,
    )
    relativos = puntos.copy()
    relativos[:, :2] = (puntos[:, :2] - puntos[0, :2]) @ rotacion.T
    rotados = relativos + puntos[0]
    rotados[:, 2] = puntos[:, 2]
    assert np.allclose(features(puntos), features(rotados), atol=1e-5)


def test_mano_izquierda_se_espeja():
    puntos = mano_sintetica()
    espejados = puntos.copy()
    espejados[:, 0] = 1.0 - espejados[:, 0]
    assert np.allclose(features(espejados, "Left"), features(puntos, "Right"), atol=1e-5)


def test_canonico_wrist_origen_y_eje_y():
    canonico = canonicalizar_lote(mano_sintetica())
    assert np.allclose(canonico[0], 0.0, atol=1e-6)
    assert abs(float(canonico[9, 0])) < 1e-5
    assert float(canonico[9, 1]) > 0.0
    assert np.isclose(float(np.linalg.norm(canonico[9])), 1.0, atol=1e-5)


def test_escala_mano_positiva():
    assert escala_mano(mano_sintetica()) > 0.0


def test_lote_y_secuencia():
    puntos = mano_sintetica()
    lote = np.stack([puntos, puntos])
    secuencia = np.stack([lote, lote])
    assert features(lote).shape == (2, 63)
    assert features(secuencia).shape == (2, 2, 63)
