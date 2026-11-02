"""Filtros deterministas sobre el texto que el modelo devuelve, antes de que llegue al usuario.

ADK se detiene en el primer after_model_callback que devuelve una respuesta, así que todos
los filtros de salida van en este único callback.
"""
import re

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

from app.citas import quitar_rutas_internas
from app.privacidad import tapar_datos_personales

# "[Altura máxima actual, ej. PB+2 o 8m]" -> "[Altura máxima actual]". En los borradores
# (sección 11 F) los corchetes marcan el dato que falta; un ejemplo ahí induce al usuario a
# copiar datos que nadie verificó.
_EJEMPLO_EN_CORCHETES = re.compile(
    r"\[([^\[\]]*?)[\s,:;(]*(?:p\.\s?ej\.|ej\.|por ejemplo)[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]",
    re.IGNORECASE,
)


def quitar_ejemplos_en_corchetes(texto: str) -> str:
    return _EJEMPLO_EN_CORCHETES.sub(
        lambda m: f"[{m.group(1)}]" if m.group(1).strip() else m.group(0), texto
    )


def filtrar_salida(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> LlmResponse | None:
    cambio = False
    for part in (llm_response.content.parts if llm_response.content else None) or []:
        if part.text:
            filtrado = quitar_ejemplos_en_corchetes(
                quitar_rutas_internas(tapar_datos_personales(part.text))
            )
            if filtrado != part.text:
                part.text = filtrado
                cambio = True
    return llm_response if cambio else None
