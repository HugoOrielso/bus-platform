"""
counter_service.py — Escribe en las tablas de Prisma (viajes + conteos)
Si no existe bus o ruta, los crea automaticamente.

Guías implementadas:
  - Guía 3: Estructuras de Control Lógico y Reglas de Negocio (if/elif/else)
  - Guía 4: Algoritmos de Interacción e Input/Output (f-strings, formateo)
  - Guía 5: Estructuras Iterativas y Diccionarios (dicts clave:valor, listas)
  - Guía 6: Arrays y Matrices (vectores en memoria, matriz horaria [24×3])
  - Guía 7: Subalgoritmos y Lambdas (funciones SRP, funciones lambda con filter/map/sorted)
  - Guía 8: Persistencia — escribir_log() integrado en registrar_evento
  - Guía 9: POO — historial_objetos usa EventoConteo; registrar_evento_poo() crea objetos
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from database import Conteo, Viaje, Bus, Ruta
from dotenv import load_dotenv
import os

load_dotenv()

# ── Guía 4 — Act #1: Captura dinámica de parámetros desde variables de entorno ──
BUS_ID  = os.getenv("BUS_ID")
RUTA_ID = os.getenv("RUTA_ID")

# ── Guía 6 — Act #1: Vector en memoria de los últimos eventos (buffer FIFO) ──
MAX_HISTORIAL_MEMORIA = 100
historial_memoria: list = []   # Vector de dicts (compatibilidad API — Guía 5)

# ── Guía 9 — Act #3: Vector de objetos EventoConteo (reemplaza lista de dicts) ──
# Sustituye historial_memoria cuando se usa la capa POO
from models import EventoConteo, ViajeActivo
historial_objetos: list = []   # Vector de objetos EventoConteo (Guía 9 + Guía 6)


# ─────────────────────────────────────────────────────────────────────────────
# GUÍA 7 — Act #2: FUNCIONES LAMBDA (Paradigma Funcional)
# Aplicadas con sorted(), filter() y map() sobre los vectores del proyecto
# ─────────────────────────────────────────────────────────────────────────────

# Guía 7 — Lambda 1: Ordenar historial por timestamp (más reciente primero)
# ANTES → def ordenar(e): return e['timestamp'] + sorted(hist, key=ordenar, ...)
# AHORA → lambda expresivo en una sola línea
ordenar_reciente = lambda eventos: sorted(
    eventos, key=lambda e: e["timestamp"], reverse=True
)

# Guía 7 — Lambda 2: Filtrar solo eventos de SUBIDA del historial
# ANTES → bucle for con if e['tipo'] == 'SUBIDA': result.append(e)
# AHORA → filter() con lambda
solo_subidas = lambda eventos: list(
    filter(lambda e: e["tipo"] == "SUBIDA", eventos)
)

# Guía 7 — Lambda 3: Filtrar solo eventos de BAJADA del historial
solo_bajadas = lambda eventos: list(
    filter(lambda e: e["tipo"] == "BAJADA", eventos)
)

# Guía 7 — Lambda 4: Calcular confianza promedio sobre el historial
# ANTES → loop for con acumulador manual
# AHORA → sum(map(...)) / len — encadenado funcional
confianza_promedio = lambda eventos: round(
    sum(map(lambda e: e["confianza"] or 0.0, eventos)) / max(len(eventos), 1), 3
)

# Guía 7 — Lambda 5: Ordenar matriz horaria por horas pico (más subidas primero)
# Recibe la matriz [24][3] y retorna lista de (hora, fila) ordenada por subidas desc
horas_pico = lambda matriz: sorted(
    enumerate(matriz), key=lambda item: item[1][0], reverse=True
)

# Guía 7 — Lambda 6: Mapear conteos a formato de reporte legible para consola
# Guía 4 — Act #2: f-string en lambda para output formateado
formato_reporte = lambda conteos: list(map(
    lambda c: f"[{c['tipo']:<7}] {c['timestamp'][:19]} │ Conf: {c['confianza'] or 'N/A'}",
    conteos
))

# ── Guía 9 — Act #3: Lambda sobre lista de objetos EventoConteo ──────────────
# Integración Guía 7 + Guía 9: lambda que trabaja con objetos en lugar de dicts
filtrar_subidas_obj = lambda lst: list(filter(
    lambda e: e.tipo == "SUBIDA", lst
))
filtrar_bajadas_obj = lambda lst: list(filter(
    lambda e: e.tipo == "BAJADA", lst
))


# ─────────────────────────────────────────────────────────────────────────────
# GUÍA 7 — Act #1 y Act #2: NUEVAS FUNCIONES EXTRAÍDAS (Subalgoritmos SRP)
# ─────────────────────────────────────────────────────────────────────────────

def calcular_ocupacion(pasajeros_actual: int, capacidad: int) -> float:
    """
    Guía 7 — Act #1: Subalgoritmo extraído — calcula % de ocupación del bus.
    Responsabilidad única: solo hace el cálculo del porcentaje.
    Guía 7 — Act #1: Paso por VALOR — int es inmutable; modificarlo aquí no afecta al caller.
    Guía 3 — Act #1: if/else para evitar división por cero (Edge Case).
    Guía 4 — Act #2: Retorna float redondeado a 2 decimales.
    """
    # Guía 3 — Act #1: Validación de precondición antes del cálculo
    if capacidad <= 0:
        return 0.0
    return round((pasajeros_actual / capacidad) * 100, 2)


def normalizar_evento(evento: str) -> str:
    """
    Guía 7 — Act #1: Subalgoritmo extraído — mapea evento de cámara a tipo normalizado.
    Responsabilidad única: solo hace conversión de cadenas.
    Guía 7 — Act #1: Paso por VALOR — str es inmutable en Python.
    Guía 5 — Act #3: Usa .strip() y .lower() para normalizar cadena antes del mapeo.
    Guía 3 — Act #1: if/else para mapeo exhaustivo (nunca retorna None).
    """
    # Guía 5 — Act #3: .strip().lower() para normalizar entrada antes de comparar
    return "SUBIDA" if evento.strip().lower() == "subio" else "BAJADA"


def filtrar_horas_activas(matriz: list) -> list:
    """
    Guía 7 — Act #1: Subalgoritmo extraído — filtra filas de la matriz con actividad.
    Guía 7 — Act #1: Paso por REFERENCIA — lista es mutable; se lee sin modificar.
    Guía 6 — Act #2: Itera sobre la matriz [24][3] accediendo por doble índice.
    Guía 5 — Act #1: List comprehension con filtro (for + if) sobre la matriz.
    Guía 3 — Act #1: Condición or para incluir horas con subidas O bajadas.
    """
    # Guía 5 — Act #1: List comprehension — for+if sobre filas de la matriz
    # Guía 6 — Act #2: Acceso por doble índice fila[0]=subidas, fila[1]=bajadas
    return [
        {
            "hora":    f"{i:02d}:00",   # Guía 4: f-string con formato HH:MM
            "subidas": fila[0],          # Guía 6: columna 0 de la matriz
            "bajadas": fila[1],          # Guía 6: columna 1 de la matriz
            "neto":    fila[2],          # Guía 6: columna 2 de la matriz
        }
        for i, fila in enumerate(matriz)          # Guía 5: for con índice
        if fila[0] > 0 or fila[1] > 0             # Guía 3: filtro lógico
    ]


def resumen_viaje(viaje) -> dict:
    """
    Guía 7 — Act #1: Subalgoritmo extraído — centraliza el formateo de métricas del viaje.
    Responsabilidad única: solo serializa el objeto Viaje a diccionario.
    Guía 5 — Act #2: Retorna diccionario clave:valor con métricas del viaje.
    Guía 4 — Act #2: ID truncado a 8 chars para legibilidad en logs.
    """
    # Guía 5 — Act #2: Diccionario de resumen del viaje
    return {
        "id":       viaje.id[:8],           # Guía 4: truncado para legibilidad
        "subidas":  viaje.totalSubidas,
        "bajadas":  viaje.totalBajadas,
        "actuales": viaje.pasajerosActual,
        "estado":   viaje.estado,
    }


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

    Guía 7 — Act #1: Subalgoritmo de responsabilidad única — solo gestiona ruta.
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
    Guía 7 — Act #1: Subalgoritmo SRP — solo gestiona bus.
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

    # Guía 3 — Act #1: Bloque else implícito — crear bus por defecto
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

    # Guía 4 — Act #2: Salida formateada con f-string
    print(f"[BUS CREADO] Placa: {bus.placa:<12} | ID: {bus.id}")
    print(f"  >> Agrega a tu .env → BUS_ID={bus.id}")
    return bus


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN: GESTIÓN DE VIAJE
# ─────────────────────────────────────────────────────────────────────────────

def obtener_viaje_activo(db: Session, bus_id: str) -> Viaje | None:
    """
    Guía 3 — Act #2: Operadores de Control — filtra por estado 'EN_CURSO'.
    Guía 7 — Act #1: Subalgoritmo SRP — solo consulta, no crea.
    """
    return (
        db.query(Viaje)
        .filter_by(busId=bus_id, estado="EN_CURSO")
        .order_by(Viaje.fechaInicio.desc())
        .first()
    )


def iniciar_viaje(db: Session, bus: Bus, ruta: Ruta) -> Viaje:
    """
    Guía 3 — Act #1: Creación controlada — separada de registrar_evento (SRP Guía 7).
    Guía 7 — Act #1: Subalgoritmo SRP — solo crea viaje, no registra conteos.
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

    # Guía 4 — Act #2: f-string con ID truncado para log legible
    print(f"[VIAJE INICIADO] ID: {viaje.id[:8]}... | Bus: {bus.placa}")
    return viaje


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN: REGISTRO DE EVENTOS — VERSIÓN DICT (Compatibilidad Guías 3-6)
# ─────────────────────────────────────────────────────────────────────────────

