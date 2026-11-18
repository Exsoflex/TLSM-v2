from __future__ import annotations

from tlsm.gloss import Glosador, normalizar


def claves(texto: str) -> list[str]:
    return [g.clave for g in Glosador().glosar(texto)]


def test_normalizar_acentos_y_enie():
    assert normalizar("Adiós") == "adios"
    assert normalizar("MAÑANA") == "mañana"


def test_palabra_conocida_y_puntuacion():
    assert claves("Hola, gracias") == ["HOLA", "PAUSA", "GRACIAS"]


def test_frase_de_dos_palabras():
    assert claves("buenos días") == ["BUENOS_DIAS"]
    assert claves("por favor") == ["POR_FAVOR"]


def test_desconocida_se_deletrea():
    assert claves("xyz") == ["X", "Y", "Z"]


def test_enie_se_deletrea_como_etiqueta():
    resultado = claves("mañana")
    assert resultado == ["M", "A", "N_TILDE", "A", "N", "A"]


def test_vacio():
    assert Glosador().glosar("   ") == []


def test_duracion_por_tipo():
    glosas = Glosador().glosar("hola z")
    assert glosas[0].tipo == "palabra"
    assert glosas[-1].tipo == "letra"
    assert all(g.duracion_ms > 0 for g in glosas)
