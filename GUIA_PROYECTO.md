# GUÍA Y MEMORIA DEL PROYECTO TLSM

> Documento vivo. Es la fuente de verdad del proyecto y mi memoria de trabajo.
> Se actualiza al final de cada etapa. Si algo aquí contradice al código, gana el código
> y hay que corregir este documento.

**Última actualización:** 2026-11-20
**Ubicación oficial:** `C:\dev\TLSM` (fuera de OneDrive)
**Repositorio remoto:** https://github.com/Exsoflex/TLSM-v2 (rama `main`).
**Manual operativo:** sección 16 (captura → consolidación → entrenamiento → detector).

---

## 0. Cómo usar este documento

1. Antes de empezar, leer las secciones 2 (decisiones), 3 (estado) y 8 (plan).
2. Al terminar, actualizar la bitácora (sección 14) y mover los checks de la fase.
3. Toda decisión nueva se anota en la sección 2 con fecha. No se decide "de memoria".
4. Los números de la sección 4 son mediciones reales; si se recapturan datos, se actualizan.

---

## 1. Visión y alcance

**Qué es:** un traductor de Lengua de Señas Mexicana (LSM) que eventualmente funcione en dos direcciones.

| Dirección | Entrada | Salida | Cuándo |
|---|---|---|---|
| Señas → texto/voz | Cámara | Texto en pantalla + voz (TTS) | Ahora |
| Voz/texto → señas | Micrófono o teclado | Avatar 3D ejecutando señas | Fase 5 |

**Alcance por etapas:**
1. Abecedario completo (dactilología): 27 letras (A–Z + Ñ).
2. Palabras aisladas (vocabulario).
3. Frases con algo de gramática de LSM.
4. Bidireccionalidad con avatar 3D.

**Objetivo de producto:**
- App de escritorio que funcione **offline**.
- Versión **web** alojada en un servidor, compartiendo el mismo núcleo.
- Descargable/instalable y **distribuible a escuelas** sin conflictos de licencia.

**Público:** personas oyentes que están aprendiendo LSM (nosotros incluidos) y, a futuro,
personas sordas y sus familias. Todavía **no** hay validación con la comunidad sorda:
es el riesgo abierto más importante (sección 12).

---

## 2. Decisiones tomadas

| Fecha | Decisión | Razón / consecuencias |
|---|---|---|
| 2026-11-18 | **Sí se pueden recapturar los datos.** | Esquema v2 desde cero; la v1 queda como referencia y línea base. |
| 2026-11-18 | Empezar por **letras individuales**, luego palabras. | Reduce el problema; el abecedario está definido en el diccionario oficial. |
| 2026-11-18 | Producto **offline de escritorio** + **web futura**. | El núcleo es independiente de la UI y de OpenCV. |
| 2026-11-18 | La dirección **voz → texto → señas 3D** es fase 5, pero la arquitectura la prevé desde ahora. | Interfaces `Glosador`, `RenderizadorSenias`, `Transcriptor`. |
| 2026-11-18 | Fuente normativa: `docs/diccionario_oficial.pdf` (*Manos con voz*, 2011). | Material oficial disponible; no sustituye validación con personas sordas. |
| 2026-11-18 | **No trabajar dentro de OneDrive.** | OneDrive deshidrató `.git` y DLLs; corrompió repo y venv. |
| 2026-11-18 | Repositorio git nuevo y limpio. | El `.git` viejo está dañado (faltan `.pack`, commits ilegibles). |
| 2026-11-18 | Migrar a **MediaPipe Tasks** (1.x). | `mediapipe.solutions` fue eliminado en MediaPipe 1.x. |
| 2026-11-18 | Python **3.11**. | Compatible con MediaPipe 1.2.3, scikit-learn 1.9 y numpy 2.4. |
| 2026-11-18 | Licencia del proyecto: **MIT**. | Permite distribuir a escuelas y modificar sin obligar copyleft. |
| 2026-11-18 | Solo dependencias permisivas: Apache-2.0, BSD, MIT, MPL-2.0 y datos CC-BY. | Evitar problemas legales al distribuir. |
| 2026-11-18 | **Excluir MMS-Player (GPL-3.0)** y **SignAvatars (sin licencia)**. | Copyleft fuerte / sin permiso de reutilización. Solo referencia conceptual. |
| 2026-11-18 | **MSL-150** es **CC-BY-4.0** y se puede usar con atribución. | Aún no se incluye; sirve para arrancar palabras en la fase 5. |
| 2026-11-18 | UI de escritorio: **OpenCV** para el MVP. | Menos dependencias; se evaluará Qt/PySide6 cuando haya producto. |
| 2026-11-18 | Datos v2: 21 landmarks × `(x,y,z)`, normalización canónica. | Elimina dependencia de posición, escala y rotación; +precisión comprobada. |
| 2026-11-18 | Split de evaluación por **sesión**; "bloque" solo como aproximación temporal. | Evitar fuga de frames consecutivos. |
| 2026-11-18 | Muestreo dinámico a **tasa fija de 15 fps**. | La v1 muestreaba distinto en entrenamiento e inferencia. |
| 2026-11-18 | El core **no importa `cv2`** ni UI. | Permite escritorio y web con la misma lógica. |
| 2026-11-18 | Texto → señas: primero **clips pregrabados**, luego avatar 3D. | Reduce el riesgo de subestimar el avatar. |

**Pendiente de decidir:** repo remoto (¿nuevo o reutilizar `Exsoflex/TLSM`?), alcance del ASR
offline en el lanzamiento y origen de los clips/avatar.

---

## 3. Estado actual

### 3.1 Completado

**Fase 0 — rescate (2026-11-18)**
- Proyecto copiado a `C:\dev\TLSM`.
- Respaldo en `C:\dev\_backup_TLSM_2026-11-18` (40.3 MB, sin `venv` ni `.git`).
- El proyecto original de OneDrive **no se borró**.
- `.venv` nuevo con Python **3.11.9**.
- Dependencias fijadas: `mediapipe==1.2.3`, `opencv-contrib-python==5.1.0.95`,
  `numpy==2.4.6`, `pandas==3.1.1`, `scikit-learn==1.9.1`, `joblib==1.6.0`,
  `matplotlib==3.11.2`, `pyttsx3==2.99`, `pypdf==7.1.1`.
- `assets/mediapipe/hand_landmarker.task` (7.8 MB, Apache-2.0).
- `scripts/check_entorno.py` y `scripts/demo_camara.py` funcionando.
- Cámara `0` verificada a **640×480** (el driver no entrega 1280×720).
- Commits iniciales `c116221` y `00f7537`.

**Fase 1 — reacomodo (2026-11-18)**
- `legacy/` con todo el código y datos v1; rutas con `ñ` renombradas a ASCII.
- `src/tlsm/` (layout `src`), `tests/`, `data/`, `models/`, `reports/`.
- `.gitignore` para datos, modelos, reportes, `venv` y cachés.
- `.gitattributes` para LF/CRLF y binarios.
- `pyproject.toml` con dependencias, extras y configuración de `pytest`/`ruff`.
- `LICENSE` (MIT) y `THIRD_PARTY_LICENSES.md`.
- Licencias verificadas por GitHub API/PyPI (sección 6).

