"""Extracción y normalización de features a partir de landmarks de la mano.

Contrato:
    - Entrada: 21 landmarks (x, y, z) normalizados por MediaPipe.
    - Salida: vector float32 de 63 dimensiones (21 x 3).

La normalización es lo que hace que el modelo no dependa de la posición, el tamaño
ni la rotación de la mano en la imagen. Es la mejora más importante respecto a la v1.
"""

from __future__ import annotations

import numpy as np

from .config import VERSION_FEATURES, ConfigFeatures

PUNTOS_POR_MANO = 21
DIMENSIONES = 3
FEATURES_POR_MANO = PUNTOS_POR_MANO * DIMENSIONES  # 63

# Punto de referencia para la escala: MCP del dedo medio (landmark 9).
PUNTO_ESCALA = 9


def _config(cfg: ConfigFeatures | None) -> ConfigFeatures:
    return cfg or ConfigFeatures()


def canonicalizar_lote(
    puntos: np.ndarray,
    handedness: str | list[str] | np.ndarray | None = None,
    cfg: ConfigFeatures | None = None,
) -> np.ndarray:
    """Normaliza uno o varios conjuntos de 21 landmarks.

    Acepta formas:
        - (21, 3)
        - (N, 21, 3)
        - (N, T, 21, 3)

    Devuelve la misma forma con los landmarks canónicos.
    """
    cfg = _config(cfg)
    p = np.asarray(puntos, dtype=np.float32)
    if p.shape[-2:] != (PUNTOS_POR_MANO, DIMENSIONES):
        raise ValueError(f"Se esperaban landmarks (..., 21, 3); recibido {p.shape}")

    unico = p.ndim == 2
    secuencia = p.ndim == 4
    if unico:
        p = p[None, ...]

    if secuencia:
        n, t = p.shape[:2]
        p = p.reshape(n * t, PUNTOS_POR_MANO, DIMENSIONES)
    else:
        n, t = p.shape[0], 1

    p = p.copy()

    # 1) Traslación: la muñeca (landmark 0) pasa a ser el origen.
    p -= p[:, 0:1, :]

    # 2) Escala: dividir por el tamaño de la mano.
    if cfg.normalizar_escala:
        escala = np.linalg.norm(p[:, PUNTO_ESCALA, :], axis=1, keepdims=True)
        escala[escala < 1e-6] = 1.0
        p /= escala[:, :, None]

    # 3) Rotación en el plano de la imagen: alinear muñeca -> MCP medio con +Y.
    if cfg.rotar:
        vx = p[:, PUNTO_ESCALA, 0]
        vy = p[:, PUNTO_ESCALA, 1]
        theta = np.arctan2(vx, vy)
        cos = np.cos(theta)[:, None]
        sin = np.sin(theta)[:, None]
        x = p[:, :, 0].copy()
        y = p[:, :, 1].copy()
        p[:, :, 0] = x * cos - y * sin
        p[:, :, 1] = x * sin + y * cos

    # 4) Canonicalizar mano izquierda como derecha (opcional).
    if cfg.espejar_zurdas and handedness is not None:
        if isinstance(handedness, str):
            etiquetas = [handedness] * len(p)
        else:
            etiquetas = list(handedness)
            if secuencia:
                etiquetas = list(np.repeat(np.asarray(etiquetas), t))
        if len(etiquetas) != len(p):
            raise ValueError("handedness no coincide con el número de muestras")
        mascara = np.array([h == "Left" for h in etiquetas], dtype=bool)
        p[mascara, :, 0] *= -1

    # 5) Profundidad opcional.
    if not cfg.usar_z:
        p[:, :, 2] = 0.0

    if secuencia:
        p = p.reshape(n, t, PUNTOS_POR_MANO, DIMENSIONES)
    if unico:
        return p[0]
    return p


def vectorizar(puntos_canonicos: np.ndarray) -> np.ndarray:
    """Aplana (…, 21, 3) a (…, 63)."""
    return np.asarray(puntos_canonicos, dtype=np.float32).reshape(
        *puntos_canonicos.shape[:-2], FEATURES_POR_MANO
    )


def features(
    puntos: np.ndarray, handedness: str | None = None, cfg: ConfigFeatures | None = None
) -> np.ndarray:
    """Atajo: landmarks crudos -> vector canónico de 63 dimensiones."""
    return vectorizar(canonicalizar_lote(puntos, handedness, cfg))


def features_lote(
    puntos: np.ndarray,
    handedness: list[str] | np.ndarray | None = None,
    cfg: ConfigFeatures | None = None,
) -> np.ndarray:
    """Atajo por lotes: (N, 21, 3) -> (N, 63)."""
    return vectorizar(canonicalizar_lote(puntos, handedness, cfg))


def escala_mano(puntos: np.ndarray) -> float:
    """Distancia muñeca -> MCP del dedo medio, en coordenadas de imagen."""
    p = np.asarray(puntos, dtype=np.float32)
    return float(np.linalg.norm(p[PUNTO_ESCALA] - p[0]))


__all__ = [
    "FEATURES_POR_MANO",
    "VERSION_FEATURES",
    "canonicalizar_lote",
    "escala_mano",
    "features",
    "features_lote",
    "vectorizar",
]
