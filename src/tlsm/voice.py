"""Salida de voz offline.

`pyttsx3` usa SAPI5 en Windows (MPL-2.0). Se ejecuta en un solo hilo con una cola
para evitar el problema de la v1, que creaba un motor nuevo por cada frase.
"""

from __future__ import annotations

import contextlib
import queue
import threading
from typing import Protocol

from .config import ConfigVoz


class SalidaVoz(Protocol):
    disponible: bool

    def decir(self, texto: str) -> None: ...

    def cerrar(self) -> None: ...


class VozNula:
    """Implementación para pruebas o para cuando no hay audio."""

    disponible = False

    def decir(self, texto: str) -> None:
        return None

    def cerrar(self) -> None:
        return None


class VozPyttsx3:
    """Un solo motor y un solo hilo, con cola de frases."""

    def __init__(self, cfg: ConfigVoz | None = None) -> None:
        self.cfg = cfg or ConfigVoz()
        self.disponible = False
        self.error: str | None = None
        self._cola: queue.Queue[str | None] = queue.Queue()
        self._listo = threading.Event()
        self._hilo = threading.Thread(target=self._trabajar, name="tts", daemon=True)
        self._hilo.start()
        self._listo.wait(timeout=5.0)

    def _trabajar(self) -> None:
        try:
            import pyttsx3

            motor = pyttsx3.init()
            motor.setProperty("rate", self.cfg.velocidad)
            motor.setProperty("volume", self.cfg.volumen)
        except Exception as exc:  # noqa: BLE001 - sin audio la app debe seguir
            self.error = f"{type(exc).__name__}: {exc}"
            self._listo.set()
            return

        self.disponible = True
        self._listo.set()
        while True:
            texto = self._cola.get()
            if texto is None:
                break
            try:
                motor.say(texto)
                motor.runAndWait()
            except Exception:  # noqa: BLE001 - una frase fallida no debe tumbar el hilo
                continue
        with contextlib.suppress(Exception):
            motor.stop()

    def decir(self, texto: str) -> None:
        if not texto.strip() or not self.cfg.activa:
            return
        self._cola.put(texto)

    def cerrar(self) -> None:
        self._cola.put(None)
        self._hilo.join(timeout=3.0)


__all__ = ["SalidaVoz", "VozNula", "VozPyttsx3"]
