"""
main.py — Microservicio FastAPI para conteo de pasajeros
Escribe en bus_platform (misma DB que Express/Prisma)

Guías implementadas:
  - Guía 3: Estructuras de Control (validaciones en endpoints)
  - Guía 4: Input/Output (parámetros de query; respuestas JSON como output)
  - Guía 5: Diccionarios (respuestas API como dicts; historial como lista de dicts)
  - Guía 6: Arrays y Matrices (endpoint /reporte/horario retorna matriz)
  - Guía 7: Subalgoritmos — run() orquestador; diagnostico_sistema() consolidado
  - Guía 8: Persistencia — lifespan restaura y guarda config.txt + CSV al cerrar
  - Guía 9: POO — endpoints /conteo/poo y /historial/objetos usan clases EventoConteo
"""

import os
from fastapi import FastAPI, Depends, HTTPException, Query
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
from detector import DetectorPersonas
from counter_service import (
    registrar_evento,
    registrar_evento_poo,
    obtener_conteo_actual,
    obtener_historial,
    obtener_historial_memoria,
    obtener_historial_objetos,
    generar_matriz_horaria,
    imprimir_reporte_horario,
    filtrar_horas_activas,
    calcular_ocupacion,
    # Guía 7: Lambdas importadas para uso en endpoints
    solo_subidas,
    solo_bajadas,
    confianza_promedio,
    horas_pico,
    ordenar_reciente,
)

# Guía 3 — Act #1: Variable global del detector (singleton del proceso)
detector: DetectorPersonas = None


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK DE CÁMARA → BASE DE DATOS + PERSISTENCIA
# Guía 7 — Act #1: Subalgoritmo orquestador del evento de detección
# ─────────────────────────────────────────────────────────────────────────────

