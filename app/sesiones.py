"""Sesiones gestionadas de Vertex para que la conversación sobreviva entre instancias.

El contenedor (fast_api_app) usaba sesiones en memoria: con varias instancias, cada
mensaje podía caer en una que no conocía la conversación. Agent Runtime no expone el id
del engine (el prefijo GOOGLE_CLOUD_AGENT_ENGINE está reservado), pero agents-cli escribe
en APP_URL la ruta del engine, que lo incluye.
"""
import logging
import os
import re
from typing import Any

from google.adk.cli.service_registry import get_service_registry
from google.adk.sessions import Session, VertexAiSessionService

ESQUEMA = "sesionesvertex"
SESION_TTL = f"{7 * 24 * 3600}s"


class SesionesVertex(VertexAiSessionService):
    """Sesiones gestionadas que vencen a los 7 días (por defecto Vertex las guarda un año)."""

    async def create_session(self, **kwargs: Any) -> Session:
        kwargs.setdefault("ttl", SESION_TTL)
        return await super().create_session(**kwargs)


def engine_id() -> str | None:
    match = re.search(r"/reasoningEngines/(\d+)", os.environ.get("APP_URL", ""))
    return match.group(1) if match else None


def session_service_uri() -> str | None:
    """URI para get_fast_api_app; None (sesiones en memoria) en local o sin id de engine."""
    id_engine = engine_id()
    if not id_engine:
        logging.warning("APP_URL sin id de engine: se usan sesiones en memoria.")
        return None
    get_service_registry().register_session_service(
        ESQUEMA,
        lambda uri, **_: SesionesVertex(
            project="clean-sunspot-496815-c5", location="us-east1", agent_engine_id=id_engine
        ),
    )
    return f"{ESQUEMA}://{id_engine}"
