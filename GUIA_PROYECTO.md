# GUÍA Y MEMORIA DEL PROYECTO TLSM

> Documento vivo. Es la fuente de verdad del proyecto y mi memoria de trabajo.
> Se actualiza al final de cada etapa. Si algo aquí contradice al código, gana el código
> y hay que corregir este documento.

**Última actualización:** 2026-11-18
**Ubicación oficial:** `C:\dev\TLSM` (fuera de OneDrive)
**Repositorio remoto de referencia:** https://github.com/Exsoflex/TLSM

---

## 0. Cómo usar este documento

1. Antes de empezar una sesión de trabajo, leer las secciones 2 (decisiones), 3 (estado) y 8 (plan).
2. Al terminar, actualizar la bitácora (sección 14) y mover los checks de la fase correspondiente.
3. Toda decisión nueva se anota en la sección 2 con fecha. No se toman decisiones "de memoria".
4. Los números de la sección 4 son mediciones reales sobre los datos de la v1; si se recapturan datos, se actualizan.

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
- Descargable/instalable.

**Público:** personas oyentes que están aprendiendo LSM (nosotros incluidos), y a futuro personas sordas y sus familias. Todavía **no** hay validación con la comunidad sorda; eso es un riesgo abierto (ver sección 12).

---

## 2. Decisiones tomadas

| Fecha | Decisión | Razón / consecuencias |
|---|---|---|
| 2026-11-18 | **Sí se pueden recapturar los datos.** | Se hará un esquema v2 desde cero; los datasets v1 quedan como referencia. |
| 2026-11-18 | Empezar por **letras individuales**, luego palabras. | Reduce el problema; el abecedario ya está definido en el diccionario oficial. |
| 2026-11-18 | Producto **offline de escritorio** + **web futura**. | El núcleo debe ser independiente de la UI y de OpenCV. |
| 2026-11-18 | La dirección **voz → texto → señas 3D** es fase 5, pero la arquitectura debe preverla desde ahora. | No acoplar el reconocimiento a la UI ni al modelo actual. |
| 2026-11-18 | Fuente normativa: `docs/diccionario_oficial.pdf` (*Manos con voz*, 2011). | Es el material oficial que tenemos. No sustituye validación con personas sordas. |
| 2026-11-18 | **No trabajar dentro de OneDrive.** | OneDrive deshidrató `.git` y DLLs; corrompió el repo y el venv. |
| 2026-11-18 | Nuevo repositorio limpio; el historial viejo queda en GitHub y en el respaldo. | El `.git` local está dañado (faltan `.pack`, hay commits ilegibles). |
| 2026-11-18 | Migrar a **MediaPipe Tasks** (1.x). | `mediapipe.solutions.hands` fue eliminado en MediaPipe 1.x. |
| 2026-11-18 | Python **3.11**. | Compatible con MediaPipe 1.2.3, scikit-learn 1.9 y numpy 2.4. |

**Pendiente de decidir (ver sección 13):** reutilizar el repo de GitHub o crear uno nuevo, tecnología de UI de escritorio, alcance del ASR offline y origen del avatar 3D.

---

## 3. Estado actual (después de la Etapa 0)

### 3.1 Lo que ya está hecho

- Proyecto copiado a `C:\dev\TLSM`.
- Respaldo intacto del proyecto original: `C:\dev\_backup_TLSM_2026-11-18` (40.3 MB, sin `venv` ni `.git`).
- El proyecto original en OneDrive **no se borró**; sigue ahí como respaldo adicional.
- Entorno virtual nuevo: `.venv` con **Python 3.11.9**.
- Dependencias instaladas y fijadas:
  - `mediapipe==1.2.3`
  - `opencv-contrib-python==5.1.0.95` (no instalar `opencv-python` en paralelo)
  - `numpy==2.4.6`, `pandas==3.1.1`, `scikit-learn==1.9.1`, `joblib==1.6.0`
  - `matplotlib`, `pyttsx3`, `pypdf`
- Modelo de manos descargado: `assets/mediapipe/hand_landmarker.task` (7.8 MB).
- Scripts nuevos:
  - `scripts/check_entorno.py` — verifica versiones, modelo y cámaras.
  - `scripts/demo_camara.py` — detección de manos con Tasks API, dibuja landmarks y FPS.
