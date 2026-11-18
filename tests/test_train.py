from __future__ import annotations

import numpy as np

from tlsm.model_io import PaqueteModelo, cargar_modelo, guardar_modelo
from tlsm.train import dividir_indices, entrenar


def _datos_sinteticos(
    clases: tuple[str, ...] = ("A", "B", "C", "D"), sesiones: int = 4, n: int = 25
):
    rng = np.random.default_rng(0)
    centros = {clase: rng.normal(0, 1.0, 63) for clase in clases}
    X, y, sesion = [], [], []
    for s in range(sesiones):
        for clase in clases:
            X.append(centros[clase] + rng.normal(0, 0.25, (n, 63)))
            y.extend([clase] * n)
            sesion.extend([f"s{s}"] * n)
    return np.vstack(X).astype(np.float32), np.array(y), np.array(sesion)


def test_split_por_sesion_no_mezcla_grupos():
    _, y, sesion = _datos_sinteticos()
    train, test, modo = dividir_indices(y, sesion, "sesion", seed=1)
    assert modo == "sesion"
    assert set(sesion[train]).isdisjoint(set(sesion[test]))


def test_split_bloque_es_contiguo_por_clase():
    _, y, sesion = _datos_sinteticos(sesiones=1)
    train, test, modo = dividir_indices(y, sesion, "bloque", test_size=0.2)
    assert modo == "bloque"
    assert len(test) > 0
    for clase in np.unique(y):
        indices = np.flatnonzero(y == clase)
        assert max(train[np.isin(train, indices)]) < min(test[np.isin(test, indices)])


def test_entrenamiento_clasifica_bien():
    X, y, sesion = _datos_sinteticos()
    paquete, metricas = entrenar(X, y, sesion, tipo="estatico", modo_split="sesion", seed=0)
    assert metricas["accuracy"] >= 0.95
    assert metricas["macro_f1"] >= 0.95
    assert metricas["modo_split"] == "sesion"
    assert len(metricas["matriz"]) == len(metricas["etiquetas"])


def test_guardar_y_cargar_modelo(tmp_path):
    X, y, sesion = _datos_sinteticos(clases=("A", "B"), sesiones=4, n=15)
    paquete, _ = entrenar(X, y, sesion, tipo="estatico", modo_split="sesion", seed=0)
    ruta = guardar_modelo(tmp_path / "modelo.joblib", paquete)
    recuperado = cargar_modelo(ruta)
    assert recuperado.etiquetas == paquete.etiquetas
    etiqueta, confianza, margen = recuperado.predecir(X[:1])
    assert etiqueta in paquete.etiquetas
    assert 0.0 <= confianza <= 1.0
    assert margen >= 0.0


def test_paquete_dinamico_aplana_secuencia():
    class Fijo:
        classes_ = np.array(["J", "A"])

        def predict_proba(self, X):
            return np.tile(np.array([[0.9, 0.1]]), (len(X), 1))

    paquete = PaqueteModelo(
        modelo=Fijo(),
        etiquetas=["J", "A"],
        tipo="dinamico",
        formato_entrada="secuencia_aplanada",
    )
    etiqueta, confianza, _ = paquete.predecir(np.zeros((1, 20, 63), dtype=np.float32))
    assert etiqueta == "J"
    assert confianza > 0.8
