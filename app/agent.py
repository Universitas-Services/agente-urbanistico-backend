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

from google.cloud import discoveryengine

def consulta_normativa_urbanistica(query: str) -> str:
    """Busca información legal, ordenanzas y normativas urbanísticas en la base documental (Datastore).
    
    Usa esta herramienta cuando necesites encontrar artículos específicos de leyes, 
    ordenanzas municipales o regulaciones sobre zonificación y variables urbanas.
    """
    try:
        project_id = "clean-sunspot-496815-c5"
        location = "global"
        data_store_id = "ds-derecho-urbanistico_1782317718928_gcs_store"
        
        client = discoveryengine.SearchServiceClient()
        serving_config = client.serving_config_path(
            project=project_id,
            location=location,
            data_store=data_store_id,
            serving_config="default_config",
        )
        
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=5,
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                    return_snippet=True
                ),
                extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                    max_extractive_answer_count=3,
                    max_extractive_segment_count=1
                )
            )
        )
        
        response = client.search(request)
        
        resultados = []
        for result in response.results:
            document = result.document
            
            # Extract answers
            if "extractive_answers" in document.derived_struct_data:
                for answer in document.derived_struct_data["extractive_answers"]:
                    content = answer.get("content", "")
                    if content:
                        resultados.append(f"- {content}")
                        
            # Extract segments if answers are not enough
            elif "extractive_segments" in document.derived_struct_data:
                for segment in document.derived_struct_data["extractive_segments"]:
                    content = segment.get("content", "")
                    if content:
                        resultados.append(f"- {content}")
                        
        if not resultados:
            return "Tras un análisis de la base documental, no se encontró información suficiente para responder la consulta de forma específica para este territorio o tema."
            
        return "Información recuperada de la base documental:\n\n" + "\n\n".join(resultados)
        
    except Exception as e:
        print(f"Error querying Datastore: {e}")
        return f"Error al consultar la base documental: {e}"

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