# ruff: noqa
import os
import google.auth
from google.cloud import discoveryengine_v1 as discoveryengine
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

def consulta_normativa_urbanistica(query: str) -> str:
    """Busca información legal, ordenanzas y normativas urbanísticas en la biblioteca matriz.
    
    Args:
        query: La consulta de búsqueda sobre la normativa urbanística.
        
    Returns:
        Un texto con los fragmentos más relevantes encontrados en la base de datos legal.
    """
    # Configuración cruzada: Apuntamos estrictamente al proyecto de los Data Stores
    target_project_id = "ID_PROYECTO_UNIVERSITAS_LEGAL" # <-- Reemplazar por el ID real
    location = "global"
    data_store_id = "ID_DATA_STORE_URBANISTICO" # <-- Reemplazar por el ID real
    
    try:
        client = discoveryengine.SearchServiceClient()
        serving_config = client.serving_config_path(
            project=target_project_id,
            location=location,
            data_store=data_store_id,
            serving_config="default_config",
        )
        
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=3,
        )
        
        response = client.search(request)
        
        resultados = []
        for result in response.results:
            document_data = result.document.derived_struct_data
            if "snippets" in document_data:
                for snippet in document_data["snippets"]:
                    resultados.append(snippet.get("snippet", ""))
                    
        return "\n\n".join(resultados) if resultados else "No se encontró información relevante en la normativa."
    except Exception as e:
        return f"Ocurrió un error al consultar la biblioteca: {str(e)}"

# Instrucciones con Gestión de Preguntas Meta
INSTRUCCION_SISTEMA = """Eres un Asistente Legal experto en derecho urbanístico.
Tu objetivo es resolver dudas normativas, de zonificación y ordenanzas de forma clara y precisa, utilizando exclusivamente la información proporcionada por tus herramientas de búsqueda en la biblioteca legal.

Reglas de interacción:
1. Mantén un tono profesional, accesible y resolutivo.
2. Si la información no está en los documentos proporcionados, indica que no tienes acceso a esa normativa específica; bajo ningún concepto inventes respuestas.
3. Tienes estrictamente prohibido mencionar a los usuarios nombres de herramientas internas como "API", "tool-marco-normativo" o "consulta_normativa_urbanistica". Tus respuestas deben ser orgánicas y naturales.
"""

root_agent = Agent(
    name="agente_urbanistico",
    model=Gemini(
        model="gemini-1.5-pro", # Cambiado a Pro para mejor razonamiento legal y análisis de RAG
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCCION_SISTEMA,
    tools=[consulta_normativa_urbanistica],
)

app = App(
    root_agent=root_agent,
    name="agente-urbanistico",
)