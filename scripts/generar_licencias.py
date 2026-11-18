"""Copia los textos de licencia de las dependencias instaladas.

Se ejecuta antes de publicar un instalador, para cumplir con los avisos de
Apache-2.0, BSD, MIT y MPL-2.0. El resultado va a `licenses/`, que no se versiona.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\generar_licencias.py
"""

from __future__ import annotations

import shutil
from importlib.metadata import distributions
from pathlib import Path

from _path import RAIZ, asegurar_src

asegurar_src()

PREFIJOS = ("LICENSE", "LICENCE", "COPYING", "NOTICE", "COPYRIGHT")


def main() -> int:
    destino = RAIZ / "licenses"
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)

    filas: list[str] = []
    copiados = 0

    for dist in sorted(distributions(), key=lambda d: (d.metadata["Name"] or "").lower()):
        nombre = dist.metadata["Name"]
        version = dist.version
        if not nombre:
            continue
        for archivo in dist.files or []:
            if not archivo.name.upper().startswith(PREFIJOS):
                continue
            origen = Path(archivo.locate())
            if not origen.is_file():
                continue
            etiqueta = f"{nombre}-{version}-{origen.name}"
            shutil.copyfile(origen, destino / etiqueta)
            filas.append(f"| {nombre} | {version} | `{etiqueta}` |")
            copiados += 1

    indice = destino / "INDICE.md"
    indice.write_text(
        "# Licencias de dependencias instaladas\n\n"
        "Generado por `scripts/generar_licencias.py`. Se debe distribuir junto con la app.\n\n"
        "| Paquete | Versión | Archivo |\n|---|---|---|\n" + "\n".join(filas) + "\n",
        encoding="utf-8",
    )

    print(f"Licencias copiadas: {copiados}")
    print(f"Indice: {indice}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
