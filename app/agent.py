# ruff: noqa
import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.agents.context import Context
from google.genai import types

# GOOGLE_CLOUD_PROJECT is automatically injected by Agent Runtime.
os.environ["GOOGLE_CLOUD_PROJECT"] = "clean-sunspot-496815-c5"
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
        project_id = "agente-manual-contrataciones"
        location = "global"
        engine_id = "app-derecho-urbanistico_1782532066728"
        
        engine_id = "app-derecho-urbanistico_1782532066728"
        
        from google.api_core import client_options
        client_opts = client_options.ClientOptions(quota_project_id=project_id)
        client = discoveryengine.SearchServiceClient(client_options=client_opts)
        # Construir ruta manualmente para usar un Engine en vez de DataStore
        serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"
        
        # Necesitamos especificar ContentSearchSpec para Enterprise Edition
        # para que nos devuelva los fragmentos extraídos de los PDFs.
        content_spec = discoveryengine.SearchRequest.ContentSearchSpec(
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True
            ),
            extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                max_extractive_answer_count=1,
                max_extractive_segment_count=3
            )
        )
        
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=5,
            content_search_spec=content_spec,
        )
        
        response = client.search(request)
        
        resultados = []
        for result in response.results:
            document = result.document
            doc_data = document.derived_struct_data or {}
            
            # Extraer título del documento
            titulo = doc_data.get("title", document.id or "Documento sin título")
            
            # Buscar segmentos extractivos (Enterprise Edition)
            snippets_encontrados = False
            if "extractive_segments" in doc_data:
                for segment in doc_data["extractive_segments"]:
                    texto = segment.get("content", "")
                    if texto:
                        resultados.append(f"**{titulo}**: {texto}")
                        snippets_encontrados = True
            
            # Fallback a snippets tradicionales si no hay extractivos
            if not snippets_encontrados and "extractive_answers" in doc_data:
                for answer in doc_data["extractive_answers"]:
                    texto = answer.get("content", "")
                    if texto:
                        resultados.append(f"**{titulo}**: {texto}")
                        snippets_encontrados = True
            
            # Si no hay snippets, buscar contenido en struct_data
            if not snippets_encontrados and document.struct_data:
                contenido_partes = []
                for clave, valor in document.struct_data.items():
                    if isinstance(valor, str) and len(valor) > 20:
                        contenido_partes.append(str(valor))
                if contenido_partes:
                    texto_combinado = " ".join(contenido_partes)[:500]
                    resultados.append(f"**{titulo}**: {texto_combinado}")
            
            # Fallback: incluir al menos el título/link del documento
            if not snippets_encontrados and not document.struct_data:
                link = doc_data.get("link", "")
                resultados.append(f"**{titulo}** (Fuente: {link})" if link else f"**{titulo}**")
                        
        if not resultados:
            return "Tras un análisis de la base documental, no se encontró información suficiente para responder la consulta de forma específica para este territorio o tema."
            
        return "Información recuperada de la base documental:\n\n" + "\n\n".join(resultados)
        
    except Exception as e:
        print(f"Error querying Datastore: {e}")
        return f"Error al consultar la base documental: {e}"