def registrar_evento(db: Session, evento: str, personas_actual: int, confianza: float = None):
    """
    Guía 3 — Act #1 y #2: Motor de decisiones principal.
    Guía 7 — Act #1: Orquestador — delega a subalgoritmos especializados.
    Guía 8 — Act #1: Integración de persistencia — llama a escribir_log() en cada evento.
    Guía 5 — Act #2: Construye dict del evento para historial en memoria.
    Guía 6 — Act #1: Gestiona vector historial_memoria con control de tamaño (FIFO).
    """
    ruta  = obtener_o_crear_ruta(db)
    bus   = obtener_o_crear_bus(db, ruta)
    viaje = obtener_viaje_activo(db, bus.id)

    # Guía 3 — Act #1: Regla de negocio — si no hay viaje activo, crear uno
    if not viaje:
        viaje = iniciar_viaje(db, bus, ruta)

    # Guía 7 — Act #1: Delegar normalización al subalgoritmo especializado
    tipo = normalizar_evento(evento)  # Guía 7: llamada a función de responsabilidad única

    # ── Registro en base de datos ──────────────────────────────────────────────
    conteo = Conteo(
        id        = str(uuid.uuid4()),
        viajeId   = viaje.id,
        tipo      = tipo,
        fuente    = "CAMARA",
        confianza = confianza,
    )
    db.add(conteo)

    # Guía 3 — Act #1: if/else para actualizar el contador correcto del viaje
    if tipo == "SUBIDA":
        viaje.totalSubidas += 1
    else:
        viaje.totalBajadas += 1

    viaje.pasajerosActual = personas_actual
    db.commit()

    # ── Guía 8 — Act #1: Persistencia en archivo de log (modo append) ─────────
    # Integración Guía 8: cada evento también se escribe en data/eventos.log
    try:
        from persistence import escribir_log
        escribir_log(tipo, personas_actual, confianza)
    except Exception as e:
        # Guía 3 — Act #2: Operador not — si falla el log, el sistema no se detiene
        print(f"[ADVERTENCIA] No se pudo escribir log: {e}")

    # ── Guía 5 — Act #2: Construir dict del evento para historial en memoria ──
    evento_dict = {
        "tipo":            tipo,
        "personas_actual": personas_actual,
        "confianza":       confianza,
        "viaje_id":        viaje.id[:8],
        "timestamp":       str(datetime.now()),
    }

    # Guía 6 — Act #1: Gestión del vector en memoria con control de tamaño (FIFO)
    if len(historial_memoria) >= MAX_HISTORIAL_MEMORIA:
        historial_memoria.pop(0)   # Elimina el elemento más antiguo del vector
    historial_memoria.append(evento_dict)

    # Guía 4 — Act #2: Output formateado con f-string alineado para log de consola
    print(f"  [{tipo:<7}] Personas: {personas_actual:>3} | Viaje: {viaje.id[:8]}... | Confianza: {confianza or 'N/A'}")


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN: REGISTRO DE EVENTOS — VERSIÓN POO (Guía 9)
# ─────────────────────────────────────────────────────────────────────────────