**Fase 2 — núcleo v2 (2026-11-18)**
- `config.py`, `features.py`, `landmarks.py`, `camera.py`, `datasets.py`, `capture.py`,
  `capture_ui.py`, `drawing.py`, `recognize.py`, `text.py`, `voice.py`, `train.py`,
  `model_io.py`, `ui.py`, `gloss.py`, `render.py`, `transcribe.py`.
- Scripts: `importar_v1.py`, `entrenar.py`, `capturar.py`, `capturar_ui.py`, `app.py`,
  `generar_licencias.py`, además de los de la fase 0.
- Paquete instalado en modo editable (`pip install -e .`).
- **50 tests** en verde; `ruff check` y `ruff format` limpios.
- Datos v1 convertidos a v2: 12,599 muestras estáticas y 709 secuencias dinámicas.
- Modelos base entrenados y evaluados (sección 4.3).
- La app de escritorio abre, detecta manos, clasifica letras y compone texto con voz.
- **Repositorio remoto creado:** https://github.com/Exsoflex/TLSM-v2 (commit `f735dd0`).
- **Interfaz de captura guiada** (`scripts/capturar_ui.py`): cuadrícula de 27 letras con
  progreso, guía oficial por letra, rondas automáticas, guardado por ronda, reanudación de
  sesión y auto-avance a la siguiente letra pendiente.
- **Primera sesión v2 capturada:** `2026-11-20_1307`, 300 muestras de A (3 rondas).
- `consolidar.py` ahora **suma** las sesiones de `data/raw` al dataset procesado y reemplaza
  solo las sesiones repetidas; antes habría borrado la v1. Opción `--desde-cero` para
  reconstruir solo desde `data/raw`.
- `importar_v1.py` también mezcla: reimportar la v1 conserva las sesiones nuevas.
- **Manual operativo completo en la sección 16:** preparación, captura, consolidación,
  entrenamiento, detector, flujo para añadir letras, ejemplo de jornada, problemas comunes
  y checklist.

### 3.2 Lo que todavía NO está

- Faltan **15 letras** del abecedario oficial: estáticas P, R, S, T, U, V, W, Y
  y dinámicas Q, X, Z. (Las 13 estáticas y 3 dinámicas existentes vienen de la v1;
  A ya tiene una sesión nueva de 300 muestras.)
- No hay detector de palabras ni frases: solo letras y movimientos aislados.
- No hay validación con personas sordas ni con más firmantes.
- No hay instalador (`PyInstaller`) ni versión web.
- No hay avatar 3D ni clips de señas; solo el contrato y el glosador preliminar.

### 3.3 Verificación rápida

```powershell
cd C:\dev\TLSM
.\.venv\Scripts\python.exe scripts\check_entorno.py --sin-camara
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico
.\.venv\Scripts\python.exe scripts\app.py
.\.venv\Scripts\python.exe scripts\capturar_ui.py --solo-faltantes
```

---

## 4. Diagnóstico y resultados

### 4.1 Dataset v1 estático (`legacy/v1/modelos/dataset_senas.csv`)

- 12,599 filas × 43 columnas (42 features + etiqueta).
- Features: 21 landmarks × `(x,y)` relativos a la muñeca, **sin `z`** y **sin normalizar escala**.
- 13 clases: A–I, L, M, N, O. 900 muestras por clase, **L con 1,799**.
- 2 features constantes (`x0`, `y0`); escala de mano varía **4.57×**.
- Sin metadatos de firmante, sesión, cámara, distancia ni iluminación.

### 4.2 Dataset v1 dinámico (`legacy/v1/modelos/dataset_movimiento.pkl`)

- 709 secuencias `(20, 42)`, aplanadas a 840 features en la v1.
- Etiquetas: `J` 255, `K` 152, `N_TILDE` 151, `HOLA` 151.
- Mezcla letras con una palabra en el mismo clasificador.
- RandomForest sobre el vector aplanado: pierde el orden temporal.

### 4.3 Línea base v2 (medición real)

Conversión con `scripts/importar_v1.py` y entrenamiento con `scripts/entrenar.py --tipo ...`.
El **2026-11-20** se sumó la primera sesión v2 (`2026-11-20_1307`, 300 muestras de A) y se
reentrenó. Split **bloque** (80/20 contiguo por clase) porque hay dos sesiones, pero una es
la v1 completa; el split por sesión honesto requiere al menos 3.

| Modelo | Train / Test | Accuracy | Macro-F1 |
|---|---|---|---|
| Estático (13 clases, 12,899 muestras) | 10,319 / 2,580 | **0.982** | **0.983** |
| Dinámico (4 clases, 709 secuencias) | 568 / 141 | **0.986** | **0.983** |

Clases con más error en estático: D (recall 0.89), O (recall 0.86), A (precisión 0.94).
El resto está en 0.94–1.00. El dinámico mantiene J, HOLA y Ñ casi perfectos; K tiene
recall 0.93.

**Comparación con la v1:**

| Evaluación | v1 | v2 |
|---|---|---|
| Split aleatorio (falso) | 99.9% | no se usa |
| Split temporal, features v1 | 91.3% | — |
| Split temporal + escala | 96.2% | — |
| Bloque + features canónicas | — | **98.1%** |

**Advertencia:** sigue siendo un solo firmante, una sola sesión y una cámara. La meta de
≥95% macro-F1 en **sesión no vista** solo se puede declarar después de la fase 3.

### 4.4 Problemas de la v1 (para no repetirlos)

- Split aleatorio de frames consecutivos → métricas infladas.
- Sin `z`, sin escala y sin rotación canónica.
- Índices de cámara inconsistentes (0 vs 1) y resolución asumida de 480 px.
- Muestreo de movimiento distinto en entrenamiento e inferencia.
- `pyttsx3.init()` por frase y en hilos nuevos; audio encimado.
- Se perdía la última letra y no se podían repetir letras sin retirar la mano.
- Rutas relativas al CWD, identificadores con `ñ`, números mágicos duplicados.
- Sin configuración, logs, tests ni manejo de errores.

---

## 5. Abecedario oficial de LSM (según *Manos con voz*)

El diccionario define **27 letras**: A–Z + Ñ. Abecedario en páginas 15–19 del PDF.

**Letras estáticas (21):** A, B, C, D, E, F, G, H, I, L, M, N, O, P, R, S, T, U, V, W, Y.

**Letras con movimiento (6):**

| Letra | Movimiento descrito en el manual |
|---|---|
| **J** | El meñique estirado dibuja una J en el aire. |
| **K** | Pulgar entre índice y medio; se mueve la muñeca hacia arriba. |
| **Ñ** | Índice y medio sobre el pulgar; se mueve la muñeca a los lados. |
| **Q** | Índice y pulgar en garra, palma abajo; muñeca a los lados. |
| **X** | Índice y pulgar en garra; movimiento al frente y de regreso. |
| **Z** | Índice estirado; dibuja una Z en el aire. |

**Cobertura actual (v1):**
- Estáticas: A–I, L, M, N, O (13 de 21).
- Dinámicas: J, K, Ñ (3 de 6).
- Faltan estáticas **P, R, S, T, U, V, W, Y** y dinámicas **Q, X, Z**.
- El dataset dinámico incluye además la palabra **HOLA**, que se debe separar del
  clasificador de letras cuando exista un modelo de palabras.

