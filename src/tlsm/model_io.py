"""Guardado y carga de paquetes de modelo.

Un paquete incluye el clasificador, sus etiquetas y los metadatos necesarios para
saber con qué versión de features fue entrenado. Así evitamos cargar un modelo
incompatible sin darnos cuenta.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from .config import VERSION_FEATURES

FORMATOS = frozenset({"vector", "secuencia_aplanada"})


@dataclass
class PaqueteModelo:
    modelo: Any
    etiquetas: list[str]
    tipo: str  # "estatico" | "dinamico"
    formato_entrada: str = "vector"
    version_features: str = VERSION_FEATURES
    metadatos: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.etiquetas = [str(e) for e in self.etiquetas]
        if self.formato_entrada not in FORMATOS:
            raise ValueError(f"formato_entrada inválido: {self.formato_entrada}")

    # ------------------------------------------------------------------
    # Inferencia
    # ------------------------------------------------------------------

    def _preparar(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float32)
        if self.formato_entrada == "secuencia_aplanada":
            X = X.reshape(len(X), -1)
        return X

    def probabilidades(self, X: np.ndarray) -> list[dict[str, float]]:
        """Devuelve una lista de diccionarios {etiqueta: probabilidad}."""
        X = self._preparar(X)
        if X.ndim == 1:
            X = X[None, :]
        proba = self.modelo.predict_proba(X)
        clases = [str(c) for c in self.modelo.classes_]
        return [{c: float(p) for c, p in zip(clases, fila, strict=True)} for fila in proba]

    def predecir(self, X: np.ndarray) -> tuple[str, float, float]:
        """Devuelve (etiqueta, confianza, margen sobre la segunda opción)."""
        probs = self.probabilidades(X)[0]
        orden = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
        etiqueta, confianza = orden[0]
        segundo = orden[1][1] if len(orden) > 1 else 0.0
        return etiqueta, confianza, confianza - segundo


def guardar_modelo(ruta: Path | str, paquete: PaqueteModelo) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(paquete, ruta, compress=3)
    return ruta


def cargar_modelo(ruta: Path | str) -> PaqueteModelo:
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el modelo: {ruta}")
    paquete = joblib.load(ruta)
    if not isinstance(paquete, PaqueteModelo):
        raise TypeError(f"{ruta} no contiene un PaqueteModelo de TLSM")
    return paquete


__all__ = ["PaqueteModelo", "cargar_modelo", "guardar_modelo"]
