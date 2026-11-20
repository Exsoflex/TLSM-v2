# TLSM — Traductor de Lengua de Señas Mexicana

Aplicación de escritorio para reconocer **Lengua de Señas Mexicana (LSM)** con la cámara.

Repositorio: **https://github.com/Exsoflex/TLSM-v2**

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

**Línea base con los datos v1 + primera sesión v2 (13 letras estáticas):**

| Modelo | Split | Accuracy | Macro-F1 |
|---|---|---|---|
| Estático | bloques contiguos por clase | **0.982** | **0.983** |
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

# 4. Convertir los datos v1 al esquema v2 (solo la primera vez)
.\.venv\Scripts\python.exe scripts\importar_v1.py

# 5. Entrenar modelos v2
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo dinamico

# 6. Captura guiada de datos (interfaz recomendada)
.\.venv\Scripts\python.exe scripts\capturar_ui.py

# Alternativa: una sola letra desde la terminal
.\.venv\Scripts\python.exe scripts\capturar.py --letra A --firmante S01

# 7. Consolidar sesiones capturadas y reentrenar
#    (consolidar suma sin borrar; se puede repetir)
.\.venv\Scripts\python.exe scripts\consolidar.py
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo dinamico
```

## Captura guiada de datos

`scripts/capturar_ui.py` es la forma recomendada de grabar el abecedario. Muestra las 27
letras con su progreso, la descripción oficial de cada seña y guarda sola cada ronda; no
hay que escribir un comando por letra.

```powershell
# Empezar una sesión nueva (pregunta firmante y sesión)
.\.venv\Scripts\python.exe scripts\capturar_ui.py

# Todo explícito, con 3 rondas por letra
.\.venv\Scripts\python.exe scripts\capturar_ui.py --firmante S01 --sesion 2026-11-18_01

# Solo algunas letras o solo las que faltan
.\.venv\Scripts\python.exe scripts\capturar_ui.py --letras A,B,C,J --rondas 3
.\.venv\Scripts\python.exe scripts\capturar_ui.py --solo-faltantes
```

**Cómo se usa**

1. Escribe el identificador del firmante (`S01`) y el nombre de la sesión
   (`2026-11-18_01`). Si repites la misma sesión, la app **retoma el progreso**.
2. Elige la letra con las flechas (o `A`/`D`/`W`/`S`) y pulsa `ESPACIO`.
3. **Letras estáticas** (A, B, C, …): mantén la seña quieta; la app descarta los frames con
   movimiento y guarda 100 muestras por ronda.
4. **Letras dinámicas** (`*` en la cuadrícula: J, K, Ñ, Q, X, Z): tras la cuenta regresiva,
   haz el movimiento; se guardan 20 frames por secuencia, 10 secuencias por ronda.
5. Al terminar las 3 rondas, la letra queda en verde y la app **salta sola a la siguiente
   pendiente**. `TAB` también salta a la siguiente pendiente.

| Tecla | Acción |
|---|---|
| `ESPACIO` | iniciar o continuar una ronda |
| `TAB` | ir a la siguiente letra pendiente |
| Flechas / `A` `D` `W` `S` | moverse por la cuadrícula de letras |
| `R` | descartar la ronda en curso |
| `H` | mostrar/ocultar la ayuda |
| `Q` / `ESC` | salir (lo ya guardado se conserva) |

**Consejos para datos útiles**

- Buena luz frontal, fondo limpio y la mano completa dentro del cuadro.
- Graba varias sesiones y, si puedes, **varios firmantes**; un solo firmante hace que el
  modelo memorice a la persona.
- No mezcles la seña de una letra con otra: si dudas, descarta con `R` y repite.
- Los datos quedan en `data/raw/<sesion>/static_<LETRA>.npz` y `dynamic_<LETRA>.npz`.

**Opciones principales**

| Opción | Por defecto | Para qué |
|---|---|---|
| `--firmante` | pregunta / `S01` | identifica a la persona |
| `--sesion` | fecha y hora | agrupa y permite retomar |
| `--letras` | todas | lista separada por comas (`A,B,J`) |
| `--rondas` | `3` | rondas por letra |
| `--muestras-ronda` | `100` | muestras por ronda estática |
| `--secuencias-ronda` | `10` | secuencias por ronda dinámica |
| `--solo-faltantes` | desactivado | empieza en la primera letra pendiente |
| `--sin-auto-avance` | desactivado | no cambia de letra al completarla |
| `--camara` | `0` | índice de cámara |
| `--sin-espejo` | desactivado | desactiva el espejo de la imagen |

Al terminar, consolida y reentrena:

```powershell
.\.venv\Scripts\python.exe scripts\consolidar.py
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo dinamico
```

## Detector y entrenamiento

El **detector principal** es `scripts/app.py` (interfaz OpenCV) sobre `src/tlsm/recognize.py`.
Combina dos modelos:

- **Estático:** letras con la mano quieta (A–I, L, M, N, O en el modelo actual).
- **Dinámico:** secuencias de 20 frames (J, K, Ñ y Hola en el modelo actual).

No hay que programar nada para añadir una letra: se captura, se consolida y se reentrena.
El modelo aprende las clases que existan en el dataset, sin tocar código. **Lo que no esté
entrenado no se reconoce**; si haces una letra nueva, el modelo responderá con la más parecida
de las que conoce.

### Flujo completo

```powershell
# 1. Capturar (interfaz guiada)
.\.venv\Scripts\python.exe scripts\capturar_ui.py --firmante S01 --sesion 2026-11-20_01

