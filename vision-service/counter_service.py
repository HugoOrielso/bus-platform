"""
counter_service.py — Escribe en las tablas de Prisma (viajes + conteos)
Si no existe bus o ruta, los crea automaticamente.

Guías implementadas:
  - Guía 3: Estructuras de Control Lógico y Reglas de Negocio (if/elif/else, operadores lógicos)
  - Guía 4: Algoritmos de Interacción e Input/Output (formateo de salida con f-strings)
  - Guía 5: Estructuras Iterativas y Diccionarios (diccionarios clave:valor, listas de dicts)
  - Guía 6: Arrays y Matrices (retorno de listas estructuradas como vectores)
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from database import Conteo, Viaje, Bus, Ruta
from dotenv import load_dotenv
import os

load_dotenv()

# ── Variables de entorno para identificar bus y ruta configurados ──────────────
BUS_ID  = os.getenv("BUS_ID")
RUTA_ID = os.getenv("RUTA_ID")

# ── Guía 6 (Vectores): Historial en memoria de los últimos eventos del viaje ──
# Se trata como un vector de tamaño máximo fijo (MAX_HISTORIAL_MEMORIA)
MAX_HISTORIAL_MEMORIA = 100
historial_memoria = []  # Vector unidimensional de eventos en RAM


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN: GESTIÓN DE RUTA
# ─────────────────────────────────────────────────────────────────────────────

def obtener_o_crear_ruta(db: Session) -> Ruta:
    """
    Guía 3 — Act #1: Reglas de Negocio con if/elif/else
    Jerarquía de búsqueda de ruta:
      1. Si existe RUTA_ID en .env → buscar esa ruta específica
      2. Si hay alguna ruta activa → usarla
      3. Si no existe ninguna → crearla con datos por defecto
    Nunca retorna None; garantiza que el motor de decisiones siempre tenga ruta.
    """

    # Guía 3 — Act #1: Primer condicional — buscar ruta por ID de entorno
    if RUTA_ID:
        ruta = db.query(Ruta).filter_by(id=RUTA_ID).first()
        # Guía 3 — Act #2: Operador lógico implícito — solo retorna si existe
        if ruta:
            return ruta

    # Guía 3 — Act #1: Segunda condición — buscar cualquier ruta activa (fallback)
    ruta = db.query(Ruta).filter_by(activa=True).first()
    if ruta:
        return ruta

    # Guía 3 — Act #1: Bloque else implícito — crear ruta por defecto si no existe ninguna
    ruta = Ruta(
        id      = str(uuid.uuid4()),
        nombre  = "Ruta Principal",
        origen  = "Terminal Central",
        destino = "Terminal Norte",
        activa  = True,
    )
    db.add(ruta)
    db.commit()
    db.refresh(ruta)

    # Guía 4 — Act #2: Salida formateada con f-string para trazabilidad en consola
    print(f"[RUTA CREADA] Nombre: {ruta.nombre:<20} | ID: {ruta.id}")
    return ruta


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN: GESTIÓN DE BUS
# ─────────────────────────────────────────────────────────────────────────────

def obtener_o_crear_bus(db: Session, ruta: Ruta) -> Bus:
    """
    Guía 3 — Act #1: Reglas de Negocio con if/elif/else
    Jerarquía de búsqueda de bus:
      1. Si existe BUS_ID en .env → buscar ese bus específico
      2. Si hay algún bus activo → usarlo
      3. Si no existe ninguno → crearlo con datos por defecto
    """

    # Guía 3 — Act #1: Primer condicional — buscar bus por ID de entorno
    if BUS_ID:
        bus = db.query(Bus).filter_by(id=BUS_ID).first()
        if bus:
            return bus

    # Guía 3 — Act #1: Segunda condición — buscar cualquier bus activo (fallback)
    bus = db.query(Bus).filter_by(activo=True).first()
    if bus:
        return bus

    # Guía 3 — Act #1: Bloque else implícito — crear bus por defecto si no existe ninguno
    now = datetime.now()
    bus = Bus(
        id        = str(uuid.uuid4()),
        placa     = os.getenv("BUS_PLACA", "BUS-001"),
        nombre    = "Bus Camera Principal",
        capacidad = 40,
        activo    = True,
        rutaId    = ruta.id,
        createdAt = now,
        updatedAt = now,
    )
    db.add(bus)
    db.commit()
    db.refresh(bus)

    # Guía 4 — Act #2: Salida formateada con f-string — instrucciones para el operador
    print(f"[BUS CREADO] Placa: {bus.placa:<12} | ID: {bus.id}")
    print(f"  >> Agrega a tu .env → BUS_ID={bus.id}")
    return bus


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN: GESTIÓN DE VIAJE
# ─────────────────────────────────────────────────────────────────────────────

def obtener_viaje_activo(db: Session, bus_id: str) -> Viaje | None:
    """
    Guía 3 — Act #2: Operadores de Control — filtra por estado 'EN_CURSO'
    Retorna el viaje más reciente en curso para el bus dado, o None si no existe.
    """
    return (
        db.query(Viaje)
        .filter_by(busId=bus_id, estado="EN_CURSO")
        .order_by(Viaje.fechaInicio.desc())
        .first()
    )


def iniciar_viaje(db: Session, bus: Bus, ruta: Ruta) -> Viaje:
    """
    Guía 3 — Act #1: Creación controlada de un nuevo viaje con estado inicial 'EN_CURSO'.
    Se invoca solo cuando no existe un viaje activo (regla de negocio).
    """
    viaje = Viaje(
        id     = str(uuid.uuid4()),
        busId  = bus.id,
        rutaId = ruta.id,
        estado = "EN_CURSO",
    )
    db.add(viaje)
    db.commit()
    db.refresh(viaje)

    # Guía 4 — Act #2: f-string con formato de ID truncado para legibilidad en log
    print(f"[VIAJE INICIADO] ID: {viaje.id[:8]}... | Bus: {bus.placa}")
    return viaje


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN: REGISTRO DE EVENTOS (núcleo del sistema)
# ─────────────────────────────────────────────────────────────────────────────

def registrar_evento(db: Session, evento: str, personas_actual: int, confianza: float = None):
    """
    Guía 3 — Act #1 y #2: Motor de decisiones principal
    Traduce el evento de cámara ('subio'/'bajo') a reglas de negocio:
      - Determina el tipo de conteo (SUBIDA/BAJADA)
      - Inicia viaje si no hay uno activo
      - Actualiza contadores del viaje

    Guía 5 — Act #1: El historial en memoria usa append() como operación iterativa
    Guía 6 — Act #1: historial_memoria actúa como vector con tamaño máximo controlado
    """
    ruta  = obtener_o_crear_ruta(db)
    bus   = obtener_o_crear_bus(db, ruta)
    viaje = obtener_viaje_activo(db, bus.id)

    # Guía 3 — Act #1: Regla de negocio — si no hay viaje activo, se crea uno automáticamente
    if not viaje:
        viaje = iniciar_viaje(db, bus, ruta)

    # Guía 3 — Act #1: if/else para mapear evento de texto a tipo de conteo normalizado
    if evento == "subio":
        tipo = "SUBIDA"
    else:
        tipo = "BAJADA"

    # ── Registro del conteo en base de datos ──────────────────────────────────
    conteo = Conteo(
        id        = str(uuid.uuid4()),
        viajeId   = viaje.id,
        tipo      = tipo,
        fuente    = "CAMARA",
        confianza = confianza,
    )
    db.add(conteo)

    # Guía 3 — Act #1: Estructura if/else para actualizar el contador correcto del viaje
    if tipo == "SUBIDA":
        viaje.totalSubidas += 1
    else:
        viaje.totalBajadas += 1

    viaje.pasajerosActual = personas_actual
    db.commit()

    # ── Guía 5 — Act #2: Construir diccionario del evento para historial en memoria ──
    # Diccionario clave:valor que representa un evento de conteo como objeto de negocio
    evento_dict = {
        "tipo":             tipo,
        "personas_actual":  personas_actual,
        "confianza":        confianza,
        "viaje_id":         viaje.id[:8],
        "timestamp":        str(datetime.now()),
    }

    # Guía 6 — Act #1: Gestión del vector en memoria con control de tamaño máximo
    # Si el vector supera MAX_HISTORIAL_MEMORIA, se elimina el elemento más antiguo (FIFO)
    if len(historial_memoria) >= MAX_HISTORIAL_MEMORIA:
        historial_memoria.pop(0)   # Guía 6: operación sobre vector — eliminar cabeza
    historial_memoria.append(evento_dict)  # Guía 6: inserción en vector

    # Guía 4 — Act #2: Output formateado con f-string para log de consola estructurado
    print(f"  [{tipo:<7}] Personas: {personas_actual:>3} | Viaje: {viaje.id[:8]}... | Confianza: {confianza or 'N/A'}")


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN: CONSULTAS DE ESTADO
# ─────────────────────────────────────────────────────────────────────────────

def obtener_conteo_actual(db: Session) -> dict:
    """
    Guía 5 — Act #2: Retorna un diccionario clave:valor con el estado actual del viaje.
    Guía 3 — Act #1: if/else para diferenciar entre 'sin viaje' y 'viaje activo'.
    Guía 4 — Act #2: Las claves del diccionario siguen convención snake_case estándar.
    """
    ruta  = obtener_o_crear_ruta(db)
    bus   = obtener_o_crear_bus(db, ruta)
    viaje = obtener_viaje_activo(db, bus.id)

    # Guía 3 — Act #1: Regla de negocio — estado 'SIN_VIAJE' si no hay viaje activo
    if not viaje:
        # Guía 5 — Act #2: Diccionario clave:valor para estado sin viaje activo
        return {
            "bus_id":             bus.id,
            "placa":              bus.placa,
            "viaje_activo":       None,
            "pasajeros_actuales": 0,
            "total_subidas":      0,
            "total_bajadas":      0,
            "estado":             "SIN_VIAJE",
        }

    # Guía 5 — Act #2: Diccionario clave:valor con datos completos del viaje en curso
    return {
        "bus_id":             bus.id,
        "placa":              bus.placa,
        "viaje_id":           viaje.id,
        "pasajeros_actuales": viaje.pasajerosActual,
        "total_subidas":      viaje.totalSubidas,
        "total_bajadas":      viaje.totalBajadas,
        "estado":             viaje.estado,
        "fecha_inicio":       str(viaje.fechaInicio),
    }


def obtener_historial(db: Session, limit: int = 50) -> list:
    """
    Guía 6 — Act #1: Retorna un vector (lista unidimensional) de conteos.
    Cada elemento es un diccionario que representa un registro de la base de datos.
    Guía 3 — Act #1: if/else para retornar lista vacía si no hay viaje activo.
    Guía 5 — Act #1: List comprehension (for implícito) para transformar objetos ORM a dicts.
    """
    ruta  = obtener_o_crear_ruta(db)
    bus   = obtener_o_crear_bus(db, ruta)
    viaje = obtener_viaje_activo(db, bus.id)

    # Guía 3 — Act #1: Regla de negocio — vector vacío si no hay viaje activo
    if not viaje:
        return []

    conteos = (
        db.query(Conteo)
        .filter_by(viajeId=viaje.id)
        .order_by(Conteo.timestamp.desc())
        .limit(limit)
        .all()
    )

    # Guía 6 — Act #1: List comprehension — construye vector de diccionarios (array de objetos)
    # Guía 5 — Act #1: Iteración for sobre colección de registros ORM → transformación masiva
    return [
        {
            "id":        c.id,
            "tipo":      c.tipo,
            "fuente":    c.fuente,
            "confianza": c.confianza,
            "timestamp": str(c.timestamp),
        }
        for c in conteos  # Guía 5 — Act #1: ciclo for sobre colección de datos de BD
    ]


def obtener_historial_memoria() -> list:
    """
    Guía 6 — Act #1: Retorna el vector en memoria de los últimos eventos detectados.
    No requiere conexión a BD — útil para consultas rápidas de bajo costo.

    Guía 5 — Act #1: Itera sobre el vector historial_memoria con for para generar reporte.
    Guía 4 — Act #2: Salida con f-string alineada para presentación estructurada.
    """
    # Guía 6 — Act #1: Recorrido del vector unidimensional en memoria
    for i, evento in enumerate(historial_memoria):  # Guía 5 — Act #1: for con índice
        # Guía 4 — Act #2: f-string con alineación de columnas para dashboard de consola
        print(f"  [{i+1:>3}] {evento['tipo']:<7} | Personas: {evento['personas_actual']:>3} | {evento['timestamp']}")
    return list(historial_memoria)  # Guía 6: retorna copia del vector


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN: ESTADÍSTICAS — GUÍA 6 (Matrices)
# ─────────────────────────────────────────────────────────────────────────────

def generar_matriz_horaria(db: Session) -> list:
    """
    Guía 6 — Act #2: Modelado de Datos Multidimensionales (Matrices)
    Construye una matriz [hora][métrica] donde:
      - Filas    → 24 horas del día (índice 0–23)
      - Columnas → [subidas, bajadas, pasajeros_neto] (3 métricas)

    Acceso: matriz[hora][0] = subidas en esa hora
            matriz[hora][1] = bajadas en esa hora
            matriz[hora][2] = pasajeros_neto en esa hora

    Guía 3 — Act #1: if/elif/else para validar rango de hora antes de actualizar celda
    Guía 5 — Act #1: ciclos for anidados para inicializar y recorrer la matriz
    """

    # Guía 6 — Act #2: Inicialización de matriz rectangular 24x3 (todas las celdas en 0)
    # Garantía de simetría: todas las filas tienen exactamente 3 columnas (buena práctica)
    HORAS    = 24
    METRICAS = 3  # [subidas, bajadas, neto]

    # Guía 6 — Act #2: List comprehension para inicializar matriz 24×3 con ceros
    matriz_horaria = [[0] * METRICAS for _ in range(HORAS)]

    # Obtener viaje activo para consultar sus conteos
    ruta  = obtener_o_crear_ruta(db)
    bus   = obtener_o_crear_bus(db, ruta)
    viaje = obtener_viaje_activo(db, bus.id)

    # Guía 3 — Act #1: Regla de negocio — si no hay viaje, retornar matriz vacía inicializada
    if not viaje:
        return matriz_horaria

    conteos = db.query(Conteo).filter_by(viajeId=viaje.id).all()

    # Guía 5 — Act #1: Ciclo for para procesar cada conteo e insertar en la matriz
    for conteo in conteos:
        hora = conteo.timestamp.hour  # Extraer índice de fila (hora del día 0–23)

        # Guía 3 — Act #1: Validación de rango con if/elif/else antes de escribir en matriz
        if hora < 0 or hora >= HORAS:
            # Hora fuera de rango — ignorar para no desborda la matriz (Edge Case Guía 3)
            continue

        # Guía 6 — Act #2: Actualización dinámica mediante doble indexación matriz[fila][col]
        if conteo.tipo == "SUBIDA":
            matriz_horaria[hora][0] += 1   # Columna 0 → subidas
            matriz_horaria[hora][2] += 1   # Columna 2 → neto sube
        elif conteo.tipo == "BAJADA":
            matriz_horaria[hora][1] += 1   # Columna 1 → bajadas
            matriz_horaria[hora][2] -= 1   # Columna 2 → neto baja

    # Guía 6 — Act #3: Validación de integridad — verificar que la matriz sea rectangular
    # Todas las filas deben tener exactamente METRICAS columnas
    for i, fila in enumerate(matriz_horaria):  # Guía 5 — Act #1: for sobre filas de matriz
        if len(fila) != METRICAS:
            # Guía 3 — Act #2: Operador lógico en validación de integridad de estructura
            print(f"  [ADVERTENCIA] Fila {i} tiene {len(fila)} columnas (esperado {METRICAS})")

    return matriz_horaria


def imprimir_reporte_horario(matriz_horaria: list):
    """
    Guía 6 — Act #2 y #3: Recorrido de matriz con ciclos anidados para reporte global.
    Guía 4 — Act #2: Formateo avanzado de salida con f-strings alineados.
    Guía 5 — Act #1: for anidado — iterador i=fila (hora), j=columna (métrica).
    """

    # Guía 4 — Act #2: Encabezado de reporte con separadores visuales formateados
    print("\n" + "=" * 55)
    print(f"{'REPORTE HORARIO DE PASAJEROS':^55}")
    print("=" * 55)
    print(f"{'HORA':<6} {'SUBIDAS':>10} {'BAJADAS':>10} {'NETO':>10}")
    print("-" * 55)

    # Guía 6 — Act #2: Recorrido de matriz con doble índice [i][j]
    # Guía 5 — Act #1: Ciclo for sobre filas (horas) — iterador i
    for i, fila in enumerate(matriz_horaria):
        # Guía 3 — Act #1: Condicional para mostrar solo horas con actividad
        if fila[0] > 0 or fila[1] > 0:
            # Guía 4 — Act #2: f-string con alineación numérica de columnas
            print(f"  {i:02d}:00  {fila[0]:>10} {fila[1]:>10} {fila[2]:>+10}")

    print("=" * 55)