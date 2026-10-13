"""Lógica pura de la sincronización bucket → Data Store (sin dependencias de GCP).

Decide qué documentos importar o borrar y si el plan es seguro de ejecutar.
"""

from dataclasses import dataclass, field

# Carpetas publicadas (KB del agente). Deben coincidir con MACRO_SLUGS del backend
# (consultor-ia-girs, rama urbanismo: src/documents/documents.paths.ts).
# `pendientes/` y `ocultos/` quedan fuera a propósito.
MACRO_FOLDERS = (
    "legislacion",
    "ordenanzas",
    "instrumentos-internacionales",
    "sentencias",
    "sentencias-internacionales",
    "doctrina",
)

# El parser OCR de Vertex AI Search solo procesa las primeras 500 páginas de un PDF.
OCR_PAGE_LIMIT = 500


@dataclass(frozen=True)
class Limits:
    max_new_docs: int = 50
    max_new_pages: int = 3000
    # Fracción máxima del índice que se puede borrar en una ejecución.
    max_delete_ratio: float = 0.2


@dataclass
class SyncPlan:
    to_import: list[str] = field(default_factory=list)
    to_delete: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.to_import and not self.to_delete


def build_plan(bucket_uris: set[str], indexed_uris: set[str]) -> SyncPlan:
    """Importa lo que está en el bucket y no en el índice; borra lo inverso."""
    return SyncPlan(
        to_import=sorted(bucket_uris - indexed_uris),
        to_delete=sorted(indexed_uris - bucket_uris),
    )


def billable_pages(pages: int) -> int:
    """Páginas que cobra el OCR por un PDF (tope de 500)."""
    return min(pages, OCR_PAGE_LIMIT)


def check_guards(
    plan: SyncPlan,
    new_pages: int,
    bucket_count: int,
    indexed_count: int,
    limits: Limits,
) -> list[str]:
    """Devuelve los motivos para abortar; lista vacía si el plan es seguro."""
    reasons = []
    if bucket_count == 0 and indexed_count > 0:
        reasons.append(
            "El bucket no tiene PDFs en las carpetas macro pero el índice sí; "
            "posible error de configuración o de permisos."
        )
    if len(plan.to_import) > limits.max_new_docs:
        reasons.append(
            f"{len(plan.to_import)} PDFs nuevos superan el límite de {limits.max_new_docs}."
        )
    if new_pages > limits.max_new_pages:
        reasons.append(
            f"{new_pages} páginas nuevas superan el límite de {limits.max_new_pages}."
        )
    if indexed_count and len(plan.to_delete) / indexed_count > limits.max_delete_ratio:
        reasons.append(
            f"Se borrarían {len(plan.to_delete)} de {indexed_count} documentos "
            f"(más del {limits.max_delete_ratio:.0%} del índice)."
        )
    return reasons