# 2. Sumar las sesiones nuevas al dataset (se puede repetir sin duplicar)
.\.venv\Scripts\python.exe scripts\consolidar.py

# 3. Entrenar los dos modelos
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo dinamico

# 4. Usar el detector
.\.venv\Scripts\python.exe scripts\app.py
```

`consolidar.py` **conserva** lo que ya estaba procesado (incluida la v1) y **reemplaza**
solo las sesiones que aparezcan en `data/raw`. Ejecutarlo dos veces no duplica datos.

### Qué produce el entrenamiento

| Archivo | Contenido |
|---|---|
| `models/estatico_v2.joblib` | modelo de letras quietas + etiquetas + metadatos |
| `models/dinamico_v2.joblib` | modelo de movimientos + etiquetas + metadatos |
| `reports/estatico_<fecha>.json` | accuracy, macro-F1, métricas por clase y matriz |
| `reports/estatico_<fecha>.png` | matriz de confusión legible |
| `reports/dinamico_<fecha>.json/.png` | lo mismo para movimientos |

Opciones útiles:

```powershell
# Forzar un tipo de división (por defecto "auto")
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico --split sesion
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico --split bloque

# Cambiar el tamaño de prueba o la semilla
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico --test-size 0.25 --seed 7

# Guardar en otra ruta o no generar el reporte
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo dinamico --salida models/prueba.joblib --sin-reporte
```

**Cómo leer las métricas:** `accuracy` es el porcentaje total; **macro-F1** promedia las
clases sin favorecer a las mayoritarias. El split `bloque` divide por tramos contiguos y sirve
cuando hay una sola sesión; el split `sesion` es el honesto y necesita al menos 3 sesiones.
Nunca uses `--split aleatorio` para reportar: mezcla frames casi idénticos y da métricas falsas.

### Teclas del detector (`scripts/app.py`)

| Tecla | Acción |
|---|---|
| `ESPACIO` | agregar un espacio al texto |
| `B` / `Retroceso` | borrar el último carácter |
| `C` | limpiar el texto |
| `V` | decir el texto con voz (TTS) |
| `L` | mostrar u ocultar los landmarks |
| `R` | reiniciar el reconocimiento |
| `Q` / `ESC` | salir |

```powershell
# Sin voz, o con otra cámara o modelos
.\.venv\Scripts\python.exe scripts\app.py --sin-voz
.\.venv\Scripts\python.exe scripts\app.py --camara 1
.\.venv\Scripts\python.exe scripts\app.py --modelo models\estatico_v2.joblib
```

### Para reconocer las 27 letras

1. Captura las que faltan: estáticas **P, R, S, T, U, V, W, Y** y dinámicas **Q, X, Z**.
2. Repite con varias sesiones y, si puedes, varios firmantes.
3. Consolida y reentrena. El detector pasará a mostrar esas clases automáticamente.

Las palabras y frases **no** están implementadas todavía: el detector actual es de letras y
movimientos aislados. Esa es la Fase 5 del plan y requiere otro dataset y, probablemente, un
modelo de secuencias.

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
├─ scripts/                # interfaz de línea de comandos y apps
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
| `capture_ui.py` | interfaz guiada de captura: cuadrícula, progreso y guardado automático |
| `drawing.py` | utilidades de dibujo OpenCV compartidas por las interfaces |
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
- **Primera sesión v2:** `2026-11-20_1307`, 300 muestras de A capturadas con la interfaz.
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

- **[GUIA_PROYECTO.md](GUIA_PROYECTO.md)** — visión, decisiones, arquitectura, plan, riesgos,
  bitácora y **manual de uso completo** (sección 16: captura → consolidación → entrenamiento
  → detector).
- `THIRD_PARTY_LICENSES.md` — cumplimiento de licencias.
- `docs/diccionario_oficial.pdf` — *Diccionario de Lengua de Señas Mexicana "Manos con voz"* (2011).
- `docs/diccionario_oficial.txt` — texto extraído para búsquedas.
