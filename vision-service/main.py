"""
Guías implementadas:
  - Guía 3: Estructuras de Control (validaciones de estado en endpoints)
  - Guía 4: Input/Output (parámetros de query como input; respuestas JSON como output)
  - Guía 5: Diccionarios (respuestas API como dicts clave:valor; historial como lista de dicts)
  - Guía 6: Arrays y Matrices (endpoint /reporte/horario retorna matriz de datos)
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
from detector import DetectorPersonas
from counter_service import (
    registrar_evento,
    obtener_conteo_actual,
    obtener_historial,
    obtener_historial_memoria,
    generar_matriz_horaria,
    imprimir_reporte_horario,
)

# ── Variable global del detector (singleton del proceso) ──────────────────────
# Guía 3 — Act #1: Se valida con if antes de usar en cada endpoint
detector: DetectorPersonas = None
import os

# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK DE CÁMARA → BASE DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

def on_cambio_personas(evento: str, personas_actual: int):
    """
    Guía 3 — Act #1: Callback invocado por el detector cuando hay cambio de personas.
    Implementa la regla de negocio de persistencia: captura → registro en BD.

    Guía 4 — Act #1: 'evento' y 'personas_actual' son los parámetros de entrada
    que alimentan el sistema de conteo (equivalente a los inputs del usuario).
    """
    db = SessionLocal()
    try:
        # Guía 3 — Act #2: Operadores lógicos — solo registra eventos válidos
        if evento and personas_actual >= 0:
            registrar_evento(db, evento, personas_actual)
        else:
            # Guía 4 — Act #2: f-string para log de datos inválidos
            print(f"[ADVERTENCIA] Evento ignorado: evento='{evento}', personas={personas_actual}")
    finally:
        # Guía 3 — Act #2: finally garantiza cierre de sesión (regla de negocio de recursos)
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# CICLO DE VIDA DE LA APLICACIÓN
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Guía 3 — Act #1: Control de flujo de startup/shutdown del microservicio.
    El bloque antes del yield = inicialización; después = limpieza.
    """
    global detector

    # Guía 4 — Act #2: Output de inicio del sistema con f-string
    print(f"[SISTEMA] Iniciando Bus Passenger Counter v2.0")

    detector = DetectorPersonas(callback_cambio=on_cambio_personas)
    detector.iniciar()

    yield  # El servidor está activo entre yield y el cierre

    # Guía 3 — Act #2: Operador and — solo detiene si fue iniciado
    if detector:
        detector.detener()

    print("[SISTEMA] Microservicio detenido correctamente")


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE LA APLICACIÓN FASTAPI
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "Bus Passenger Counter",
    description = "Microservicio de conteo de pasajeros — escribe en bus_platform",
    version     = "2.0.0",
    lifespan    = lifespan,
)


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS DEL MICROSERVICIO
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
def raiz():
    """
    Guía 5 — Act #2: Retorna diccionario clave:valor con estado básico del servicio.
    Guía 4 — Act #2: Respuesta JSON formateada — equivalente al print() del API.
    """
    # Guía 5 — Act #2: Diccionario clave:valor como respuesta del endpoint raíz
    return {
        "status":  "ok",
        "mensaje": "Bus Passenger Counter corriendo 🚌",
        "version": "2.0.0",
    }


@app.get("/conteo")
def conteo_actual(db: Session = Depends(get_db)):
    """
    Guía 5 — Act #2: Endpoint que retorna el estado como diccionario clave:valor.
    Guía 3 — Act #1: Valida si el detector está activo antes de incluir su estado.
    Guía 4 — Act #2: Respuesta JSON con datos formateados del viaje en curso.
    """
    # Guía 5 — Act #2: Obtener diccionario de conteo actual
    datos = obtener_conteo_actual(db)

    # Guía 3 — Act #1: if/else para incluir estado del detector solo si está activo
    if detector:
        datos["detector"] = detector.estado()  # Guía 5: anidamiento de diccionarios
    else:
        datos["detector"] = {"corriendo": False, "mensaje": "Detector no iniciado"}

    return datos


@app.get("/historial")
def historial(
    limit: int = Query(default=50, ge=1, le=500, description="Número de registros a retornar"),
    db: Session = Depends(get_db)
):
    """
    Guía 6 — Act #1: Retorna un vector (lista) de los últimos N conteos del viaje activo.
    Guía 4 — Act #1: 'limit' es un parámetro de entrada (input) con validación de rango.
    Guía 3 — Act #1: La validación ge=1, le=500 aplica reglas de negocio sobre el input.
    Guía 5 — Act #1: El historial es una lista de diccionarios (lista de dicts).
    """
    # Guía 6 — Act #1: Retorna vector de conteos desde BD
    return obtener_historial(db, limit=limit)


