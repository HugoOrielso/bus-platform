"""
models.py — Clases de Dominio de Negocio (POO Nivel I)

Guías implementadas:
  - Guía 9: POO Nivel I — Classes, Objects, __init__, __str__, @property,
            getters, setters, encapsulamiento, abstracción
  - Guía 7: Subalgoritmos — métodos como subalgoritmos con responsabilidad única
  - Guía 8: Persistencia — ViajeActivo se auto-carga desde config.txt al instanciarse
  - Guía 5: Diccionarios — to_dict() para serialización API; EventoConteo sustituye dicts
  - Guía 6: Arrays — _historial como vector de objetos EventoConteo
  - Guía 4: Input/Output — __str__ como output formateado; f-strings en representación
  - Guía 3: Control Lógico — validaciones en setters y constructores con if/elif/else
"""

from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# CLASE EventoConteo — Entidad atómica de registro
# Guía 9 — Act #1 y #2: Clase con atributos privados, getters y __str__
# Sustituye los dicts {'tipo':..., 'timestamp':...} de la Guía 5
# ─────────────────────────────────────────────────────────────────────────────

class EventoConteo:
    """
    Guía 9 — Act #1: Entidad atómica de registro de pasajero.
    Principio de encapsulamiento: todos los atributos son privados (_nombre).
    Abstracción: el caller solo conoce tipo/personas/confianza; no el timestamp interno.

    Sustituye el diccionario simple de la Guía 5:
      ANTES → {'tipo': 'SUBIDA', 'personas_actual': 3, 'confianza': 0.9}
      AHORA → EventoConteo('SUBIDA', 3, 0.9)
    """

    # Guía 9 — Act #2: Atributo de CLASE (compartido por todas las instancias)
    # Define los únicos valores válidos para el campo tipo
    TIPOS_VALIDOS = {"SUBIDA", "BAJADA"}

    def __init__(self, tipo: str, personas: int, confianza: float = None):
        """
        Guía 9 — Act #1: Constructor (__init__) con validación de parámetros.
        Guía 3 — Act #1: Regla de negocio — tipo debe ser SUBIDA o BAJADA (if/else).
        Guía 7 — Act #2: Paso por valor — str e int son inmutables en Python.
        """

        # Guía 3 — Act #1: Validación de tipo con if/else — regla de negocio del constructor
        if tipo not in self.TIPOS_VALIDOS:
            raise ValueError(
                f"Tipo inválido: '{tipo}'. Use uno de: {self.TIPOS_VALIDOS}"
            )

        # Guía 9 — Act #1: Atributos PRIVADOS (encapsulamiento — convención _nombre)
        self._tipo      = tipo
        self._personas  = personas
        self._confianza = confianza
        self._timestamp = datetime.now()  # Se registra automáticamente al crear el objeto

    # ── Guía 9 — Act #2: Getters con @property (solo lectura) ────────────────

    @property
    def tipo(self) -> str:
        """Guía 9 — Act #2: Getter — expone _tipo de solo lectura."""
        return self._tipo

    @property
    def personas(self) -> int:
        """Guía 9 — Act #2: Getter — expone _personas de solo lectura."""
        return self._personas

    @property
    def confianza(self) -> float:
        """Guía 9 — Act #2: Getter — expone _confianza de solo lectura."""
        return self._confianza

    @property
    def timestamp(self) -> datetime:
        """Guía 9 — Act #2: Getter — expone _timestamp de solo lectura."""
        return self._timestamp

    # ── Guía 9 — Act #2: Métodos de instancia ────────────────────────────────

    def to_dict(self) -> dict:
        """
        Guía 9 — Act #3: Serialización del objeto a diccionario para la API.
        Guía 5 — Act #2: Retorna estructura clave:valor compatible con los endpoints.
        Guía 7 — Act #1: Subalgoritmo de responsabilidad única — solo serializa.
        Integración Guía 9 + Guía 5: convierte objeto POO al dict que espera el API.
        """
        return {
            "tipo":            self._tipo,
            "personas_actual": self._personas,
            "confianza":       self._confianza,
            "timestamp":       str(self._timestamp),
            "viaje_id":        "",  # Se completa al registrar en BD
        }

    def __str__(self) -> str:
        """
        Guía 9 — Act #2: Método especial __str__ — representación profesional del objeto.
        Guía 4 — Act #2: f-string con formato alineado para output de consola.
        Se invoca automáticamente con print(evento_conteo).
        """
        return (
            f"EventoConteo("
            f"{self._tipo} │ "
            f"{self._personas} personas │ "
            f"conf={self._confianza or 'N/A'} │ "
            f"{self._timestamp:%H:%M:%S}"
            f")"
        )