**Notas del manual que afectan el diseño:**
- La LSM tiene gramática propia y regionalismos; el orden del español es solo una metodología.
- El femenino y el plural se marcan con señas adicionales.
- Algunas letras cambian cuando forman parte de un ideograma (m, n, t).
- La expresión facial y corporal es parte de la lengua, no decoración.

---

## 6. Herramientas y licencias

> Verificado por GitHub API y PyPI el 2026-11-18.

### 6.1 Percepción

| Herramienta | Licencia | Uso |
|---|---|---|
| **MediaPipe Tasks** 1.2.3 | Apache-2.0 | `HandLandmarker`; después `PoseLandmarker` y `FaceLandmarker`. |
| **MediaPipe Tasks for Web** | Apache-2.0 | Landmarks en el navegador (WASM); clave para la web. |
| **OpenCV** (`opencv-contrib-python`) | Apache-2.0 | Captura, dibujo y ventanas. Solo adaptador de escritorio. |

**Decisión:** `HandLandmarker` en modo VIDEO. Para palabras/frases se agregará cuerpo y rostro.

### 6.2 Datos y modelos de LSM

| Recurso | Licencia | Uso |
|---|---|---|
| **MSL-150** (`armandobecerril/MSL-150-Dataset`, Zenodo `10.5281/zenodo.17783312`) | **CC-BY-4.0** | 150 señas de LSM con keypoints de MediaPipe Holistic; 1 firmante. Arranque del vocabulario de palabras. |
| `robbolla11/Mexican-Sign-Language-Alphabet-Real-Time-Detection` | Verificar | Referencia, no dependencia. |
| WLASL / AUTSL / Phoenix-14T | Académicas | Solo arquitectura y comparación; no son LSM. |
| `VIPL-SLP/Awesome-Sign-Language-Processing`, `ZechengLi19/Awesome-Sign-Language` | Listas | Consulta para modelos de secuencia. |

**Conclusión:** no existe un dataset público grande y confiable del **abecedario LSM**;
lo tenemos que crear nosotros. MSL-150 sirve para palabras, con atribución.

### 6.3 Texto ↔ señas

| Recurso | Licencia | Decisión |
|---|---|---|
| **sign-language-translator** (`sign-language-translator/sign-language-translator`) | Apache-2.0 | Referencia principal para texto→señas. Se puede integrar. |
| **SignWriting** (`sign-language-processing/signwriting-translation`) | MIT | Anotación formal; no necesario para el MVP. |
| **MMS-Player** (DFKI) | **GPL-3.0** | **Excluido** del producto. Solo referencia conceptual. |
| **SignAvatars** (ECCV 2024) | **Sin licencia** | **Excluido**. No se reutiliza sin permiso. |

**Estrategia texto→señas:** reproducir clips pregrabados por glosa, luego avatar 3D con el
mismo contrato `RenderizadorSenias`. No generar movimiento 3D desde cero al inicio.

### 6.4 Voz

| Recurso | Licencia | Notas |
|---|---|---|
| **pyttsx3** 2.99 | MPL-2.0 | TTS actual, offline en Windows (SAPI5). Un solo hilo y cola. |
| **faster-whisper** 1.2.1 | MIT | ASR offline rápido en CPU. Adaptador ya escrito. |
| **Piper TTS** 1.8.0 | MIT (el motor) | Mejor calidad; **revisar licencia de cada voz** (algunas CC-BY-NC-SA). |
| **Vosk** | Apache-2.0 | Alternativa ligera; calidad inferior. |

**Decisión:** `pyttsx3` para el MVP; Piper cuando la calidad importe. ASR en fase 5, con la
interfaz `Transcriptor` ya definida.

### 6.5 Web y despliegue

| Recurso | Licencia | Uso |
|---|---|---|
| **FastAPI + WebSocket** | MIT | Inferencia en servidor si hace falta. |
| **three.js** | MIT | Avatar 3D en web. |
| **ONNX Runtime** | MIT | Exportar el clasificador y no depender de `pickle`/versión de sklearn. |
| **Gradio / Streamlit** | Apache-2.0 | Demos rápidas, no producción. |

**Estrategia:** el navegador extrae landmarks con MediaPipe WASM y envía features, no video.
Así se protege la privacidad y se reduce ancho de banda. Si el modelo es pequeño, corre
entero en el cliente.

### 6.6 Desarrollo

- **Git LFS / DVC** para datasets y modelos grandes (a partir de la fase 3).
- **Ruff** (lint + format) y **pytest** ya configurados.
- **scikit-learn** para el baseline; **PyTorch** solo si los modelos de secuencia lo justifican.

---

## 7. Arquitectura

### 7.1 Principio rector

**El núcleo no sabe de cámaras, ventanas, navegadores ni altavoces.** Recibe landmarks o
texto y devuelve eventos, texto o glosas. Eso permite escritorio offline y web sin duplicar
lógica, y añadir el avatar 3D sin reescribir.

```
                 ENTRADAS
   cámara ──► landmarks ─┐
   micrófono ──► ASR ────┤
   teclado ──► texto ────┤
                         ▼
                 ┌───────────────┐
                 │  NÚCLEO TLSM  │
                 │  features     │
                 │  clasificador │
                 │  segmentador  │
                 │  compositor   │
                 │  glosas       │
                 └───────┬───────┘
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
     TEXTO             VOZ (TTS)       AVATAR 3D
   (pantalla)        (altavoz)        (señas)
```

### 7.2 Módulos e interfaces (implementados)

| Componente | Archivo | Contrato |
|---|---|---|
| Fuente de landmarks | `landmarks.py` | `FuenteManos.detectar_bgr(frame) -> list[FrameLandmarks]` |
| Features | `features.py` | `features(puntos, handedness) -> float32[63]` |
| Captura | `capture.py` | `CapturadorEstatico/Dinamico.actualizar(...) -> EstadoCaptura` |
| Captura guiada (UI) | `capture_ui.py` | `AppCaptura.ejecutar() -> int`; sesión, rondas y progreso |
| Dibujo compartido | `drawing.py` | `envolver_texto`, `dibujar_mano`, `barra_progreso` |
| Clasificadores | `model_io.py` | `PaqueteModelo.predecir(X) -> (etiqueta, confianza, margen)` |
| Reconocimiento | `recognize.py` | `Reconocedor.actualizar(deteccion) -> list[Evento]` |
| Texto | `text.py` | `CompositorTexto.agregar_evento / actualizar_mano` |
| Voz | `voice.py` | `SalidaVoz.decir(texto)` (cola, un hilo) |
| Glosado | `gloss.py` | `Glosador.glosar(texto) -> list[Glosa]` |
| Render | `render.py` | `RenderizadorSenias.renderizar(glosas, destino)` |
| ASR | `transcribe.py` | `Transcriptor.transcribir(audio) -> str` |
| UI | `ui.py` | adaptador OpenCV; no contiene lógica de negocio |

### 7.3 Contratos de datos

