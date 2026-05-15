"""
persistence.py — Módulo de Persistencia de Datos en Archivos

Guías implementadas:
  - Guía 8: Data Persistence — Gestión de Archivos (TXT y CSV, modos r/w/a,
            with open(), try/except para manejo robusto de errores I/O)
  - Guía 5: Diccionarios (config como dict clave:valor; historial como lista de dicts)
  - Guía 6: Arrays y Matrices (exportación de la matriz horaria [24×3] a CSV)
  - Guía 7: Subalgoritmos (cada función tiene responsabilidad única — SRP)
"""

import csv
import os
from datetime import datetime

# ── Guía 8 — Act #1: Rutas de archivos de persistencia ───────────────────────
# Todos los archivos se centralizan en la carpeta 'data/' para organización
DATA_DIR      = "data"
LOG_FILE      = os.path.join(DATA_DIR, "eventos.log")        # modo 'a' — histórico
CONFIG_FILE   = os.path.join(DATA_DIR, "config.txt")         # modo 'w' y 'r' — sesión
EXPORT_CSV    = os.path.join(DATA_DIR, "reporte_viaje.csv")  # exportación matriz horaria
HISTORIAL_CSV = os.path.join(DATA_DIR, "historial_memoria.csv")  # exportación historial

# Guía 8 — Act #1: Crear carpeta de datos si no existe (garantía de ruta válida)
os.makedirs(DATA_DIR, exist_ok=True)

# ── Guía 6 — Act #2: Encabezados de la matriz horaria [24×3] ─────────────────
# Las columnas representan las 3 métricas de la matriz (subidas, bajadas, neto)
HEADERS_MATRIZ    = ["hora", "subidas", "bajadas", "neto_pasajeros"]

# ── Guía 5 — Act #2: Encabezados del historial — coinciden con claves del dict ─
HEADERS_HISTORIAL = ["timestamp", "tipo", "personas_actual", "confianza", "viaje_id"]


# ─────────────────────────────────────────────────────────────────────────────
# ACTIVIDAD 1 — ARCHIVOS PLANOS TXT
# Guía 8: Escritura con modos 'a' (append) y 'w' (write); lectura con 'r'
# ─────────────────────────────────────────────────────────────────────────────

