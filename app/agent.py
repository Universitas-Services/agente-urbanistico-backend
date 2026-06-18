# ruff: noqa
import os
import google.auth
from google.cloud import discoveryengine_v1 as discoveryengine
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

# Captura dinámica del proyecto de CÓMPUTO (donde corre Agent Runtime)
try:
    _, project_id = google.auth.default()
    if project_id:
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception:
    pass # Ignoramos errores de auth durante el Cloud Build
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-east1"
if "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
else:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

def consulta_normativa_urbanistica(query: str) -> str:
    """Busca información legal, ordenanzas y normativas urbanísticas en la biblioteca matriz."""
    
    # Configuración cruzada: Apuntamos estrictamente al proyecto del DATA STORE
    target_project_id = "ID_PROYECTO_DATA_STORE" # <-- Reemplazar por el ID del proyecto que tiene los documentos
    location = "global"
    data_store_id = "ID_DATA_STORE_URBANISTICO" # <-- Reemplazar por el ID de tu Data Store
    
    try:
        client = discoveryengine.SearchServiceClient()
        serving_config = client.serving_config_path(
            project=target_project_id, # Usamos el target_project_id, NO el project_id local
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

# Instrucciones blindadas (Se mantienen igual)
INSTRUCCION_SISTEMA = """Eres un Asistente Legal experto en derecho urbanístico de Universitas.
Tu objetivo es resolver dudas normativas, de zonificación y ordenanzas de forma clara y precisa, utilizando exclusivamente la información de la biblioteca legal proporcionada.

Reglas de interacción:
1. Mantén un tono profesional, accesible y corporativo.
2. Si la información no está en los documentos proporcionados, indica que no tienes acceso a esa normativa específica; no inventes respuestas.
3. Bajo ninguna circunstancia menciones nombres de herramientas técnicas internas (como "API", "Discovery Engine", "Data Store" o "consulta_normativa_urbanistica"). Tus respuestas deben ser completamente naturales.
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