- **`FrameLandmarks`**: `puntos: float32[21,3]`, `mano`, `confianza`, `ts_ms`.
- **Muestra estática**: `features: float32[63]`, `label`, metadatos de sesión.
- **Secuencia dinámica**: `features: float32[T,63]`, `fps`, metadatos.
- **`Evento`**: `etiqueta`, `confianza`, `tipo` (`static`/`dynamic`), `ts_ms`.
- **`Glosa`**: `clave`, `texto`, `tipo` (`palabra`/`letra`/`pausa`), `duracion_ms`,
  `no_manual` (reservado para cejas/mirada/boca).

### 7.4 Camino web/offline

- **Offline:** `.venv` + modelo `.task` + modelos `.joblib`. Empaquetar con PyInstaller después.
- **Web:** MediaPipe WASM en el navegador + inferencia ONNX en cliente o FastAPI en servidor.
- El core solo recibe features; no depende de OpenCV ni de la cámara.

### 7.5 Camino voz → texto → señas

1. ASR (`faster-whisper`) → texto.
2. Normalización (minúsculas, acentos, puntuación).
3. Glosado español → LSM; palabras conocidas + deletreo como respaldo.
4. Selección de clips/animaciones y tiempos.
5. Render en avatar 3D o reproducción de video.
6. Marcadores no manuales (fase posterior; el contrato `Glosa` los prevé).

**Importante:** una traducción palabra por palabra **no es LSM**. El MVP produce
"español signado" y hay que decirlo explícitamente.

---

## 8. Plan por fases

### Fase 0 — Rescate ✅ (2026-11-18)

- [x] Respaldo fuera de OneDrive.
- [x] Proyecto nuevo en `C:\dev\TLSM`.
- [x] `.gitignore`, `.gitattributes`, `requirements.txt`, `requirements.lock.txt`.
- [x] `venv` nuevo con Python 3.11.
- [x] MediaPipe Tasks + modelo `hand_landmarker.task`.
- [x] `check_entorno.py` y `demo_camara.py`.
- [x] Guía y commits iniciales.

### Fase 1 — Reacomodo ✅ (2026-11-18)

- [x] `src/tlsm/`, `tests/`, `scripts/`.
- [x] `legacy/` con el código y datos v1.
- [x] Rutas con `ñ` renombradas a ASCII.
- [x] `pyproject.toml`, `LICENSE` MIT, `THIRD_PARTY_LICENSES.md`.
- [x] Datos, modelos y reportes fuera de git.
- [x] Publicar el repo remoto: https://github.com/Exsoflex/TLSM-v2.

**Criterio:** `git status` limpio, repo < 50 MB, `check_entorno` pasa. ✅

### Fase 2 — Núcleo v2 ✅ (2026-11-18)

- [x] `config.py` sin números mágicos.
- [x] `features.py` con traslación, escala, rotación y espejo; tests de invariancia.
- [x] `capture.py` con cuenta regresiva y muestreo fijo.
- [x] `datasets.py` con esquema v2 y metadatos.
- [x] `train.py` con split por sesión/bloque y métricas honestas.
- [x] `recognize.py` con ventana de votos y buffer dinámico a 15 fps.
- [x] `voice.py` con cola y un solo worker.
- [x] `ui.py` de escritorio.
- [x] `gloss.py`, `render.py`, `transcribe.py` (contratos y primer adaptador).
- [x] Importar v1 y entrenar línea base.
- [x] Interfaz de captura guiada con cuadrícula, progreso y guardado automático.
- [x] 50 tests y lint limpios.

**Criterio:** pipeline de punta a punta con datos v1 y métricas honestas. ✅

### Fase 3 — Recaptura del abecedario ⏳ en curso

- [x] Primera sesión v2 capturada con la interfaz guiada: 300 muestras de A.
- [ ] Capturar las **27 letras** (21 estáticas + 6 dinámicas).
- [ ] Mínimo 3 sesiones por letra; idealmente 2+ firmantes.
- [ ] Registrar metadatos: firmante, sesión, cámara, distancia, iluminación, fondo.
- [ ] Aumento de datos: espejo, ruido, escala, pequeñas rotaciones.
- [ ] Separar el clasificador de letras del de palabras (HOLA no va con letras).
- [ ] Congelar dataset v2 y reporte de evaluación.
- [ ] Publicar datos/modelos como Release o con LFS/DVC.

**Criterio:** ≥95% macro-F1 en **sesión no vista** para las 27 letras, con matriz de
confusión revisada.

### Fase 4 — Producto (escritorio + web)

- [ ] Pulir UI: historial, configuración de cámara, modo espejo, temas.
- [ ] Empaquetado instalable (PyInstaller) y modo offline.
- [ ] Demo web (MediaPipe WASM + ONNX en navegador, o FastAPI + WebSocket).
- [ ] Métricas de latencia/FPS en equipo objetivo.
- [ ] `generar_licencias.py` integrado en el build.

### Fase 5 — Palabras, bidireccionalidad y avatar 3D

- [ ] Vocabulario inicial (MSL-150 como arranque, con atribución).
- [ ] Modelo de secuencias (1D-CNN/GRU/Transformer) si el baseline no alcanza.
- [ ] ASR offline (`faster-whisper`) y TTS (Piper).
- [ ] Glosador español → LSM + respaldo a deletreo.
- [ ] Avatar 3D con clips pregrabados; después animación procedural.
- [ ] Validación con personas sordas e intérpretes.

---

## 9. Esquema de datos v2 (implementado)

### 9.1 Features canónicas (63 dimensiones)

1. Restar la muñeca (landmark 0) → traslación.
2. Dividir entre `||landmark[9] - landmark[0]||` → escala.
3. Rotar para alinear `wrist → middle_mcp` con el eje +Y → rotación en el plano.
4. Espejar en X las manos izquierdas → una sola convención.
5. Conservar `z` escalado (configurable con `ConfigFeatures.usar_z`).

Se guardan **ambas** versiones: landmarks crudos (`raw`) y features (`X`), para reprocesar.

### 9.2 Archivos

```
data/raw/<sesion>/static_<ETIQUETA>.npz
    X, raw, y, meta_json
data/raw/<sesion>/dynamic_<ETIQUETA>.npz
    X (N,T,63), raw (N,T,21,3), y, fps, meta_json
data/processed/static_v2.npz
    X, raw, y, sesion, firmante
data/processed/dynamic_v2.npz
    X, raw, y, sesion, firmante, fps
```

### 9.3 Metadatos obligatorios

| Campo | Ejemplo | Por qué |
|---|---|---|
| `label` | `A`, `N_TILDE`, `HOLA` | Etiqueta canónica ASCII. |
| `display` | `A`, `Ñ`, `Hola` | Texto para UI. |
| `is_dynamic` | `false` | Distingue letra estática de movimiento. |
| `firmante` | `S01` | Permite splits por firmante. |
| `sesion` | `2026-11-18_1411` | Evita fuga entre train/test. |
| `camara` | `camara_0` | Diagnosticar dominio. |
| `modelo_landmarks` | `mediapipe-1.2.3-hand_landmarker-float16` | Versionado. |
| `version_app` | `0.2.0` | Reproducibilidad. |
| `creado` | ISO-8601 | Auditoría. |
| `notas` | texto libre | Distancia, luz, fondo. |

Los campos de etiqueta/`is_dynamic` se derivan del nombre del archivo y de
`config.LETRAS_DINAMICAS`; no se duplican en el `.npz` para evitar inconsistencias.

