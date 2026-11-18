"""Demo de detección de manos con la API moderna de MediaPipe Tasks.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\demo_camara.py
    .\\.venv\\Scripts\\python.exe scripts\\demo_camara.py --camera 1 --width 1280 --height 720

Teclas:
    ESC / Q   salir
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

RAIZ = Path(__file__).resolve().parents[1]
MODELO_POR_DEFECTO = RAIZ / "assets" / "mediapipe" / "hand_landmarker.task"

COLORES = {
    "Left": (0, 200, 255),
    "Right": (0, 255, 0),
    "Unknown": (200, 200, 200),
}


def abrir_camara(indice: int, ancho: int, alto: int) -> cv2.VideoCapture:
    backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else 0
    captura = cv2.VideoCapture(indice, backend) if backend else cv2.VideoCapture(indice)
    if not captura.isOpened() and backend:
        captura.release()
        captura = cv2.VideoCapture(indice)
    captura.set(cv2.CAP_PROP_FRAME_WIDTH, ancho)
    captura.set(cv2.CAP_PROP_FRAME_HEIGHT, alto)
    return captura


def dibujar_mano(frame, landmarks, color) -> None:
    alto, ancho = frame.shape[:2]
    puntos = []
    for punto in landmarks:
        x = int(min(max(punto.x, 0.0), 1.0) * ancho)
        y = int(min(max(punto.y, 0.0), 1.0) * alto)
        puntos.append((x, y))

    for conexion in vision.HandLandmarksConnections.HAND_CONNECTIONS:
        cv2.line(frame, puntos[conexion.start], puntos[conexion.end], color, 2)

    for x, y in puntos:
        cv2.circle(frame, (x, y), 4, (255, 255, 255), -1)
        cv2.circle(frame, (x, y), 4, color, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Demo de detección de manos TLSM")
    parser.add_argument("--camera", type=int, default=0, help="Índice de cámara (default: 0)")
    parser.add_argument("--width", type=int, default=1280, help="Ancho solicitado")
    parser.add_argument("--height", type=int, default=720, help="Alto solicitado")
    parser.add_argument("--max-manos", type=int, default=1, help="Máximo de manos a detectar")
    parser.add_argument("--modelo", type=Path, default=MODELO_POR_DEFECTO, help="Ruta del .task")
    args = parser.parse_args()

    if not args.modelo.exists():
        print(f"No existe el modelo: {args.modelo}")
        return 1

    captura = abrir_camara(args.camera, args.width, args.height)
    if not captura.isOpened():
        print(f"No se pudo abrir la cámara {args.camera}.")
        return 1

    opciones = vision.HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(args.modelo)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=args.max_manos,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    inicio = time.perf_counter()
    inicio_frame = inicio
    ultimo_ts = -1
    fps = 0.0

    try:
        with vision.HandLandmarker.create_from_options(opciones) as detector:
            while True:
                ok, frame = captura.read()
                if not ok:
                    print("No se pudo leer un frame de la cámara.")
                    break

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb = rgb.copy()
                imagen = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

                timestamp = int((time.perf_counter() - inicio) * 1000)
                if timestamp <= ultimo_ts:
                    timestamp = ultimo_ts + 1
                ultimo_ts = timestamp

                resultado = detector.detect_for_video(imagen, timestamp)

                for indice, landmarks in enumerate(resultado.hand_landmarks):
                    etiqueta = "Unknown"
                    score = 0.0
                    if indice < len(resultado.handedness) and resultado.handedness[indice]:
                        categoria = resultado.handedness[indice][0]
                        etiqueta = categoria.category_name
                        score = categoria.score

                    color = COLORES.get(etiqueta, COLORES["Unknown"])
                    dibujar_mano(frame, landmarks, color)
                    cv2.putText(
                        frame,
                        f"{etiqueta} {score:.2f}",
                        (10, 70 + indice * 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        color,
                        2,
                    )

                ahora = time.perf_counter()
                fps = 0.9 * fps + 0.1 * (1.0 / max(ahora - inicio_frame, 1e-6))
                inicio_frame = ahora
                cv2.putText(
                    frame,
                    f"FPS: {fps:5.1f}  |  Manos: {len(resultado.hand_landmarks)}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 0),
                    2,
                )
                cv2.putText(
                    frame,
                    "ESC/Q salir",
                    (10, frame.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (200, 200, 200),
                    1,
                )

                cv2.imshow("TLSM - Demo MediaPipe Tasks", frame)
                tecla = cv2.waitKey(1) & 0xFF
                if tecla in (27, ord("q")):
                    break
    finally:
        captura.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
