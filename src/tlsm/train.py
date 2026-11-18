"""Entrenamiento y evaluación con división honesta.

Regla de oro: nunca dividir frames al azar. Los frames consecutivos son casi
idénticos y producen métricas falsas (en la v1 daban 99.9% en vez de 91.3%).

Modos de división:
    - "sesion": grupos completos por sesión. Es el modo correcto.
    - "bloque": bloques contiguos por clase. Sirve como aproximación temporal
      cuando todos los datos vienen de una sola sesión (caso de la v1).
    - "aleatorio": solo para comparar y detectar fuga de datos. Nunca para reportar.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit, StratifiedShuffleSplit

from .config import REPORTES, VERSION_APP, VERSION_FEATURES, display
from .model_io import PaqueteModelo

MODOS_SPLIT = ("auto", "sesion", "bloque", "aleatorio")


def dividir_indices(
    y: np.ndarray,
    sesion: np.ndarray,
    modo: str = "auto",
    test_size: float = 0.2,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, str]:
    y = np.asarray(y)
    sesion = np.asarray(sesion).astype(str)
    if modo not in MODOS_SPLIT:
        raise ValueError(f"Modo de split inválido: {modo}")

    if modo == "auto":
        modo = "sesion" if len(np.unique(sesion)) >= 3 else "bloque"

    if modo == "sesion":
        grupos = len(np.unique(sesion))
        if grupos < 3:
            raise ValueError(
                f"El split por sesión necesita al menos 3 sesiones y hay {grupos}. "
                "Usa --split bloque mientras tanto."
            )
        divisor = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
        train, test = next(divisor.split(np.zeros(len(y)), y, groups=sesion))
        return np.sort(train), np.sort(test), "sesion"

    if modo == "bloque":
        train_idx: list[int] = []
        test_idx: list[int] = []
        for etiqueta in np.unique(y):
            indices = np.flatnonzero(y == etiqueta)
            if len(indices) < 2:
                train_idx.extend(indices.tolist())
                continue
            corte = int(round(len(indices) * (1.0 - test_size)))
            corte = max(1, min(len(indices) - 1, corte))
            train_idx.extend(indices[:corte].tolist())
            test_idx.extend(indices[corte:].tolist())
        return np.array(sorted(train_idx)), np.array(sorted(test_idx)), "bloque"

    divisor = StratifiedShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train, test = next(divisor.split(np.zeros(len(y)), y))
    return np.sort(train), np.sort(test), "aleatorio"


def _crear_modelo(seed: int) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        max_features="sqrt",
        n_jobs=-1,
        random_state=seed,
    )


def _evaluar(paquete: PaqueteModelo, X: np.ndarray, y: np.ndarray) -> dict:
    probabilidades = paquete.probabilidades(X)
    predicciones = np.array([max(p, key=p.get) for p in probabilidades])
    etiquetas = sorted({str(e) for e in np.unique(y)} | set(paquete.etiquetas))

    matriz = confusion_matrix(y, predicciones, labels=etiquetas)
    reporte = classification_report(
        y,
        predicciones,
        labels=etiquetas,
        output_dict=True,
        zero_division=0,
    )
    por_clase = {
        etiqueta: {
            "precision": float(reporte[etiqueta]["precision"]),
            "recall": float(reporte[etiqueta]["recall"]),
            "f1": float(reporte[etiqueta]["f1-score"]),
            "soporte": int(reporte[etiqueta]["support"]),
        }
        for etiqueta in etiquetas
        if etiqueta in reporte
    }
    return {
        "accuracy": float(accuracy_score(y, predicciones)),
        "macro_f1": float(
            f1_score(y, predicciones, labels=etiquetas, average="macro", zero_division=0)
        ),
        "weighted_f1": float(
            f1_score(y, predicciones, labels=etiquetas, average="weighted", zero_division=0)
        ),
        "por_clase": por_clase,
        "matriz": matriz.tolist(),
        "etiquetas": etiquetas,
    }


def entrenar(
    X: np.ndarray,
    y: np.ndarray,
    sesion: np.ndarray,
    tipo: str = "estatico",
    modo_split: str = "auto",
    test_size: float = 0.2,
    seed: int = 42,
) -> tuple[PaqueteModelo, dict]:
    if tipo not in {"estatico", "dinamico"}:
        raise ValueError(f"Tipo inválido: {tipo}")
    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y).astype(str)

    train, test, modo = dividir_indices(y, sesion, modo_split, test_size, seed)
    if len(test) == 0 or len(train) == 0:
        raise ValueError("La división dejó un conjunto vacío; revisa los datos.")

    modelo = _crear_modelo(seed)
    formato = "vector" if tipo == "estatico" else "secuencia_aplanada"
    X_train = X[train].reshape(len(train), -1) if tipo == "dinamico" else X[train]
    modelo.fit(X_train, y[train])

    paquete = PaqueteModelo(
        modelo=modelo,
        etiquetas=[str(c) for c in modelo.classes_],
        tipo=tipo,
        formato_entrada=formato,
        version_features=VERSION_FEATURES,
        metadatos={
            "version_app": VERSION_APP,
            "creado": datetime.now(UTC).isoformat(timespec="seconds"),
            "modo_split": modo,
            "test_size": test_size,
            "seed": seed,
            "n_train": int(len(train)),
            "n_test": int(len(test)),
        },
    )

    metricas = _evaluar(paquete, X[test], y[test])
    metricas.update(
        {
            "tipo": tipo,
            "modo_split": modo,
            "n_train": int(len(train)),
            "n_test": int(len(test)),
            "n_total": int(len(y)),
            "clases": [str(c) for c in np.unique(y)],
            "distribucion": {
                str(k): int(v) for k, v in zip(*np.unique(y, return_counts=True), strict=True)
            },
            "sesiones": [str(s) for s in np.unique(sesion)],
            "version_features": VERSION_FEATURES,
            "version_app": VERSION_APP,
            "fecha": datetime.now(UTC).isoformat(timespec="seconds"),
        }
    )
    return paquete, metricas


def guardar_reporte(
    metricas: dict, tipo: str, directorio: Path | str = REPORTES
) -> tuple[Path, Path]:
    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{tipo}_{sello}"

    json_path = directorio / f"{base}.json"
    json_path.write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")

    png_path = directorio / f"{base}.png"
    _graficar_matriz(metricas, png_path)
    return json_path, png_path


def _graficar_matriz(metricas: dict, destino: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    etiquetas = metricas["etiquetas"]
    matriz = np.asarray(metricas["matriz"])
    legibles = [display(e) for e in etiquetas]

    tamano = max(6.0, 0.6 * len(etiquetas))
    figura, eje = plt.subplots(figsize=(tamano, tamano))
    imagen = eje.imshow(matriz, cmap="Blues")
    figura.colorbar(imagen, ax=eje, fraction=0.046)
    eje.set(
        xticks=np.arange(len(etiquetas)),
        yticks=np.arange(len(etiquetas)),
        xticklabels=legibles,
        yticklabels=legibles,
        ylabel="Real",
        xlabel="Predicho",
        title=f"Matriz de confusion ({metricas['tipo']}, split {metricas['modo_split']})",
    )
    plt.setp(eje.get_xticklabels(), rotation=45, ha="right")
    limite = matriz.max() if matriz.size else 0
    for i in range(matriz.shape[0]):
        for j in range(matriz.shape[1]):
            valor = matriz[i, j]
            if valor:
                eje.text(
                    j,
                    i,
                    str(int(valor)),
                    ha="center",
                    va="center",
                    color="white" if valor > limite / 2 else "black",
                    fontsize=8,
                )
    figura.tight_layout()
    figura.savefig(destino, dpi=130)
    plt.close(figura)


def resumen_texto(metricas: dict) -> str:
    lineas = [
        f"Tipo: {metricas['tipo']}  |  Split: {metricas['modo_split']}",
        f"Muestras: {metricas['n_train']} train / {metricas['n_test']} test "
        f"({metricas['n_total']} total)",
        f"Accuracy: {metricas['accuracy']:.3f}  |  Macro-F1: {metricas['macro_f1']:.3f}",
        f"Clases: {len(metricas['clases'])}",
        "",
        f"{'Clase':<10} {'Prec':>6} {'Recall':>6} {'F1':>6} {'N':>5}",
    ]
    for etiqueta in metricas["etiquetas"]:
        datos = metricas["por_clase"].get(etiqueta)
        if not datos:
            continue
        lineas.append(
            f"{display(etiqueta):<10} {datos['precision']:>6.2f} {datos['recall']:>6.2f} "
            f"{datos['f1']:>6.2f} {datos['soporte']:>5}"
        )
    return "\n".join(lineas)


__all__ = [
    "MODOS_SPLIT",
    "dividir_indices",
    "entrenar",
    "guardar_reporte",
    "resumen_texto",
]
