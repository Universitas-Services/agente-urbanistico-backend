"""Sincroniza el Data Store de Vertex AI Search con las carpetas macro del bucket.

Pensado para correr cada hora como Cloud Run Job:
  - PDFs nuevos en las carpetas macro (aprobados en el admin) → se importan.
  - PDFs que ya no están (ocultados o rechazados) → se borran del índice.
  - Sin cambios → no hace nada.
Si el plan supera los límites de seguridad no ejecuta nada y termina con código 2.

Uso local:  python -m sync.main --dry-run
"""

import argparse
import io
import json
import os
import sys

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud import storage
from pypdf import PdfReader

from sync.planning import (
    MACRO_FOLDERS,
    OCR_PAGE_LIMIT,
    Limits,
    billable_pages,
    build_plan,
    check_guards,
)

EXIT_GUARD_TRIPPED = 2


def log(message: str, severity: str = "INFO", **fields) -> None:
    """Log estructurado: Cloud Logging interpreta `severity` y `message`."""
    print(
        json.dumps({"severity": severity, "message": message, **fields}, ensure_ascii=False),
        flush=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", default=os.environ.get("PROJECT_ID", "agente-manual-contrataciones"))
    parser.add_argument("--bucket", default=os.environ.get("BUCKET", "derecho-urbanistico-prueba"))
    parser.add_argument("--root", default=os.environ.get("ROOT_FOLDER", "urbanismo"))
    parser.add_argument("--data-store-id", default=os.environ.get("DATA_STORE_ID", "ds-urbanismo-kb"))
    parser.add_argument("--max-new-docs", type=int, default=int(os.environ.get("MAX_NEW_DOCS", 50)))
    parser.add_argument("--max-new-pages", type=int, default=int(os.environ.get("MAX_NEW_PAGES", 3000)))
    parser.add_argument("--max-delete-ratio", type=float, default=float(os.environ.get("MAX_DELETE_RATIO", 0.2)))
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=os.environ.get("DRY_RUN", "").lower() in ("1", "true"),
        help="Muestra el plan sin importar ni borrar nada.",
    )
    return parser.parse_args()


def list_bucket_pdfs(client: storage.Client, bucket: str, root: str) -> set[str]:
    """PDFs directamente dentro de cada carpeta macro (no recursivo)."""
    uris = set()
    for folder in MACRO_FOLDERS:
        blobs = client.list_blobs(bucket, prefix=f"{root}/{folder}/", delimiter="/")
        for blob in blobs:
            if blob.name.lower().endswith(".pdf"):
                uris.add(f"gs://{bucket}/{blob.name}")
    return uris


def list_indexed_documents(
    client: discoveryengine.DocumentServiceClient, parent: str
) -> dict[str, str]:
    """Mapa URI de origen → nombre del documento en el Data Store."""
    indexed = {}
    for doc in client.list_documents(parent=parent):
        if doc.content.uri:
            indexed[doc.content.uri] = doc.name
        else:
            log("Documento sin URI de origen en el índice", "WARNING", document=doc.name)
    return indexed


def count_billable_pages(client: storage.Client, uris: list[str]) -> int:
    total = 0
    for uri in uris:
        bucket, _, name = uri.removeprefix("gs://").partition("/")
        try:
            data = client.bucket(bucket).blob(name).download_as_bytes()
            pages = len(PdfReader(io.BytesIO(data)).pages)
        except Exception as e:
            # Si no se puede leer, asumir el peor caso que cobra el OCR.
            log("No se pudo contar páginas; se asume el máximo", "WARNING", uri=uri, error=str(e))
            pages = OCR_PAGE_LIMIT
        total += billable_pages(pages)
    return total


def main() -> int:
    args = parse_args()
    limits = Limits(args.max_new_docs, args.max_new_pages, args.max_delete_ratio)
    parent = (
        f"projects/{args.project_id}/locations/global/collections/default_collection/"
        f"dataStores/{args.data_store_id}/branches/default_branch"
    )

    storage_client = storage.Client(project=args.project_id)
    doc_client = discoveryengine.DocumentServiceClient(
        client_options=ClientOptions(quota_project_id=args.project_id)
    )

    bucket_uris = list_bucket_pdfs(storage_client, args.bucket, args.root)
    indexed = list_indexed_documents(doc_client, parent)
    plan = build_plan(bucket_uris, set(indexed))

    new_pages = count_billable_pages(storage_client, plan.to_import) if plan.to_import else 0
    log(
        "Plan de sincronización",
        dry_run=args.dry_run,
        bucket_pdfs=len(bucket_uris),
        indexed_docs=len(indexed),
        to_import=plan.to_import,
        to_delete=plan.to_delete,
        new_billable_pages=new_pages,
    )

    if plan.is_empty:
        log("Sin cambios; nada que hacer.")
        return 0

    reasons = check_guards(plan, new_pages, len(bucket_uris), len(indexed), limits)
    if reasons:
        log(
            "Límite de seguridad superado: no se ejecuta nada. Revisar y correr a mano si corresponde.",
            "ERROR",
            reasons=reasons,
        )
        return EXIT_GUARD_TRIPPED

    if args.dry_run:
        log("Modo simulación: no se importó ni borró nada.")
        return 0

    if plan.to_import:
        operation = doc_client.import_documents(
            request=discoveryengine.ImportDocumentsRequest(
                parent=parent,
                gcs_source=discoveryengine.GcsSource(
                    input_uris=plan.to_import, data_schema="content"
                ),
                reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
            )
        )
        operation.result(timeout=3600)
        metadata = operation.metadata
        log(
            "Importación terminada",
            "INFO" if not metadata.failure_count else "ERROR",
            success=metadata.success_count,
            failures=metadata.failure_count,
        )

    for uri in plan.to_delete:
        doc_client.delete_document(name=indexed[uri])
        log("Documento borrado del índice", uri=uri)

    return 0


if __name__ == "__main__":
    sys.exit(main())
