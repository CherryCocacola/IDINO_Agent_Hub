"""
Vector store integration package.

Provides the ``QdrantService`` wrapper for interacting with the Qdrant
vector database, including collection management, hybrid search, and
CRUD operations on vector points.
"""

from app.integrations.vector_store.qdrant_client import QdrantService

__all__ = ["QdrantService"]
