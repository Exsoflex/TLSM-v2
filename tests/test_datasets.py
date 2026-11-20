from __future__ import annotations

import numpy as np
import pytest

from tlsm.datasets import (
    Metadatos,
    cargar_dinamico,
    cargar_estatico,
    cargar_procesado,
    combinar_dinamicos,
    combinar_estaticos,
    guardar_dinamico,
    guardar_estatico,
    guardar_procesado,
    mezclar_procesado,
    resumen_etiquetas,
)


def _estatico(n: int = 3) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    return rng.random((n, 63), dtype=np.float32), rng.random((n, 21, 3), dtype=np.float32)


def test_guardar_y_agregar_estatico(tmp_path):
    X, raw = _estatico()
    meta = Metadatos(sesion="2026-11-18_01", firmante="S01", camara="camara_0")
    guardar_estatico(tmp_path, "A", X, raw, meta)
    guardar_estatico(tmp_path, "A", X, raw, meta)

    datos = cargar_estatico(tmp_path / "static_A.npz")
    assert datos["X"].shape == (6, 63)
    assert datos["raw"].shape == (6, 21, 3)
    assert datos["meta"].sesion == "2026-11-18_01"
    assert datos["meta"].firmante == "S01"
    assert set(datos["y"]) == {"A"}


def test_combinar_estaticos(tmp_path):
    X, raw = _estatico(2)
    guardar_estatico(tmp_path, "A", X, raw, Metadatos("s1", "S01", "c0"))
    guardar_estatico(tmp_path, "B", X, raw, Metadatos("s1", "S01", "c0"))

    combinado = combinar_estaticos(tmp_path)
    assert combinado["X"].shape == (4, 63)
    assert resumen_etiquetas(combinado["y"]) == {"A": 2, "B": 2}
    assert set(combinado["sesion"]) == {"s1"}


def test_guardar_dinamico(tmp_path):
    rng = np.random.default_rng(1)
    X = rng.random((2, 20, 63), dtype=np.float32)
    raw = rng.random((2, 20, 21, 3), dtype=np.float32)
    meta = Metadatos("s1", "S01", "c0")

    guardar_dinamico(tmp_path, "J", X, raw, 15.0, meta)
    datos = cargar_dinamico(tmp_path / "dynamic_J.npz")
    assert datos["X"].shape == (2, 20, 63)
    assert datos["fps"] == 15.0
    assert set(datos["y"]) == {"J"}

    combinado = combinar_dinamicos(tmp_path)
    assert combinado["X"].shape == (2, 20, 63)
    assert combinado["fps"] == 15.0


def test_dinamico_rechaza_forma_incorrecta(tmp_path):
    meta = Metadatos("s1", "S01", "c0")
    X = np.zeros((1, 10, 63), dtype=np.float32)
    raw = np.zeros((1, 10, 21, 3), dtype=np.float32)
    guardar_dinamico(tmp_path, "J", X, raw, 15.0, meta)
    with pytest.raises(ValueError):
        guardar_dinamico(
            tmp_path,
            "J",
            np.zeros((1, 20, 63)),
            np.zeros((1, 20, 21, 3)),
            15.0,
            meta,
        )


def _procesado(sesion: str, etiqueta: str, n: int = 2) -> dict:
    X, raw = _estatico(n)
    return {
        "X": X,
        "raw": raw,
        "y": np.array([etiqueta] * n, dtype=str),
        "sesion": np.array([sesion] * n, dtype=str),
        "firmante": np.array(["S01"] * n, dtype=str),
    }


def test_mezclar_procesado_conserva_y_agrega():
    previo = _procesado("v1", "A", 3)
    nuevo = _procesado("s2", "B", 2)

    combinado = mezclar_procesado(previo, nuevo)

    assert len(combinado["X"]) == 5
    assert resumen_etiquetas(combinado["y"]) == {"A": 3, "B": 2}
    assert set(combinado["sesion"]) == {"v1", "s2"}
    assert combinado["raw"].shape == (5, 21, 3)


def test_mezclar_procesado_reemplaza_sesion_sin_duplicar():
    previo = _procesado("v1", "A", 3)
    primera = _procesado("s2", "B", 2)
    combinado = mezclar_procesado(previo, primera)

    recapturada = _procesado("s2", "B", 4)
    combinado = mezclar_procesado(combinado, recapturada)

    assert len(combinado["X"]) == 7
    assert resumen_etiquetas(combinado["y"]) == {"A": 3, "B": 4}
    assert list(combinado["sesion"]).count("s2") == 4


def test_mezclar_procesado_sin_previo_y_fps():
    nuevo = _procesado("s2", "J", 1)
    nuevo["fps"] = 15.0
    assert mezclar_procesado(None, nuevo) is not nuevo
    assert mezclar_procesado(None, nuevo)["fps"] == 15.0

    previo = dict(nuevo)
    previo["sesion"] = np.array(["s1"], dtype=str)
    previo["fps"] = 12.0
    with pytest.raises(ValueError):
        mezclar_procesado(previo, nuevo)


def test_guardar_y_cargar_procesado(tmp_path):
    datos = _procesado("s1", "A", 2)
    ruta = guardar_procesado(
        tmp_path / "static_v2.npz",
        datos["X"],
        datos["y"],
        datos["sesion"],
        datos["firmante"],
        raw=datos["raw"],
    )
    recuperado = cargar_procesado(ruta)
    assert recuperado["X"].shape == (2, 63)
    assert set(recuperado["y"]) == {"A"}
    assert set(recuperado["sesion"]) == {"s1"}