- `README.md`, `requirements.txt`, `requirements.lock.txt`, `.gitignore`, `.gitattributes`.
- Verificado en esta máquina: cámara `0` disponible a **640×480** (el driver no entrega 1280×720).
- Repositorio git nuevo e independiente. Commit inicial: **`c116221`** (36 archivos, ~48 MB con datos y PDF).
- **Sin remoto configurado a propósito** hasta decidir si se reutiliza `Exsoflex/TLSM` o se crea uno nuevo.

### 3.2 Lo que todavía NO funciona

- **El código legado no corre con el entorno nuevo**: `reconocimiento_final.py` y los demás usan `mp.solutions.hands`, que ya no existe. Es esperado; se reescribe en la Fase 2.
- La app actual no tiene UI nueva, ni captura v2, ni modelo v2.
- El repo nuevo aún no tiene historial más allá del commit inicial.

### 3.3 Verificación rápida

```powershell
cd C:\dev\TLSM
.\.venv\Scripts\python.exe scripts\check_entorno.py --sin-camara
.\.venv\Scripts\python.exe scripts\demo_camara.py --camera 0
```

---

## 4. Diagnóstico de la v1 (mediciones reales)

### 4.1 Dataset estático (`modelos/dataset_señas.csv`)

- 12,599 filas × 43 columnas (42 features + etiqueta).
- Features: 21 landmarks × (x, y) relativos a la muñeca. **Sin `z`** y **sin normalización de escala**.
- 13 clases: A–I, L, M, N, O. 900 muestras por clase, **L con 1,799**.
- 2 features constantes (`x0`, `y0`).
- Escala de la mano (muñeca → MCP del medio) varía **4.57×** entre muestras.
- No hay metadatos de firmante, sesión, cámara, distancia ni iluminación.

### 4.2 Dataset de movimiento (`modelos/dataset_movimiento.pkl`)

- 709 secuencias, todas `(20, 42)` → 840 features al aplanar.
- Etiquetas: `J` 255, `K` 152, `N_tilde` 151, `Hola` 151.
- Mezcla letras con una palabra ("Hola") en el mismo clasificador.
- RandomForest sobre el vector aplanado: pierde el orden temporal.

### 4.3 Métricas: el problema del split aleatorio

| Evaluación | Accuracy |
|---|---|
| Split aleatorio (como `entrenar_modelo.py`) | **99.9%** |
| Split temporal por clase (holdout honesto) | **91.3%** |
| Split temporal + normalización por tamaño de mano | **96.2%** |

Los frames consecutivos son casi idénticos; el split aleatorio los reparte entre train y test y "filtra" la respuesta. Por eso el 99.96% de accuracy de entrenamiento no significa nada.

**Confusiones principales (holdout temporal):** C↔E (50), C↔A (41), G↔H (28), M↔N (22), O↔A/C (25), F↔B (18).

**Conclusión:** normalizar por escala de mano es la mejora más barata y ya está comprobada (+4.5 puntos). Agregar `z` y una rotación canónica debería mejorar más.

### 4.4 Código

Problemas concretos encontrados en la v1:

- `reconocimiento_final.py` asume que el frame mide 480 px de alto (`np.hstack`) y nunca configura la resolución de cámara.
- Índices de cámara inconsistentes: `0` en unos scripts, `1` en `dataset_movimiento.py` y `reconocimiento_final.py`.
- El muestreo de movimiento en inferencia (frames acumulados solo si superan un umbral) **no coincide** con el de entrenamiento (20 frames a 60 ms fijos).
- `buffer_pos` y `buffer_frames` se llenan con criterios distintos.
- Para llenar el buffer de gesto se requieren 20 frames consecutivos con movimiento; los gestos lentos no se detectan.
- `pyttsx3.init()` por cada frase y en un hilo nuevo; puede bloquear o encimar audio.
- La última letra antes de retirar la mano se pierde; no se pueden repetir letras sin retirar la mano.
- Rutas relativas al CWD (`"modelos/..."`), identificadores con `ñ` y acentos, números mágicos duplicados en 4 archivos.
- Sin configuración, logs, tests ni manejo de errores de cámara/modelo.