def registrar_evento_poo(evento: str, personas: int, confianza: float = None) -> None:
    """
    Guía 9 — Act #3: Versión POO de registrar_evento — usa objetos EventoConteo.
    Guía 7 — Act #1: Subalgoritmo nuevo — responsabilidad única sobre objetos.
    Guía 6 — Act #1: historial_objetos es un vector de objetos (no dicts).
    Guía 9 — Act #2: Llama a __str__ del objeto para output profesional.
    Guía 8 — Act #1: También persiste el evento en log de archivo.
    """
    # Guía 7 — Act #1: Delegar normalización al subalgoritmo especializado
    tipo = normalizar_evento(evento)

    # Guía 9 — Act #1: Instanciar objeto EventoConteo (en lugar de crear un dict)
    nuevo_evento = EventoConteo(tipo, personas, confianza)

    # Guía 6 — Act #1: Control de tamaño del vector de objetos (FIFO)
    if len(historial_objetos) >= MAX_HISTORIAL_MEMORIA:
        historial_objetos.pop(0)
    historial_objetos.append(nuevo_evento)  # Guía 6: inserción de objeto en vector

    # ── Guía 8 — Act #1: Persistencia en log de archivo ───────────────────────
    try:
        from persistence import escribir_log
        escribir_log(tipo, personas, confianza)
    except Exception as e:
        print(f"[ADVERTENCIA] No se pudo escribir log POO: {e}")

    # Guía 9 — Act #2: print() invoca __str__ del objeto — output profesional
    # Guía 4 — Act #2: La representación del objeto ya tiene f-string formateado
    print(nuevo_evento)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN: CONSULTAS DE ESTADO
