"""
counter_service.py — Escribe en las tablas de Prisma (viajes + conteos)
Si no existe bus o ruta, los crea automaticamente.
"""
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from database import Conteo, Viaje, Bus, Ruta
from dotenv import load_dotenv
import os

load_dotenv()

BUS_ID  = os.getenv("BUS_ID")
RUTA_ID = os.getenv("RUTA_ID")


def obtener_o_crear_ruta(db: Session) -> Ruta:
    #guía 3
    if RUTA_ID:
        ruta = db.query(Ruta).filter_by(id=RUTA_ID).first()
        if ruta:
            return ruta

    #guía 1
    ruta = db.query(Ruta).filter_by(activa=True).first()
    if ruta:
        return ruta

    #guía 1
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
    print(f"Ruta creada: {ruta.nombre} | id: {ruta.id}")
    return ruta


def obtener_o_crear_bus(db: Session, ruta: Ruta) -> Bus:
    #guía 3
    if BUS_ID:
        bus = db.query(Bus).filter_by(id=BUS_ID).first()
        if bus:
            return bus

    bus = db.query(Bus).filter_by(activo=True).first()
    #guía 3
    if bus:
        return bus
    # guía 1
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
    print(f"Bus creado: {bus.placa} | id: {bus.id}")
    print(f"  Agrega a tu .env -> BUS_ID={bus.id}")
    return bus


def obtener_viaje_activo(db: Session, bus_id: str) -> Viaje | None:
    return (
        db.query(Viaje)
        .filter_by(busId=bus_id, estado="EN_CURSO")
        .order_by(Viaje.fechaInicio.desc())
        .first()
    )


def iniciar_viaje(db: Session, bus: Bus, ruta: Ruta) -> Viaje:
    viaje = Viaje(
        id     = str(uuid.uuid4()),
        busId  = bus.id,
        rutaId = ruta.id,
        estado = "EN_CURSO",
    )
    db.add(viaje)
    db.commit()
    db.refresh(viaje)
    print(f"Viaje iniciado: {viaje.id[:8]}... | Bus: {bus.placa}")
    return viaje


def registrar_evento(db: Session, evento: str, personas_actual: int, confianza: float = None):
    ruta  = obtener_o_crear_ruta(db)
    bus   = obtener_o_crear_bus(db, ruta)
    viaje = obtener_viaje_activo(db, bus.id)

    if not viaje:  ##Guía 3
        viaje = iniciar_viaje(db, bus, ruta)

    tipo = "SUBIDA" if evento == "subio" else "BAJADA"

    conteo = Conteo(
        id        = str(uuid.uuid4()),
        viajeId   = viaje.id,
        tipo      = tipo,
        fuente    = "CAMARA",
        confianza = confianza,
    )
    db.add(conteo)

    #guía 3
    if tipo == "SUBIDA":
        viaje.totalSubidas += 1
    else:
        viaje.totalBajadas += 1

    viaje.pasajerosActual = personas_actual
    db.commit()
    print(f"  [{tipo}] Personas: {personas_actual} | Viaje: {viaje.id[:8]}...")


def obtener_conteo_actual(db: Session) -> dict:
    ruta  = obtener_o_crear_ruta(db)
    bus   = obtener_o_crear_bus(db, ruta)
    viaje = obtener_viaje_activo(db, bus.id)

    # uso de diccionario guía 5 y guía 3
    if not viaje:
        return {
            "bus_id":             bus.id,
            "placa":              bus.placa,
            "viaje_activo":       None,
            "pasajeros_actuales": 0,
            "total_subidas":      0,
            "total_bajadas":      0,
            "estado":             "SIN_VIAJE",
        }
    # uso de diccionario guia 5
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
    ruta  = obtener_o_crear_ruta(db)
    bus   = obtener_o_crear_bus(db, ruta)
    viaje = obtener_viaje_activo(db, bus.id)

    #guía 3
    if not viaje:
        return []

    conteos = (
        db.query(Conteo)
        .filter_by(viajeId=viaje.id)
        .order_by(Conteo.timestamp.desc())
        .limit(limit)
        .all()
    )
    # uso de arrays guía 6
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