@app.get("/historial/memoria")
def historial_en_memoria():
    """
    Guía 6 — Act #1: Retorna el vector en memoria de eventos recientes (sin BD).
    Guía 5 — Act #2: Cada elemento del vector es un diccionario de evento.
    Útil para diagnóstico rápido sin costo de query a base de datos.
    """
    # Guía 6 — Act #1: Vector de eventos en RAM (más rápido que consultar BD)
    eventos = obtener_historial_memoria()

    # Guía 5 — Act #2: Respuesta como diccionario con el vector embebido
    return {
        "total_eventos": len(eventos),   # Guía 6: longitud del vector
        "eventos":       eventos,         # Guía 6: el vector completo
    }


@app.get("/reporte/horario")
def reporte_horario(db: Session = Depends(get_db)):
    """
    Guía 6 — Act #2: Endpoint que genera y retorna la matriz horaria de pasajeros.
    La matriz tiene estructura [hora][métrica] → 24 filas × 3 columnas.

    Guía 5 — Act #1: Itera sobre la matriz para construir respuesta estructurada.
    Guía 3 — Act #1: Filtra horas sin actividad antes de incluirlas en la respuesta.
    Guía 4 — Act #2: Nombres de columnas claros para legibilidad del output JSON.
    """
    # Guía 6 — Act #2: Generar matriz horaria [24][3]
    matriz = generar_matriz_horaria(db)

    # Guía 4 — Act #2: Imprimir reporte en consola (output formateado)
    imprimir_reporte_horario(matriz)

    # Guía 5 — Act #1: List comprehension para transformar matriz a lista de dicts legibles
    # Guía 6 — Act #2: Acceso por doble índice matriz[hora][metrica]
    reporte = [
        {
            "hora":     f"{hora:02d}:00",    # Guía 4: f-string para formatear hora con ceros
            "subidas":  matriz[hora][0],      # Guía 6: matriz[fila][columna 0]
            "bajadas":  matriz[hora][1],      # Guía 6: matriz[fila][columna 1]
            "neto":     matriz[hora][2],      # Guía 6: matriz[fila][columna 2]
        }
        for hora in range(24)                 # Guía 5 — Act #1: for sobre índices de filas
        if matriz[hora][0] > 0 or matriz[hora][1] > 0   # Guía 3: filtrar horas sin actividad
    ]

    # Guía 5 — Act #2: Respuesta como diccionario con metadata y datos de la matriz
    return {
        "dimension":       "24 horas × 3 métricas [subidas, bajadas, neto]",
        "horas_con_datos": len(reporte),   # Guía 6: estadística sobre la matriz
        "reporte":         reporte,         # Guía 6: representación serializada de la matriz
    }


@app.post("/conteo/reset")
def reset_detector():
    """
    Guía 3 — Act #1: Regla de negocio — solo reinicia si el detector existe y está activo.
    Guía 5 — Act #2: Retorna diccionario con estado resultante del reset.
    Guía 4 — Act #2: Respuesta JSON informativa sobre la operación ejecutada.
    """
    # Guía 3 — Act #1: Condicional para verificar existencia del detector
    if not detector:
        # Guía 3 — Act #1: elif/else — error controlado si no hay detector
        raise HTTPException(status_code=503, detail="Detector no iniciado")

    # Guía 3 — Act #1: Reseteo controlado de estado interno del detector
    detector.personas_prev   = 0
    detector.personas_actual = 0
    detector.historial_frames = []  # Guía 6: limpiar vector de historial

    # Guía 4 — Act #2: Output de confirmación como diccionario JSON
    print("[RESET] Detector reiniciado manualmente")

    # Guía 5 — Act #2: Diccionario de respuesta con estado post-reset
    return {
        "status":  "ok",
        "mensaje": "Detector y vector de historial reiniciados",
    }


@app.get("/health")
def health():
    """
    Guía 5 — Act #2: Endpoint de salud — retorna diccionario con estado del sistema.
    Guía 3 — Act #1: if/else para reportar estado del detector según disponibilidad.
    Guía 4 — Act #2: Respuesta JSON con formato estandarizado para monitoreo.
    """
    # Guía 3 — Act #1: if/else para determinar estado del sistema
    if detector and detector.corriendo:
        estado_detector = detector.estado()   # Guía 5: diccionario de estado
        estado_sistema  = "healthy"
    elif detector and not detector.corriendo:
        estado_detector = {"corriendo": False}
        estado_sistema  = "degraded"
    else:
        estado_detector = "no iniciado"
        estado_sistema  = "unhealthy"

    # Guía 5 — Act #2: Respuesta como diccionario anidado clave:valor
    return {
        "status":   estado_sistema,
        "detector": estado_detector,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA DIRECTO (para debugging local)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Guía 4 — Act #1: Parámetros de configuración del servidor como input de entorno.
    Guía 3 — Act #1: Condicional __name__ == '__main__' para ejecución directa.
    """
    import uvicorn

    # Guía 4 — Act #1: Captura de parámetros de servidor desde entorno (input del sistema)
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # Guía 4 — Act #2: Output de inicio con parámetros formateados
    print(f"[SERVER] Iniciando en http://{HOST}:{PORT}")

    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)