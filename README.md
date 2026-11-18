# TLSM — Traductor de Lengua de Señas Mexicana

Proyecto de reconocimiento y traducción de **Lengua de Señas Mexicana (LSM)**.

- **Ahora:** reconocimiento de letras del abecedario (dactilología) desde la cámara.
- **Después:** palabras, frases y traducción bidireccional:
  - señas → texto → voz
  - voz → texto → señas (avatar 3D)
- **Objetivo de producto:** aplicación de escritorio que funcione **offline** y una versión **web** alojada en un servidor.

> ⚠️ El código actual es el **prototipo original** y todavía no corre con el entorno nuevo:
> usa la API `mediapipe.solutions.hands`, que fue eliminada en MediaPipe 1.x.
> La migración a la API moderna (`mediapipe.tasks`) está planificada en la Fase 2.

## Estado

| Fase | Estado |
|---|---|
| 0. Rescate de repo y entorno | ✅ completada (2026-11-18) |
| 1. Reacomodo y archivo del legado | ⏳ siguiente |
| 2. Núcleo v2 (captura, features, modelo) | pendiente |
| 3. Recaptura de datos | pendiente |
| 4. Producto (UI, voz, web) | pendiente |
| 5. Avatar 3D y bidireccionalidad | pendiente |

La guía completa, hallazgos, decisiones y bitácora están en **[GUIA_PROYECTO.md](GUIA_PROYECTO.md)**.

## Requisitos

- Windows 10/11
- Python **3.11**
- Cámara web

## Instalación

```powershell
cd C:\dev\TLSM
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\check_entorno.py
```

> El proyecto **no debe vivir dentro de OneDrive**: OneDrive deshidrata `.git`, los DLL y los `.pack`,
> y rompe el repositorio y el entorno virtual. Trabajar en `C:\dev\TLSM`.

## Scripts disponibles

```powershell
# Verificar entorno, versiones, modelo y cámaras
.\.venv\Scripts\python.exe scripts\check_entorno.py

# Demo: detección de manos con la API moderna de MediaPipe
.\.venv\Scripts\python.exe scripts\demo_camara.py
.\.venv\Scripts\python.exe scripts\demo_camara.py --camera 1 --width 1280 --height 720
```

## Estructura actual

```
TLSM/
├─ assets/mediapipe/       # modelo hand_landmarker.task (MediaPipe Tasks)
├─ captura/                # [legado] captura de datasets
├─ entrenamiento/          # [legado] entrenamiento
├─ reconocimiento/         # [legado] prototipos y app final
├─ modelos/                # datasets y modelos entrenados (v1)
├─ docs/                   # diccionario oficial LSM (PDF + texto extraído)
└─ scripts/                # scripts nuevos del proyecto
```

> El `venv` viejo (roto) se quedó en el proyecto original de OneDrive y en el respaldo;
> **no** se copió al proyecto nuevo. El entorno nuevo es `.venv/` (Python 3.11).

La estructura objetivo se describe en la guía (Fase 1).

## Documentación

- `docs/diccionario_oficial.pdf` — *Diccionario de Lengua de Señas Mexicana "Manos con voz"* (2011).
- `docs/diccionario_oficial.txt` — texto extraído para búsquedas (los acentos están dañados por la fuente del PDF).