### 4.5 Infraestructura

- `venv` roto: faltaban `cv2.pyd` y el DLL de MediaPipe.
- `.git` corrupto: faltaban los `.pack` (OneDrive los deshidrató) y había commits ilegibles.
- 16,215 de 16,241 archivos versionados eran del `venv`.
- Sin `.gitignore` ni `requirements.txt`.
- Repo de GitHub: ~222 MB por el `venv`.

---

## 5. Abecedario oficial de LSM (según *Manos con voz*)

El diccionario define **27 letras**: A–Z + Ñ. La sección de abecedario está en las páginas 15–19 del PDF (páginas 17–21 del PDF físico).

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

> **Corrección importante:** en el dataset v1, J, K y Ñ están en el modelo de movimiento, lo cual **sí coincide** con el manual. Faltan Q, X y Z. Las 8 letras estáticas que faltan son P, R, S, T, U, V, W, Y.

**Notas del manual que afectan el diseño:**
- La LSM tiene gramática propia y regionalismos; el orden del español es solo una metodología.
- El femenino y el plural se marcan con señas adicionales.
- Algunas letras cambian cuando forman parte de un ideograma (m, n, t).
- La expresión facial y corporal es parte de la lengua, no decoración.

---

## 6. Herramientas y recursos evaluados

> Verificado por PyPI/GitHub el 2026-11-18. Las licencias marcadas "verificar" no se revisaron a fondo todavía.

### 6.1 Percepción (manos, cuerpo, rostro)

| Herramienta | Uso | Notas |
|---|---|---|
| **MediaPipe Tasks** (`mediapipe==1.2.3`) | HandLandmarker, PoseLandmarker, FaceLandmarker | API actual. La API `solutions` ya no existe. Modelos `.task` descargables. Apache 2.0. |
| **MediaPipe Tasks for Web** (`@mediapipe/tasks-vision`) | Correr landmarks en el navegador (WASM) | Clave para la versión web: la cámara no tiene que subir video al servidor. |
| **OpenCV** | Captura, dibujo, ventanas | Solo en adaptadores de escritorio; no en el núcleo. |
| **cvzone** | Utilidades de dibujo | Opcional; no lo necesitamos. |

**Decisión:** usar `HandLandmarker` en modo VIDEO. Para palabras/frases, agregar `PoseLandmarker` y `FaceLandmarker` (o el modelo Holistic de Tasks, si está disponible).

### 6.2 Datos y modelos de LSM

| Recurso | Qué es | Cómo lo usaríamos |
|---|---|---|
| **MSL-150** (`armandobecerril/MSL-150-Dataset`, Zenodo DOI 10.5281/zenodo.17783312) | Dataset de **150 señas de LSM** con keypoints de MediaPipe Holistic (226 puntos), 1 firmante nativo, 1080p/30fps. El GitHub trae una muestra; el completo pesa ~13.9 GB. | Arrancar el vocabulario de palabras sin grabar todo desde cero. Ojo: un solo firmante, vocabulario de dominio específico, ambiente controlado. **Verificar licencia.** |
| **`robbolla11/Mexican-Sign-Language-Alphabet-Real-Time-Detection`** | Proyecto pequeño de detección del alfabeto LSM en vivo. | Referencia, no dependencia. |
| **WLASL / AUTSL / Phoenix-14T** | Datasets grandes de ASL/turco/alemán. | Solo para arquitectura y comparación; **no son LSM**. |
| **`VIPL-SLP/Awesome-Sign-Language-Processing`** y **`ZechengLi19/Awesome-Sign-Language`** | Listas curadas de papers, datasets y código. | Consulta para elegir modelos de secuencia. |

**Conclusión:** no existe un dataset público grande y confiable del **abecedario LSM**. Lo tenemos que crear nosotros; MSL-150 sirve para palabras.

### 6.3 Traducción texto ↔ señas

