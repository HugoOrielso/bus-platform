"""
detector.py — Deteccion de personas con OpenCV + ventana visual
"""
import cv2
import imutils
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

    def _detectar_personas(self, frame):
        frame_small = imutils.resize(frame, width=min(400, frame.shape[1]))
        frame_gray  = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
        (rects, _)  = self.hog.detectMultiScale(
            frame_gray,
            winStride=(4, 4),
            padding=(8, 8),
            scale=1.03,
            hitThreshold=0,
        )
        scale = frame.shape[1] / frame_small.shape[1]
        rects_scaled = []
        #guía 2 y guía 4 (ints)
        for (x, y, w, h) in rects:
            rects_scaled.append((
                int(x * scale),
                int(y * scale),
                int(w * scale),
                int(h * scale),
            ))
        return len(rects_scaled), rects_scaled

    def _dibujar_frame(self, frame):
        #guía 2
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
        #guía 4
        frame_count = 0
        #guía 2
        while self.corriendo:
            ret, frame = self.cap.read()
            #guía 3
            if not ret:
                time.sleep(0.1)
                continue
            frame_count += 1
            #guía 3
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