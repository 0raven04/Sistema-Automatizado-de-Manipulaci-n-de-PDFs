import uuid
from pathlib import Path
from django.core.exceptions import ValidationError

def generar_id_operacion() -> str:
    """Genera un ID de operación único utilizando UUID4."""
    return str(uuid.uuid4())

def validar_ruta(base_dir: Path, ruta_candidata: Path) -> Path:
    """
    Valida que la ruta candidata esté dentro del directorio base.

    Esto ayuda a prevenir ataques de path traversal al asegurarse de que
    el archivo se guarde solo dentro de un directorio controlado.

    Args:
        base_dir: El directorio base permitido.
        ruta_candidata: La ruta que se desea validar.

    Returns:
        La ruta absoluta validada.

    Raises:
        ValidationError: Si la ruta candidata no está dentro del directorio base.
    """
    ruta_candidata = ruta_candidata.resolve()
    if not ruta_candidata.is_relative_to(base_dir):
        raise ValidationError("Ruta no válida: fuera del directorio permitido.")
    return ruta_candidata