# ─────────────────────────────────────────────────────────────────────────────
# CLASE ViajeActivo — Entidad principal de dominio de negocio
# Guía 9 — Act #1, #2 y #3: Clase con getters, setter validado y __str__
# ─────────────────────────────────────────────────────────────────────────────

class ViajeActivo:
    """
    Guía 9 — Act #1: Entidad de dominio que representa el viaje de bus en curso.
    Principio de encapsulamiento: métricas (_subidas, _bajadas, _actuales) privadas.
    Principio de abstracción: el caller solo llama registrar_subida()/registrar_bajada();
    no necesita conocer la estructura interna de la BD.

    Integra Guía 8: se auto-carga desde config.txt al instanciarse.
    Integra Guía 6: _historial es un vector de objetos EventoConteo.
    Sustituye el manejo disperso de diccionarios del counter_service.py de la Guía 5.
    """

    def __init__(self, bus_placa: str, capacidad: int = 40):
        """
        Guía 9 — Act #1: Constructor — inicializa todos los atributos del viaje.
        Guía 7 — Act #1: Paso por valor — str e int son inmutables.
        Guía 8 — Act #1: Auto-carga de configuración desde config.txt (Persistencia).
        """

        # Guía 9 — Act #1: Atributos PÚBLICOS — accesibles directamente
        self.bus_placa = bus_placa
        self.estado    = "EN_CURSO"

        # Guía 9 — Act #2: capacidad es privada — controlada por setter con validación
        # La asignación aquí pasa por el @setter definido abajo
        self.capacidad = capacidad

        # Guía 9 — Act #1: Atributos PRIVADOS — encapsulamiento de métricas sensibles
        self._subidas  = 0
        self._bajadas  = 0
        self._actuales = 0

        # Guía 6 — Act #1: _historial es un vector de objetos EventoConteo
        # Sustituye la lista de dicts de la Guía 5
        self._historial: list = []

        # ── Guía 8 — Act #1: Auto-carga de configuración desde archivo config.txt ──
        # Integración Guía 8 + Guía 9: el objeto se auto-configura desde persistencia
        try:
            from persistence import cargar_config
            config = cargar_config()
            # Guía 5 — Act #2: .get() en dict para acceso seguro a claves
            self._bus_id  = config.get("BUS_ID",  None)
            self._ruta_id = config.get("RUTA_ID", None)
        except Exception:
            # Guía 3 — Act #1: Fallback si persistence no está disponible
            self._bus_id  = None
            self._ruta_id = None

    # ── Guía 9 — Act #2: Setter con validación para atributo sensible ─────────

    @property
    def capacidad(self) -> int:
        """Guía 9 — Act #2: Getter de capacidad — expone _capacidad de solo lectura."""
        return self._capacidad

    @capacidad.setter
    def capacidad(self, valor: int) -> None:
        """
        Guía 9 — Act #2: Setter con validación — controla el acceso al dato sensible.
        Guía 3 — Act #1: if/else — regla de negocio: capacidad no puede ser negativa.
        El setter lanza ValueError con mensaje descriptivo si la validación falla.
        """
        # Guía 3 — Act #1: Validación de negocio en setter — if para rechazar valores inválidos
        if valor < 0:
            raise ValueError(
                f"Capacidad inválida: {valor}. Debe ser >= 0 (número de asientos del bus)"
            )
        self._capacidad = valor  # Guía 9: solo asigna si pasa la validación

    # ── Guía 9 — Act #2: Getters de solo lectura para métricas privadas ───────

    @property
    def total_subidas(self) -> int:
        """Guía 9 — Act #2: Getter — _subidas es privado; solo se lee, no se asigna directo."""
        return self._subidas

    @property
    def total_bajadas(self) -> int:
        """Guía 9 — Act #2: Getter — _bajadas es privado; solo se lee, no se asigna directo."""
        return self._bajadas

    @property
    def pasajeros_actuales(self) -> int:
        """Guía 9 — Act #2: Getter — _actuales es privado; contador en tiempo real."""
        return self._actuales

    # ── Guía 9 — Act #2: Métodos de instancia (behaviors del objeto) ─────────

    def registrar_subida(self) -> None:
        """
        Guía 9 — Act #2: Método de instancia — actualiza métricas al subir un pasajero.
        Guía 7 — Act #1: Subalgoritmo de responsabilidad única — solo gestiona subida.
        Guía 3 — Act #1: Sin validación aquí (regla de negocio: siempre puede subir).
        """
        self._subidas  += 1
        self._actuales += 1

    def registrar_bajada(self) -> None:
        """
        Guía 9 — Act #2: Método de instancia — actualiza métricas al bajar un pasajero.
        Guía 7 — Act #1: Subalgoritmo de responsabilidad única — solo gestiona bajada.
        Guía 3 — Act #1: max(0, ...) garantiza que _actuales nunca sea negativo (regla de negocio).
        """
        self._bajadas  += 1
        # Guía 3 — Act #1: Regla de negocio — pasajeros actuales nunca bajan de 0
        self._actuales  = max(0, self._actuales - 1)

    def calcular_ocupacion(self) -> float:
        """
        Guía 9 — Act #2: Método de comportamiento — calcula % de ocupación del bus.
        Guía 7 — Act #1: Subalgoritmo con responsabilidad única — solo calcula porcentaje.
        Guía 3 — Act #1: if/else para evitar división por cero en capacidad inválida.
        Guía 4 — Act #2: Retorna float redondeado a 2 decimales (formato profesional).
        """
        # Guía 3 — Act #1: Validación de precondición — capacidad debe ser positiva
        if self._capacidad <= 0:
            return 0.0
        return round((self._actuales / self._capacidad) * 100, 2)

    def agregar_evento(self, evento: "EventoConteo") -> None:
        """
        Guía 9 — Act #2: Método que agrega un EventoConteo al historial del viaje.
        Guía 6 — Act #1: _historial actúa como vector de objetos EventoConteo.
        Guía 9 — Act #3: Sustituye el append de dicts de la Guía 5 por append de objetos.
        """
        # Guía 6 — Act #1: append sobre vector de objetos (en lugar de dicts)
        self._historial.append(evento)

    def obtener_historial_dicts(self) -> list:
        """
        Guía 9 — Act #3: Compatibilidad API — convierte vector de objetos a lista de dicts.
        Guía 5 — Act #1: List comprehension (for implícito) para transformar objetos.
        Guía 6 — Act #1: Itera sobre el vector _historial de objetos EventoConteo.
        """
        # Guía 5 — Act #1: for sobre vector de objetos → lista de dicts para el API
        return [evento.to_dict() for evento in self._historial]

    def finalizar(self) -> None:
        """
        Guía 9 — Act #2: Método que cambia el estado del viaje a FINALIZADO.
        Guía 7 — Act #1: Subalgoritmo de responsabilidad única — solo cambia estado.
        Guía 3 — Act #1: Podría agregar validación de estado actual (regla de negocio).
        """
        self.estado = "FINALIZADO"

    def to_dict(self) -> dict:
        """
        Guía 9 — Act #3: Serialización del objeto ViajeActivo a dict para endpoints.
        Guía 5 — Act #2: Retorna estructura clave:valor compatible con respuestas JSON.
        Guía 7 — Act #1: Subalgoritmo independiente — solo serializa, no modifica.
        """
        return {
            "bus_placa":          self.bus_placa,
            "estado":             self.estado,
            "capacidad":          self._capacidad,
            "pasajeros_actuales": self._actuales,
            "total_subidas":      self._subidas,
            "total_bajadas":      self._bajadas,
            "ocupacion_pct":      self.calcular_ocupacion(),
            "bus_id":             self._bus_id,
            "ruta_id":            self._ruta_id,
        }

    def __str__(self) -> str:
        """
        Guía 9 — Act #2: Método especial __str__ — representación profesional en consola.
        Guía 4 — Act #2: f-string con alineación de columnas para output formateado.
        Se invoca automáticamente con print(viaje_activo).
        """
        return (
            f"ViajeActivo │ "
            f"Bus: {self.bus_placa:<12} │ "
            f"Estado: {self.estado:<12} │ "
            f"Pasajeros: {self._actuales:>3}/{self._capacidad} "
            f"({self.calcular_ocupacion():.1f}%) │ "
            f"Subidas: {self._subidas} │ "
            f"Bajadas: {self._bajadas}"
        )