"""Composición del texto reconocido.

Separa la lógica de "cuándo agregar una letra" de la UI y del modelo.
"""

from __future__ import annotations

import time

from .config import ConfigReconocimiento, display


class CompositorTexto:
    def __init__(self, cfg: ConfigReconocimiento | None = None) -> None:
        self.cfg = cfg or ConfigReconocimiento()
        self.texto = ""
        self.ultima_etiqueta = ""
        self.ultimo_agregado = 0.0
        self.mano_presente = True
        self.ultima_mano = time.monotonic()
        self._espacio_por_ausencia = False

    # ------------------------------------------------------------------
    # Eventos del reconocedor
    # ------------------------------------------------------------------

    def agregar_evento(self, etiqueta: str, ahora: float | None = None) -> bool:
        """Agrega una etiqueta confirmada. Devuelve True si modificó el texto."""
        if not etiqueta:
            return False
        ahora = time.monotonic() if ahora is None else ahora

        if ahora - self.ultimo_agregado < 0.15:
            return False

        if (
            etiqueta == self.ultima_etiqueta
            and ahora - self.ultimo_agregado < self.cfg.cooldown_repetir_s
        ):
            return False

        self.texto += display(etiqueta)
        self.ultima_etiqueta = etiqueta
        self.ultimo_agregado = ahora
        self._espacio_por_ausencia = False
        return True

    # ------------------------------------------------------------------
    # Presencia de la mano y edición
    # ------------------------------------------------------------------

    def actualizar_mano(self, presente: bool, ahora: float | None = None) -> None:
        """Gestiona la liberación de la última letra y el espacio automático."""
        ahora = time.monotonic() if ahora is None else ahora

        if presente:
            self.mano_presente = True
            self.ultima_mano = ahora
            self._espacio_por_ausencia = False
            return

        if self.mano_presente:
            self.mano_presente = False
            self.ultima_mano = ahora
            # Al retirar la mano se "suelta" la letra: permite repetirla.
            self.ultima_etiqueta = ""

        if (
            not self._espacio_por_ausencia
            and self.texto
            and not self.texto.endswith(" ")
            and ahora - self.ultima_mano >= self.cfg.ausencia_para_espacio_s
        ):
            self.texto += " "
            self._espacio_por_ausencia = True
            self.ultimo_agregado = ahora

    def espacio(self) -> None:
        if self.texto and not self.texto.endswith(" "):
            self.texto += " "
        self.ultima_etiqueta = ""

    def borrar(self) -> None:
        self.texto = self.texto[:-1]
        self.ultima_etiqueta = ""

    def limpiar(self) -> None:
        self.texto = ""
        self.ultima_etiqueta = ""

    def soltar(self) -> None:
        """Permite volver a reconocer la misma letra (p. ej. al cambiar de seña)."""
        self.ultima_etiqueta = ""


__all__ = ["CompositorTexto"]
