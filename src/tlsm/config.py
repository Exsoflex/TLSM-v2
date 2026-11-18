"""Configuración central del proyecto TLSM.

Regla: ningún número mágico en el resto del código. Todo parámetro ajustable vive aquí.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parents[2]
ASSETS = RAIZ / "assets"
MODELO_MANOS = ASSETS / "mediapipe" / "hand_landmarker.task"

DATA = RAIZ / "data"
DATA_RAW = DATA / "raw"
DATA_PROCESSED = DATA / "processed"
MODELOS = RAIZ / "models"
REPORTES = RAIZ / "reports"

MODELO_ESTATICO = MODELOS / "estatico_v2.joblib"
MODELO_DINAMICO = MODELOS / "dinamico_v2.joblib"

VERSION_APP = "0.2.0"
VERSION_FEATURES = "v2-21x3-canonico"
MODELO_LANDMARKS = "mediapipe-1.2.3-hand_landmarker-float16"

# ---------------------------------------------------------------------------
# Etiquetas
# ---------------------------------------------------------------------------

LETRAS: tuple[str, ...] = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ("N_TILDE",)

# Letras con movimiento según el diccionario oficial "Manos con voz".
LETRAS_DINAMICAS: frozenset[str] = frozenset({"J", "K", "N_TILDE", "Q", "X", "Z"})
LETRAS_ESTATICAS: tuple[str, ...] = tuple(
    letra for letra in LETRAS if letra not in LETRAS_DINAMICAS
)

DISPLAY: dict[str, str] = {"N_TILDE": "Ñ"}
DISPLAY_ASCII: dict[str, str] = {"N_TILDE": "N~"}


def display(etiqueta: str) -> str:
    """Texto legible para consola, reportes y web (las etiquetas internas son ASCII)."""
    return DISPLAY.get(etiqueta, etiqueta)


def display_ascii(etiqueta: str) -> str:
    """Texto para OpenCV: las fuentes Hershey no dibujan la Ñ."""
    return DISPLAY_ASCII.get(etiqueta, display(etiqueta))


def es_letra(etiqueta: str) -> bool:
    return etiqueta in LETRAS


def es_dinamica(etiqueta: str) -> bool:
    return etiqueta in LETRAS_DINAMICAS


# ---------------------------------------------------------------------------
# Configuración de cámara y features
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConfigCamara:
    indice: int = 0
    ancho: int = 640
    alto: int = 480
    espejo: bool = True


@dataclass(frozen=True)
class ConfigFeatures:
    usar_z: bool = True
    normalizar_escala: bool = True
    rotar: bool = True
    espejar_zurdas: bool = True


@dataclass(frozen=True)
class ConfigCaptura:
    muestras_estaticas: int = 300
    intervalo_estatico_ms: int = 40
    muestras_dinamicas: int = 30
    frames_dinamicos: int = 20
    fps_dinamicos: float = 15.0
    cuenta_regresiva_s: float = 3.0
    movimiento_maximo_estatico: float = 0.012
    estable_frames: int = 3


@dataclass(frozen=True)
class ConfigReconocimiento:
    # Estático
    ventana_estatica: int = 10
    votos_minimos: int = 7
    confianza_minima: float = 0.60
    margen_minimo: float = 0.15
    cooldown_letra_s: float = 0.45
    # Movimiento
    ventana_movimiento: int = 20
    fps_movimiento: float = 15.0
    umbral_inicio: float = 0.006
    frames_para_iniciar: int = 2
    umbral_movimiento_total: float = 0.05
    confianza_movimiento: float = 0.55
    cooldown_gesto_s: float = 1.0
    # Texto
    ausencia_para_espacio_s: float = 1.5
    cooldown_repetir_s: float = 1.2


@dataclass(frozen=True)
class ConfigUI:
    alto: int = 480
    ancho_panel: int = 420
    fuente: int = 0  # cv2.FONT_HERSHEY_SIMPLEX
    mostrar_landmarks: bool = True


@dataclass(frozen=True)
class ConfigVoz:
    velocidad: int = 160
    volumen: float = 1.0
    activa: bool = True


@dataclass(frozen=True)
class ConfigProyecto:
    camara: ConfigCamara = field(default_factory=ConfigCamara)
    features: ConfigFeatures = field(default_factory=ConfigFeatures)
    captura: ConfigCaptura = field(default_factory=ConfigCaptura)
    reconocimiento: ConfigReconocimiento = field(default_factory=ConfigReconocimiento)
    ui: ConfigUI = field(default_factory=ConfigUI)
    voz: ConfigVoz = field(default_factory=ConfigVoz)


CONFIG = ConfigProyecto()
