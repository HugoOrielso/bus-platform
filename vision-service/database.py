"""
database.py — Mapea las tablas de Prisma en bus_platform.

Guías implementadas:
  - Guía 3: Estructuras de Control (validación de URL de conexión)
  - Guía 4: Input/Output (variables de entorno como parámetros de configuración)
  - Guía 5: Diccionarios (estructura de modelos ORM como objetos clave:valor)
  - Guía 6: Arrays (relaciones one-to-many son equivalentes a vectores de objetos)
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship
from dotenv import load_dotenv
import os

load_dotenv()

# ── Guía 4 — Act #1: Captura dinámica de parámetros desde variables de entorno ──
# os.getenv() actúa como el input() del sistema — lee configuración externa
_raw_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bus_platform")

# Guía 3 — Act #2: Operador de cadena para limpiar parámetros extra de la URL
# Se separa la URL en la parte base, eliminando query params (?schema=..., etc.)
DATABASE_URL = _raw_url.split("?")[0]

# Guía 3 — Act #1: Validación de URL — si está vacía, lanzar error descriptivo
if not DATABASE_URL:
    raise ValueError("[ERROR] DATABASE_URL no está configurada en el archivo .env")

# Guía 4 — Act #2: Salida formateada informando la base de datos conectada
print(f"[DB] Conectando a: {DATABASE_URL.split('@')[-1]}")  # Oculta credenciales

engine       = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


# ─────────────────────────────────────────────────────────────────────────────
# MODELOS ORM — Representación de tablas como clases Python
# Guía 5 — Act #2: Cada modelo es equivalente a un diccionario de esquema de BD
# ─────────────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


class Bus(Base):
    """
    Guía 5 — Act #2: Modelo Bus como objeto complejo con múltiples atributos (clave:valor).
    Guía 6 — Act #1: La relación 'viajes' es un vector de objetos Viaje asociados a este Bus.
    """
    __tablename__ = "buses"

    # Guía 5 — Act #2: Atributos como estructura clave:valor del objeto Bus
    id         = Column(String, primary_key=True)
    placa      = Column(String, unique=True)
    nombre     = Column(String)
    capacidad  = Column(Integer)
    activo     = Column(Boolean, default=True)
    rutaId     = Column(String, ForeignKey("rutas.id"), nullable=True)
    createdAt  = Column(DateTime, server_default=func.now())
    updatedAt  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Guía 6 — Act #1: Relación one-to-many — 'viajes' actúa como vector de Viaje[]
    viajes = relationship("Viaje", back_populates="bus")


class Ruta(Base):
    """
    Guía 5 — Act #2: Modelo Ruta como diccionario de datos de la ruta de transporte.
    Guía 6 — Act #1: La relación 'viajes' es un vector de todos los viajes de esta ruta.
    """
    __tablename__ = "rutas"

    id        = Column(String, primary_key=True)
    nombre    = Column(String)
    origen    = Column(String)
    destino   = Column(String)
    activa    = Column(Boolean, default=True)
    createdAt = Column(DateTime, server_default=func.now())

    # Guía 6 — Act #1: Vector de viajes asociados a esta ruta
    viajes = relationship("Viaje", back_populates="ruta")


class Viaje(Base):
    """
    Guía 5 — Act #2: Modelo Viaje — objeto complejo con métricas de pasajeros.
    Guía 3 — Act #1: El campo 'estado' implementa una máquina de estados (EN_CURSO / FINALIZADO).
    Guía 6 — Act #1: La relación 'conteos' es un vector de todos los eventos del viaje.
    """
    __tablename__ = "viajes"

    id              = Column(String, primary_key=True)
    busId           = Column(String, ForeignKey("buses.id"), nullable=False)
    rutaId          = Column(String, ForeignKey("rutas.id"), nullable=False)

    # Guía 3 — Act #1: El estado define la regla de negocio del viaje
    # Valores posibles: "EN_CURSO", "FINALIZADO", "CANCELADO"
    estado          = Column(String, default="EN_CURSO")

    fechaInicio     = Column(DateTime, server_default=func.now())
    fechaFin        = Column(DateTime, nullable=True)

    # Guía 5 — Act #2: Métricas como atributos clave:valor del objeto Viaje
    totalSubidas    = Column(Integer, default=0)
    totalBajadas    = Column(Integer, default=0)
    pasajerosActual = Column(Integer, default=0)
    createdAt       = Column(DateTime, server_default=func.now())

    bus     = relationship("Bus",    back_populates="viajes")
    ruta    = relationship("Ruta",   back_populates="viajes")

    # Guía 6 — Act #1: Vector de conteos asociados a este viaje (relación one-to-many)
    conteos = relationship("Conteo", back_populates="viaje")


class Conteo(Base):
    """
    Guía 5 — Act #2: Modelo Conteo — registro atómico de un evento de subida/bajada.
    Guía 3 — Act #1: El campo 'tipo' solo acepta valores "SUBIDA" o "BAJADA" (regla de negocio).
    """
    __tablename__ = "conteos"

    id        = Column(String, primary_key=True)
    viajeId   = Column(String, ForeignKey("viajes.id"), nullable=False)

    # Guía 3 — Act #1: Campo tipo con valores controlados por regla de negocio
    tipo      = Column(String, nullable=False)   # "SUBIDA" | "BAJADA"
    fuente    = Column(String, default="CAMARA") # "CAMARA" | "MANUAL"
    confianza = Column(Float,  nullable=True)    # 0.0 – 1.0 (nivel de certeza del detector)
    timestamp = Column(DateTime, server_default=func.now())

    viaje = relationship("Viaje", back_populates="conteos")


# ─────────────────────────────────────────────────────────────────────────────
# GENERADOR DE SESIÓN DE BASE DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

def get_db():
    """
    Guía 3 — Act #2: Patrón de gestión de recursos con try/finally
    Garantiza que la sesión de BD siempre se cierre, incluso si hay excepciones.
    Equivalente a: si conexión abierta → usarla → en cualquier caso, cerrarla.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        # Guía 3 — Act #2: Bloque finally garantiza cierre de conexión (regla de negocio de recursos)
        db.close()