### 9.4 Protocolo de captura con `capturar_ui.py`

1. **Preparar:** luz frontal, fondo limpio, cámara a 640×480, mano completa en el cuadro.
2. **Identificar:** `--firmante S01` y una sesión por persona/día (`--sesion 2026-11-18_01`).
   Repetir la misma sesión **retoma** el progreso; no sobrescribe lo anterior.
3. **Configurar:** por defecto 3 rondas por letra, 100 muestras estáticas o 10 secuencias
   de 20 frames por ronda. Para una primera pasada se puede bajar a 1 ronda.
4. **Grabar:** elegir letra, `ESPACIO`, mantener la seña quieta (estáticas) o ejecutar el
   movimiento tras la cuenta regresiva (dinámicas). `R` descarta una ronda mala.
5. **Verificar:** cada letra completa se marca en verde; la app salta a la siguiente
   pendiente. Al salir, repetir la sesión para confirmar el progreso.
6. **Cerrar el ciclo:** `scripts/consolidar.py` (suma sin borrar la v1) y luego
   `scripts/entrenar.py --tipo estatico` y `--tipo dinamico`.

**Reglas de calidad:** no cambiar de mano ni de distancia a mitad de una letra; evitar
señas mezcladas; no usar la misma sesión para entrenar y evaluar sin separar por bloques;
registrar en `--notas` cualquier cambio de cámara, luz o fondo.

---

## 10. Protocolo de evaluación

**Regla de oro:** nunca dividir frames al azar. Los frames consecutivos son casi duplicados.

- **Split por sesión** (y por firmante cuando haya más de uno). `train.dividir_indices`.
- **"Bloque"** solo cuando hay una sola sesión: 80/20 contiguo por clase, como proxy temporal.
- **"Aleatorio"** solo para demostrar fuga de datos; nunca para reportar.
- Reportar: accuracy, **macro-F1**, recall por clase, matriz de confusión, tasa de rechazo de
  "desconocido" y falsos positivos en reposo.
- Para movimiento: accuracy a nivel **evento**, no frame.
- Medir latencia y FPS en el equipo objetivo.
- Guardar reporte en `reports/` con fecha y versión del modelo.

**Metas:**
- 27 letras, sesión no vista: **≥95% macro-F1**.
- 20 palabras, sesión no vista: **≥90% macro-F1**.
- Falsos positivos en reposo: **<5%**.

---

## 11. Convenciones

- Python 3.11, layout `src/`, imports absolutos (`from tlsm.features import ...`).
- **Identificadores en inglés y ASCII** (`wrist_x`, `senas`); textos de UI/docs en español.
- Etiquetas canónicas ASCII: `N_TILDE`, no `Ñ`; `display()` para consola/reportes y
  `display_ascii()` para OpenCV (Hershey no dibuja la Ñ).
- Type hints, `dataclass` para configuración, `pathlib` para rutas.
- Nada de números mágicos: todo en `config.py`.
- Un solo lugar para extraer features; prohibido duplicarlo.
- `ruff` + `pytest` en cada cambio.
- Scripts desde la raíz: `python scripts/...`.
- No versionar `venv/`, `__pycache__`, videos crudos, datasets ni modelos.
- Commits pequeños y en español.

---

## 12. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Un solo firmante / un solo entorno | El modelo memoriza a la persona | Capturar varias sesiones y firmantes; medir por firmante. |
| Fuga por frames consecutivos | Métricas falsamente altas | Split por sesión/firmante; "bloque" como proxy. |
| MediaPipe cambia de API | Reescritura | Aislado en `landmarks.py`; versión fijada. |
| OneDrive rompe git/venv | Pérdida de trabajo | Proyecto en `C:\dev`; respaldos. |
| Binarios grandes en git | Repo lento/roto | LFS/DVC/Releases desde la fase 3. |
| Avatar 3D subestimado | Meses de trabajo | Clips pregrabados primero; contrato `RenderizadorSenias`. |
| MMS-Player GPL-3.0 | Obligaciones de licencia | Excluido; solo referencia. |
| Dependencia no permisiva | No se puede distribuir | Revisión en `THIRD_PARTY_LICENSES.md` antes de integrar. |
| Voz de Piper con licencia NC | No se puede distribuir | Revisar licencia de cada voz. |
| Sin validación de la comunidad sorda | Producto culturalmente incorrecto | Buscar intérpretes/asociaciones; validar alfabeto y vocabulario. |
| Regionalismos de LSM | Cobertura limitada | Documentar variante regional; permitir configuración. |
| Web con cámara | Latencia/privacidad | Inferencia en el navegador con WASM. |
| ASR/TTS con acento mexicano | Mala experiencia | Probar modelos en español MX; permitir edición de texto. |

---

## 13. Preguntas abiertas

1. **GitHub:** ¿repo nuevo o reutilizar `Exsoflex/TLSM` con historial limpio?
   Propuesta: repo nuevo y dejar el viejo como archivo.
2. **Validación:** ¿cómo conseguimos retroalimentación de personas sordas o intérpretes?
   Es el riesgo más importante del proyecto.
3. **Avatar:** ¿clips 2D primero o rig 3D desde el inicio? Propuesta: clips, mismo contrato.
4. **Dos manos:** ¿desde el abecedario o solo en palabras? Propuesta: una mano para letras.
5. **ASR:** ¿requisito del lanzamiento offline o fase 5? Propuesta: fase 5, interfaz lista.
6. **Repo remoto:** resuelto; el proyecto vive en `Exsoflex/TLSM-v2`.

---

## 14. Bitácora

### 2026-11-18 — Diagnóstico y Fase 0

- Revisión de los 24 archivos del proyecto y de los datasets/modelos.
- Medición de la fuga: 99.9% (aleatorio) vs 91.3% (temporal) vs 96.2% (temporal + escala).
- Detección de `venv` roto, `.git` corrupto, `venv` versionado y proyecto en OneDrive.
- Respaldo y migración a `C:\dev\TLSM`.
- Entorno Python 3.11.9 + MediaPipe 1.2.3 (Tasks API).
- `check_entorno.py` y `demo_camara.py` funcionando; cámara 0 a 640×480.
- Extracción del diccionario oficial: 27 letras, 21 estáticas y 6 con movimiento.
- Herramientas y licencias evaluadas.
- Commits `c116221` y `00f7537`.

### 2026-11-18 — Fases 1 y 2

- Licencias verificadas: MSL-150 CC-BY-4.0; SLT Apache-2.0; MediaPipe Apache-2.0;
  faster-whisper MIT; Piper MIT; pyttsx3 MPL-2.0. Excluidos MMS-Player (GPL-3.0) y
  SignAvatars (sin licencia).
- Proyecto bajo **MIT** con política de dependencias permisivas.
- Legado movido a `legacy/`; rutas con `ñ` normalizadas.
- Núcleo v2 completo: features canónicas de 63 dimensiones, captura guiada, dataset `.npz`
  con metadatos, reconocimiento con ventana de votos y buffer dinámico, compositor de texto,
  TTS con cola, UI OpenCV, glosador y contratos de render/ASR.
