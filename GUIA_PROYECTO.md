# GUÍA Y MEMORIA DEL PROYECTO TLSM

> Documento vivo. Es la fuente de verdad del proyecto y mi memoria de trabajo.
> Se actualiza al final de cada etapa. Si algo aquí contradice al código, gana el código
> y hay que corregir este documento.

**Última actualización:** 2026-11-18
**Ubicación oficial:** `C:\dev\TLSM` (fuera de OneDrive)
**Repositorio remoto:** https://github.com/Exsoflex/TLSM-v2 (rama `main`).

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
- **46 tests** en verde; `ruff check` y `ruff format` limpios.
- Datos v1 convertidos a v2: 12,599 muestras estáticas y 709 secuencias dinámicas.
- Modelos base entrenados y evaluados (sección 4.3).
- La app de escritorio abre, detecta manos, clasifica letras y compone texto con voz.
- **Repositorio remoto creado:** https://github.com/Exsoflex/TLSM-v2 (commit `f735dd0`).
- **Interfaz de captura guiada** (`scripts/capturar_ui.py`): cuadrícula de 27 letras con
  progreso, guía oficial por letra, rondas automáticas, guardado por ronda, reanudación de
  sesión y auto-avance a la siguiente letra pendiente.

### 3.2 Lo que todavía NO está

- Faltan **15 letras** del abecedario oficial: estáticas P, R, S, T, U, V, W, Y
  y dinámicas Q, X, Z. (Las 13 estáticas y 3 dinámicas existentes vienen de la v1.)
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

### 4.3 Línea base v2 (medición real de esta sesión)

Conversión con `scripts/importar_v1.py` y entrenamiento con
`scripts/entrenar.py --tipo ...`. Split **bloque** (80/20 contiguo por clase) porque
todos los datos v1 pertenecen a una sola sesión.

| Modelo | Train / Test | Accuracy | Macro-F1 |
|---|---|---|---|
| Estático (13 clases) | 10,079 / 2,520 | **0.981** | **0.982** |
| Dinámico (4 clases) | 568 / 141 | **0.986** | **0.983** |

Clases con más error en estático: A (precisión 0.91), D (recall 0.89), O (recall 0.86).
El resto está en 0.93–1.00.

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
- [x] 46 tests y lint limpios.

**Criterio:** pipeline de punta a punta con datos v1 y métricas honestas. ✅

### Fase 3 — Recaptura del abecedario ⏳ siguiente

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
6. **Cerrar el ciclo:** `scripts/consolidar.py` y luego `scripts/entrenar.py`.

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
6. **Repo remoto:** `gh` no está autenticado. Hace falta `gh auth login` o un token.

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
  estática, dinámica, descarte y navegación. Total: **46 tests**.
- Prueba real con cámara 0 (640×480): la interfaz compone y dibuja correctamente.
- **Siguiente:** fase 3, capturar letras faltantes (P, R, S, T, U, V, W, Y; Q, X, Z) y
  nuevas sesiones/firmantes con esta interfaz.

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

## 16. Archivos del legado (no borrar por accidente)

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

## 17. Cómo retomar el trabajo

1. Leer secciones 2, 3 y 8.
2. `git status` y `pytest` para confirmar que todo sigue sano.
3. Si se va a capturar: definir letra, sesión y firmante; usar `scripts/capturar.py`.
4. Tras capturar: `scripts/consolidar.py` une `data/raw/<sesion>/` en `data/processed/`,
   validando fps y etiquetas.
5. Reentrenar con `scripts/entrenar.py` y revisar `reports/` antes de tocar la UI.
6. Actualizar esta guía y hacer commit.

**Nota:** `consolidar.py` reemplaza el contenido de `data/processed/static_v2.npz` y
`dynamic_v2.npz`. Si se quieren conservar los datos v1 junto con los nuevos, importar la v1
dentro de una sesión de `data/raw/` o respaldar los `.npz` procesados antes de consolidar.
