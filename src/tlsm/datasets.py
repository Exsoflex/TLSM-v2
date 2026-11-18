"""Lectura, escritura y conversión de datasets.

Formato v2 (raw, por sesión):
    data/raw/<sesion>/static_<ETIQUETA>.npz
        X:        float32 (N, 63)          features canónicas
        raw:      float32 (N, 21, 3)       landmarks crudos
        y:        str (N,)                 etiqueta
        meta_json: str                     metadatos de la sesión

    data/raw/<sesion>/dynamic_<ETIQUETA>.npz
        X:        float32 (N, T, 63)
        raw:      float32 (N, T, 21, 3)
        y:        str (N,)
        fps:      float
        meta_json: str

Formato procesado (para entrenar):
    data/processed/static_v2.npz
        X, raw, y, sesion, firmante, split
    data/processed/dynamic_v2.npz
        X, raw, y, sesion, firmante, split, fps
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .config import MODELO_LANDMARKS, VERSION_APP, ConfigFeatures
from .features import FEATURES_POR_MANO, features_lote

PUNTOS_POR_MANO = 21


@dataclass(frozen=True)
class Metadatos:
    sesion: str
    firmante: str
    camara: str
    creado: str = field(default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds"))
    modelo_landmarks: str = MODELO_LANDMARKS
    version_app: str = VERSION_APP
    notas: str = ""

    def a_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @staticmethod
    def desde_json(texto: str) -> Metadatos:
        datos = json.loads(texto)
        return Metadatos(**datos)


def _directorio(ruta: Path | str) -> Path:
    ruta = Path(ruta)
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def _meta_json(meta: Metadatos) -> np.ndarray:
    return np.array(meta.a_json())


def _leer_meta(npz: np.lib.npyio.NpzFile) -> Metadatos:
    valor = npz["meta_json"]
    return Metadatos.desde_json(valor.item() if hasattr(valor, "item") else str(valor))


def guardar_estatico(
    directorio: Path | str,
    etiqueta: str,
    X: np.ndarray,
    raw: np.ndarray,
    meta: Metadatos,
    agregar: bool = True,
) -> Path:
    """Guarda muestras estáticas; si el archivo existe, agrega por defecto."""
    directorio = _directorio(directorio)
    archivo = directorio / f"static_{etiqueta}.npz"
    X = np.asarray(X, dtype=np.float32)
    raw = np.asarray(raw, dtype=np.float32)
    if X.ndim != 2 or X.shape[1] != FEATURES_POR_MANO:
        raise ValueError(f"X estático debe ser (N, {FEATURES_POR_MANO}); recibido {X.shape}")
    if raw.shape != (len(X), PUNTOS_POR_MANO, 3):
        raise ValueError(f"raw debe ser ({len(X)}, 21, 3); recibido {raw.shape}")

    y = np.array([etiqueta] * len(X), dtype=str)
    if agregar and archivo.exists():
        with np.load(archivo, allow_pickle=False) as previo:
            X = np.concatenate([previo["X"], X], axis=0)
            raw = np.concatenate([previo["raw"], raw], axis=0)
            y = np.concatenate([previo["y"].astype(str), y], axis=0)
    y = y.astype(str)

    np.savez_compressed(archivo, X=X, raw=raw, y=y, meta_json=_meta_json(meta))
    return archivo


def guardar_dinamico(
    directorio: Path | str,
    etiqueta: str,
    X: np.ndarray,
    raw: np.ndarray,
    fps: float,
    meta: Metadatos,
    agregar: bool = True,
) -> Path:
    """Guarda secuencias dinámicas; si el archivo existe, agrega por defecto."""
    directorio = _directorio(directorio)
    archivo = directorio / f"dynamic_{etiqueta}.npz"
    X = np.asarray(X, dtype=np.float32)
    raw = np.asarray(raw, dtype=np.float32)
    if X.ndim != 3 or X.shape[2] != FEATURES_POR_MANO:
        raise ValueError(f"X dinámico debe ser (N, T, {FEATURES_POR_MANO}); recibido {X.shape}")
    if raw.shape != (X.shape[0], X.shape[1], PUNTOS_POR_MANO, 3):
        raise ValueError(f"raw debe ser (N, T, 21, 3); recibido {raw.shape}")
    if len(X) == 0:
        raise ValueError("No hay secuencias para guardar")

    y = np.array([etiqueta] * len(X), dtype=str)
    if agregar and archivo.exists():
        with np.load(archivo, allow_pickle=False) as previo:
            if previo["X"].shape[1:] != X.shape[1:]:
                raise ValueError(
                    f"La secuencia existente tiene forma {previo['X'].shape[1:]}, "
                    f"la nueva {X.shape[1:]}"
                )
            X = np.concatenate([previo["X"], X], axis=0)
            raw = np.concatenate([previo["raw"], raw], axis=0)
            y = np.concatenate([previo["y"].astype(str), y], axis=0)
    y = y.astype(str)

    np.savez_compressed(
        archivo,
        X=X,
        raw=raw,
        y=y,
        fps=np.array(float(fps)),
        meta_json=_meta_json(meta),
    )
    return archivo


def cargar_estatico(archivo: Path | str) -> dict:
    with np.load(Path(archivo), allow_pickle=False) as d:
        return {
            "X": d["X"],
            "raw": d["raw"],
            "y": d["y"].astype(str),
            "meta": _leer_meta(d),
        }


def cargar_dinamico(archivo: Path | str) -> dict:
    with np.load(Path(archivo), allow_pickle=False) as d:
        return {
            "X": d["X"],
            "raw": d["raw"],
            "y": d["y"].astype(str),
            "fps": float(d["fps"]),
            "meta": _leer_meta(d),
        }


def combinar_estaticos(directorio: Path | str) -> dict:
    archivos = sorted(Path(directorio).glob("static_*.npz"))
    if not archivos:
        raise FileNotFoundError(f"No hay archivos static_*.npz en {directorio}")
    X, raw, y, sesion, firmante = [], [], [], [], []
    for archivo in archivos:
        datos = cargar_estatico(archivo)
        X.append(datos["X"])
        raw.append(datos["raw"])
        y.append(datos["y"])
        sesion.extend([datos["meta"].sesion] * len(datos["y"]))
        firmante.extend([datos["meta"].firmante] * len(datos["y"]))
    return {
        "X": np.concatenate(X),
        "raw": np.concatenate(raw),
        "y": np.concatenate(y),
        "sesion": np.array(sesion, dtype=object),
        "firmante": np.array(firmante, dtype=object),
    }


def combinar_dinamicos(directorio: Path | str) -> dict:
    archivos = sorted(Path(directorio).glob("dynamic_*.npz"))
    if not archivos:
        raise FileNotFoundError(f"No hay archivos dynamic_*.npz en {directorio}")
    X, raw, y, sesion, firmante = [], [], [], [], []
    fps = []
    for archivo in archivos:
        datos = cargar_dinamico(archivo)
        X.append(datos["X"])
        raw.append(datos["raw"])
        y.append(datos["y"])
        sesion.extend([datos["meta"].sesion] * len(datos["y"]))
        firmante.extend([datos["meta"].firmante] * len(datos["y"]))
        fps.append(datos["fps"])
    if len(set(round(f, 3) for f in fps)) > 1:
        raise ValueError(f"Los FPS de las secuencias no coinciden: {sorted(set(fps))}")
    return {
        "X": np.concatenate(X),
        "raw": np.concatenate(raw),
        "y": np.concatenate(y),
        "sesion": np.array(sesion, dtype=object),
        "firmante": np.array(firmante, dtype=object),
        "fps": fps[0],
    }


def guardar_procesado(
    archivo: Path | str,
    X: np.ndarray,
    y: np.ndarray,
    sesion: np.ndarray,
    firmante: np.ndarray,
    raw: np.ndarray | None = None,
    fps: float | None = None,
) -> Path:
    archivo = Path(archivo)
    archivo.parent.mkdir(parents=True, exist_ok=True)
    datos: dict[str, np.ndarray] = {
        "X": np.asarray(X, dtype=np.float32),
        "y": np.asarray(y, dtype=str),
        "sesion": np.asarray(sesion, dtype=str),
        "firmante": np.asarray(firmante, dtype=str),
    }
    if raw is not None:
        datos["raw"] = np.asarray(raw, dtype=np.float32)
    if fps is not None:
        datos["fps"] = np.array(float(fps))
    np.savez_compressed(archivo, **datos)
    return archivo


def cargar_procesado(archivo: Path | str) -> dict:
    with np.load(Path(archivo), allow_pickle=False) as d:
        datos = {
            "X": d["X"],
            "y": d["y"].astype(str),
            "sesion": d["sesion"].astype(str),
            "firmante": d["firmante"].astype(str),
        }
        if "raw" in d:
            datos["raw"] = d["raw"]
        if "fps" in d:
            datos["fps"] = float(d["fps"])
        return datos


def importar_v1_estatico(
    csv_path: Path | str, salida: Path | str, cfg: ConfigFeatures | None = None
) -> dict:
    """Convierte el CSV v1 (42 columnas x,y) al formato v2 (63 features)."""
    df = pd.read_csv(csv_path)
    if "letra" not in df.columns:
        raise ValueError("El CSV v1 debe tener una columna 'letra'")
    columnas = [c for c in df.columns if c != "letra"]
    if len(columnas) != PUNTOS_POR_MANO * 2:
        raise ValueError(f"Se esperaban 42 columnas de coordenadas; hay {len(columnas)}")

    y = df["letra"].astype(str).str.upper().to_numpy()
    puntos = df[columnas].to_numpy(dtype=np.float32).reshape(-1, PUNTOS_POR_MANO, 2)
    puntos3 = np.concatenate(
        [puntos, np.zeros((len(puntos), PUNTOS_POR_MANO, 1), dtype=np.float32)], axis=2
    )
    X = features_lote(puntos3, handedness=None, cfg=cfg)

    sesion = np.array(["v1"] * len(X), dtype=object)
    firmante = np.array(["v1"] * len(X), dtype=object)
    return {
        "X": X,
        "raw": puntos3,
        "y": y,
        "sesion": sesion,
        "firmante": firmante,
        "archivo": guardar_procesado(salida, X, y, sesion, firmante, raw=puntos3),
    }


def importar_v1_dinamico(
    pkl_path: Path | str, salida: Path | str, cfg: ConfigFeatures | None = None
) -> dict:
    """Convierte el dataset v1 de movimiento (lista de secuencias 20x42)."""
    datos = joblib.load(pkl_path)
    if not isinstance(datos, list) or not datos:
        raise ValueError("Se esperaba una lista [(secuencia, etiqueta), ...]")

    secuencias = np.array([np.asarray(seq, dtype=np.float32) for seq, _ in datos])
    if secuencias.ndim != 3 or secuencias.shape[2] != PUNTOS_POR_MANO * 2:
        raise ValueError(f"Secuencias v1 con forma inesperada: {secuencias.shape}")
    n, t, _ = secuencias.shape
    puntos = secuencias.reshape(n, t, PUNTOS_POR_MANO, 2)
    puntos3 = np.concatenate(
        [puntos, np.zeros((n, t, PUNTOS_POR_MANO, 1), dtype=np.float32)], axis=3
    )
    X = features_lote(puntos3, handedness=None, cfg=cfg)
    y = np.array([str(etiqueta).upper() for _, etiqueta in datos], dtype=object)

    sesion = np.array(["v1"] * len(X), dtype=object)
    firmante = np.array(["v1"] * len(X), dtype=object)
    resultado = {
        "X": X,
        "raw": puntos3,
        "y": y,
        "sesion": sesion,
        "firmante": firmante,
        "fps": 1.0 / 0.06,
        "archivo": guardar_procesado(salida, X, y, sesion, firmante, raw=puntos3, fps=1.0 / 0.06),
    }
    return resultado


def resumen_etiquetas(y: np.ndarray) -> dict[str, int]:
    etiquetas, conteos = np.unique(np.asarray(y), return_counts=True)
    return {str(e): int(c) for e, c in zip(etiquetas, conteos, strict=True)}


def contar_sesion(directorio: Path | str) -> dict[str, int]:
    """Cuenta muestras estáticas y secuencias dinámicas guardadas por etiqueta.

    Sirve para retomar una sesión de captura: muestra qué letras ya tienen datos.
    """
    directorio = Path(directorio)
    if not directorio.is_dir():
        return {}

    conteos: dict[str, int] = {}
    for archivo in sorted(directorio.glob("static_*.npz")):
        etiqueta = archivo.stem[len("static_") :]
        with np.load(archivo, allow_pickle=False) as datos:
            conteos[etiqueta] = conteos.get(etiqueta, 0) + len(datos["y"])
    for archivo in sorted(directorio.glob("dynamic_*.npz")):
        etiqueta = archivo.stem[len("dynamic_") :]
        with np.load(archivo, allow_pickle=False) as datos:
            conteos[etiqueta] = conteos.get(etiqueta, 0) + len(datos["y"])
    return conteos


def hash_archivo(archivo: Path | str, bloques: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(archivo, "rb") as f:
        while bloque := f.read(bloques):
            h.update(bloque)
    return h.hexdigest()


__all__ = [
    "Metadatos",
    "cargar_dinamico",
    "cargar_estatico",
    "cargar_procesado",
    "combinar_dinamicos",
    "combinar_estaticos",
    "contar_sesion",
    "guardar_dinamico",
    "guardar_estatico",
    "guardar_procesado",
    "hash_archivo",
    "importar_v1_dinamico",
    "importar_v1_estatico",
    "resumen_etiquetas",
]
