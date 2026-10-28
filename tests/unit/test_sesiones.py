import asyncio

import pytest
from google.adk.cli.service_registry import get_service_registry
from google.adk.sessions import VertexAiSessionService

from app.sesiones import SESION_TTL, SesionesVertex, session_service_uri

APP_URL = (
    "https://us-east1-aiplatform.googleapis.com/reasoningEngines/v1/projects/529295899189"
    "/locations/us-east1/reasoningEngines/2958970508298682368/api"
)


@pytest.mark.parametrize("app_url", [None, "", "https://us-east1-aiplatform.googleapis.com/reasoningEngines"])
def test_sin_engine_id_usa_memoria(monkeypatch: pytest.MonkeyPatch, app_url: str | None) -> None:
    if app_url is None:
        monkeypatch.delenv("APP_URL", raising=False)
    else:
        monkeypatch.setenv("APP_URL", app_url)
    assert session_service_uri() is None


def test_con_engine_id_usa_sesiones_gestionadas(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_URL", APP_URL)
    uri = session_service_uri()
    servicio = get_service_registry().create_session_service(uri)
    assert isinstance(servicio, SesionesVertex)
    assert servicio._agent_engine_id == "2958970508298682368"
    assert servicio._location == "us-east1"


def test_crear_sesion_aplica_vigencia_de_7_dias(monkeypatch: pytest.MonkeyPatch) -> None:
    recibido = {}

    async def falso_create(self, **kwargs):
        recibido.update(kwargs)

    monkeypatch.setattr(VertexAiSessionService, "create_session", falso_create)
    servicio = SesionesVertex(project="p", location="us-east1", agent_engine_id="123")
    asyncio.run(servicio.create_session(app_name="a", user_id="u"))
    assert recibido["ttl"] == SESION_TTL == "604800s"
