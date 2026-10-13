# Sincronización de la base de conocimiento

Mantiene el Data Store `ds-urbanismo-kb` (Vertex AI Search, proyecto `agente-manual-contrataciones`)
alineado con las carpetas publicadas del bucket `derecho-urbanistico-prueba`.

El backend del admin mueve los PDFs entre `urbanismo/pendientes/`, las carpetas macro y
`urbanismo/ocultos/`, pero no avisa a Vertex AI Search. Este job corre cada hora y:

| Situación | Acción |
|---|---|
| PDF en una carpeta macro que no está en el índice (aprobado) | Se importa (OCR, se cobra una sola vez) |
| Documento en el índice que ya no está en el bucket (ocultado/rechazado) | Se borra del índice |
| Sin cambios | Nada |

Carpetas indexadas: `legislacion`, `ordenanzas`, `instrumentos-internacionales`, `sentencias`,
`sentencias-internacionales`, `doctrina`. `pendientes/` y `ocultos/` nunca se indexan.

## Límites de seguridad

Si una ejecución supera alguno de estos límites, no hace nada y termina con código 2
(la ejecución del Cloud Run Job queda como fallida y visible en la consola):

| Variable | Default | Protege contra |
|---|---|---|
| `MAX_NEW_DOCS` | 50 | Cargas masivas inesperadas |
| `MAX_NEW_PAGES` | 3000 | Costo de OCR (~$4.50 por ejecución como máximo) |
| `MAX_DELETE_RATIO` | 0.2 | Borrar más del 20% del índice por error |

También aborta si el bucket aparece vacío y el índice no (permisos o configuración rotos).

## Uso

```bash
pip install -r sync/requirements.txt
python -m sync.main --dry-run   # muestra el plan sin modificar nada
python -m sync.main             # ejecuta
```

Configuración por variables de entorno: `PROJECT_ID`, `BUCKET`, `ROOT_FOLDER`, `DATA_STORE_ID`,
`MAX_NEW_DOCS`, `MAX_NEW_PAGES`, `MAX_DELETE_RATIO`, `DRY_RUN`.

## Limitación conocida

Un PDF reemplazado con el mismo nombre no se vuelve a indexar. El backend siempre genera nombres
nuevos (`{hash}-{archivo}.pdf`) al subir o corregir, así que en el flujo normal no ocurre.
