# TLSM — Traductor de Lengua de Señas Mexicana

Aplicación de escritorio para reconocer **Lengua de Señas Mexicana (LSM)** con la cámara.

- **Ahora:** letras del abecedario (dactilología), estáticas y con movimiento.
- **Después:** palabras, frases y traducción bidireccional:
  - señas → texto → voz
  - voz → texto → señas (avatar 3D)
- **Producto:** app de escritorio **offline** y, más adelante, versión **web**.

> Este repositorio nació de un prototipo (v1) que tenía fuga de datos y dependía de una API
> de MediaPipe ya eliminada. La v2 reescribe el núcleo con features canónicas, metadatos,
> división honesta de datos y una arquitectura que permite añadir el avatar 3D sin rehacer todo.

## Estado

| Fase | Estado |
|---|---|
| 0. Rescate de repo y entorno | ✅ 2026-11-18 |
| 1. Reacomodo y archivo del legado | ✅ 2026-11-18 |
| 2. Núcleo v2 (features, captura, modelo, UI) | ✅ 2026-11-18 |
| 3. Recaptura del abecedario completo (27 letras) | ⏳ siguiente |
| 4. Producto (instalable, web) | pendiente |
| 5. Palabras, bidireccionalidad y avatar 3D | pendiente |

**Línea base con los datos v1 (13 letras estáticas):**

| Modelo | Split | Accuracy | Macro-F1 |
|---|---|---|---|
| Estático | bloques contiguos por clase | **0.981** | **0.982** |
| Dinámico (J, K, Ñ, Hola) | bloques contiguos por clase | **0.986** | **0.983** |

Son datos de un solo firmante y una sola sesión, así que **no** equivalen a la meta de
sesión no vista. La meta real está en la guía.

La guía completa, decisiones, hallazgos y bitácora están en **[GUIA_PROYECTO.md](GUIA_PROYECTO.md)**.

## Requisitos

- Windows 10/11
- Python **3.11**
- Cámara web

## Instalación

```powershell
cd C:\dev\TLSM
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe scripts\check_entorno.py
```

Para desarrollo:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check src scripts tests
```

> El proyecto **no debe vivir dentro de OneDrive**: OneDrive deshidrata `.git`, los DLL y los
> `.pack`, y rompe el repositorio y el entorno virtual. Trabajar en `C:\dev\TLSM`.

## Uso rápido

```powershell
# 1. Verificar entorno, modelo y cámaras
.\.venv\Scripts\python.exe scripts\check_entorno.py

# 2. Demo de detección de manos
.\.venv\Scripts\python.exe scripts\demo_camara.py

# 3. App de reconocimiento (requiere un modelo entrenado)
.\.venv\Scripts\python.exe scripts\app.py

# 4. Convertir los datos v1 al esquema v2
.\.venv\Scripts\python.exe scripts\importar_v1.py

# 5. Entrenar modelos v2
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo dinamico

# 6. Capturar datos nuevos
.\.venv\Scripts\python.exe scripts\capturar.py --letra A --firmante S01
.\.venv\Scripts\python.exe scripts\capturar.py --letra J --firmante S01

# 7. Consolidar sesiones capturadas y reentrenar
.\.venv\Scripts\python.exe scripts\consolidar.py
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico
```

### Teclas de la app

| Tecla | Acción |
|---|---|
| `ESPACIO` | agregar espacio |
| `B` / `Retroceso` | borrar último carácter |
| `C` | limpiar texto |
| `V` | hablar el texto (TTS) |
| `L` | mostrar/ocultar landmarks |
| `Q` / `ESC` | salir |

## Estructura

```
TLSM/
├─ assets/
│  ├─ mediapipe/           # hand_landmarker.task (Apache-2.0)
│  └─ senias/              # clips de señas para texto -> señas (fase 5)
├─ data/                   # raw/ y processed/ (no se versionan)
├─ docs/                   # diccionario oficial LSM (PDF + texto)
├─ legacy/                 # código y datos de la v1, solo referencia
├─ models/                 # modelos entrenados (no se versionan)
├─ reports/                # métricas y matrices de confusión (no se versionan)
├─ scripts/                # interfaz de línea de comandos
├─ src/tlsm/               # núcleo reutilizable (sin cámara ni ventana)
├─ tests/                  # pytest
├─ GUIA_PROYECTO.md        # memoria y decisiones del proyecto
└─ THIRD_PARTY_LICENSES.md
```

### Núcleo (`src/tlsm`)

| Módulo | Responsabilidad |
|---|---|
| `config.py` | rutas, etiquetas, parámetros (sin números mágicos) |
| `features.py` | landmarks → vector canónico de 63 dimensiones |
| `landmarks.py` | MediaPipe Tasks `HandLandmarker` (único módulo que conoce MediaPipe) |
| `camera.py` | cámara de escritorio (OpenCV) |
| `datasets.py` | esquema v2 `.npz`, metadatos e importación de la v1 |
| `capture.py` | captura guiada estática/dinámica con muestreo fijo |
| `recognize.py` | máquina de estados de reconocimiento → eventos |
| `text.py` | composición del texto (repetición, espacio, borrar) |
| `train.py` | entrenamiento, split por sesión/bloque, métricas |
| `model_io.py` | paquetes de modelo versionados |
| `ui.py` | interfaz de escritorio (OpenCV) |
| `voice.py` | TTS offline con un solo hilo y cola (`pyttsx3`) |
| `gloss.py` | español → glosas LSM (español signado + deletreo) |
| `render.py` | contrato `RenderizadorSenias` + clips pregrabados |
| `transcribe.py` | contrato de ASR + adaptador `faster-whisper` opcional |

## Datos

- **v1 estático:** 12,599 muestras de 13 letras (A–I, L, M, N, O), solo `x,y`.
- **v1 dinámico:** 709 secuencias de 20 frames (J, K, Ñ, Hola).
- **Abecedario oficial:** 27 letras. Faltan por capturar:
  - estáticas: **P, R, S, T, U, V, W, Y**
  - dinámicas: **Q, X, Z**
- El esquema v2 guarda 21 landmarks × `(x,y,z)` normalizados (traslación, escala,
  rotación y espejo de manos izquierdas) y metadatos de sesión, firmante y cámara.
- Los datasets y modelos no se versionan: se regeneran con los scripts.

## Licencias

- Código del proyecto: **MIT** (`LICENSE`).
- Dependencias: solo Apache-2.0, BSD, MIT y MPL-2.0 (ver `THIRD_PARTY_LICENSES.md`).
- **MSL-150** (dataset de 150 señas de LSM): **CC-BY-4.0**, usable con atribución.
- **Excluidos:** MMS-Player (GPL-3.0) y SignAvatars (sin licencia).
- Antes de publicar un instalador: `python scripts/generar_licencias.py`.

## Documentación

- `GUIA_PROYECTO.md` — visión, decisiones, arquitectura, plan, riesgos y bitácora.
- `THIRD_PARTY_LICENSES.md` — cumplimiento de licencias.
- `docs/diccionario_oficial.pdf` — *Diccionario de Lengua de Señas Mexicana "Manos con voz"* (2011).
- `docs/diccionario_oficial.txt` — texto extraído para búsquedas.
