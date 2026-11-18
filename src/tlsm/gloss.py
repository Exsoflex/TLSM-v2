"""Glosado: español -> secuencia de glosas LSM.

Esto es un punto de partida, no un traductor de LSM. El orden de las palabras del
español no es el de la LSM y la gramática es propia; por eso el MVP produce
"español signado": palabras conocidas + deletreo para lo desconocido.

La interfaz está pensada para que un glosador real (o un modelo de traducción) la
sustituya sin cambiar la UI ni el renderizador.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

VOCABULARIO: dict[str, str] = {
    "hola": "HOLA",
    "adios": "ADIOS",
    "gracias": "GRACIAS",
    "por favor": "POR_FAVOR",
    "perdon": "PERDON",
    "si": "SI",
    "no": "NO",
    "buenos dias": "BUENOS_DIAS",
    "buenas tardes": "BUENAS_TARDES",
    "buenas noches": "BUENAS_NOCHES",
    "como estas": "COMO_ESTAS",
    "bien": "BIEN",
    "mal": "MAL",
    "ayuda": "AYUDA",
    "agua": "AGUA",
    "comida": "COMIDA",
    "escuela": "ESCUELA",
    "maestro": "MAESTRO",
    "maestra": "MAESTRA",
    "alumno": "ALUMNO",
    "alumna": "ALUMNA",
    "familia": "FAMILIA",
    "mama": "MAMA",
    "papa": "PAPA",
    "amigo": "AMIGO",
    "amiga": "AMIGA",
    "nombre": "NOMBRE",
    "que": "QUE",
    "quien": "QUIEN",
    "donde": "DONDE",
    "cuando": "CUANDO",
    "por que": "POR_QUE",
    "sordo": "SORDO",
    "sorda": "SORDA",
    "oyente": "OYENTE",
    "interprete": "INTERPRETE",
}

# Frases de varias palabras: se buscan antes que las palabras sueltas.
FRASES: dict[str, str] = {clave: valor for clave, valor in VOCABULARIO.items() if " " in clave}
PALABRAS: dict[str, str] = {
    clave: valor for clave, valor in VOCABULARIO.items() if " " not in clave
}

SIMBOLOS = {
    "?": "INTERROGACION",
    "!": "EXCLAMACION",
    ",": "PAUSA",
    ".": "PAUSA",
    ";": "PAUSA",
}

DURACION_PALABRA_MS = 1200
DURACION_LETRA_MS = 500
DURACION_PAUSA_MS = 350


@dataclass(frozen=True)
class Glosa:
    """Unidad mínima de renderización."""

    clave: str  # HOLA, A, PAUSA...
    texto: str  # palabra original o letra
    tipo: str  # "palabra" | "letra" | "pausa"
    duracion_ms: int
    no_manual: dict[str, str] = field(default_factory=dict)


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes y con la ñ protegida como N_TILDE."""
    texto = texto.strip().lower()
    texto = texto.replace("ñ", "\x00")
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return texto.replace("\x00", "ñ")


def _etiqueta_letra(caracter: str) -> str:
    return "N_TILDE" if caracter == "ñ" else caracter.upper()


class Glosador:
    """Convierte texto libre en una lista de glosas."""

    def __init__(
        self,
        vocabulario: dict[str, str] | None = None,
        frases: dict[str, str] | None = None,
    ) -> None:
        self.vocabulario = dict(VOCABULARIO if vocabulario is None else vocabulario)
        self.frases = dict(FRASES if frases is None else frases)
        self.palabras = {
            clave: valor for clave, valor in self.vocabulario.items() if " " not in clave
        }
        if frases is not None:
            self.frases = dict(frases)
        elif vocabulario is not None:
            self.frases = {k: v for k, v in self.vocabulario.items() if " " in k}

    def glosar(self, texto: str) -> list[Glosa]:
        normalizado = normalizar(texto)
        if not normalizado:
            return []

        # Separar símbolos de puntuación como tokens.
        tokens = re.findall(r"[a-zñ]+|[?!,.;]", normalizado)
        glosas: list[Glosa] = []
        i = 0
        while i < len(tokens):
            if tokens[i] in SIMBOLOS:
                glosas.append(
                    Glosa(
                        SIMBOLOS[tokens[i]],
                        tokens[i],
                        "pausa",
                        DURACION_PAUSA_MS,
                    )
                )
                i += 1
                continue

            encontrada = False
            for largo in (3, 2):
                if i + largo <= len(tokens):
                    frase = " ".join(tokens[i : i + largo])
                    if frase in self.frases:
                        glosas.append(
                            Glosa(self.frases[frase], frase, "palabra", DURACION_PALABRA_MS)
                        )
                        i += largo
                        encontrada = True
                        break
            if encontrada:
                continue

            palabra = tokens[i]
            if palabra in self.palabras:
                glosas.append(
                    Glosa(self.palabras[palabra], palabra, "palabra", DURACION_PALABRA_MS)
                )
            else:
                glosas.extend(
                    Glosa(_etiqueta_letra(c), c, "letra", DURACION_LETRA_MS) for c in palabra
                )
            i += 1
        return glosas


__all__ = ["DURACION_LETRA_MS", "DURACION_PALABRA_MS", "Glosa", "Glosador", "normalizar"]
