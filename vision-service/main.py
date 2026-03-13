"""
main.py — Microservicio FastAPI para conteo de pasajeros
Escribe en bus_platform (misma DB que Express/Prisma)
"""
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
from detector import DetectorPersonas
from counter_service import registrar_evento, obtener_conteo_actual, obtener_historial

detector: DetectorPersonas = None


def on_cambio_personas(evento: str, personas_actual: int):
    db = SessionLocal()
    try:
        registrar_evento(db, evento, personas_actual)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global detector
    detector = DetectorPersonas(callback_cambio=on_cambio_personas)
    detector.iniciar()
    yield
    detector.detener()


app = FastAPI(
    title="Bus Passenger Counter",
    description="Microservicio de conteo de pasajeros — escribe en bus_platform",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/")
def raiz():
    return {"status": "ok", "mensaje": "Bus Passenger Counter corriendo 🚌"}


@app.get("/conteo")
def conteo_actual(db: Session = Depends(get_db)):
    """Conteo actual del viaje EN_CURSO del bus configurado."""
    datos = obtener_conteo_actual(db)
    datos["detector"] = detector.estado() if detector else {}
    return datos


@app.get("/historial")
def historial(limit: int = 50, db: Session = Depends(get_db)):
    """Últimos N conteos del viaje activo."""
    return obtener_historial(db, limit=limit)


@app.post("/conteo/reset")
def reset_detector():
    """Reinicia el estado interno del detector (no toca la DB)."""
    if detector:
        detector.personas_prev   = 0
        detector.personas_actual = 0
    return {"status": "ok", "mensaje": "Detector reseteado"}


@app.get("/health")
def health():
    return {
        "status":   "ok",
        "detector": detector.estado() if detector else "no iniciado",
    }