- Scripts de importación, entrenamiento, captura y app.
- 38 tests en verde; `ruff check` y `ruff format` limpios; paquete instalado editable.
- Datos v1 convertidos: 12,599 muestras estáticas y 709 secuencias.
- Línea base v2: estático **98.1%** accuracy / **98.2%** macro-F1; dinámico **98.6%** / **98.3%**
  (split por bloques, una sola sesión).
- **Siguiente:** fase 3, recaptura de las 27 letras con varias sesiones y firmantes.

### 2026-11-18 — Repositorio remoto e interfaz de captura

- Repo publicado en https://github.com/Exsoflex/TLSM-v2 (MIT, rama `main`).
- Nuevo `src/tlsm/drawing.py`: `envolver_texto`, `dibujar_mano` y `barra_progreso`
  compartidos; `ui.py` dejó de duplicarlos.
- Nuevo `src/tlsm/capture_ui.py` y lanzador `scripts/capturar_ui.py`:
  - cuadrícula de 27 letras con progreso por letra y marca `*` para las dinámicas;
  - guía tomada del diccionario oficial para cada letra;
  - rondas de 100 muestras estáticas o 10 secuencias de 20 frames;
  - guardado automático por ronda, reanudación por sesión y auto-avance;
  - atajos para elegir letra, saltar a la pendiente, descartar ronda y ver ayuda.
- `datasets.contar_sesion()` para retomar una sesión y mostrar el progreso.
- Pruebas nuevas: `contar_sesion`, render de panel/cuadrícula y transiciones de ronda
  estática, dinámica, descarte y navegación. Total: **46 tests** (después 50 con la
  consolidación incremental).
- Prueba real con cámara 0 (640×480): la interfaz compone y dibuja correctamente.
- **Siguiente:** fase 3, capturar letras faltantes (P, R, S, T, U, V, W, Y; Q, X, Z) y
  nuevas sesiones/firmantes con esta interfaz.

### 2026-11-20 — Consolidación incremental y reentrenamiento

- Detectado un fallo de flujo: `consolidar.py` reconstruía `data/processed` solo con
  `data/raw` y habría borrado las 12,599 muestras de la v1.
- Nuevo `datasets.mezclar_procesado()`: conserva sesiones ajenas a `data/raw` y reemplaza
  completas las sesiones recapturadas; ejecutar `consolidar.py` dos veces no duplica.
- `consolidar.py` gana `--desde-cero` (reconstruir solo desde `data/raw`) y muestra
  sesiones y firmantes.
- Primera sesión v2 capturada: `2026-11-20_1307`, 300 muestras de A. El dataset estático
  pasa a 12,899 muestras; el dinámico sigue en 709.
- Reentrenados ambos modelos: estático **0.982 accuracy / 0.983 macro-F1**; dinámico
  **0.986 / 0.983** (split bloque).
- Probado el detector `scripts/app.py` con los modelos nuevos: abre, carga las 13 clases
  estáticas y las 4 dinámicas y detecta manos.
- `importar_v1.py` ahora es incremental: reimportar la v1 no borra las sesiones nuevas.
- Manual de uso completo agregado a la guía (sección 16) y enlazado desde el README.
- **50 tests** en verde; lint limpio.
- **Siguiente:** capturar P, R, S, T, U, V, W, Y (estáticas) y Q, X, Z (dinámicas), y
  sumar más sesiones/firmantes antes de congelar el dataset.

---

## 15. Comandos útiles

```powershell
# Entrar al proyecto
cd C:\dev\TLSM

# Verificar entorno
.\.venv\Scripts\python.exe scripts\check_entorno.py

# Demo de cámara
.\.venv\Scripts\python.exe scripts\demo_camara.py --camera 0

# App de reconocimiento
.\.venv\Scripts\python.exe scripts\app.py

# Captura
.\.venv\Scripts\python.exe scripts\capturar_ui.py
.\.venv\Scripts\python.exe scripts\capturar.py --letra A --firmante S01

# Consolidar sesiones nuevas
.\.venv\Scripts\python.exe scripts\consolidar.py

# Datos y modelos
.\.venv\Scripts\python.exe scripts\importar_v1.py
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo dinamico

# Calidad
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check src scripts tests
.\.venv\Scripts\ruff.exe format src scripts tests

# Licencias para distribuir
.\.venv\Scripts\python.exe scripts\generar_licencias.py

# Git
git status
git add -A
git commit -m "Fase 2: nucleo v2, modelos base y UI"
```

---

## 16. Manual de uso completo: captura → entrenamiento → detector

Esta sección explica el recorrido operativo completo. Para comandos sueltos, ver la
sección 15.

### 16.1 Preparación (una vez por equipo)

```powershell
# Entrar al proyecto (nunca trabajes desde OneDrive)
cd C:\dev\TLSM

# Crear el entorno solo la primera vez
py -3.11 -m venv .venv

# Instalar el paquete y las herramientas de desarrollo
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

# Verificar Python, MediaPipe, modelo de manos y cámara
.\.venv\Scripts\python.exe scripts\check_entorno.py
```

Si el `.venv` ya existe, basta con:

```powershell
cd C:\dev\TLSM
.\.venv\Scripts\python.exe scripts\check_entorno.py
```

**Importar la v1 (solo si todavía no está importada):**

```powershell
.\.venv\Scripts\python.exe scripts\importar_v1.py
```

La importación es segura: reemplaza únicamente la sesión llamada `v1` y conserva las
sesiones nuevas que ya estén consolidadas. Los datos quedan en:

```
data/raw/<sesion>/              # capturas nuevas
data/processed/static_v2.npz    # dataset para entrenar
data/processed/dynamic_v2.npz
models/estatico_v2.joblib       # modelos entrenados
models/dinamico_v2.joblib
reports/                        # métricas y matrices
```

Los datasets, modelos y reportes **no se versionan en git**; se regeneran con los scripts.

### 16.2 Captura guiada de datos

```powershell
# Sesión nueva: pregunta firmante y nombre de sesión
.\.venv\Scripts\python.exe scripts\capturar_ui.py

# Todo explícito
.\.venv\Scripts\python.exe scripts\capturar_ui.py --firmante S01 --sesion 2026-11-21_01

# Solo las letras que faltan en el abecedario
.\.venv\Scripts\python.exe scripts\capturar_ui.py --firmante S01 --sesion 2026-11-21_01 `
  --letras P,R,S,T,U,V,W,Y,Q,X,Z --rondas 3
