# Licencias de terceros

El proyecto TLSM se distribuye bajo **MIT**. Para poder distribuirlo a escuelas sin
problemas legales, solo se integran dependencias con licencias permisivas.

> Este documento se actualiza cada vez que se agrega o quita una dependencia.
> Antes de publicar un instalador, ejecutar `scripts/generar_licencias.py` para
> copiar los textos de licencia que vienen dentro de los paquetes instalados.

## Dependencias de ejecución

| Componente | Versión | Licencia | Uso |
|---|---|---|---|
| MediaPipe | 1.2.3 | Apache-2.0 | Landmarks de manos/cuerpo/rostro |
| Modelo `hand_landmarker.task` | float16 v1 | Apache-2.0 | Pesos distribuidos por Google |
| OpenCV (`opencv-contrib-python`) | 5.1.0.95 | Apache-2.0 | Captura, dibujo y ventanas |
| NumPy | 2.4.6 | BSD-3-Clause | Cálculo numérico |
| pandas | 3.1.1 | BSD-3-Clause | Lectura de datasets |
| scikit-learn | 1.9.1 | BSD-3-Clause | Clasificadores |
| SciPy | 1.17.1 | BSD-3-Clause | Dependencia de scikit-learn |
| joblib | 1.6.0 | BSD-3-Clause | Serialización de modelos |
| matplotlib | 3.11.2 | PSF-based (BSD compatible) | Reportes y matrices de confusión |
| pyttsx3 | 2.99 | MPL-2.0 | Síntesis de voz offline |
| comtypes | 1.5.0 | MIT | Dependencia de pyttsx3 en Windows |
| pywin32 | 312 | PSF-2.0 | Dependencia de pyttsx3 en Windows |

Todas son compatibles con un producto distribuido bajo MIT. Las licencias
Apache-2.0 y BSD solo exigen conservar avisos de copyright y licencia.

## Recursos de datos

| Recurso | Licencia | Estado |
|---|---|---|
| **MSL-150** (150 señas de LSM, keypoints) | **CC-BY-4.0** | Se puede usar con atribución. Aún no se incluye en el repo. |
| Diccionario *Manos con voz* (PDF en `docs/`) | Uso educativo; permitida la reproducción con autorización de los coeditores | Se usa como referencia. No se redistribuye fuera del repo sin revisar condiciones. |

## Herramientas opcionales (no incluidas todavía)

| Herramienta | Licencia | Decisión |
|---|---|---|
| faster-whisper | MIT | Se puede integrar para voz → texto. |
| Whisper (pesos) | MIT | Se puede integrar. |
| Piper TTS | MIT | Se puede integrar. **Revisar la licencia de cada voz**; algunas son CC-BY-NC-SA y no se pueden usar en distribución. |
| sign-language-translator | Apache-2.0 | Se puede usar como referencia o dependencia. |
| SignWriting tools | MIT | Se puede usar para anotación. |

## Herramientas excluidas por licencia

| Herramienta | Licencia | Motivo |
|---|---|---|
| **MMS-Player** (DFKI) | **GPL-3.0** | Copyleft fuerte. No se integra ni se distribuye con el producto MIT. Solo se consulta como referencia conceptual. |
| **SignAvatars** | **Sin licencia** | No se puede reutilizar sin permiso explícito. No se usa. |

## Atribución obligatoria de MSL-150 (si se usa)

Si se incorporan datos de MSL-150:

> Dataset MSL-150, de Armando Becerril y colaboradores, distribuido bajo
> Creative Commons Attribution 4.0 International (CC-BY-4.0),
> DOI: 10.5281/zenodo.17783312.

## Nota sobre el modelo de MediaPipe

El archivo `assets/mediapipe/hand_landmarker.task` es distribuido por Google bajo
Apache-2.0. Al redistribuir el instalador se debe conservar este aviso y la licencia
del paquete MediaPipe que se instala con Python.
