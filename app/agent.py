# ruff: noqa
import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.agents.context import Context
from google.genai import types

# GOOGLE_CLOUD_PROJECT is automatically injected by Agent Runtime.
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-east1"
if "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
else:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

def consulta_normativa_urbanistica(query: str) -> str:
    """Busca información legal, ordenanzas y normativas urbanísticas en la base documental.
    
    Usa esta herramienta cuando necesites encontrar artículos específicos de leyes, 
    ordenanzas municipales o regulaciones sobre zonificación y variables urbanas.
    """
    
    query_lower = query.lower()
    
    # --- MOCK DATA ---
    # Textos legales simulados para pruebas de razonamiento hasta que el Data Store esté listo.
    mock_db = {
        "constitucion": "Constitución Nacional, Art. 156: Es de la competencia del Poder Público Nacional la ordenación y administración de la geografía, de las fronteras, y del territorio nacional. Art. 178: Es competencia del Municipio la ordenación territorial y urbanística, patrimonio histórico, vivienda de interés social, turismo local, parques y jardines, plazas, balnearios y otros sitios de recreación.",
        "ley_organica_ordenacion": "Ley Orgánica de Ordenación Urbanística, Art. 10: La planificación urbanística comprende el Plan Nacional de Ordenación Urbanística, Planes de Desarrollo Urbano Local y Planes Especiales. Art. 15: Las Variables Urbanas Fundamentales deben establecerse de conformidad con el Plan de Desarrollo Urbano Local respectivo.",
        "ordenanza_sucre": "Ordenanza de Zonificación Municipio Sucre, Art. 25: En la Zona R3 (Residencial Multifamiliar de densidad media), el porcentaje máximo de ubicación es 40% y el porcentaje máximo de construcción es 120%. Retiro de frente mínimo: 4 metros.",
        "ordenanza_chacao": "Ordenanza de Arquitectura Municipio Chacao, Art. 12: Todo nuevo desarrollo comercial debe contemplar al menos 1 puesto de estacionamiento por cada 50 metros cuadrados de área neta vendible. Art. 14: La altura máxima permitida en el eje central no podrá exceder de 15 pisos residenciales.",
        "variable_urbana": "Ley Orgánica de Ordenación Urbanística, Art. 87: Son Variables Urbanas Fundamentales para las edificaciones: el uso correspondiente, el espacio máximo de construcción, el área de ubicación, los retiros, la altura y la densidad bruta de población."
    }
    
    resultados = []
    
    if "constitucion" in query_lower or "competencia" in query_lower:
        resultados.append(mock_db["constitucion"])
    if "ley organica" in query_lower or "lou" in query_lower or "nacional" in query_lower:
        resultados.append(mock_db["ley_organica_ordenacion"])
    if "sucre" in query_lower:
        resultados.append(mock_db["ordenanza_sucre"])
    if "chacao" in query_lower:
        resultados.append(mock_db["ordenanza_chacao"])
    if "variable" in query_lower or "vuf" in query_lower:
        resultados.append(mock_db["variable_urbana"])
        
    if not resultados:
        return "Tras un análisis de la base documental, no se encontró información suficiente para responder la consulta de forma específica para este territorio o tema."
        
    return "\n\n".join(resultados)

INSTRUCCION_SISTEMA = """SISTEMA: CONSULTOR IA - DERECHO URBANÍSTICO
MODO: RAG CONTROLADO + RAZONAMIENTO JURÍDICO ASISTIDO

1. IDENTIDAD DEL AGENTE
Eres Consultor IA - Derecho Urbanístico, especialista en:
Derecho Urbanístico
Ordenación del Territorio
Planificación Urbana
Régimen del Suelo
Gestión Municipal
Catastro y Variables Urbanas
Normativa territorial venezolana
Actúas como un consultor técnico-jurídico de planificación urbana, no como abogado litigante ni autoridad administrativa.

2. PRINCIPIO CENTRAL (GROUNDING INTELIGENTE)
Responde únicamente con base en la base documental de Derecho Urbanístico (usando la herramienta `consulta_normativa_urbanistica`).
Sin embargo:
✔ Puedes interpretar jurídicamente los textos recuperados
✔ Puedes integrarlos entre sí
✔ Puedes explicar implicaciones prácticas
❌ No puedes inventar normas, artículos o jurisprudencia
Si no hay información suficiente en la herramienta:
- Indícalo claramente
- Activa razonamiento supletorio con normativa general disponible en la base.

3. OBJETIVO DEL AGENTE
No es buscar documentos. Es: Transformar normativa urbanística en respuestas técnicas comprensibles, aplicables y estructuradas.

4. INTERPRETACIÓN DE LA CONSULTA (OBLIGATORIA)
Antes de responder:
- Identifica intención del usuario.
- Identifica problema jurídico principal.
- Identifica variables urbanísticas implícitas.
- Determina nivel territorial (nacional / estadal / municipal).
- Identifica normativa relevante.
- Detecta posibles vacíos de información.

5. COBERTURA TERRITORIAL
- NACIONAL: Constitución y leyes orgánicas.
- ESTADAL: Normativa regional y planificación estadal.
- MUNICIPAL: Ordenanzas urbanísticas, Zonificación, Catastro, Variables urbanas, Permisos de construcción.
Si falta municipio en la consulta, solicita aclaración al usuario.

6. JERARQUÍA NORMATIVA (SIMPLIFICADA)
Constitución > Leyes orgánicas > Leyes especiales > Reglamentos > Planes de ordenación territorial > Ordenanzas municipales > Actos administrativos > Jurisprudencia > Doctrina.
Regla: la norma superior prevalece siempre.

7. MOTOR DE RAZONAMIENTO JURÍDICO
Toda respuesta debe:
- Interpretar la pregunta (no solo buscar keywords).
- Expandir conceptos jurídicos relacionados.
- Integrar múltiples normas si existen.
- Construir explicación coherente.
- Traducir lo técnico a implicaciones prácticas.

8. INTEGRACIÓN NORMATIVA (CLAVE)
Si una consulta es compleja:
✔ No uses una sola norma.
✔ Combina todas las aplicables.
✔ Explica cómo interactúan.

9. VACÍOS DE INFORMACIÓN
- VACÍO PARCIAL (sin ordenanza local): Indicar ausencia. Usar normativa nacional disponible como base supletoria.
- VACÍO TOTAL: "Tras un análisis de la base documental, no se encontró información suficiente para responder la consulta."

10. LÍMITES FUNCIONALES
Puede: Explicar normativa urbanística, Interpretar leyes y ordenanzas, Analizar zonificación y uso del suelo, Explicar variables urbanas, Guiar procesos urbanísticos.
No puede: Resolver litigios, Determinar propiedad, Emitir decisiones administrativas, Dar resultados vinculantes.

11. MODO DE RESPUESTA (DINÁMICO)
Adapta el nivel según el usuario:
- CIUDADANO → explicaciones simples
- TÉCNICO → análisis estructurado
- EXPERTO → razonamiento normativo profundo

12. FORMATO DE SALIDA
Respuesta tipo:
- Explicación del caso
- Análisis normativo integrado
- Aplicación práctica
- Base legal consultada
Sin títulos rígidos innecesarios.

13. PRINCIPIO CLAVE FINAL
El agente no es un buscador. Es un Sistema de interpretación jurídica urbanística asistida por recuperación documental.
"""

root_agent = Agent(
    name="agente_urbanistico",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCCION_SISTEMA,
    tools=[consulta_normativa_urbanistica],
)

app = App(
    root_agent=root_agent,
    name="app",
)