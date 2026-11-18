import cv2
import mediapipe as mp
import csv
import os
import time

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

archivo = "modelos/dataset_señas.csv"

# ==============================
# CREAR ARCHIVO SI NO EXISTE
# ==============================
if not os.path.exists(archivo):
    with open(archivo, mode="w", newline="") as f:
        writer = csv.writer(f)
        header = []

        for i in range(21):
            header.append(f"x{i}")
            header.append(f"y{i}")

        header.append("letra")
        writer.writerow(header)

# ==============================
# CONFIGURACIÓN
# ==============================
cap = cv2.VideoCapture(0)

letra = input("Ingresa la letra que quieres capturar: ").upper()

contador = 0
max_muestras = 300

cooldown = 0.04  # tiempo entre capturas (ajústalo si quieres)
ultimo_guardado = time.time()

pausado = False

# ==============================
# CAPTURA
# ==============================
with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.8,
        min_tracking_confidence=0.8) as hands:

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        resultado = hands.process(rgb)

        if resultado.multi_hand_landmarks and not pausado:

            for hand_landmarks in resultado.multi_hand_landmarks:

                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # CONTROL DE COOLDOWN
                if time.time() - ultimo_guardado < cooldown:
                    continue

                fila = []

                muñeca_x = hand_landmarks.landmark[0].x
                muñeca_y = hand_landmarks.landmark[0].y

                for lm in hand_landmarks.landmark:
                    fila.append(lm.x - muñeca_x)
                    fila.append(lm.y - muñeca_y)

                fila.append(letra)

                with open(archivo, mode="a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(fila)

                contador += 1
                ultimo_guardado = time.time()

                if contador >= max_muestras:
                    break

        # ==============================
        # UI
        # ==============================
        cv2.putText(frame, f"Letra: {letra}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0), 2)

        cv2.putText(frame, f"Muestras: {contador}/{max_muestras}", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        estado = "PAUSADO" if pausado else "CAPTURANDO"
        cv2.putText(frame, estado, (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0,0,255) if pausado else (0,255,0), 2)

        cv2.imshow("Recolectando datos", frame)

        # ==============================
        # CONTROLES
        # ==============================
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            break

        elif key == ord('p'):  # pausar
            pausado = not pausado

        elif key == ord('n'):  # nueva letra
            letra = input("Nueva letra: ").upper()
            contador = 0

        if contador >= max_muestras:
            print(f"✔ {max_muestras} muestras capturadas para {letra}")
            letra = input("Ingresa nueva letra: ").upper()
            contador = 0

# ==============================
# FINAL
# ==============================
cap.release()
cv2.destroyAllWindows()

print("Datos guardados correctamente.")