```

**Qué muestra la pantalla:**

- Cámara y landmarks de la mano a la izquierda.
- Letra actual, tipo (estática/dinámica), guía oficial y mensajes a la derecha.
- Barra de progreso de la ronda y rondas hechas.
- Cuadrícula de las 27 letras: gris = sin datos, amarillo = en progreso, verde = completa,
  `*` = letra dinámica.
- `H` abre la ayuda dentro de la app.

**Paso a paso:**

1. Escribe el firmante (`S01`) y la sesión (`2026-11-21_01`). Enter acepta el valor sugerido.
2. Elige una letra con las flechas (o `A`/`D`/`W`/`S`).
3. Pulsa `ESPACIO`.
4. **Estática:** espera la cuenta regresiva y mantén la seña quieta. Se guardan 100 muestras
   por ronda; los frames con movimiento se descartan.
5. **Dinámica:** tras la cuenta regresiva ejecuta el movimiento. Se guardan 10 secuencias de
   20 frames por ronda, muestreadas a 15 fps.
6. Cada ronda se guarda sola. Al completar 3 rondas la letra se pone verde y la app salta a
   la siguiente pendiente. `TAB` también salta a la siguiente pendiente.
7. `Q` o `ESC` sale; todo lo guardado se conserva.

| Tecla | Acción |
|---|---|
| `ESPACIO` | iniciar o continuar una ronda |
| `TAB` | ir a la siguiente letra pendiente |
| Flechas / `A` `D` `W` `S` | moverse por la cuadrícula |
| `R` | descartar la ronda en curso |
| `H` | mostrar u ocultar la ayuda |
| `Q` / `ESC` | salir |

| Opción | Por defecto | Para qué |
|---|---|---|
| `--firmante` | pregunta / `S01` | identifica a la persona |
| `--sesion` | fecha y hora | agrupa datos y permite retomar |
| `--letras` | todas | lista separada por comas (`A,B,J`) |
| `--rondas` | `3` | rondas por letra |
| `--muestras-ronda` | `100` | muestras por ronda estática |
| `--secuencias-ronda` | `10` | secuencias por ronda dinámica |
| `--solo-faltantes` | desactivado | empieza en la primera pendiente de la sesión |
| `--sin-auto-avance` | desactivado | no cambia de letra al completarla |
| `--camara` | `0` | índice de cámara |
| `--sin-espejo` | desactivado | desactiva el espejo de la imagen |
| `--notas` | vacío | distancia, luz, fondo u observaciones |

**Reanudar:** si repites el mismo `--sesion`, la app lee `data/raw/<sesion>/` y continúa desde
la última ronda guardada. Cada sesión nueva empieza en 0 aunque la letra ya exista en la v1:
eso es correcto, porque cada sesión es un dominio distinto.

**Recomendaciones de calidad:**

- Luz frontal, fondo limpio y mano completa dentro del cuadro.
- No cambies de mano, distancia ni cámara a mitad de una letra.
- Si una ronda sale mal, descártala con `R`.
- Graba varias sesiones y, si puedes, varios firmantes. Un solo firmante hace que el modelo
  memorice a la persona.
- No mezcles letras: si dudas, repite la seña en otra ronda.

Los archivos quedan como `data/raw/<sesion>/static_<LETRA>.npz` y
`data/raw/<sesion>/dynamic_<LETRA>.npz`.

### 16.3 Consolidar las sesiones

```powershell
.\.venv\Scripts\python.exe scripts\consolidar.py
```

Qué hace:

- Toma todas las carpetas de `data/raw/`.
- Las suma a `data/processed/static_v2.npz` y `dynamic_v2.npz`.
- **Conserva** los datos que no vienen de `data/raw` (por ejemplo, la v1).
- **Reemplaza** completas las sesiones que ya estaban consolidadas, sin duplicarlas.
- Verifica que los FPS de las secuencias dinámicas coincidan.

Se puede ejecutar las veces que haga falta; el resultado es idempotente. Salida típica:

```
Estatico: 12899 muestras -> C:\dev\TLSM\data\processed\static_v2.npz
  clases: {'A': 1200, 'B': 900, ...}
  firmantes: ['S01', 'v1']
  sesiones: ['2026-11-20_1307', 'v1']
```

**`--desde-cero`:** ignora el dataset procesado anterior y reconstruye solo con `data/raw`.
Úsalo únicamente si quieres descartar la v1; si lo usas sin querer, vuelve a ejecutar
`scripts/importar_v1.py`.

### 16.4 Entrenar los modelos

```powershell
# Letras con la mano quieta
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico

# Movimientos (J, K, Ñ, Hola, ...)
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo dinamico
```

Cada comando:

1. Carga el dataset procesado.
2. Divide entrenamiento/prueba de forma honesta.
3. Entrena un `RandomForestClassifier`.
4. Evalúa y guarda el paquete `.joblib` con etiquetas y metadatos.
5. Genera un reporte JSON y una matriz de confusión PNG.

| Split | Cuándo se usa | Qué significa |
|---|---|---|
| `auto` (defecto) | siempre | `sesion` si hay 3+ sesiones; si no, `bloque` |
| `sesion` | 3+ sesiones | sesiones completas separadas; es el honesto |
| `bloque` | 1–2 sesiones | 80/20 contiguo por clase; aproximación temporal |
| `aleatorio` | solo diagnóstico | mezcla frames casi idénticos; **no reportar** |

Salidas:

| Archivo | Contenido |
|---|---|
| `models/estatico_v2.joblib` | modelo estático + etiquetas + metadatos |
| `models/dinamico_v2.joblib` | modelo dinámico + etiquetas + metadatos |
| `reports/estatico_<fecha>.json` | accuracy, macro-F1, métricas por clase, matriz |
| `reports/estatico_<fecha>.png` | matriz de confusión legible |
| `reports/dinamico_<fecha>.json/.png` | lo mismo para movimientos |

Opciones:

```powershell
# Forzar el tipo de split
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico --split sesion
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico --split bloque

# Cambiar proporción de prueba y semilla
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico --test-size 0.25 --seed 7

# Otra ruta de salida o sin reporte
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo dinamico `
  --salida models/prueba.joblib --sin-reporte
```

**Cómo leer las métricas:**

- `accuracy`: porcentaje total de aciertos.
- `macro-F1`: promedio por clase, sin favorecer a las clases con más muestras. Es la métrica
  que importa cuando hay clases desbalanceadas.
- Matriz de confusión: filas = seña real, columnas = predicción. Los errores fuera de la
  diagonal indican qué letras se confunden.
- Los metadatos del `.joblib` guardan split, semilla, número de muestras y versión de features.

Línea base actual (2026-11-20, split `bloque`):

| Modelo | Datos | Accuracy | Macro-F1 |
|---|---|---|---|
| Estático | 12,899 muestras, 13 clases | **0.982** | **0.983** |
| Dinámico | 709 secuencias, 4 clases | **0.986** | **0.983** |

Para ver qué clases reconoce un modelo:

```powershell
.\.venv\Scripts\python.exe -c "from tlsm.config import MODELO_ESTATICO, MODELO_DINAMICO; from tlsm.model_io import cargar_modelo; print('estatico:', cargar_modelo(MODELO_ESTATICO).etiquetas); print('dinamico:', cargar_modelo(MODELO_DINAMICO).etiquetas)"
```

### 16.5 Usar el detector principal

```powershell
.\.venv\Scripts\python.exe scripts\app.py
```

La ventana muestra la cámara, los landmarks y un panel con:

- Texto compuesto.
- Seña actual y confianza.
- Estado de los modelos cargados.
- FPS y avisos (por ejemplo, si la voz no está disponible).

| Tecla | Acción |
|---|---|
| `ESPACIO` | agregar un espacio al texto |
| `B` / `Retroceso` | borrar el último carácter |
| `C` | limpiar el texto |
| `V` | decir el texto con voz (TTS) |
| `L` | mostrar u ocultar los landmarks |
| `R` | reiniciar el reconocimiento |
| `Q` / `ESC` | salir |

Opciones:

