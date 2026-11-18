"""Renderizado de glosas a señas.

Hoy no hay avatar 3D. Lo que sí está definido es el contrato:

    Glosador -> lista[Glosa] -> RenderizadorSenias -> video/avatar

La primera implementación reproduce clips pregrabados por glosa. Si falta un clip,
se informa en vez de inventar movimiento. Cuando llegue el avatar 3D, se agrega otro
renderizador sin tocar el reconocimiento, la UI ni el glosador.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .config import ASSETS
from .gloss import Glosa

DIRECTORIO_CLIPS = ASSETS / "senias"
EXTENSIONES = (".mp4", ".webm", ".mov", ".mkv")


@dataclass(frozen=True)
class Segmento:
    glosa: Glosa
    inicio_ms: int
    duracion_ms: int


def construir_plan(glosas: list[Glosa]) -> list[Segmento]:
    """Asigna tiempos acumulados a cada glosa (sin transiciones todavía)."""
    plan: list[Segmento] = []
    cursor = 0
    for glosa in glosas:
        plan.append(Segmento(glosa, cursor, glosa.duracion_ms))
        cursor += glosa.duracion_ms
    return plan


class RenderizadorSenias(Protocol):
    disponible: bool

    def faltantes(self, glosas: list[Glosa]) -> list[str]: ...

    def renderizar(self, glosas: list[Glosa], destino: Path | str) -> Path: ...


class RenderizadorNulo:
    """Placeholder para cuando el avatar todavía no existe."""

    disponible = False

    def faltantes(self, glosas: list[Glosa]) -> list[str]:
        return sorted({g.clave for g in glosas if g.tipo != "pausa"})

    def renderizar(self, glosas: list[Glosa], destino: Path | str) -> Path:
        raise NotImplementedError(
            "El avatar 3D aún no está implementado. Usa RenderizadorClips cuando "
            "haya clips en assets/senias/."
        )


class RenderizadorClips:
    """Concatena clips de video por glosa.

    Limitación conocida: OpenCV no maneja audio, así que el resultado es mudo.
    Para la versión final se usará ffmpeg o el avatar 3D.
    """

    def __init__(self, directorio: Path | str = DIRECTORIO_CLIPS) -> None:
        self.directorio = Path(directorio)

    @property
    def disponible(self) -> bool:
        return self.directorio.is_dir() and bool(self.clips_disponibles())

    def clips_disponibles(self) -> dict[str, Path]:
        if not self.directorio.is_dir():
            return {}
        encontrados: dict[str, Path] = {}
        for archivo in self.directorio.iterdir():
            if archivo.suffix.lower() in EXTENSIONES and archivo.is_file():
                encontrados[archivo.stem.upper()] = archivo
        return encontrados

    def clip(self, clave: str) -> Path | None:
        return self.clips_disponibles().get(clave.upper())

    def faltantes(self, glosas: list[Glosa]) -> list[str]:
        return sorted({g.clave for g in glosas if g.tipo != "pausa" and self.clip(g.clave) is None})

    def renderizar(self, glosas: list[Glosa], destino: Path | str) -> Path:
        faltantes = self.faltantes(glosas)
        if faltantes:
            raise FileNotFoundError(f"Faltan clips para: {', '.join(faltantes)}")

        import cv2

        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        escritor: cv2.VideoWriter | None = None
        fps = 25.0
        tamano: tuple[int, int] | None = None

        try:
            for glosa in glosas:
                if glosa.tipo == "pausa":
                    continue
                ruta = self.clip(glosa.clave)
                if ruta is None:
                    continue
                captura = cv2.VideoCapture(str(ruta))
                while True:
                    ok, frame = captura.read()
                    if not ok:
                        break
                    if tamano is None:
                        tamano = (frame.shape[1], frame.shape[0])
                        escritor = cv2.VideoWriter(
                            str(destino),
                            cv2.VideoWriter_fourcc(*"mp4v"),
                            fps,
                            tamano,
                        )
                    if escritor is not None:
                        if (frame.shape[1], frame.shape[0]) != tamano:
                            frame = cv2.resize(frame, tamano)
                        escritor.write(frame)
                captura.release()
        finally:
            if escritor is not None:
                escritor.release()

        if not destino.exists():
            raise RuntimeError("No se generó ningún video: los clips estaban vacíos")
        return destino


__all__ = [
    "DIRECTORIO_CLIPS",
    "RenderizadorClips",
    "RenderizadorNulo",
    "RenderizadorSenias",
    "Segmento",
    "construir_plan",
]
