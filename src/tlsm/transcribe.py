"""Voz -> texto (ASR).

El MVP no necesita ASR, pero la interfaz se define ahora para que la fase
bidireccional no obligue a reestructurar. `faster-whisper` es MIT y corre offline.
Se importa de forma perezosa: el paquete es opcional.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np


class Transcriptor(Protocol):
    disponible: bool

    def transcribir(self, audio: np.ndarray, sample_rate: int = 16000) -> str: ...


class TranscriptorNulo:
    disponible = False

    def transcribir(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        return ""


class TranscriptorFasterWhisper:
    """Adaptador mínimo sobre faster-whisper (CPU por defecto)."""

    def __init__(
        self,
        modelo: str = "small",
        idioma: str = "es",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self.modelo = modelo
        self.idioma = idioma
        self.device = device
        self.compute_type = compute_type
        self._motor = None
        self.error: str | None = None
        try:
            from faster_whisper import WhisperModel  # noqa: F401
        except ImportError:
            self.error = "faster-whisper no está instalado (pip install 'tlsm[speech]')"

    @property
    def disponible(self) -> bool:
        return self.error is None

    def _cargar(self):
        if self._motor is None:
            from faster_whisper import WhisperModel

            self._motor = WhisperModel(
                self.modelo,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._motor

    def transcribir(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        if not self.disponible:
            return ""
        audio = np.asarray(audio, dtype=np.float32)
        if audio.size == 0:
            return ""
        if sample_rate != 16000:
            raise ValueError("faster-whisper espera audio a 16 kHz")
        segmentos, _ = self._cargar().transcribe(
            audio,
            language=self.idioma,
            vad_filter=True,
        )
        return " ".join(segmento.text.strip() for segmento in segmentos).strip()


__all__ = ["Transcriptor", "TranscriptorFasterWhisper", "TranscriptorNulo"]