def on_cambio_personas(evento: str, personas_actual: int):
    """
    Guía 7 — Act #1: Subalgoritmo de callback — responsabilidad única de despacho.
    Guía 3 — Act #2: Operadores lógicos — solo registra eventos válidos (and).
    Guía 8 — Act #1: registrar_evento() internamente llama a escribir_log().
    Guía 9 — Act #3: También registra en el vector POO con registrar_evento_poo().
    """
    db = SessionLocal()
    try:
        # Guía 3 — Act #2: and — solo registra si el evento y las personas son válidas
        if evento and personas_actual >= 0:
            # Versión dict (compatibilidad Guías 3-8)
            registrar_evento(db, evento, personas_actual)
            # Guía 9 — Act #3: Versión POO — registra también en vector de objetos
            registrar_evento_poo(evento, personas_actual)
        else:
            # Guía 4 — Act #2: f-string para advertencia de dato inválido
            print(f"[ADVERTENCIA] Evento ignorado: evento='{evento}', personas={personas_actual}")
    finally:
        # Guía 3 — Act #2: finally — garantiza cierre de sesión de BD siempre
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# CICLO DE VIDA DE LA APLICACIÓN
# Guía 7 — Act #3: Función lifespan como orquestador de inicio/cierre
# Guía 8 — Act #1: Restaura config al iniciar; guarda config y CSV al cerrar
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Guía 7 — Act #3: Orquestador del ciclo de vida — toda la lógica en subalgoritmos.
    Guía 8 — Act #1: Al INICIAR → cargar_config() restaura sesión previa desde config.txt.
    Guía 8 — Act #2: Al CERRAR → guardar_config() + exportar_historial_csv() persisten estado.
    Guía 3 — Act #1: if/else para reportar sesión restaurada vs nuevo inicio.
    """
    global detector

    # ── Guía 8 — Act #1: INICIO — Restaurar sesión anterior desde archivo ──────
    from persistence import cargar_config, guardar_config, exportar_historial_csv

    config_previa = cargar_config()  # Guía 8: lectura de config.txt (modo 'r')

    # Guía 3 — Act #1: if/else — reportar si hay sesión previa o es inicio nuevo
    if config_previa.get("BUS_ID"):
        # Guía 4 — Act #2: f-string con datos de la sesión restaurada
        print(f"[SISTEMA] Retomando sesión — Bus: {config_previa.get('PLACA', '?')}")
    else:
        print("[SISTEMA] Primer inicio — no hay sesión previa")

    print("[SISTEMA] Iniciando Bus Passenger Counter v2.0")

    # Guía 9 — Act #1: Instanciar DetectorPersonas (objeto POO principal)
    detector = DetectorPersonas(callback_cambio=on_cambio_personas)
    detector.iniciar()

    yield  # El servidor está activo entre yield y el bloque de cierre

    # ── Guía 8 — Act #1 y #2: CIERRE — Guardar estado en archivos ──────────────
    db = SessionLocal()
    try:
        from counter_service import obtener_o_crear_ruta, obtener_o_crear_bus

        ruta = obtener_o_crear_ruta(db)
        bus  = obtener_o_crear_bus(db, ruta)

        # Guía 8 — Act #1: Guardar configuración en config.txt (modo 'w')
        guardar_config(bus.id, ruta.id, bus.placa)

        # Guía 8 — Act #2: Exportar historial en memoria a CSV antes de cerrar
        historial_actual = obtener_historial_memoria()
        exportar_historial_csv(historial_actual)

        # Guía 4 — Act #2: Output de confirmación de persistencia al cerrar
        print(f"[SISTEMA] Estado guardado — {len(historial_actual)} eventos exportados")

    finally:
        db.close()

    # Guía 3 — Act #2: Operador and — solo detiene detector si fue iniciado
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
# GUÍA 7 — Act #3: SUBALGORITMOS ORQUESTADORES (funciones auxiliares de main)
# ─────────────────────────────────────────────────────────────────────────────

def diagnostico_sistema(db: Session) -> dict:
    """
    Guía 7 — Act #3: Subalgoritmo que consolida el estado completo del sistema.
    ANTES → lógica dispersa en 3 endpoints distintos.
    AHORA → un solo subalgoritmo reutilizable por cualquier endpoint.
    Guía 5 — Act #2: Retorna diccionario anidado con todos los datos del sistema.
    Guía 9 — Act #3: Incluye estadísticas del vector de objetos EventoConteo.
    """
    # Guía 7 — Act #1: Delegar a subalgoritmos especializados
    datos   = obtener_conteo_actual(db)
    eventos = obtener_historial_memoria()

    # Guía 7 — Act #2: Lambdas aplicadas sobre el historial
    subidas = solo_subidas(eventos)
    bajadas = solo_bajadas(eventos)

    # Guía 5 — Act #2: Añadir métricas calculadas al dict de respuesta
    datos["total_eventos_memoria"] = len(eventos)
    datos["subidas_en_memoria"]    = len(subidas)
    datos["bajadas_en_memoria"]    = len(bajadas)

    # Guía 7 — Act #2: Lambda confianza_promedio sobre historial
    if eventos:
        datos["confianza_promedio"] = confianza_promedio(eventos)

    # Guía 9 — Act #3: Estadísticas del vector de objetos POO
    objetos = obtener_historial_objetos()
    datos["eventos_poo_en_memoria"] = len(objetos)

    return datos


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS DEL MICROSERVICIO
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
def raiz():
    """
    Guía 5 — Act #2: Retorna dict clave:valor con estado básico del servicio.
    Guía 4 — Act #2: Respuesta JSON formateada — equivalente al print() del API.
    """
    return {
        "status":  "ok",
        "mensaje": "Bus Passenger Counter corriendo 🚌",
        "version": "2.0.0",
    }


@app.get("/conteo")
def conteo_actual(db: Session = Depends(get_db)):
    """
    Guía 5 — Act #2: Endpoint que retorna estado como diccionario clave:valor.
    Guía 7 — Act #3: Delega a diagnostico_sistema() — subalgoritmo consolidador.
    Guía 9 — Act #1: Si detector existe, incluye estado del objeto DetectorPersonas.
    """
    # Guía 7 — Act #3: Un solo subalgoritmo en lugar de lógica dispersa
    datos = diagnostico_sistema(db)

    # Guía 3 — Act #1: if/else para incluir estado del detector solo si está activo
    if detector:
        # Guía 9 — Act #2: estado() es un método del objeto DetectorPersonas
        datos["detector"] = detector.estado()
    else:
        datos["detector"] = {"corriendo": False, "mensaje": "Detector no iniciado"}

    return datos


@app.get("/historial")
def historial(
    limit: int = Query(default=50, ge=1, le=500, description="Número de registros a retornar"),
    orden: str = Query(default="desc", description="Orden: 'asc' o 'desc'"),
    db: Session = Depends(get_db)
):
    """
    Guía 6 — Act #1: Retorna vector de los últimos N conteos del viaje activo.
    Guía 4 — Act #1: 'limit' y 'orden' son parámetros de entrada con validación.
    Guía 7 — Act #2: Aplica lambda ordenar_reciente si orden='desc'.
    Guía 3 — Act #1: if/elif para aplicar ordenamiento según parámetro.
    """
    # Guía 6 — Act #1: Obtener vector de conteos desde BD
    conteos = obtener_historial(db, limit=limit)

    # Guía 3 — Act #1: if/elif para aplicar ordenamiento según parámetro de entrada
    if orden == "desc":
        # Guía 7 — Act #2: Lambda ordenar_reciente sobre el vector de conteos
        return ordenar_reciente(conteos)
    elif orden == "asc":
        return list(reversed(conteos))
    else:
        return conteos


@app.get("/historial/memoria")
def historial_en_memoria():
    """
    Guía 6 — Act #1: Retorna el vector en memoria de eventos recientes (sin BD).
    Guía 5 — Act #2: Cada elemento del vector es un diccionario de evento.
    Guía 7 — Act #2: Aplica lambda formato_reporte para preview en consola.
    """
    from counter_service import formato_reporte
    eventos = obtener_historial_memoria()

    # Guía 7 — Act #2: Lambda formato_reporte aplicada al vector de eventos
    if eventos:
        print("[PREVIEW] Últimos eventos en memoria:")
        for linea in formato_reporte(eventos[-5:]):  # Solo los últimos 5
            print(f"  {linea}")

    # Guía 5 — Act #2: Respuesta como diccionario con el vector embebido
    return {
        "total_eventos": len(eventos),
        "eventos":       eventos,
    }


@app.get("/historial/objetos")
def historial_poo():
    """
    Guía 9 — Act #3: Endpoint que expone el vector de objetos EventoConteo.
    Guía 9 — Act #2: Llama a to_dict() de cada objeto para serialización API.
    Guía 6 — Act #1: Retorna vector de dicts construidos desde objetos POO.
    Guía 7 — Act #2: Lambdas filtrar_subidas_obj/filtrar_bajadas_obj sobre vector POO.
    """
    from counter_service import filtrar_subidas_obj, filtrar_bajadas_obj

    objetos = obtener_historial_objetos()  # Guía 6: vector de objetos EventoConteo

    # Guía 9 — Act #2: to_dict() convierte objeto a dict para JSON
    # Guía 5 — Act #1: List comprehension (for implícito) sobre vector de objetos
    eventos_dict = [obj.to_dict() for obj in objetos]

    # Guía 7 — Act #2: Lambdas sobre vector de objetos (Integración Guía 7 + Guía 9)
    subidas_obj = filtrar_subidas_obj(objetos)
    bajadas_obj = filtrar_bajadas_obj(objetos)

    # Guía 5 — Act #2: Diccionario de respuesta con metadata y datos
    return {
        "total_objetos":   len(objetos),
        "total_subidas":   len(subidas_obj),   # Guía 7: resultado de lambda
        "total_bajadas":   len(bajadas_obj),   # Guía 7: resultado de lambda
        "eventos":         eventos_dict,        # Guía 9: objetos serializados a dict
    }


@app.get("/reporte/horario")
def reporte_horario(db: Session = Depends(get_db)):
    """
    Guía 6 — Act #2: Genera y retorna la matriz horaria de pasajeros [24×3].
    Guía 7 — Act #1: filtrar_horas_activas() extrae solo filas con actividad.
    Guía 7 — Act #2: Lambda horas_pico identifica las horas de mayor demanda.
    Guía 8 — Act #2: exportar_matriz_csv() persiste la matriz en archivo CSV.
    """
    # Guía 6 — Act #2: Generar matriz [24][3]
    matriz = generar_matriz_horaria(db)

    # Guía 4 — Act #2: Imprimir reporte en consola con f-strings alineados
    imprimir_reporte_horario(matriz)

    # Guía 7 — Act #1: Subalgoritmo filtrar_horas_activas sobre la matriz
    horas_activas = filtrar_horas_activas(matriz)

    # Guía 7 — Act #2: Lambda horas_pico — top 3 horas con más subidas
    top_pico = horas_pico(matriz)[:3]   # Primeros 3 de la lista ordenada

    # Guía 8 — Act #2: Exportar la matriz a CSV al generar el reporte
    try:
        from persistence import exportar_matriz_csv
        exportar_matriz_csv(matriz)
    except Exception as e:
        print(f"[ADVERTENCIA] No se pudo exportar matriz a CSV: {e}")

    # Guía 5 — Act #2: Respuesta como diccionario con metadata y datos de la matriz
    return {
        "dimension":       "24 horas × 3 métricas [subidas, bajadas, neto]",
        "horas_con_datos": len(horas_activas),
        "top_3_horas_pico": [
            {"hora": f"{hora:02d}:00", "subidas": fila[0]}
            for hora, fila in top_pico                       # Guía 7: resultado de lambda
        ],
        "reporte": horas_activas,  # Guía 7: resultado del subalgoritmo filtrar_horas_activas
    }


@app.get("/log/reciente")
def log_reciente(
    lineas: int = Query(default=20, ge=1, le=200, description="Número de líneas del log")
):
    """
    Guía 8 — Act #1: Endpoint que lee las últimas N líneas del log de archivo.
    Guía 6 — Act #1: Retorna vector (lista) de strings con las líneas del log.
    Guía 4 — Act #1: 'lineas' es parámetro de entrada con validación de rango.
    """
    from persistence import leer_log_reciente

    # Guía 8 — Act #1: leer_log_reciente() lee el archivo data/eventos.log
    lineas_log = leer_log_reciente(lineas)  # Guía 6: retorna vector de strings

    # Guía 5 — Act #2: Respuesta como diccionario con vector embebido
    return {
        "archivo":       "data/eventos.log",
        "total_lineas":  len(lineas_log),
        "log":           lineas_log,          # Guía 6: vector de strings
    }


@app.post("/conteo/reset")
def reset_detector():
    """
    Guía 3 — Act #1: Regla de negocio — solo reinicia si el detector existe.
    Guía 9 — Act #2: Accede a atributos del objeto detector directamente.
    Guía 6 — Act #1: Limpia el vector historial_frames del objeto detector.
    """
    # Guía 3 — Act #1: Validación de existencia del detector
    if not detector:
        raise HTTPException(status_code=503, detail="Detector no iniciado")

    # Guía 9 — Act #2: Modificación de atributos públicos del objeto DetectorPersonas
    detector.personas_prev    = 0
    detector.personas_actual  = 0
    detector.historial_frames = []  # Guía 6: limpiar vector de historial del objeto

    print("[RESET] Detector y vector de historial reiniciados")

    # Guía 5 — Act #2: Diccionario de respuesta con estado post-reset
    return {
        "status":  "ok",
        "mensaje": "Detector y vector de historial reiniciados",
    }


@app.get("/health")
def health():
    """
    Guía 5 — Act #2: Retorna diccionario anidado con estado del sistema.
    Guía 3 — Act #1: if/elif/else para determinar nivel de salud del sistema.
    Guía 9 — Act #2: detector.estado() invoca método del objeto DetectorPersonas.
    """
    # Guía 3 — Act #1: if/elif/else para los 3 estados posibles del sistema
    if detector and detector.corriendo:
        estado_detector = detector.estado()  # Guía 9: método del objeto
        estado_sistema  = "healthy"
    elif detector and not detector.corriendo:
        estado_detector = {"corriendo": False}
        estado_sistema  = "degraded"
    else:
        estado_detector = "no iniciado"
        estado_sistema  = "unhealthy"

    # Guía 5 — Act #2: Diccionario de respuesta con anidamiento
    return {
        "status":   estado_sistema,
        "detector": estado_detector,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GUÍA 7 — Act #3: FUNCIÓN ORQUESTADORA run()
# Todo el flujo de inicio en un subalgoritmo — if __name__ reducido a una línea
# ─────────────────────────────────────────────────────────────────────────────

def run() -> None:
    """
    Guía 7 — Act #3: Orquestador principal — concentra la lógica de arranque.
    ANTES → código suelto en el cuerpo del módulo.
    AHORA → todo dentro de run(); if __name__ solo la llama.
    Guía 4 — Act #1: Captura HOST y PORT desde entorno como parámetros de entrada.
    """
    import uvicorn

    # Guía 4 — Act #1: Variables de configuración leídas desde entorno (input del sistema)
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # Guía 4 — Act #2: f-string de confirmación de arranque
    print(f"[SERVER] Iniciando en http://{HOST}:{PORT}")

    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)


# Guía 7 — Act #3: Punto de entrada reducido a una sola llamada funcional
if __name__ == "__main__":
    run()   # Una sola línea — toda la lógica está en subalgoritmos