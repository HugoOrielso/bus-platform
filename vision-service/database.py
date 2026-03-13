"""
database.py — Mapea las tablas de Prisma en bus_platform.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship
from dotenv import load_dotenv
import os

load_dotenv()

_raw_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bus_platform")
DATABASE_URL = _raw_url.split("?")[0]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Bus(Base):
    __tablename__ = "buses"
    id         = Column(String, primary_key=True)
    placa      = Column(String, unique=True)
    nombre     = Column(String)
    capacidad  = Column(Integer)
    activo     = Column(Boolean, default=True)
    rutaId     = Column(String, ForeignKey("rutas.id"), nullable=True)
    createdAt  = Column(DateTime, server_default=func.now())
    updatedAt  = Column(DateTime, server_default=func.now(), onupdate=func.now())
    viajes     = relationship("Viaje", back_populates="bus")


class Ruta(Base):
    __tablename__ = "rutas"
    id        = Column(String, primary_key=True)
    nombre    = Column(String)
    origen    = Column(String)
    destino   = Column(String)
    activa    = Column(Boolean, default=True)
    createdAt = Column(DateTime, server_default=func.now())
    viajes    = relationship("Viaje", back_populates="ruta")


class Viaje(Base):
    __tablename__ = "viajes"
    id              = Column(String, primary_key=True)
    busId           = Column(String, ForeignKey("buses.id"), nullable=False)
    rutaId          = Column(String, ForeignKey("rutas.id"), nullable=False)
    estado          = Column(String, default="EN_CURSO")
    fechaInicio     = Column(DateTime, server_default=func.now())
    fechaFin        = Column(DateTime, nullable=True)
    totalSubidas    = Column(Integer, default=0)
    totalBajadas    = Column(Integer, default=0)
    pasajerosActual = Column(Integer, default=0)
    createdAt       = Column(DateTime, server_default=func.now())
    bus             = relationship("Bus", back_populates="viajes")
    ruta            = relationship("Ruta", back_populates="viajes")
    conteos         = relationship("Conteo", back_populates="viaje")


class Conteo(Base):
    __tablename__ = "conteos"
    id        = Column(String, primary_key=True)
    viajeId   = Column(String, ForeignKey("viajes.id"), nullable=False)
    tipo      = Column(String, nullable=False)
    fuente    = Column(String, default="CAMARA")
    confianza = Column(Float, nullable=True)
    timestamp = Column(DateTime, server_default=func.now())
    viaje     = relationship("Viaje", back_populates="conteos")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()