| Recurso | Qué es | Cómo lo usaríamos |
|---|---|---|
| **`sign-language-translator/sign-language-translator`** (SLT, ~384★) | Framework en Python para construir traductores texto↔señas para cualquier lengua; incluye GUI web, concatenación de videos de señas y modelos de pose. | Referencia principal para la dirección texto→señas. **Verificar si soporta LSM y su licencia.** |
| **SignWriting** (`sign-language-processing/signwriting`, `signwriting-translation`) | Sistema de escritura de señas; hay experimentos de traducción español↔señas con SignWriting. | Anotación/representación formal de señas. No es necesario para el MVP. |
| **MMS-Player** (`DFKI-SignLanguage/MMS-Player`) | Generador de animación de avatar 3D desde archivos MMS (glosas + tiempos + inflexiones), ejecutado en Blender. Exporta MP4/FBX/BVH/JSON. **GPL-3.0.** | Referencia para el motor de animación. La licencia GPL es un riesgo si distribuimos el producto. |
| **SignAvatars** (`ZhengdiYu/SignAvatars`, ECCV 2024) | Dataset/benchmark de movimiento holístico 3D (SMPL-X/MANO). | Investigación para animación generativa; no es una herramienta de producción. |

**Estrategia recomendada para texto→señas (Fase 5):** no generar movimiento 3D desde cero. Primero **reproducir clips de señas pregrabadas** (video o pose) sobre un avatar 3D. Después, si hace falta, pasar a animación procedural. La interfaz `SignRenderer` debe permitir ambos sin reescribir el resto.

### 6.4 Voz

| Recurso | Uso | Notas |
|---|---|---|
| **faster-whisper** (`1.2.1`) | ASR offline (voz → texto) | Mucho más rápido que Whisper original en CPU; modelos `tiny`/`base`/`small` para español. Licencia MIT. |
| **openai-whisper** | Alternativa de referencia | Más pesado. |
| **Vosk** | ASR offline ligero | Modelos pequeños; calidad inferior a Whisper. |
| **Piper TTS** (`piper-tts==1.8.0`) | TTS neuronal offline | Mejor calidad que `pyttsx3`; hay voces en español. Verificar disponibilidad de voz `es_MX`. |
| **pyttsx3** | TTS actual | Funciona offline en Windows (SAPI5), pero suena robótico y hay que usarlo con una cola y un solo worker. |

**Decisión:** mantener `pyttsx3` para el MVP y migrar a Piper cuando la calidad importe. El ASR entra hasta la fase 5, pero la interfaz `Transcriber` se define desde ahora.

### 6.5 Web y despliegue

| Recurso | Uso |
|---|---|
| **FastAPI + WebSocket** | Servir inferencia en tiempo real si se necesita servidor. |
| **MediaPipe Tasks for Web** | Landmarks en el navegador; menos latencia y más privacidad. |
| **three.js** (o React Three Fiber) | Render del avatar 3D en web. |
| **ONNX Runtime** | Exportar el clasificador y evitar depender de la versión de scikit-learn/pickle. |
| **Gradio / Streamlit** | Prototipos rápidos de demo; no para producción. |

**Estrategia offline/web:** el núcleo (`src/tlsm`) no importa `cv2` ni UI. Los adaptadores son:
- Escritorio: OpenCV + cámara local + ventana.
- Web: MediaPipe WASM en el navegador + WebSocket al backend, o inferencia ONNX en el cliente.

### 6.6 Datos, calidad y herramientas de desarrollo

- **Git LFS** o **DVC** para datasets/modelos grandes (el repo actual ya pesa ~40 MB y crecerá).
- **Ruff** (lint + format) y **pytest** desde la Fase 1.
- **uv** (opcional) para entornos más rápidos y reproducibles.
- **scikit-learn** para el baseline; **PyTorch** solo si los modelos de secuencia lo justifican (Fase 5).
- **MLflow/W&B** no hacen falta todavía.

---

## 7. Arquitectura objetivo

### 7.1 Principio rector

**El núcleo no sabe de cámaras, ventanas, navegadores ni altavoces.** Solo recibe landmarks/texto y devuelve eventos/texto/señas. Esto es lo que permite tener escritorio offline y web sin duplicar lógica, y agregar el avatar 3D sin reescribir.

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

### 7.2 Capas e interfaces