# ─────────────────────────────────────────────────────────────────────────────

def obtener_conteo_actual(db: Session) -> dict:
    """
    Guía 5 — Act #2: Retorna diccionario clave:valor con estado actual del viaje.
    Guía 3 — Act #1: if/else para diferenciar 'sin viaje' vs 'viaje activo'.
    Guía 7 — Act #1: Subalgoritmo SRP — solo consulta estado, no modifica.
    """
    ruta  = obtener_o_crear_ruta(db)
    bus   = obtener_o_crear_bus(db, ruta)
    viaje = obtener_viaje_activo(db, bus.id)

    # Guía 3 — Act #1: Regla de negocio — estado 'SIN_VIAJE' si no hay viaje activo
    if not viaje:
        # Guía 5 — Act #2: Diccionario clave:valor para estado sin viaje
        return {
            "bus_id":             bus.id,
            "placa":              bus.placa,
            "viaje_activo":       None,
            "pasajeros_actuales": 0,
            "total_subidas":      0,
            "total_bajadas":      0,
            "estado":             "SIN_VIAJE",
            # Guía 7 — Act #1: ocupacion calculada con subalgoritmo especializado
            "ocupacion_pct":      calcular_ocupacion(0, 40),
        }

    # Guía 5 — Act #2: Diccionario completo con métricas del viaje en curso
    return {
        "bus_id":             bus.id,
        "placa":              bus.placa,
        "viaje_id":           viaje.id,
        "pasajeros_actuales": viaje.pasajerosActual,
        "total_subidas":      viaje.totalSubidas,
        "total_bajadas":      viaje.totalBajadas,
        "estado":             viaje.estado,
        "fecha_inicio":       str(viaje.fechaInicio),
        # Guía 7 — Act #1: Delegar cálculo de ocupación al subalgoritmo
        "ocupacion_pct":      calcular_ocupacion(viaje.pasajerosActual, 40),
    }