def escribir_log(evento: str, personas: int, confianza=None) -> bool:
    """
    Guía 8 — Act #1: Escritura de log con modo 'a' (append).
    El modo append acumula sin borrar — es el historial completo del sistema.

    Guía 7 — Act #1: Subalgoritmo de responsabilidad única — solo escribe log.
    Guía 4 — Act #2: f-string con alineación de columnas para log legible.
    Guía 8 — Act #3: try/except para capturar PermissionError y OSError.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Guía 4 — Act #2: f-string formateado con alineación de columnas
        linea = (
            f"[{timestamp}] {evento:<7} │ "
            f"Personas: {personas:>3} │ "
            f"Confianza: {confianza if confianza is not None else 'N/A'}"
        )

        # Guía 8 — Act #1: with open() en modo 'a' — garantiza cierre seguro del archivo
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(linea + "\n")  # Cada evento en una línea nueva

        print(f"[LOG] Evento guardado → {LOG_FILE}")
        return True

    # Guía 8 — Act #3: Manejo específico de errores de permisos del sistema operativo
    except PermissionError as e:
        print(f"[ERROR] Sin permisos para escribir log: {e}")
        return False

    # Guía 8 — Act #3: Error genérico de OS (disco lleno, path inválido)
    except OSError as e:
        print(f"[ERROR] Error de sistema al escribir log: {e}")
        return False


def guardar_config(bus_id: str, ruta_id: str, placa: str) -> bool:
    """
    Guía 8 — Act #1: Escritura de configuración con modo 'w' (write/sobreescritura).
    El modo 'w' sobreescribe siempre — guarda el estado más reciente de la sesión.

    Guía 7 — Act #1: Subalgoritmo de responsabilidad única — solo persiste config.
    Guía 5 — Act #2: El archivo config.txt almacena pares clave=valor (equivalente a dict).
    Guía 8 — Act #3: try/except para capturar PermissionError.
    """
    try:
        # Guía 8 — Act #1: with open() en modo 'w' — sobreescribe el archivo cada vez
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            # Guía 5 — Act #2: Estructura clave=valor en archivo plano (equivalente a dict)
            f.write(f"BUS_ID={bus_id}\n")
            f.write(f"RUTA_ID={ruta_id}\n")
            f.write(f"PLACA={placa}\n")
            f.write(f"ULTIMA_SESION={datetime.now().isoformat()}\n")

        # Guía 4 — Act #2: f-string informativo de confirmación
        print(f"[CONFIG] Configuración guardada: {placa} → {CONFIG_FILE}")
        return True

    # Guía 8 — Act #3: Captura de error de permisos de escritura
    except PermissionError as e:
        print(f"[ERROR] Sin permisos para guardar config: {e}")
        return False


def cargar_config() -> dict:
    """
    Guía 8 — Act #1: Lectura de archivo con modo 'r' (read).
    Restaura la sesión previa al iniciar el microservicio.

    Guía 5 — Act #2: Retorna dict clave:valor parseado desde el archivo TXT.
    Guía 5 — Act #3: Usa .strip() y .split() para normalizar cadenas al leer.
    Guía 7 — Act #1: Subalgoritmo de responsabilidad única — solo lee config.
    Guía 8 — Act #3: try/except para FileNotFoundError (primer inicio).
    """
    # Guía 5 — Act #2: Diccionario que acumulará las claves del archivo
    config = {}

    try:
        # Guía 8 — Act #1: with open() en modo 'r' — lectura segura del archivo
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            # Guía 5 — Act #1: Ciclo for sobre líneas del archivo (iterar colección)
            for linea in f:
                linea = linea.strip()  # Guía 5 — Act #3: .strip() para limpiar \n y espacios

                # Guía 3 — Act #2: Operador 'in' para verificar formato clave=valor
                if "=" in linea:
                    # Guía 5 — Act #3: .split() para fragmentar la línea en clave y valor
                    clave, valor = linea.split("=", 1)
                    config[clave.strip()] = valor.strip()  # Guía 5: inserción en dict

        # Guía 4 — Act #2: Output formateado con datos de la sesión restaurada
        print(
            f"[CONFIG] Sesión restaurada: Bus {config.get('PLACA', '?')} │ "
            f"Última sesión: {config.get('ULTIMA_SESION', 'N/A')}"
        )

    # Guía 8 — Act #3: FileNotFoundError — primer inicio, no existe config previo
    except FileNotFoundError:
        print("[CONFIG] No hay sesión previa — iniciando desde cero")

    # Guía 8 — Act #3: Exception base — cualquier error inesperado de lectura
    except Exception as e:
        print(f"[CONFIG] Error al cargar config: {e}")

    return config  # Guía 5: retorna dict (vacío si no había archivo)


def leer_log_reciente(n_lineas: int = 20) -> list:
    """
    Guía 8 — Act #1: Lectura de las últimas N líneas del log histórico.
    Guía 6 — Act #1: Retorna un vector (lista) de strings con las líneas del log.
    Guía 7 — Act #1: Subalgoritmo independiente de lectura de log.
    Guía 8 — Act #3: try/except para FileNotFoundError si aún no hay log.
    """
    try:
        # Guía 8 — Act #1: with open() modo 'r' para lectura del log
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            # Guía 6 — Act #1: readlines() retorna vector de líneas (lista unidimensional)
            todas_las_lineas = f.readlines()

        # Guía 6 — Act #1: Slicing del vector — últimas n_lineas (cola del buffer)
        return [linea.strip() for linea in todas_las_lineas[-n_lineas:]]

    # Guía 8 — Act #3: El log no existe si no hubo eventos aún
    except FileNotFoundError:
        print("[LOG] Archivo de log no encontrado — sin eventos previos")
        return []  # Guía 6: vector vacío


# ─────────────────────────────────────────────────────────────────────────────
# ACTIVIDAD 2 — DATOS ESTRUCTURADOS CSV
# Guía 8: csv.DictWriter y csv.writer, exportación de dicts y matrices
# ─────────────────────────────────────────────────────────────────────────────

def exportar_historial_csv(historial: list) -> bool:
    """
    Guía 8 — Act #2: Exportación del historial (lista de dicts) a CSV.
    Guía 5 — Act #2: Cada fila del CSV corresponde a un diccionario del historial.
    Guía 5 — Act #1: Ciclo for sobre la lista de dicts para escribir cada fila.
    Guía 7 — Act #1: Paso por referencia — 'historial' es una lista mutable leída sin modificar.
    Guía 8 — Act #3: try/except para PermissionError, ValueError y TypeError.
    """
    try:
        # Guía 8 — Act #2: with open() modo 'w' con newline='' (requerido por csv)
        with open(HISTORIAL_CSV, "w", newline="", encoding="utf-8") as f:
            # Guía 5 — Act #2: DictWriter usa las claves del dict como encabezados
            writer = csv.DictWriter(f, fieldnames=HEADERS_HISTORIAL)
            writer.writeheader()  # Guía 8: primera fila = encabezados del CSV

            # Guía 5 — Act #1: for sobre lista de dicts — cada elemento es un evento
            for evento in historial:
                # Guía 8 — Act #2: Validación de tipos — numérico vs alfanumérico
                fila = {
                    "timestamp":      str(evento.get("timestamp", "")),
                    "tipo":           str(evento.get("tipo", "")),
                    "personas_actual": int(evento.get("personas_actual", 0)),    # numérico
                    "confianza":      float(evento.get("confianza") or 0.0),     # numérico
                    "viaje_id":       str(evento.get("viaje_id", "")),
                }
                writer.writerow(fila)  # Guía 8: escritura de fila CSV

        # Guía 4 — Act #2: f-string con total de registros exportados
        print(f"[CSV] {len(historial)} eventos exportados → {HISTORIAL_CSV}")
        return True

    # Guía 8 — Act #3: Error de permisos de escritura
    except PermissionError as e:
        print(f"[ERROR] Sin permisos para escribir CSV: {e}")
        return False

    # Guía 8 — Act #3: Error de tipo de dato al construir la fila CSV
    except (ValueError, TypeError) as e:
        print(f"[ERROR] Error de tipo de dato en CSV: {e}")
        return False


def exportar_matriz_csv(matriz: list) -> bool:
    """
    Guía 6 — Act #2: Exportación de la matriz horaria [24×3] a CSV.
    Guía 8 — Act #2: Usa csv.writer para escribir filas de la matriz.
    Guía 5 — Act #1: Ciclo for sobre las 24 filas (horas) de la matriz.
    Guía 7 — Act #1: Paso por referencia — 'matriz' es lista de listas, leída sin modificar.
    Guía 8 — Act #3: try/except con Exception base para garantizar estabilidad.
    """
    try:
        # Guía 8 — Act #2: with open() modo 'w' para exportación de la matriz
        with open(EXPORT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(HEADERS_MATRIZ)  # Guía 8: fila de encabezados

            # Guía 5 — Act #1: for sobre rango 24 (índices de fila de la matriz)
            for hora in range(24):
                # Guía 6 — Act #2: Acceso por doble índice matriz[hora][metrica]
                writer.writerow([
                    f"{hora:02d}:00",        # Alfanumérico: formato HH:MM
                    int(matriz[hora][0]),     # Numérico: columna subidas
                    int(matriz[hora][1]),     # Numérico: columna bajadas
                    int(matriz[hora][2]),     # Numérico: columna neto
                ])

        print(f"[CSV] Matriz horaria [24×3] exportada → {EXPORT_CSV}")
        return True

    # Guía 8 — Act #3: Exception base — garantiza que el servidor no se detenga por esto
    except Exception as e:
        print(f"[ERROR] Error exportando matriz a CSV: {e}")
        return False


def leer_historial_csv() -> list:
    """
    Guía 8 — Act #2: Lectura del CSV de historial para restaurar estado en memoria.
    Guía 5 — Act #1: for sobre filas del CSV — reconstruye lista de dicts.
    Guía 6 — Act #1: Retorna vector (lista) de dicts reconstruidos desde el archivo.
    Guía 8 — Act #3: try/except para FileNotFoundError y ValueError.
    """
    historial_restaurado = []  # Guía 6: vector a rellenar

    try:
        # Guía 8 — Act #2: with open() modo 'r' para lectura de CSV
        with open(HISTORIAL_CSV, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)  # Guía 5: DictReader retorna cada fila como dict

            # Guía 5 — Act #1: for sobre filas del CSV (cada fila es un dict)
            for fila in reader:
                try:
                    # Guía 8 — Act #2: Validación de tipos al leer — conversión controlada
                    evento = {
                        "timestamp":      fila.get("timestamp", ""),
                        "tipo":           fila.get("tipo", ""),
                        "personas_actual": int(fila.get("personas_actual", 0)),
                        "confianza":      float(fila.get("confianza", 0.0)),
                        "viaje_id":       fila.get("viaje_id", ""),
                    }
                    historial_restaurado.append(evento)  # Guía 6: inserción en vector

                # Guía 8 — Act #3: Error de conversión en fila individual — skip y continuar
                except (ValueError, TypeError) as e:
                    print(f"[CSV] Fila ignorada por error de tipo: {e}")
                    continue  # Guía 5 — Act #1C: continue para saltar filas corruptas

        print(f"[CSV] {len(historial_restaurado)} eventos restaurados desde {HISTORIAL_CSV}")

    # Guía 8 — Act #3: El CSV no existe si no se cerró correctamente antes
    except FileNotFoundError:
        print("[CSV] No hay historial previo en disco — iniciando vacío")

    return historial_restaurado  # Guía 6: retorna vector (puede ser vacío)