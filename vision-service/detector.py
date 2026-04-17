"""
detector.py — Deteccion de personas con OpenCV + ventana visual

Guías implementadas:
  - Guía 3: Estructuras de Control (if/elif/else para decisiones de detección y estados)
  - Guía 4: Input/Output (variables de entorno como input; f-strings para output visual)
  - Guía 5: Diccionarios (estado del detector como dict clave:valor; ciclos de monitoreo)
  - Guía 6: Arrays y Matrices (historial de conteos por frame como vector; rects como matriz)
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

# ── Guía 4 — Act #1: Captura dinámica de parámetros desde entorno (input del sistema) ──
# Equivalente al input() del sistema operativo: lee configuración en tiempo de ejecución
CAMERA_INDEX       = int(os.getenv("CAMERA_INDEX", 0))
DETECTION_INTERVAL = int(os.getenv("DETECTION_INTERVAL", 3))

# ── Guía 3 — Act #1: Constantes de umbrales para reglas de negocio del detector ──
UMBRAL_CONFIANZA   = float(os.getenv("UMBRAL_CONFIANZA", 0.3))   # Score mínimo del HOG
UMBRAL_OVERLAP     = float(os.getenv("UMBRAL_OVERLAP",   0.65))  # Supresión de cajas duplicadas
ANCHO_MAX_FRAME    = int(os.getenv("ANCHO_MAX_FRAME",    400))   # Ancho máximo para procesamiento

# ── Guía 6 — Act #1: Vector de historial de conteos por frame (tamaño máximo fijo) ──
MAX_HISTORIAL_FRAMES = 30   # Tamaño máximo del vector en memoria (últimos 30 frames)


class DetectorPersonas:
    """
    Guía 3 — Act #1 y #2: Clase que encapsula el motor de decisiones de detección.
    Cada método implementa reglas de negocio con estructuras if/elif/else.

    Guía 5 — Act #2: El estado interno se expone como diccionario clave:valor.
    Guía 6 — Act #1: historial_frames es un vector de conteos históricos por frame.
    """

    def __init__(self, callback_cambio):
        # ── Inicialización del detector HOG (Histogram of Oriented Gradients) ──
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        # ── Guía 5 — Act #2: Atributos del detector organizados como propiedades de objeto ──
        self.cap             = None
        self.corriendo       = False
        self.personas_prev   = 0
        self.personas_actual = 0
        self.callback        = callback_cambio
        self._thread         = None
        self._rects          = []      # Vector de rectángulos de detección actual

        # Guía 6 — Act #1: Vector unidimensional de historial de conteos por frame
        # Actúa como buffer circular de tamaño MAX_HISTORIAL_FRAMES
        self.historial_frames = []

    # ─────────────────────────────────────────────────────────────────────────
    # MÉTODOS DE CICLO DE VIDA
    # ─────────────────────────────────────────────────────────────────────────

    def iniciar(self):
        """
        Guía 3 — Act #1: Regla de negocio — validar apertura de cámara antes de iniciar.
        Si la cámara no está disponible, lanza excepción controlada.
        Guía 4 — Act #2: Output formateado confirmando estado de inicio del sistema.
        """
        self.cap = cv2.VideoCapture(CAMERA_INDEX)

        # Guía 3 — Act #1: Condicional crítico — la cámara debe estar operativa
        if not self.cap.isOpened():
            # Guía 4 — Act #2: Mensaje de error formateado con f-string
            raise RuntimeError(f"[ERROR] No se pudo abrir la cámara en índice {CAMERA_INDEX}")

        self.corriendo = True
        self._thread   = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

        # Guía 4 — Act #2: Confirmación de inicio con parámetros formateados
        print(f"[DETECTOR] Iniciado — Cámara índice: {CAMERA_INDEX} | Intervalo: {DETECTION_INTERVAL} frames")

    def detener(self):
        """
        Guía 3 — Act #1: Secuencia de cierre controlado del detector.
        Guía 4 — Act #2: Output de confirmación de detención.
        """
        self.corriendo = False
        cv2.destroyAllWindows()

        # Guía 3 — Act #2: Operador and — solo libera si la cámara fue abierta
        if self.cap and self.cap.isOpened():
            self.cap.release()

        print("[DETECTOR] Detenido correctamente")

    # ─────────────────────────────────────────────────────────────────────────
    # MOTOR DE DETECCIÓN HOG
    # ─────────────────────────────────────────────────────────────────────────

    def _detectar_personas(self, frame) -> tuple[int, list]:
        """
        Guía 3 — Act #1 y #2: Motor de decisiones de visión computacional.
        Aplica reglas de negocio para filtrar detecciones válidas:
          - Si no hay rectángulos → retornar 0
          - Si confianza < umbral → descartar (filtro)
          - Si overlap > umbral   → suprimir duplicado (NMS)

        Guía 6 — Act #2: rects_np es una matriz Nx4 donde:
          - Filas    → cada persona detectada
          - Columnas → [x1, y1, x2, y2] (coordenadas del bounding box)
        Acceso: rects_np[i][0] = x1 de la persona i

        Guía 5 — Act #1: List comprehension con filtro (for + if) sobre colección de rects
        """

        # ── Preprocesamiento del frame ────────────────────────────────────────
        frame_small = imutils.resize(frame, width=min(ANCHO_MAX_FRAME, frame.shape[1]))
        frame_gray  = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
        frame_gray  = cv2.equalizeHist(frame_gray)

        # ── Detección HOG ─────────────────────────────────────────────────────
        (rects, weights) = self.hog.detectMultiScale(
            frame_gray,
            winStride    = (6, 6),
            padding      = (12, 12),
            scale        = 1.05,
            hitThreshold = UMBRAL_CONFIANZA,
        )

        # Guía 3 — Act #1: Regla de negocio — si no hay detecciones, retornar vacío
        if len(rects) == 0:
            return 0, []

        # Guía 5 — Act #1: List comprehension con filtro — solo rects con peso > umbral
        # Equivalente a un ciclo for con continue si no cumple la condición
        rects_filtrados = [
            r for r, w in zip(rects, weights)
            if w > UMBRAL_CONFIANZA  # Guía 3 — Act #2: Operador lógico de filtro
        ]

        # Guía 3 — Act #1: Regla de negocio — si todos fueron filtrados, retornar vacío
        if not rects_filtrados:
            return 0, []

        # ── Guía 6 — Act #2: Construir matriz Nx4 de coordenadas ─────────────
        # Cada fila = una detección; columnas = [x1, y1, x2, y2]
        # Acceso por doble índice: rects_np[fila][columna]
        rects_np = non_max_suppression(
            np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects_filtrados]),
            probs        = None,
            overlapThresh = UMBRAL_OVERLAP,
        )

        # ── Escalar coordenadas al tamaño original del frame ──────────────────
        scale = frame.shape[1] / frame_small.shape[1]

        # Guía 6 — Act #2: List comprehension sobre la matriz rects_np
        # Guía 5 — Act #1: for sobre cada fila de la matriz de coordenadas
        rects_scaled = [
            (
                int(x1 * scale),           # Columna 0 escalada
                int(y1 * scale),           # Columna 1 escalada
                int((x2 - x1) * scale),    # Ancho escalado
                int((y2 - y1) * scale),    # Alto escalado
            )
            for (x1, y1, x2, y2) in rects_np  # Guía 6: iteración sobre filas de matriz
        ]

        return len(rects_scaled), rects_scaled

    # ─────────────────────────────────────────────────────────────────────────
    # RENDERIZADO VISUAL
    # ─────────────────────────────────────────────────────────────────────────

    def _dibujar_frame(self, frame):
        """
        Guía 6 — Act #1: Itera sobre el vector self._rects para dibujar cada detección.
        Guía 5 — Act #1: Ciclo for sobre colección de rectángulos detectados.
        Guía 4 — Act #2: Output visual formateado con texto superpuesto en el frame.
        """

        # Guía 5 — Act #1: Ciclo for sobre vector de rectángulos de detección
        for (x, y, w, h) in self._rects:  # Guía 6: cada elemento es [x, y, w, h]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "Persona", (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # ── Guía 4 — Act #2: Overlay con métricas formateadas en pantalla ────
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (360, 75), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

        # Guía 4 — Act #2: f-string equivalente en OpenCV — texto formateado en frame
        cv2.putText(frame, f"Personas: {self.personas_actual}",
                    (10, 38), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 2)
        cv2.putText(frame, f"Prev: {self.personas_prev} | Q = cerrar",
                    (10, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
        return frame

    # ─────────────────────────────────────────────────────────────────────────
    # BUCLE PRINCIPAL DEL DETECTOR
    # ─────────────────────────────────────────────────────────────────────────

    def _loop(self):
        """
        Guía 5 — Act #1B: Ciclo while para monitoreo continuo (condición de parada dinámica).
        El bucle continúa mientras self.corriendo sea True — condición de parada controlada.

        Guía 3 — Act #1: Motor de decisiones principal:
          - si cantidad cambia → determinar si fue subida o bajada
          - si cantidad > prev → evento "subio"
          - elif cantidad < prev → evento "bajo"
          - else → sin cambio (no se registra)

        Guía 6 — Act #1: historial_frames actúa como vector buffer FIFO de conteos.
        """
        frame_count = 0

        # Guía 5 — Act #1B: Ciclo while con condición dinámica (monitoreo de sensor)
        while self.corriendo:
            ret, frame = self.cap.read()

            # Guía 3 — Act #2: Operador not para verificar lectura válida de frame
            if not ret:
                time.sleep(0.1)
                continue  # Guía 5 — Act #1C: continue para saltar frames inválidos

            frame_count += 1

            # Guía 3 — Act #2: Condición de intervalo — solo procesar cada N frames
            if frame_count % DETECTION_INTERVAL == 0:
                cantidad, rects = self._detectar_personas(frame)
                self._rects          = rects
                self.personas_actual = cantidad

                # ── Guía 6 — Act #1: Actualizar vector historial_frames (buffer FIFO) ──
                if len(self.historial_frames) >= MAX_HISTORIAL_FRAMES:
                    self.historial_frames.pop(0)   # Eliminar elemento más antiguo del vector
                self.historial_frames.append(cantidad)  # Insertar nuevo conteo en el vector

                # Guía 3 — Act #1: Regla de negocio — detectar cambio en cantidad de personas
                if cantidad != self.personas_prev:

                    # Guía 3 — Act #1: if/elif/else para determinar tipo de evento
                    if cantidad > self.personas_prev:
                        evento = "subio"   # Personas aumentaron → SUBIDA
                    elif cantidad < self.personas_prev:
                        evento = "bajo"    # Personas disminuyeron → BAJADA
                    else:
                        evento = None      # Sin cambio (no debería llegar aquí)

                    # Guía 3 — Act #2: Operador and — solo registrar si hay evento válido
                    if evento and self.callback:
                        self.callback(evento, cantidad)

                    self.personas_prev = cantidad  # Actualizar estado previo

            # ── Renderizado del frame con anotaciones ─────────────────────────
            frame_visual = self._dibujar_frame(frame.copy())
            cv2.imshow("Bus Vision — Detector de Pasajeros", frame_visual)

            # Guía 3 — Act #2: Operador bitwise & para capturar tecla 'q' (salida)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break  # Guía 5 — Act #1C: break para salida controlada del while

            time.sleep(0.033)  # ~30 FPS máximo

    # ─────────────────────────────────────────────────────────────────────────
    # CONSULTAS DE ESTADO
    # ─────────────────────────────────────────────────────────────────────────

    def estado(self) -> dict:
        """
        Guía 5 — Act #2: Retorna el estado del detector como diccionario clave:valor.
        Guía 6 — Act #1: Incluye estadísticas calculadas sobre el vector historial_frames.
        Guía 3 — Act #1: if/else para calcular promedio solo si hay datos en el vector.
        Guía 4 — Act #2: Valores numéricos formateados con redondeo estándar.
        """

        # Guía 6 — Act #1: Cálculo sobre el vector historial_frames
        # Guía 3 — Act #1: Condicional para evitar división por cero en vector vacío
        if self.historial_frames:
            # Guía 5 — Act #1: Operaciones sobre colección — sum y len del vector
            promedio_personas = round(sum(self.historial_frames) / len(self.historial_frames), 2)
            maximo_detectado  = max(self.historial_frames)  # Guía 6: max sobre vector
        else:
            promedio_personas = 0.0
            maximo_detectado  = 0

        # Guía 5 — Act #2: Diccionario clave:valor con estado completo del detector
        return {
            "corriendo":          self.corriendo,
            "personas_actual":    self.personas_actual,
            "personas_previas":   self.personas_prev,
            "camara_index":       CAMERA_INDEX,
            "intervalo_frames":   DETECTION_INTERVAL,
            "umbral_confianza":   UMBRAL_CONFIANZA,
            "promedio_personas":  promedio_personas,   # Guía 6: estadística del vector
            "maximo_detectado":   maximo_detectado,    # Guía 6: máximo del vector
            "frames_analizados":  len(self.historial_frames),  # Guía 6: longitud del vector
        }

    def imprimir_estado(self):
        """
        Guía 4 — Act #2: Output formateado con f-strings para reporte de consola.
        Muestra el estado actual del detector con alineación profesional de columnas.
        """
        datos = self.estado()

        # Guía 4 — Act #2: Reporte estructurado con f-strings y alineación de columnas
        print("\n" + "─" * 45)
        print(f"{'ESTADO DEL DETECTOR':^45}")
        print("─" * 45)
        print(f"  {'Corriendo:':<22} {str(datos['corriendo']):>10}")
        print(f"  {'Personas actual:':<22} {datos['personas_actual']:>10}")
        print(f"  {'Cámara índice:':<22} {datos['camara_index']:>10}")
        print(f"  {'Promedio (últimos frames):':<22} {datos['promedio_personas']:>10.2f}")
        print(f"  {'Máximo detectado:':<22} {datos['maximo_detectado']:>10}")
        print("─" * 45)