def obtener_historial(db: Session, limit: int = 50) -> list:
    """
    Guía 6 — Act #1: Retorna vector (lista) de los últimos N conteos desde BD.
    Guía 5 — Act #1: List comprehension para transformar ORM a lista de dicts.
    Guía 3 — Act #1: if/else — vector vacío si no hay viaje activo.
    Guía 7 — Act #1: Subalgoritmo SRP — solo consulta historial de BD.
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

    # Guía 6 — Act #1: List comprehension — construye vector de dicts desde ORM
    # Guía 5 — Act #1: for sobre colección de registros → transformación masiva
    return [
        {
            "id":        c.id,
            "tipo":      c.tipo,
            "fuente":    c.fuente,
            "confianza": c.confianza,
            "timestamp": str(c.timestamp),
        }
        for c in conteos
    ]


def obtener_historial_memoria() -> list:
    """
    Guía 6 — Act #1: Retorna el vector en memoria de eventos recientes.
    Guía 7 — Act #1: Subalgoritmo SRP — solo retorna el vector, no lo modifica.
    Sin acceso a BD — útil para consultas rápidas de bajo costo.
    """
    return list(historial_memoria)  # Guía 6: copia del vector para no exponer el original


def obtener_historial_objetos() -> list:
    """
    Guía 9 — Act #3: Retorna el vector de objetos EventoConteo.
    Guía 7 — Act #1: Subalgoritmo SRP — solo expone el vector POO.
    Guía 6 — Act #1: Retorna lista de objetos (no dicts).
    """
    return list(historial_objetos)  # Guía 6: copia del vector de objetos


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN: ESTADÍSTICAS — GUÍA 6 (Matrices) + GUÍA 7 (Subalgoritmos)
# ─────────────────────────────────────────────────────────────────────────────

def generar_matriz_horaria(db: Session) -> list:
    """
    Guía 6 — Act #2: Construye matriz [24][3] de pasajeros por hora.
    Guía 7 — Act #1: Subalgoritmo SRP — solo genera la matriz, no la imprime.
    Guía 5 — Act #1: for sobre colección de conteos para poblar la matriz.
    Guía 3 — Act #1: Validaciones de rango y estado antes de escribir en celdas.
    """
    HORAS    = 24
    METRICAS = 3  # [subidas, bajadas, neto]

    # Guía 6 — Act #2: Inicialización de matriz rectangular 24×3 con ceros
    matriz_horaria = [[0] * METRICAS for _ in range(HORAS)]

    ruta  = obtener_o_crear_ruta(db)
    bus   = obtener_o_crear_bus(db, ruta)
    viaje = obtener_viaje_activo(db, bus.id)

    # Guía 3 — Act #1: Si no hay viaje, retornar matriz inicializada en ceros
    if not viaje:
        return matriz_horaria

    conteos = db.query(Conteo).filter_by(viajeId=viaje.id).all()

    # Guía 5 — Act #1: for sobre la colección de conteos para poblar la matriz
    for conteo in conteos:
        hora = conteo.timestamp.hour

        # Guía 3 — Act #1: Validación de rango — Edge Case de hora fuera de bounds
        if hora < 0 or hora >= HORAS:
            continue  # Guía 5 — Act #1C: continue para saltar datos inválidos

        # Guía 6 — Act #2: Actualización por doble índice matriz[fila][columna]
        if conteo.tipo == "SUBIDA":
            matriz_horaria[hora][0] += 1   # columna 0 → subidas
            matriz_horaria[hora][2] += 1   # columna 2 → neto
        elif conteo.tipo == "BAJADA":
            matriz_horaria[hora][1] += 1   # columna 1 → bajadas
            matriz_horaria[hora][2] -= 1   # columna 2 → neto

    return matriz_horaria


def imprimir_reporte_horario(matriz_horaria: list):
    """
    Guía 6 — Act #2: Recorrido de matriz con ciclos for para reporte.
    Guía 4 — Act #2: Formateo avanzado de salida con f-strings alineados.
    Guía 7 — Act #1: Subalgoritmo SRP — solo imprime, no genera ni modifica.
    """
    print("\n" + "=" * 55)
    print(f"{'REPORTE HORARIO DE PASAJEROS':^55}")
    print("=" * 55)
    print(f"{'HORA':<6} {'SUBIDAS':>10} {'BAJADAS':>10} {'NETO':>10}")
    print("-" * 55)

    # Guía 6 — Act #2: for con índice sobre filas de la matriz [hora][metrica]
    for i, fila in enumerate(matriz_horaria):
        # Guía 3 — Act #1: Solo mostrar horas con actividad
        if fila[0] > 0 or fila[1] > 0:
            print(f"  {i:02d}:00  {fila[0]:>10} {fila[1]:>10} {fila[2]:>+10}")

    print("=" * 55)