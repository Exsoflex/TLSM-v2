"""Interfaz guiada de captura de datos LSM.

Objetivo: que grabar el abecedario sea rápido y difícil de hacer mal.

- Muestra las 27 letras con su progreso y una guía corta de cómo formarlas.
- Guarda automáticamente cada ronda; no hay que escribir comandos por letra.
- Distingue letras estáticas (mano quieta) de dinámicas (movimiento).
- Permite elegir firmante, sesión y número de rondas.
- Al completar una letra, salta sola a la siguiente pendiente.

Teclas:
    ESPACIO  iniciar / continuar una ronda
    TAB      siguiente letra pendiente
    FLECHAS  elegir letra (también A/D/W/S)
    R        descartar la ronda en curso
    H        ayuda
    Q / ESC  salir (lo guardado se conserva)
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import dataclass
from datetime import datetime

import cv2
import numpy as np

from .camera import abrir_camara, cerrar, leer
from .capture import CapturadorDinamico, CapturadorEstatico, EstadoCaptura
from .config import (
    CONFIG,
    DATA_RAW,
    LETRAS,
    MODELO_MANOS,
    ConfigCamara,
    display_ascii,
    es_dinamica,
)
from .datasets import Metadatos, contar_sesion, guardar_dinamico, guardar_estatico
from .drawing import FUENTE, barra_progreso, dibujar_mano, envolver_texto
from .landmarks import FrameLandmarks, FuenteManos

ANCHO_CAMARA = 640
ALTO_CAMARA = 480
ANCHO_PANEL = 460
ALTO_GRILLA = 150
ANCHO_TOTAL = ANCHO_CAMARA + ANCHO_PANEL

FONDO = (26, 26, 32)
FONDO_PANEL = (34, 34, 42)
TEXTO = (238, 238, 242)
SUAVE = (168, 168, 178)
VERDE = (95, 215, 125)
AMARILLO = (60, 205, 240)
ROJO = (90, 90, 235)
AZUL = (235, 175, 60)

PREPARACION_DINAMICA_S = 2.0
PAUSA_ENTRE_SECUENCIAS_S = 1.2

TIPS: dict[str, str] = {
    "A": "Puno cerrado, palma al frente, pulgar estirado hacia un lado.",
    "B": "Indice a menique extendidos y unidos; pulgar doblado sobre la palma.",
    "C": "Dedos unidos en posicion concava, pulgar igual; palma a un lado.",
    "D": "Indice estirado; medio, anular, menique y pulgar unidos por las puntas.",
    "E": "Dedos doblados mostrando las unas; palma al frente.",
    "F": "Mano abierta con dedos unidos; el indice doblado toca la yema del pulgar.",
    "G": "Puno con indice y pulgar estirados; palma hacia ti.",
    "H": "Puno con indice y medio extendidos y unidos; pulgar hacia arriba.",
    "I": "Puno con el menique extendido hacia arriba; palma de lado.",
    "J": "Menique extendido hacia arriba; dibuja una J en el aire.",
    "K": "Indice, medio y pulgar extendidos; pulgar entre indice y medio; muneca arriba.",
    "L": "Indice y pulgar estirados formando una L; palma al frente.",
    "M": "Indice, medio y anular sobre el pulgar; mano cerrada.",
    "N": "Indice y medio sobre el pulgar; mano cerrada.",
    "N_TILDE": "Indice y medio sobre el pulgar; mueve la muneca a los lados.",
    "O": "Todos los dedos se tocan por las puntas formando una O.",
    "P": "Indice, medio y pulgar extendidos; pulgar entre indice y medio.",
    "Q": "Indice y pulgar en garra, palma abajo; mueve la muneca a los lados.",
    "R": "Indice y medio estirados y entrelazados; palma al frente.",
    "S": "Puno con el pulgar sobre los otros dedos; palma al frente.",
    "T": "Puno con el pulgar entre el indice y el medio; palma al frente.",
    "U": "Indice y medio extendidos y unidos; palma al frente.",
    "V": "Indice y medio extendidos y separados; palma al frente.",
    "W": "Indice, medio y anular extendidos y separados; palma al frente.",
    "X": "Indice y pulgar en garra; movimiento al frente y de regreso.",
    "Y": "Menique y pulgar extendidos; palma hacia ti.",
    "Z": "Indice extendido; dibuja una Z en el aire.",
}


@dataclass(frozen=True)
class Opciones:
    firmante: str
    sesion: str
    camara: int
    rondas: int
    muestras_ronda: int
    secuencias_ronda: int
    letras: tuple[str, ...]
    auto_avanzar: bool
    notas: str
    espejo: bool


def letras_desde(texto: str) -> tuple[str, ...]:
    if not texto.strip():
        return LETRAS
    elegidas: list[str] = []
    for parte in texto.replace(";", ",").split(","):
        limpio = parte.strip().upper().replace("Ñ", "N_TILDE")
        if not limpio:
            continue
        if limpio not in LETRAS:
            raise SystemExit(f"Letra invalida: {parte}. Opciones: {', '.join(LETRAS)}")
        if limpio not in elegidas:
            elegidas.append(limpio)
    return tuple(elegidas) or LETRAS


class AppCaptura:
    def __init__(
        self,
        opciones: Opciones,
        fuente: FuenteManos,
        camara: cv2.VideoCapture,
    ) -> None:
        self.op = opciones
        self.fuente = fuente
        self.camara = camara
        self.meta = Metadatos(
            sesion=opciones.sesion,
            firmante=opciones.firmante,
            camara=f"camara_{opciones.camara}",
            notas=opciones.notas,
        )
        self.directorio = DATA_RAW / opciones.sesion
        self.conteos = contar_sesion(self.directorio)

        self.seleccion = 0
        self.fase = "inactivo"  # inactivo | preparando | grabando | ronda_lista
        self.capturador: CapturadorEstatico | CapturadorDinamico | None = None
        self.estado: EstadoCaptura | None = None
        self.preparacion_hasta = 0.0
        self.secuencias_ronda = 0
        self.mensaje = "ESPACIO para empezar"
        self.ayuda = False
        self.fps = 0.0
        self._anterior = time.perf_counter()

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------

    @property
    def letra(self) -> str:
        return self.op.letras[self.seleccion]

    @property
    def dinamica(self) -> bool:
        return es_dinamica(self.letra)

    def unidad(self, letra: str) -> int:
        return self.op.secuencias_ronda if es_dinamica(letra) else self.op.muestras_ronda

    def objetivo(self, letra: str) -> int:
        return self.op.rondas * self.unidad(letra)

    def muestras(self, letra: str) -> int:
        return self.conteos.get(letra, 0)

    def completa(self, letra: str) -> bool:
        return self.muestras(letra) >= self.objetivo(letra)

    @property
    def completas(self) -> int:
        return sum(1 for letra in self.op.letras if self.completa(letra))

    def _ronda_actual(self) -> int:
        hechas = self.muestras(self.letra) // max(1, self.unidad(self.letra))
        return min(self.op.rondas, hechas + 1)

    def _nuevo_capturador(self) -> CapturadorEstatico | CapturadorDinamico:
        if self.dinamica:
            return CapturadorDinamico(
                self.letra,
                CONFIG.captura,
                CONFIG.features,
                frames=CONFIG.captura.frames_dinamicos,
                fps=CONFIG.captura.fps_dinamicos,
            )
        return CapturadorEstatico(
            self.letra,
            CONFIG.captura,
            CONFIG.features,
            muestras=self.op.muestras_ronda,
        )

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _iniciar_ronda(self, ahora: float) -> None:
        if self.fase in ("preparando", "grabando"):
            return
        self.capturador = self._nuevo_capturador()
        self.estado = None
        self.secuencias_ronda = 0
        if self.dinamica:
            self.fase = "preparando"
            self.preparacion_hasta = ahora + PREPARACION_DINAMICA_S
            self.mensaje = "Preparate para la secuencia 1"
        else:
            self.capturador.iniciar(ahora)
            self.fase = "grabando"
            self.mensaje = "Manten la mano quieta"

    def _descartar_ronda(self) -> None:
        if self.fase not in ("preparando", "grabando"):
            return
        self.capturador = None
        self.estado = None
        self.secuencias_ronda = 0
        self.fase = "inactivo"
        self.mensaje = "Ronda descartada. ESPACIO para repetir"

    def _actualizar(self, deteccion: FrameLandmarks | None, ahora: float) -> None:
        if self.fase == "preparando":
            if deteccion is None:
                self.preparacion_hasta = ahora + PREPARACION_DINAMICA_S
                self.mensaje = "Muestra la mano para continuar"
                return
            if ahora < self.preparacion_hasta:
                return
            assert self.capturador is not None
            self.capturador.iniciar(ahora)
            self.fase = "grabando"
            self.mensaje = "Grabando movimiento..."
            return

        if self.fase != "grabando" or self.capturador is None:
            return

        estado = self.capturador.actualizar(
            deteccion.puntos if deteccion is not None else None,
            deteccion.mano if deteccion is not None else "Right",
            ahora=ahora,
        )
        self.estado = estado
        if estado.fase != "listo":
            return

        if self.dinamica:
            self._guardar_secuencia(ahora)
        else:
            self._guardar_ronda_estatica()

    def _guardar_ronda_estatica(self) -> None:
        assert isinstance(self.capturador, CapturadorEstatico)
        try:
            X, raw = self.capturador.resultado()
            guardar_estatico(self.directorio, self.letra, X, raw, self.meta)
        except Exception as exc:  # noqa: BLE001 - mostrar el error sin cerrar la app
            self.mensaje = f"ERROR al guardar: {exc}"
            self.fase = "inactivo"
            self.capturador = None
            return

        self.conteos[self.letra] = self.muestras(self.letra) + len(X)
        self.capturador = None
        self.estado = None
        self.fase = "ronda_lista"
        self.mensaje = f"Ronda guardada ({len(X)} muestras)"
        self._despues_de_ronda()

    def _guardar_secuencia(self, ahora: float) -> None:
        assert isinstance(self.capturador, CapturadorDinamico)
        try:
            X, raw, fps = self.capturador.resultado()
            guardar_dinamico(
                self.directorio,
                self.letra,
                X[None, ...],
                raw[None, ...],
                fps,
                self.meta,
            )
        except Exception as exc:  # noqa: BLE001
            self.mensaje = f"ERROR al guardar: {exc}"
            self.fase = "inactivo"
            self.capturador = None
            return

        self.conteos[self.letra] = self.muestras(self.letra) + 1
        self.secuencias_ronda += 1
        self.capturador = None
        self.estado = None

        if self.secuencias_ronda >= self.op.secuencias_ronda:
            self.secuencias_ronda = 0
            self.fase = "ronda_lista"
            self.mensaje = f"Ronda guardada ({self.op.secuencias_ronda} secuencias)"
            self._despues_de_ronda()
            return

        self.capturador = self._nuevo_capturador()
        self.fase = "preparando"
        self.preparacion_hasta = ahora + PAUSA_ENTRE_SECUENCIAS_S
        self.mensaje = (
            f"Secuencia {self.secuencias_ronda + 1}/{self.op.secuencias_ronda}: preparate"
        )

    def _despues_de_ronda(self) -> None:
        objetivo = self.objetivo(self.letra)
        if not self.completa(self.letra):
            faltan = objetivo - self.muestras(self.letra)
            self.mensaje += f" - faltan {faltan}"
            return

        if self.completas >= len(self.op.letras):
            self.mensaje = "SESION COMPLETA. Q para salir"
            return

        if not self.op.auto_avanzar:
            self.mensaje = "Letra completa. TAB para la siguiente"
            return

        siguiente = self._siguiente_pendiente()
        if siguiente is None:
            self.mensaje = "SESION COMPLETA. Q para salir"
            return
        self.seleccion = siguiente
        self.fase = "inactivo"
        self.mensaje = f"{display_ascii(self.letra)} lista. ESPACIO para empezar"

    def _siguiente_pendiente(self) -> int | None:
        total = len(self.op.letras)
        for salto in range(1, total + 1):
            indice = (self.seleccion + salto) % total
            if not self.completa(self.op.letras[indice]):
                return indice
        return None

    def _mover(self, delta: int) -> None:
        self._descartar_ronda()
        self.seleccion = (self.seleccion + delta) % len(self.op.letras)
        self.fase = "inactivo"
        self.estado = None
        self.mensaje = "ESPACIO para empezar"

    def _ir_pendiente(self) -> None:
        siguiente = self._siguiente_pendiente()
        self._descartar_ronda()
        self.fase = "inactivo"
        self.estado = None
        if siguiente is None:
            self.mensaje = "Todas las letras estan completas"
            return
        self.seleccion = siguiente
        self.mensaje = "ESPACIO para empezar"

    # ------------------------------------------------------------------
    # Teclado
    # ------------------------------------------------------------------

    def _tecla(self, key: int, ahora: float) -> bool:
        if key == -1:
            return True
        if key in (27, ord("q")) or (key & 0xFF) in (27, ord("q")):
            return False

        if key in (ord("h"), ord("H")):
            self.ayuda = not self.ayuda
            return True
        if self.ayuda:
            return True

        if key == 32 or (key & 0xFF) == 32:
            if self.fase in ("inactivo", "ronda_lista"):
                self._iniciar_ronda(ahora)
            return True

        if key in (ord("r"), ord("R")):
            self._descartar_ronda()
            return True

        if key == 9:
            self._ir_pendiente()
            return True

        if key in (81, 2424832, ord("a"), ord("A")):
            self._mover(-1)
        elif key in (83, 2555904, ord("d"), ord("D")):
            self._mover(1)
        elif key in (82, 2490368, ord("w"), ord("W")):
            self._mover(-9)
        elif key in (84, 2621440, ord("s"), ord("S")):
            self._mover(9)
        return True

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------

    def _progreso_ronda(self) -> float:
        if self.fase == "grabando" and self.estado is not None:
            if self.dinamica:
                return min(
                    1.0,
                    (self.secuencias_ronda + self.estado.progreso) / self.op.secuencias_ronda,
                )
            return self.estado.progreso
        if self.fase == "preparando":
            return self.secuencias_ronda / max(1, self.op.secuencias_ronda)
        return min(1.0, self.muestras(self.letra) / max(1, self.objetivo(self.letra)))

    def _dibujar_ayuda(self, frame: np.ndarray) -> None:
        cv2.rectangle(frame, (10, 76), (630, 452), (18, 18, 24), -1)
        cv2.rectangle(frame, (10, 76), (630, 452), AZUL, 2)
        lineas = [
            "AYUDA",
            "",
            "ESPACIO   iniciar o continuar una ronda",
            "TAB       ir a la siguiente letra pendiente",
            "FLECHAS   elegir letra (tambien A/D/W/S)",
            "R         descartar la ronda en curso",
            "H         cerrar esta ayuda",
            "Q / ESC   salir (lo guardado se conserva)",
            "",
            "Cada ronda se guarda automaticamente.",
            f"Estatica: {self.op.muestras_ronda} muestras con la mano quieta.",
            f"Dinamica: {self.op.secuencias_ronda} secuencias de "
            f"{CONFIG.captura.frames_dinamicos} frames.",
        ]
        y = 110
        for i, linea in enumerate(lineas):
            escala = 0.85 if i == 0 else 0.58
            color = AZUL if i == 0 else TEXTO
            cv2.putText(frame, linea, (30, y), FUENTE, escala, color, 1, cv2.LINE_AA)
            y += 28 if i == 0 else 25
            if y > 440:
                break

    def _dibujar(
        self, frame: np.ndarray, deteccion: FrameLandmarks | None, ahora: float
    ) -> np.ndarray:
        frame = cv2.resize(frame, (ANCHO_CAMARA, ALTO_CAMARA))
        if deteccion is not None:
            color = AZUL if deteccion.mano == "Left" else VERDE
            dibujar_mano(frame, deteccion.puntos, color)

        cv2.rectangle(frame, (0, 0), (ANCHO_CAMARA, 70), (18, 18, 24), -1)
        tipo = "DINAMICA" if self.dinamica else "ESTATICA"
        cv2.putText(
            frame,
            f"{display_ascii(self.letra)}   {tipo}",
            (16, 32),
            FUENTE,
            0.85,
            VERDE,
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            self.mensaje[:78],
            (16, 58),
            FUENTE,
            0.5,
            TEXTO,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"{self.fps:4.1f} FPS",
            (ANCHO_CAMARA - 110, 30),
            FUENTE,
            0.5,
            SUAVE,
            1,
            cv2.LINE_AA,
        )

        # Cuenta regresiva grande.
        cuenta = None
        if self.fase == "preparando":
            cuenta = max(1, math.ceil(self.preparacion_hasta - ahora))
        elif self.fase == "grabando" and self.estado is not None and self.estado.fase == "cuenta":
            cuenta = self.estado.cuenta
        if cuenta is not None:
            texto = str(cuenta)
            tamano = cv2.getTextSize(texto, FUENTE, 3.0, 4)[0]
            cv2.putText(
                frame,
                texto,
                ((ANCHO_CAMARA - tamano[0]) // 2, (ALTO_CAMARA + tamano[1]) // 2),
                FUENTE,
                3.0,
                AMARILLO,
                4,
                cv2.LINE_AA,
            )

        barra_progreso(
            frame,
            16,
            ALTO_CAMARA - 30,
            ANCHO_CAMARA - 32,
            14,
            self._progreso_ronda(),
            VERDE,
        )
        cv2.putText(
            frame,
            f"Ronda {self._ronda_actual()}/{self.op.rondas}",
            (16, ALTO_CAMARA - 46),
            FUENTE,
            0.5,
            SUAVE,
            1,
            cv2.LINE_AA,
        )

        if self.ayuda:
            self._dibujar_ayuda(frame)

        panel = self._panel()
        grilla = self._grilla()
        lienzo = np.vstack([np.hstack([frame, panel]), grilla])
        cv2.imshow("TLSM - Captura guiada", lienzo)
        return lienzo

    def _panel(self) -> np.ndarray:
        panel = np.full((ALTO_CAMARA, ANCHO_PANEL, 3), FONDO_PANEL, dtype=np.uint8)
        cv2.putText(panel, "CAPTURA DE DATOS", (18, 32), FUENTE, 0.78, TEXTO, 2, cv2.LINE_AA)
        cv2.putText(
            panel,
            f"Sesion {self.op.sesion}",
            (18, 56),
            FUENTE,
            0.45,
            SUAVE,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            panel,
            f"Firmante {self.op.firmante}  |  Camara {self.op.camara}",
            (18, 75),
            FUENTE,
            0.45,
            SUAVE,
            1,
            cv2.LINE_AA,
        )
        cv2.line(panel, (18, 90), (ANCHO_PANEL - 18, 90), (70, 70, 82), 1)

        tipo = "DINAMICA (movimiento)" if self.dinamica else "ESTATICA"
        cv2.putText(
            panel,
            display_ascii(self.letra),
            (18, 146),
            FUENTE,
            1.9,
            VERDE,
            3,
            cv2.LINE_AA,
        )
        cv2.putText(panel, tipo, (130, 132), FUENTE, 0.5, SUAVE, 1, cv2.LINE_AA)

        lineas = envolver_texto(TIPS.get(self.letra, ""), ANCHO_PANEL - 40, 0.48, 1)
        for i, linea in enumerate(lineas[:4]):
            cv2.putText(
                panel,
                linea,
                (18, 178 + i * 21),
                FUENTE,
                0.48,
                TEXTO,
                1,
                cv2.LINE_AA,
            )

        cv2.line(panel, (18, 268), (ANCHO_PANEL - 18, 268), (70, 70, 82), 1)
        estado_lineas = envolver_texto(self.mensaje, ANCHO_PANEL - 40, 0.62, 2)
        for i, linea in enumerate(estado_lineas[:2]):
            cv2.putText(
                panel,
                linea,
                (18, 300 + i * 26),
                FUENTE,
                0.62,
                AMARILLO,
                2,
                cv2.LINE_AA,
            )

        barra_progreso(
            panel,
            18,
            338,
            ANCHO_PANEL - 36,
            16,
            self._progreso_ronda(),
            VERDE,
        )
        unidad = "secuencias" if self.dinamica else "muestras"
        cv2.putText(
            panel,
            f"Ronda {self._ronda_actual()}/{self.op.rondas}   |   "
            f"{self.muestras(self.letra)}/{self.objetivo(self.letra)} {unidad}",
            (18, 378),
            FUENTE,
            0.5,
            TEXTO,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            panel,
            f"Letras completas: {self.completas}/{len(self.op.letras)}",
            (18, 402),
            FUENTE,
            0.5,
            SUAVE,
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            panel,
            "ESPACIO grabar/continuar   TAB siguiente",
            (18, 430),
            FUENTE,
            0.42,
            SUAVE,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            panel,
            "Flechas letra   R reiniciar   H ayuda   Q salir",
            (18, 450),
            FUENTE,
            0.42,
            SUAVE,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            panel,
            "Guardado automatico en data/raw/<sesion>",
            (18, 470),
            FUENTE,
            0.38,
            (120, 120, 132),
            1,
            cv2.LINE_AA,
        )
        return panel

    def _grilla(self) -> np.ndarray:
        grilla = np.full((ALTO_GRILLA, ANCHO_TOTAL, 3), FONDO, dtype=np.uint8)
        cv2.putText(
            grilla,
            f"PROGRESO   {self.completas}/{len(self.op.letras)} letras completas"
            "   |   * = movimiento",
            (14, 22),
            FUENTE,
            0.5,
            SUAVE,
            1,
            cv2.LINE_AA,
        )

        columnas = 9
        ancho_celda = (ANCHO_TOTAL - 28) // columnas
        alto_celda = 34
        x0, y0 = 14, 32

        for indice, letra in enumerate(self.op.letras):
            fila, columna = divmod(indice, columnas)
            x = x0 + columna * ancho_celda
            y = y0 + fila * alto_celda
            if y + alto_celda > ALTO_GRILLA - 6:
                break

            hechas = self.muestras(letra)
            objetivo = self.objetivo(letra)
            if hechas >= objetivo:
                relleno = (38, 82, 52)
                color_texto = VERDE
            elif hechas > 0:
                relleno = (72, 64, 34)
                color_texto = AMARILLO
            else:
                relleno = (46, 46, 54)
                color_texto = SUAVE

            cv2.rectangle(
                grilla,
                (x, y),
                (x + ancho_celda - 6, y + alto_celda - 5),
                relleno,
                -1,
            )
            if indice == self.seleccion:
                cv2.rectangle(
                    grilla,
                    (x, y),
                    (x + ancho_celda - 6, y + alto_celda - 5),
                    AZUL,
                    2,
                )

            marca = "*" if es_dinamica(letra) else ""
            cv2.putText(
                grilla,
                f"{display_ascii(letra)}{marca}",
                (x + 8, y + 22),
                FUENTE,
                0.55,
                color_texto,
                2 if indice == self.seleccion else 1,
                cv2.LINE_AA,
            )
            cv2.putText(
                grilla,
                f"{min(hechas, objetivo)}/{objetivo}",
                (x + ancho_celda - 54, y + 21),
                FUENTE,
                0.36,
                color_texto,
                1,
                cv2.LINE_AA,
            )
        return grilla

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------

    def ejecutar(self) -> int:
        try:
            while True:
                ok, frame = leer(self.camara, espejo=self.op.espejo)
                if not ok:
                    print("No se pudo leer un frame de la camara.")
                    return 1

                detecciones = self.fuente.detectar_bgr(frame)
                deteccion = detecciones[0] if detecciones else None
                ahora = time.monotonic()

                delta = max(ahora - self._anterior, 1e-6)
                self.fps = 0.9 * self.fps + 0.1 * (1.0 / delta) if self.fps else 1.0 / delta
                self._anterior = ahora

                self._actualizar(deteccion, ahora)
                self._dibujar(frame, deteccion, ahora)

                key = cv2.waitKeyEx(1)
                if not self._tecla(key, time.monotonic()):
                    break
        finally:
            cv2.destroyAllWindows()
        return 0


def _pedir(pregunta: str, defecto: str) -> str:
    if not sys.stdin.isatty():
        return defecto
    try:
        respuesta = input(pregunta).strip()
    except EOFError:
        return defecto
    return respuesta or defecto


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Captura guiada de las letras de LSM",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--firmante", default=None, help="Identificador del firmante (S01)")
    parser.add_argument("--sesion", default=None, help="Nombre de la sesion (fecha_hora)")
    parser.add_argument("--camara", type=int, default=CONFIG.camara.indice)
    parser.add_argument("--rondas", type=int, default=3, help="Rondas por letra")
    parser.add_argument("--muestras-ronda", type=int, default=100, help="Solo estaticas")
    parser.add_argument("--secuencias-ronda", type=int, default=10, help="Solo dinamicas")
    parser.add_argument("--letras", default="", help="Lista separada por comas; vacio = todas")
    parser.add_argument(
        "--solo-faltantes", action="store_true", help="Empezar en la primera pendiente"
    )
    parser.add_argument("--sin-auto-avance", action="store_true")
    parser.add_argument("--notas", default="")
    parser.add_argument("--sin-espejo", action="store_true")
    args = parser.parse_args(argv)

    if args.rondas < 1 or args.muestras_ronda < 1 or args.secuencias_ronda < 1:
        parser.error("rondas, muestras-ronda y secuencias-ronda deben ser >= 1")

    hoy = datetime.now().strftime("%Y-%m-%d_%H%M")
    firmante = args.firmante or _pedir("Firmante [S01]: ", "S01")
    sesion = args.sesion or _pedir(f"Sesion [{hoy}]: ", hoy)
    letras = letras_desde(args.letras)

    opciones = Opciones(
        firmante=firmante,
        sesion=sesion,
        camara=args.camara,
        rondas=args.rondas,
        muestras_ronda=args.muestras_ronda,
        secuencias_ronda=args.secuencias_ronda,
        letras=letras,
        auto_avanzar=not args.sin_auto_avance,
        notas=args.notas,
        espejo=not args.sin_espejo,
    )

    captura = abrir_camara(ConfigCamara(indice=args.camara))
    if not captura.isOpened():
        print(f"No se pudo abrir la camara {args.camara}.")
        return 1

    print(f"Sesion: {sesion}   Firmante: {firmante}")
    print(f"Letras: {len(letras)}   Rondas por letra: {args.rondas}")
    print("Se guarda automaticamente. ESPACIO inicia, H ayuda, Q sale.")

    try:
        with FuenteManos(modelo=MODELO_MANOS, max_manos=1) as fuente:
            app = AppCaptura(opciones, fuente, captura)
            if args.solo_faltantes:
                pendiente = app._siguiente_pendiente()
                if pendiente is not None:
                    app.seleccion = pendiente
            return app.ejecutar()
    finally:
        cerrar(captura)


if __name__ == "__main__":
    raise SystemExit(main())