| Componente | Responsabilidad | Interfaz propuesta |
|---|---|---|
| `landmarks` | Fuente de landmarks (MediaPipe Tasks, web, archivo) | `HandSource.read() -> FrameLandmarks` |
| `features` | Normalización y vector canónico | `extract(frame) -> np.ndarray` |
| `static_model` | Clasificador de señas estáticas | `predict_proba(x) -> dict[label, prob]` |
| `dynamic_model` | Clasificador de secuencias | `predict(seq) -> dict[label, prob]` |
| `segmenter` | Decidir estático vs. movimiento y recortar gestos | `update(frame) -> Event | None` |
| `composer` | Convertir eventos en texto (cooldown, repetición, espacios) | `update(event) -> str` |
| `transcriber` | Voz → texto (fase 5) | `transcribe(audio) -> str` |
| `glosser` | Español → glosas LSM (fase 5) | `gloss(text) -> list[Gloss]` |
| `sign_renderer` | Glosas → avatar/video (fase 5) | `render(glosses)` |
| `speech` | Texto → voz con cola | `speak(text)` |

### 7.3 Contratos de datos

- **`FrameLandmarks`**: `points: float32[21,3]`, `handedness: str`, `timestamp_ms: int`, `confidence: float`.
- **`Sample` estático**: `features: float32[63]`, `label: str`, `is_dynamic: bool`, metadatos.
- **`Sequence` dinámica**: `features: float32[T,63]`, `label: str`, `fps: float`, metadatos.
- **`Event`**: `label`, `confidence`, `tipo` (`static`/`dynamic`), `inicio_ms`, `fin_ms`.

### 7.4 Camino web/offline

- **Offline:** `scripts/` + `.venv` + modelo `.task` local. Empaquetar con PyInstaller en una fase posterior.
- **Web:** frontend con MediaPipe Tasks WASM; el backend solo recibe landmarks o features (no video) y devuelve predicciones. Así se protege la privacidad y se reduce ancho de banda.
- Si el modelo es pequeño (RandomForest/ONNX), puede correr **entero en el navegador** y la web no necesita GPU ni servidor de inferencia.

### 7.5 Camino voz → texto → señas 3D

1. **ASR** (faster-whisper) → texto en español.
2. **Normalización** del texto (minúsculas, puntuación, números).
3. **Glosado**: español → secuencia de glosas LSM. Empezar con un diccionario de palabras y *fallback* a deletreo.
4. **Selección de clips/animaciones** por glosa, con transiciones y tiempos.
5. **Render** en avatar 3D (three.js) o reproducción de video.
6. **Marcadores no manuales** (cejas, mirada, boca): fase posterior, pero el contrato de `Gloss` debe preverlos.

**Importante:** una traducción palabra por palabra **no es LSM**. El glosado y la gramática son un problema lingüístico, no solo de animación. Para el MVP se puede aceptar "español signado" y decirlo explícitamente.

---

## 8. Plan por fases

### Fase 0 — Rescate ✅ (2026-11-18)

- [x] Respaldo fuera de OneDrive.
- [x] Proyecto nuevo en `C:\dev\TLSM`.
- [x] `.gitignore`, `requirements.txt`, `requirements.lock.txt`.
- [x] `venv` nuevo con Python 3.11.
- [x] MediaPipe Tasks + modelo `hand_landmarker.task`.
- [x] Scripts `check_entorno.py` y `demo_camara.py`.
- [x] Esta guía.
- [ ] Commit inicial (se hace al cerrar esta etapa).

**Criterio de aceptación:** `check_entorno.py` pasa y la demo abre la cámara y dibuja la mano.

### Fase 1 — Reacomodo y archivo del legado

- [ ] Crear `src/tlsm/` (sin lógica todavía) y `scripts/`.
- [ ] Mover a `legacy/`: `Dia_1-10/`, `captura/`, `entrenamiento/`, `reconocimiento/`, `modelos/*` v1, `venv` (no versionado).
- [ ] Renombrar rutas con `ñ` a ASCII (`modelos` → `models` o `data`, `señas` → `senas`).
- [ ] `README.md` definitivo + `docs/`.
- [ ] Decidir si el repo nuevo se publica en `Exsoflex/TLSM` (force-push) o en un repo nuevo.
- [ ] Verificar que no queden binarios innecesarios ni el `venv` en git.

