"""Workaround for ADK Gemini api_client caching on Vertex AI Agent Engine.

Reasoning Engine creates a new asyncio event loop per request. The default
Gemini model caches ``api_client`` with ``@cached_property``, binding aiohttp
to the first loop and causing ``attached to a different loop`` errors.

See: https://github.com/google/adk-python/issues/5538
"""

import os

from google.adk.models import Gemini
from google.genai import Client, types


class UncachedGemini(Gemini):
    """Gemini variant that builds a fresh genai Client on each access."""

    @property
    def api_client(self) -> Client:
        use_vertex = (
            self.model.startswith("projects/")
            or os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower()
            in {"1", "true", "yes"}
        )
        kwargs: dict = {
            "http_options": types.HttpOptions(
                headers=self._tracking_headers(),
                retry_options=self.retry_options,
                base_url=self.base_url,
            )
        }
        if use_vertex:
            kwargs["vertexai"] = True
            if project := os.environ.get("GOOGLE_CLOUD_PROJECT"):
                kwargs["project"] = project
            if location := os.environ.get("GOOGLE_CLOUD_LOCATION"):
                kwargs["location"] = location
        return Client(**kwargs)
