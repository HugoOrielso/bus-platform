"""
detector.py — Deteccion de personas con OpenCV + ventana visual
"""
import numpy as np
import cv2
import imutils
from imutils.object_detection import non_max_suppression
import threading
import time
import os
from dotenv import load_dotenv

load_dotenv()

CAMERA_INDEX       = int(os.getenv("CAMERA_INDEX", 0))
DETECTION_INTERVAL = int(os.getenv("DETECTION_INTERVAL", 3))


class DetectorPersonas:
    def __init__(self, callback_cambio):
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        self.cap             = None
        self.corriendo       = False
        self.personas_prev   = 0
        self.personas_actual = 0
        self.callback        = callback_cambio
        self._thread         = None
        self._rects          = []

    def iniciar(self):
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self.cap.isOpened():
            raise RuntimeError(f"No se pudo abrir la camara en indice {CAMERA_INDEX}")
        self.corriendo = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(f"Detector iniciado — camara indice {CAMERA_INDEX}")

    def detener(self):
        self.corriendo = False
        cv2.destroyAllWindows()
        if self.cap:
            self.cap.release()
        print("Detector detenido")

    # ✅ FUNCIÓN REEMPLAZADA
    def _detectar_personas(self, frame):
        frame_small = imutils.resize(frame, width=min(400, frame.shape[1]))

        frame_gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
        frame_gray = cv2.equalizeHist(frame_gray)

        (rects, weights) = self.hog.detectMultiScale(
            frame_gray,
            winStride=(6, 6),
            padding=(12, 12),
            scale=1.05,
            hitThreshold=0.3,
        )

        if len(rects) == 0:
            return 0, []

        rects_filtrados = [
            r for r, w in zip(rects, weights) if w > 0.3
        ]

        rects_np = non_max_suppression(
            np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects_filtrados]),
            probs=None,
            overlapThresh=0.65
        )

        scale = frame.shape[1] / frame_small.shape[1]
        rects_scaled = [
            (int(x1 * scale), int(y1 * scale),
             int((x2 - x1) * scale), int((y2 - y1) * scale))
            for (x1, y1, x2, y2) in rects_np
        ]

        return len(rects_scaled), rects_scaled

    def _dibujar_frame(self, frame):
        for (x, y, w, h) in self._rects:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "Persona", (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (340, 65), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        cv2.putText(frame, f"Personas: {self.personas_actual}",
                    (10, 38), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 2)
        cv2.putText(frame, "Q = cerrar ventana",
                    (10, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
        return frame

    def _loop(self):
        frame_count = 0
        while self.corriendo:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            frame_count += 1
            if frame_count % DETECTION_INTERVAL == 0:
                cantidad, rects = self._detectar_personas(frame)
                self._rects = rects
                self.personas_actual = cantidad
                if cantidad != self.personas_prev:
                    evento = "subio" if cantidad > self.personas_prev else "bajo"
                    self.callback(evento, cantidad)
                    self.personas_prev = cantidad
            frame_visual = self._dibujar_frame(frame.copy())
            cv2.imshow("Bus Vision — Detector de Pasajeros", frame_visual)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
            time.sleep(0.033)

    def estado(self):
        return {
            "corriendo":       self.corriendo,
            "personas_actual": self.personas_actual,
            "camara_index":    CAMERA_INDEX,
        }