**Criterio:** `git status` limpio, repo < 50 MB, `check_entorno` sigue pasando.

### Fase 2 — Núcleo v2 (la reescritura)

- [ ] `config.py` con rutas y parámetros (sin números mágicos).
- [ ] `features.py`: 21 landmarks × (x,y,z), traslación a muñeca, escala por tamaño de mano, rotación canónica. Tests unitarios.
- [ ] `capture.py`: captura guiada con contador, pausa, etiqueta y metadatos.
- [ ] `dataset.py`: esquema v2 + validación (Parquet/NPZ).
- [ ] `train.py`: split por sesión/firmante, validación cruzada agrupada, métricas y matriz de confusión.
- [ ] `recognize.py`: máquina de estados única para estático y movimiento, muestreo temporal fijo.
- [ ] `voice.py`: cola de TTS con un solo worker.
- [ ] Migrar la demo a `HandLandmarker` (ya hecho en `scripts/demo_camara.py`).
- [ ] Evaluar los datos v1 con las features v2 (sin recapturar) para tener línea base.

**Criterio:** pipeline de punta a punta con los datos v1 y métricas honestas.

### Fase 3 — Recaptura del abecedario

- [ ] Capturar las **27 letras** (21 estáticas + 6 dinámicas).
- [ ] Mínimo 3 sesiones por letra, idealmente 2+ firmantes.
- [ ] Registrar metadatos: firmante, sesión, cámara, distancia, iluminación, fondo.
- [ ] Aumento de datos: espejo, ruido, escala, pequeñas rotaciones.
- [ ] Congelar dataset v2 y Reporte de evaluación.

**Criterio:** ≥95% macro-F1 en sesión no vista para las 27 letras; matriz de confusión revisada.

### Fase 4 — Producto (escritorio + web)

- [ ] UI de escritorio (OpenCV para MVP; evaluar PySide6/Qt).
- [ ] Edición de texto: espacio, borrar, limpiar, hablar, historial.
- [ ] Empaquetado instalable (PyInstaller) y modo offline.
- [ ] Demo web (MediaPipe WASM + ONNX en el navegador o FastAPI + WebSocket).
- [ ] Métricas de latencia/FPS y configuración de cámara.

### Fase 5 — Palabras, bidireccionalidad y avatar 3D

- [ ] Vocabulario inicial (usar MSL-150 como arranque, verificar licencia).
- [ ] Modelo de secuencias (1D-CNN/GRU/Transformer) si el baseline no alcanza.
- [ ] ASR offline (faster-whisper) y TTS (Piper).
- [ ] Glosador español → LSM + fallback a deletreo.
- [ ] Avatar 3D con clips pregrabados; después animación procedural.
- [ ] Validación con personas sordas/intérpretes.

---

## 9. Esquema de datos v2

### 9.1 Landmarks

- 21 puntos por mano, `(x, y, z)` normalizados a [0, 1] por MediaPipe.
- **Normalización canónica** antes de guardar features:
  1. Restar la muñeca (landmark 0) → traslación.
  2. Dividir entre `||landmark[9] - landmark[0]||` (tamaño de mano) → escala.
  3. Rotar para alinear `wrist → middle_mcp` con el eje +Y → rotación en el plano.
  4. Conservar `z` escalado.
- Guardar **ambas** versiones: landmarks crudos y features canónicas (para poder reprocesar).

### 9.2 Metadatos obligatorios por muestra

| Campo | Ejemplo | Por qué |
|---|---|---|
| `label` | `A`, `N_TILDE`, `HOLA` | Etiqueta canónica ASCII. |
| `display` | `A`, `Ñ`, `Hola` | Texto para UI. |
| `is_dynamic` | `false` | Distingue letra estática de movimiento. |
| `signer_id` | `S01` | Permite splits por firmante. |
| `session_id` | `2026-11-20_01` | Evita fuga entre train/test. |
| `camera_id` | `integrada_0` | Diagnosticar dominio. |
| `distance_cm` | `60` | Robustez a escala. |
| `lighting` | `interior` | Robustez. |
| `background` | `pared` | Robustez. |
| `fps` | `30` | Reproducir muestreo. |
| `landmark_model` | `mediapipe-1.2.3-hand_landmarker-float16` | Versionado. |
| `app_version` | `0.2.0` | Reproducibilidad. |
| `split` | `train`/`val`/`test` | Asignado por sesión, no por frame. |

