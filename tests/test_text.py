from __future__ import annotations

from tlsm.text import CompositorTexto


def test_agrega_letras_y_respeta_cooldown():
    comp = CompositorTexto()
    assert comp.agregar_evento("A", ahora=10.0) is True
    assert comp.texto == "A"
    assert comp.agregar_evento("A", ahora=10.5) is False
    assert comp.agregar_evento("B", ahora=10.2) is True
    assert comp.texto == "AB"


def test_borrar_y_limpiar():
    comp = CompositorTexto()
    comp.agregar_evento("A", ahora=1.0)
    comp.agregar_evento("B", ahora=2.0)
    comp.borrar()
    assert comp.texto == "A"
    comp.limpiar()
    assert comp.texto == ""


def test_espacio_manual_no_duplica():
    comp = CompositorTexto()
    comp.agregar_evento("A", ahora=1.0)
    comp.espacio()
    comp.espacio()
    assert comp.texto == "A "


def test_espacio_automatico_al_retirar_la_mano():
    comp = CompositorTexto()
    comp.agregar_evento("A", ahora=10.0)
    comp.actualizar_mano(True, ahora=10.0)
    comp.actualizar_mano(False, ahora=10.2)
    assert comp.texto == "A"
    comp.actualizar_mano(False, ahora=12.0)
    assert comp.texto == "A "


def test_retirar_mano_permite_repetir_letra():
    comp = CompositorTexto()
    comp.agregar_evento("A", ahora=10.0)
    assert comp.agregar_evento("A", ahora=10.5) is False
    comp.actualizar_mano(True, ahora=10.6)
    comp.actualizar_mano(False, ahora=10.7)
    assert comp.agregar_evento("A", ahora=10.8) is True
    assert comp.texto == "AA"


def test_display_de_enie():
    comp = CompositorTexto()
    comp.agregar_evento("N_TILDE", ahora=1.0)
    assert comp.texto == "Ñ"