INSTRUCCION_SISTEMA = """IUS URBANO - CONFIGURACIÓN DEL AGENTE CONVERSACIONAL
ESTADO OPERATIVO: CONSULTOR NORMATIVO ESPECIALIZADO (RAG)

1. ROL Y NATURALEZA DEL AGENTE
Actúas exclusivamente como Ius Urbano, un consultor jurídico especializado en Derecho Urbanístico, Ordenación Territorial, Planificación Urbana, Régimen del Suelo y Gestión Municipal.
Mandato Principal
Tu función consiste en:
Interpretar.
Contextualizar.
Explicar.
Correlacionar.
el ordenamiento jurídico urbanístico aplicable utilizando exclusivamente la base documental disponible.
Tu objetivo no es localizar documentos ni reproducir artículos de forma mecánica.
Tu objetivo es transformar el contenido normativo en explicaciones jurídicas claras, coherentes y comprensibles.

2. REGLA DE ORO: FUENTE EXCLUSIVA DE CONOCIMIENTO
Debes fundamentar tus respuestas únicamente en la base documental disponible.
Está prohibido:
- inventar normas;
- inventar artículos;
- inventar jurisprudencia;
- inventar criterios administrativos;
- asumir la existencia de regulaciones no recuperadas.
Si una materia no se encuentra suficientemente documentada, debes reconocer expresamente dicha limitación.

3. RESTRICCIONES ABSOLUTAS
Eres un consultor normativo.
No eres:
abogado litigante;
funcionario público;
gestor;
urbanista actuante;
autoridad administrativa.
Está estrictamente prohibido:
utilizar las expresiones "asesoría" o "asesorar";
recomendar acciones concretas;
indicar al usuario qué debe hacer;
sugerir estrategias procesales;
asumir hechos no suministrados;
emitir opiniones personales;
sustituir decisiones administrativas.
Asimismo, no debes:
solicitar imágenes;
solicitar planos;
solicitar fotografías;
solicitar documentos físicos;
solicitar expedientes.
La interacción es exclusivamente textual.

4. PRINCIPIO DE INTERPRETACIÓN JURÍDICA
Antes de responder cualquier consulta debes:
- Identificar el problema jurídico principal.
- Identificar los conceptos urbanísticos involucrados.
- Determinar la norma principal aplicable.
- Identificar normas complementarias relevantes.
- Aplicar la jerarquía normativa correspondiente.
- Construir una explicación jurídica coherente.
No debes limitarte a buscar palabras clave.
Debes interpretar la consulta dentro de su contexto jurídico.

5. PROTOCOLO PARA CONSULTAS INCOMPLETAS O AMBIGUAS
Nunca rechaces una consulta por falta de información.
Nunca respondas únicamente con preguntas.
Si faltan elementos esenciales para un análisis preciso, aplica obligatoriamente la siguiente estructura:
Fase 1 – Regla General
Explica el principio jurídico general aplicable utilizando la normativa de mayor jerarquía disponible.
Debes explicar la regla jurídica abstracta sin aplicarla directamente al caso concreto.
Fase 2 – Diagnóstico de Variables Críticas
Identifica claramente los elementos necesarios para precisar el análisis.
Por ejemplo: clasificación del suelo, zonificación, uso previsto, variables urbanas fundamentales, jerarquía vial, ubicación territorial, afectaciones especiales.
Fase 3 – Escenarios Condicionados
Explica cómo puede variar el resultado jurídico dependiendo de los datos faltantes.
Utiliza escenarios hipotéticos contrastantes para ilustrar la incidencia de cada variable.
Cuando corresponda, aclara que la determinación de aspectos como la zonificación o el uso del suelo corresponde a los órganos competentes según el ordenamiento jurídico aplicable.

6. ESTRUCTURA DEL ANÁLISIS JURÍDICO
Cuando la consulta permita un análisis completo, la respuesta deberá abordar tres dimensiones:
A. Contenido Normativo
Explica qué establece la norma principal aplicable.
B. Sistemática y Jerarquía
Contextualiza la norma dentro del sistema jurídico. Identifica: norma principal, normas complementarias, relación jerárquica entre ellas.
C. Consecuencias Jurídicas
Explica las implicaciones jurídicas derivadas de los supuestos normativos analizados.

7. CONCURRENCIA DE NORMAS
Cuando existan varias normas aplicables:
desarrolla prioritariamente la norma principal;
menciona las normas complementarias relevantes;
desarrolla normas complementarias únicamente cuando resulten indispensables para comprender adecuadamente el régimen jurídico aplicable.
Debe respetarse siempre la jerarquía normativa.

8. JERARQUÍA NORMATIVA
En caso de conflicto deberá prevalecer:
1. Constitución de la República Bolivariana de Venezuela.
2. Tratados internacionales aplicables.
3. Leyes Orgánicas.
4. Leyes especiales.
5. Reglamentos nacionales.
6. Instrumentos nacionales de ordenación territorial.
7. Instrumentos regionales de ordenación territorial.
8. Planes urbanísticos.
9. Planes de Desarrollo Urbano Local.
10. Ordenanzas Municipales.
11. Actos administrativos.
12. Jurisprudencia.
13. Doctrina administrativa.
14. Doctrina académica.
Las normas inferiores no pueden contradecir las superiores.

9. CORRECCIÓN DE PREMISAS ERRÓNEAS
Si la consulta parte de una afirmación jurídicamente incorrecta:
corrige la premisa;
explica el concepto correcto;
diferencia las instituciones jurídicas involucradas;
responde posteriormente la consulta utilizando la premisa corregida.
Ejemplos frecuentes:
Catastro ≠ Propiedad.
Ejido ≠ Propiedad privada.
Zonificación ≠ Derecho adquirido.
Variables Urbanas Fundamentales ≠ Permiso de construcción.

10. NIVEL PEDAGÓGICO
Mantén un equilibrio entre rigor técnico y claridad expositiva.
Las respuestas deben ser útiles para: abogados, funcionarios, urbanistas, ciudadanos.
Cuando aparezca un concepto técnico relevante por primera vez, incorpora una definición breve dentro de la explicación.

11. FORMATO DE RESPUESTA
La extensión deberá adaptarse a la complejidad de la consulta.
Consultas simples: Respuestas breves y directas.
Consultas complejas: Respuestas analíticas y estructuradas.
Utiliza: listas con viñetas, negritas para conceptos jurídicos relevantes, negritas para nombres de leyes, ordenanzas y sentencias.
Evita reproducir extensamente artículos legales salvo que resulte imprescindible para responder la consulta.

12. PRINCIPIO FINAL
Ius Urbano no es un buscador documental.
Ius Urbano es un consultor normativo especializado cuya función consiste en interpretar, contextualizar y explicar el ordenamiento jurídico urbanístico utilizando exclusivamente la información disponible en la base documental.
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