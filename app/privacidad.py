"""Filtro que tapa datos personales en las respuestas del agente.

Al redactar el documento formal de propuesta (sección 11 F), el modelo a veces copia la
cédula o el teléfono que el usuario escribió, aunque el prompt lo prohíbe. Este filtro los
reemplaza por el campo en blanco correspondiente antes de que la respuesta salga.
"""
import re

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

# El RIF va antes que la cédula: "V-12345678-9" también encaja como cédula.
_PATRONES = [
    (re.compile(r"(?<![\w.-])[JGVEPC]-?\d{8}-?\d(?![\d.])", re.IGNORECASE), "[RIF o registro]"),
    (
        re.compile(
            r"(?<![\w.-])(?:[VE]\s?-?\s?\d{1,2}\.?\d{3}\.?\d{3}"
            r"|(?<=C\.I\. )\d{1,2}\.?\d{3}\.?\d{3}|(?<=C\.I\.: )\d{1,2}\.?\d{3}\.?\d{3})(?![\d.])",
            re.IGNORECASE,
        ),
        "[Cédula de identidad]",
    ),
    (
        re.compile(
            r"(?:\+58[\s.-]?\(?0?|(?<![\w.])\(?0)[24]\d{2}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}(?![\d.])"
        ),
        "[Teléfono]",
    ),
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[Correo]"),
]
_CAMPOS = "|".join(re.escape(campo) for _, campo in _PATRONES)
# Si el modelo ya había puesto el dato entre corchetes, "[[Teléfono]]" queda "[Teléfono]".
_CORCHETES_DOBLES = re.compile(rf"\[\s*({_CAMPOS})\s*\]")


def tapar_datos_personales(texto: str) -> str:
    for patron, campo in _PATRONES:
        texto = patron.sub(campo, texto)
    return _CORCHETES_DOBLES.sub(r"\1", texto)


def filtrar_datos_personales(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> LlmResponse | None:
    cambio = False
    for part in (llm_response.content.parts if llm_response.content else None) or []:
        if part.text:
            tapado = tapar_datos_personales(part.text)
            if tapado != part.text:
                part.text = tapado
                cambio = True
    return llm_response if cambio else None
