"""Quita de las respuestas las etiquetas internas con que la búsqueda identifica los fragmentos.

La herramienta antepone "[carpeta] nombre_de_archivo" a cada fragmento para que el modelo
verifique de qué municipio o instrumento proviene (sección 2 A). A veces el modelo copia esa
etiqueta al citar, lo que expone la estructura de la biblioteca y no le sirve al usuario.
"""
import re

_CARPETAS = (
    "doctrina|legislacion|ordenanzas|sentencias|sentencias-internacionales"
    "|instrumentos-internacionales"
)
# "[sentencias] sentencia_tsj_sc_847_2017_exp_16-0660_aclaratoria_1080", con o sin el archivo.
_ETIQUETA = re.compile(rf"\s*\[(?:{_CARPETAS})\](?:\s*[\w\-]+)?", re.IGNORECASE)
# Nombre de archivo suelto: minúsculas unidas por al menos tres guiones bajos.
_ARCHIVO = re.compile(r"\s*`?\b[a-z0-9]+(?:_[a-z0-9\-]+){3,}\b`?")
# Paréntesis o corchetes que quedaron vacíos, con o sin "fuente:" / "ver".
_VACIOS = re.compile(r"\s*[(\[]\s*(?:(?:fuente|fuentes|ver|seg[uú]n)\s*:?\s*)?[;,]?\s*[)\]]", re.IGNORECASE)
_ESPACIO_ANTES_DE_SIGNO = re.compile(r"[ \t]+([.,;:])")
# Separadores que quedaron sin nada entre ellos: "Fuentes:;" -> "Fuentes:".
_SEPARADORES_HUERFANOS = re.compile(r"([:;,])[;,]+|[;,]+$", re.MULTILINE)
# Formato Markdown que envolvía la etiqueta y quedó vacío: "**[legislacion]**" -> "****".
_FORMATO_VACIO = re.compile(r"(\*\*|`)\s*\1[ \t]*")


def quitar_rutas_internas(texto: str) -> str:
    limpio = _ETIQUETA.sub("", texto)
    limpio = _ARCHIVO.sub("", limpio)
    if limpio == texto:
        return texto
    limpio = _VACIOS.sub("", limpio)
    limpio = _FORMATO_VACIO.sub("", limpio)
    limpio = _ESPACIO_ANTES_DE_SIGNO.sub(r"\1", limpio)
    return _SEPARADORES_HUERFANOS.sub(r"\1", limpio)