### 9.3 Formato

- Estático: `data/processed/static_v2.parquet` (o `.npz`).
- Dinámico: `data/processed/dynamic_v2.npz` con arrays `X[T,63]`, `y`, `meta`.
- Sesiones: `data/raw/<session_id>/` + `session.json`.
- Los datasets grandes **no** van en git; se publican como Release o con LFS/DVC.

---

## 10. Protocolo de evaluación

**Regla de oro:** nunca dividir frames al azar. Los frames consecutivos son casi duplicados.

- **Split por sesión** (y por firmante cuando haya más de uno).
- Reportar:
  - accuracy global;
  - **macro-F1** (clases balanceadas);
  - recall por clase;
  - matriz de confusión;
  - tasa de rechazo de "desconocido" (unknown) y falsos positivos.
- Para movimiento: accuracy a nivel **evento** (seña completa), no frame.
- Medir latencia y FPS en el equipo objetivo.
- Guardar el reporte en `reports/` con fecha y versión del modelo.

**Metas iniciales:**
- 27 letras, sesión no vista: **≥95% macro-F1**.
- 20 palabras, sesión no vista: **≥90% macro-F1**.
- Falsos positivos en reposo: **<5%**.

---

## 11. Convenciones

- Python 3.11, `src/` layout, imports absolutos (`from tlsm.features import ...`).
- **Identificadores en inglés y ASCII** (`wrist_x`, `senas`), textos de UI/documentación en español.
- Etiquetas canónicas ASCII: `N_TILDE`, no `Ñ`; `display` para lo que ve el usuario.
- Type hints, `dataclass` para configurar, `pathlib` para rutas.
- Nada de números mágicos en el código; todo en `config.py`.
- Un solo lugar para extraer features; prohibido duplicarlo.
- `ruff` + `pytest` desde la Fase 1.
- Los scripts se ejecutan siempre desde la raíz del repo (`python -m ...` o `scripts/...`).
- No versionar `venv/`, `__pycache__/`, videos crudos ni datasets grandes.
- Commits pequeños y en español o inglés consistente (elegir uno; propuesta: español).

---

## 12. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Un solo firmante / un solo entorno | El modelo memoriza a la persona | Capturar varias sesiones y firmantes; aumentar datos; medir por firmante. |
| Fuga de datos por frames consecutivos | Métricas falsamente altas | Split por sesión/firmante. |
| MediaPipe cambia de API | Reescritura | Aislar en `landmarks.py`; versión fijada. |
| OneDrive rompe git/venv | Pérdida de trabajo | Proyecto en `C:\dev`; respaldos. |
| Binarios grandes en git | Repo lento/roto | LFS/DVC/Releases a partir de la Fase 3. |
| Avatar 3D subestimado | Meses de trabajo | Empezar con clips pregrabados; interfaz `SignRenderer`. |
| MMS-Player es GPL-3.0 | Obligaciones de licencia | Usarlo solo como referencia o aislarlo; decidir antes de distribuir. |
| Sin validación de la comunidad sorda | Producto culturalmente incorrecto | Buscar intérpretes/asociaciones; validar alfabeto y vocabulario. |
| Regionalismos de LSM | Cobertura limitada | Documentar variante regional; permitir configuración. |
| Web con cámara | Latencia/privacidad | Inferencia en el navegador con WASM. |
| ASR/TTS con acento mexicano | Mala experiencia | Probar modelos en español MX; permitir edición de texto. |

---

## 13. Preguntas abiertas