```powershell
.\.venv\Scripts\python.exe scripts\app.py --sin-voz
.\.venv\Scripts\python.exe scripts\app.py --camara 1
.\.venv\Scripts\python.exe scripts\app.py --sin-espejo
.\.venv\Scripts\python.exe scripts\app.py --modelo models\estatico_v2.joblib
.\.venv\Scripts\python.exe scripts\app.py --modelo-dinamico models\dinamico_v2.joblib
.\.venv\Scripts\python.exe scripts\app.py --sin-modelo   # solo detectar manos
```

Clases actuales:

- Estáticas: A, B, C, D, E, F, G, H, I, L, M, N, O.
- Dinámicas: J, K, Ñ, HOLA.

**Importante:** el detector solo puede devolver clases entrenadas. Si haces P, R, S, T, U,
V, W, Y, Q, X o Z, responderá con la clase más parecida de las que conoce. Para reconocerlas
hay que capturarlas y reentrenar.

El detector es de **letras y movimientos aislados**, no de palabras o frases completas. La
traducción de vocabulario y el avatar 3D son fases posteriores.

### 16.6 Flujo para añadir letras nuevas

No hace falta tocar código: el modelo aprende las clases que existan en el dataset.

```powershell
# 1. Capturar solo las letras faltantes
.\.venv\Scripts\python.exe scripts\capturar_ui.py --firmante S01 --sesion 2026-11-21_01 `
  --letras P,R,S,T,U,V,W,Y,Q,X,Z --rondas 3

# 2. Consolidar (suma, no borra)
.\.venv\Scripts\python.exe scripts\consolidar.py

# 3. Reentrenar ambos modelos
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo dinamico

# 4. Comprobar que las clases nuevas aparecen
.\.venv\Scripts\python.exe -c "from tlsm.config import MODELO_ESTATICO, MODELO_DINAMICO; from tlsm.model_io import cargar_modelo; print(cargar_modelo(MODELO_ESTATICO).etiquetas); print(cargar_modelo(MODELO_DINAMICO).etiquetas)"

# 5. Usar
.\.venv\Scripts\python.exe scripts\app.py
```

Repite el ciclo con **varias sesiones y firmantes** hasta tener al menos 3 sesiones por
letra. Cuando haya 3+ sesiones, `entrenar.py` usará el split `sesion`, que es el que permite
afirmar que el modelo funciona con personas/sesiones no vistas.

### 16.7 Ejemplo completo de una jornada

```powershell
cd C:\dev\TLSM

# Verificar que todo esté sano
.\.venv\Scripts\python.exe scripts\check_entorno.py

# Capturar las letras faltantes (≈15–20 min)
.\.venv\Scripts\python.exe scripts\capturar_ui.py --firmante S01 --sesion 2026-11-21_01 `
  --letras P,R,S,T,U,V,W,Y,Q,X,Z --rondas 3

# Sumar al dataset
.\.venv\Scripts\python.exe scripts\consolidar.py

# Entrenar ambos modelos
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo estatico
.\.venv\Scripts\python.exe scripts\entrenar.py --tipo dinamico

# Revisar reports/ y probar el detector
.\.venv\Scripts\python.exe scripts\app.py

# Guardar cambios de código/documentación (datos y modelos no se versionan)
git status
git add -A
git commit -m "Fase 3: captura de letras faltantes y reentrenamiento"
git push origin main
```

### 16.8 Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `No se pudo abrir la camara 0` | Otra app la usa o no hay permiso | Cierra Zoom/Teams/navegador; prueba `--camara 1` |
| `No existe el dataset` | Falta importar o consolidar | `scripts\importar_v1.py` y/o `scripts\consolidar.py` |
| `El split por sesión necesita al menos 3 sesiones` | Pocas sesiones | Captura más o usa `--split bloque` |
| Una letra siempre se confunde | No está entrenada o faltan datos | Captura esa letra, consolida y reentrena |
| El dinámico no reacciona | Movimiento por debajo del umbral o mano fuera | Haz el gesto más amplio y mantén la mano visible |
| El texto se repite o se corta | Umbrales/cooldown | Ajusta `ConfigReconocimiento` en `config.py` |
| `Voz no disponible` | TTS del sistema | Usa `--sin-voz` o revisa `pyttsx3` |
| `pytest`/`ruff` no encontrados | No están en el PATH | Usa `.\.venv\Scripts\python.exe -m pytest` / `-m ruff` |
| Los datos nuevos no aparecen | Sesión distinta o falta consolidar | Revisa `data/raw/<sesion>/` y ejecuta `consolidar.py` |
| Git no incluye modelos/datos | Están ignorados a propósito | Se regeneran; para publicarlos usa Releases o LFS |

### 16.9 Checklist rápido

- [ ] `check_entorno.py` pasa y la cámara abre.
- [ ] La captura guarda rondas en `data/raw/<sesion>/`.
- [ ] `consolidar.py` muestra las sesiones y firmantes esperados.
- [ ] `entrenar.py` termina y guarda los dos `.joblib`.
- [ ] `reports/` tiene métricas y matriz de confusión revisadas.
- [ ] `app.py` carga los modelos y reconoce las clases entrenadas.
- [ ] La guía y el README se actualizaron si cambió el flujo.

---

## 17. Archivos del legado (no borrar por accidente)

| Archivo | Estado | Acción |
|---|---|---|
| `legacy/dia_1-10/` | Ejercicios de aprendizaje | Conservar como historia. |
| `legacy/captura/` | Captura v1 | Referencia; reescrito en v2. |
| `legacy/entrenamiento/` | Entrenamiento v1 | Referencia; reescrito en v2. |
| `legacy/reconocimiento/` | App v1 (no corre en MediaPipe 1.x) | Referencia de UX. |
| `legacy/v1/modelos/dataset_senas.csv` | Dataset v1 estático | Fuente de la línea base. |
| `legacy/v1/modelos/dataset_movimiento.pkl` | Dataset v1 dinámico | Fuente de la línea base. |
| `legacy/v1/modelos/modelo_*.pkl` | Modelos v1 | Solo referencia. |
| `legacy/v1/modelo_senas.pkl` | Modelo viejo de 10 clases | Solo referencia. |
| `legacy/README_v1.txt` | README obsoleto | Reemplazado por `README.md`. |

---

## 18. Cómo retomar el trabajo

1. Leer secciones 2, 3 y 8; para operar, seguir el manual de la sección 16.
2. `git status` y `pytest` para confirmar que todo sigue sano.
3. Si se va a capturar: definir letras, sesión y firmante; usar `scripts/capturar_ui.py`
   (o `scripts/capturar.py` para una sola letra).
4. Tras capturar: `scripts/consolidar.py` suma `data/raw/<sesion>/` a `data/processed/`,
   conserva la v1 y reemplaza solo las sesiones repetidas.
5. Reentrenar con `scripts/entrenar.py --tipo estatico` y `--tipo dinamico`; revisar
   `reports/` antes de tocar la UI.
6. Probar `scripts/app.py` y actualizar esta guía; hacer commit.

**Nota:** `consolidar.py` ya **no** borra el dataset procesado. Solo `--desde-cero`
reconstruye desde `data/raw` e ignora lo anterior; no lo uses si quieres conservar la v1.
