"""Filtro para referencias a mensajes anteriores cuando la conversación no tiene historial.

Sin historial, "haz énfasis en el punto 4" no tiene a qué referirse y el modelo tiende a
explicar la sección 4 de sus propias instrucciones. Este filtro responde pidiendo el texto
sin llamar al modelo. La regla equivalente del prompt (sección 1) cubre las frases que el
filtro no detecta.
"""
import re

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

TEXTO_ACLARACION = (
    "No tengo a la vista el mensaje anterior al que te refieres. ¿Podrías copiar el texto "
    "de ese punto o indicarme el tema sobre el que deseas profundizar?"
)

_REFERENCIA_PREVIA = re.compile(
    r"\b(punto|numeral|paso|inciso|[ií]tem|opci[oó]n)\s*(n[°º.]?\s*)?\d+\b"
    r"|\blo anterior\b"
    r"|\blo de arriba\b"
    r"|\b(mensaje|respuesta) anterior\b"
    r"|\btu (última |ultima )?respuesta\b"
    r"|\blo que (me )?(dijiste|mencionaste|explicaste|respondiste)\b",
    re.IGNORECASE,
)

# Si el mensaje nombra una norma o pregunta por las instrucciones, decide el modelo:
# "el punto 4 del artículo 87" es una consulta válida y la sección 12 cubre la extracción.
_EXCLUSIONES = re.compile(
    r"art[ií]culo|\bart\.|\bley\b|ordenanza|decreto|reglamento|gaceta|constituci[oó]n"
    r"|resoluci[oó]n|acuerdo|\bpdul\b|\bplan\b|\bloou\b|\blopa\b|norma"
    r"|instrucci|prompt|regla|configuraci|sistema",
    re.IGNORECASE,
)


def es_referencia_sin_contexto(texto: str) -> bool:
    return bool(_REFERENCIA_PREVIA.search(texto)) and not _EXCLUSIONES.search(texto)


def filtrar_referencia_sin_historial(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    contenidos = llm_request.contents or []
    # Con cualquier turno previo del modelo (respuesta o llamada a herramienta) decide el modelo.
    if not contenidos or any(c.role == "model" for c in contenidos):
        return None
    texto = "".join(p.text or "" for p in (contenidos[-1].parts or []))
    if not es_referencia_sin_contexto(texto):
        return None
    return LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text=TEXTO_ACLARACION)])
    )