1. **GitHub:** ¿reutilizamos `Exsoflex/TLSM` con un historial limpio (force-push) o creamos un repo nuevo? Propuesta: repo nuevo `tlsm` y dejar el viejo como archivo.
2. **UI de escritorio:** ¿seguimos con una ventana OpenCV para el MVP o pasamos a Qt/PySide6? Propuesta: OpenCV para el MVP, Qt cuando haya producto.
3. **ASR:** ¿es requisito para el lanzamiento offline o puede esperar a la fase 5? Propuesta: fase 5, pero con la interfaz lista.
4. **Avatar:** ¿empezamos con clips de video 2D o con un rig 3D desde el inicio? Propuesta: clips 2D primero, mismo contrato.
5. **Dos manos:** ¿desde el abecedario o solo cuando lleguen las palabras? Propuesta: una mano para letras; dos para palabras.
6. **Validación:** ¿cómo conseguimos retroalimentación de personas sordas o intérpretes de LSM? Es el riesgo más importante del proyecto.
7. **Licencia del proyecto:** ¿MIT/Apache o GPL? Afecta si usamos MMS-Player u otros componentes GPL.

---

## 14. Bitácora

### 2026-11-18 — Diagnóstico y Etapa 0

- Revisión completa de los 24 archivos del proyecto y de los datasets/modelos.
- Medición del problema de fuga de datos: 99.9% (split aleatorio) vs 91.3% (temporal).
- Prueba de normalización por escala: 96.2% (temporal).
- Detección de `venv` roto, `.git` corrupto, `venv` versionado y proyecto en OneDrive.
- Respaldo y migración a `C:\dev\TLSM`.
- Entorno nuevo con Python 3.11.9 + MediaPipe 1.2.3 (Tasks API).
- Modelo `hand_landmarker.task` descargado y probado.
- `check_entorno.py` y `demo_camara.py` funcionando.
- Extracción de texto del diccionario oficial y confirmación del abecedario:
  21 letras estáticas + 6 con movimiento (J, K, Ñ, Q, X, Z).
- Herramientas evaluadas: MSL-150, SLT, MMS-Player, SignAvatars, SignWriting, faster-whisper, Piper, ONNX, MediaPipe Web.
- Commit inicial `c116221` en el repo nuevo (sin remoto todavía).
- **Siguiente:** Fase 1 (reacomodo).

---

## 15. Comandos útiles

```powershell
# Entrar al proyecto
cd C:\dev\TLSM

# Verificar entorno
.\.venv\Scripts\python.exe scripts\check_entorno.py

# Demo de cámara
.\.venv\Scripts\python.exe scripts\demo_camara.py --camera 0

# Reinstalar dependencias exactas
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt

# Git
git status
git add .
git commit -m "Etapa 0: rescate del proyecto y entorno nuevo"
```

---

## 16. Registro de archivos legado (para no borrar por accidente)

| Archivo | Estado | Acción futura |
|---|---|---|
| `Dia_1-10/` | Ejercicios de aprendizaje | Mover a `legacy/` |
| `captura/captura_letras.py` | Útil como referencia de captura | Reescribir en Fase 2 |
| `captura/captura_movimiento.py` | No guarda datos | Archivar |
| `captura/dataset_movimiento.py` | Referencia de captura dinámica | Reescribir en Fase 2 |
| `entrenamiento/entrenar_modelo.py` | Referencia | Reescribir en Fase 2 |
| `entrenamiento/entrenar_movimiento.py` | Referencia | Reescribir en Fase 2 |
| `reconocimiento/reconocimiento_final.py` | App v1 (no corre en MediaPipe 1.x) | Archivar; usar como referencia de UX |
| `reconocimiento/reconocer_letras.py` | Prototipo superado | Archivar |
| `reconocimiento/reconocer_señas.py` | Prototipo superado; usa modelo viejo | Archivar |
| `reconocimiento/reconocimiento_movimiento.py` | Prototipo superado | Archivar |
| `modelo_señas.pkl` (raíz) | Modelo viejo de 10 clases | Borrar tras archivar |
| `modelos/dataset_señas.csv` | Dataset v1 | Conservar como referencia |
| `modelos/dataset_movimiento.pkl` | Dataset v1 | Conservar como referencia |
| `modelos/modelo_*.pkl` | Modelos v1 | Conservar como referencia |
| `README.txt` | Obsoleto | Reemplazado por `README.md` |
| `venv/` | Roto | No versionar; borrar cuando el nuevo entorno esté validado |
