import pytest
from google.adk.models import LlmResponse
from google.genai import types

from app.salida import filtrar_salida, quitar_ejemplos_en_corchetes


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ('[Nombre del sector en Tamaca, por ejemplo, sector "La Mora"]', "[Nombre del sector en Tamaca]"),
        ("[Altura máxima actual en la zona, ej. PB+2 o 8m]", "[Altura máxima actual en la zona]"),
        ("[Establecer propuesta (p. ej. 3,00 metros)]", "[Establecer propuesta]"),
        ("[Describir el estado del terreno: por ejemplo, sin uso definido]", "[Describir el estado del terreno]"),
        ("Altura: [actual, ej. PB+2] → PB+4", "Altura: [actual] → PB+4"),
        ("[Establecer una densidad coherente, ej. [X] hab/ha o [Y] viv/ha].", "[Establecer una densidad coherente]."),
    ],
)
def test_quita_ejemplos_en_corchetes(texto: str, esperado: str) -> None:
    assert quitar_ejemplos_en_corchetes(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "[densidad propuesta] y [Fundamento normativo, opcional]",
        "Por ejemplo, un semáforo en Tamaca: parroquia Tamaca.",
        "[ej. 300 hab/ha]",
    ],
)
def test_corchetes_sin_ejemplo_quedan_igual(texto: str) -> None:
    assert quitar_ejemplos_en_corchetes(texto) == texto


def _respuesta(texto: str) -> LlmResponse:
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=texto)]))


def test_aplica_ambos_filtros() -> None:
    respuesta = filtrar_salida(
        None,
        _respuesta("Proponente: Pedro Pérez, V-12.345.678 [doctrina] dictamen_avivir_estado_lara_x."),
    )
    assert respuesta is not None
    assert respuesta.content.parts[0].text == "Proponente: Pedro Pérez, [Cédula de identidad]."


def test_sin_cambios_devuelve_none() -> None:
    assert filtrar_salida(None, _respuesta("El PDUL fija directrices.")) is None


def test_ignora_llamadas_a_herramientas() -> None:
    llamada = types.Content(
        role="model",
        parts=[types.Part(function_call=types.FunctionCall(name="consulta", args={"query": "x"}))],
    )
    assert filtrar_salida(None, LlmResponse(content=llamada)) is None
