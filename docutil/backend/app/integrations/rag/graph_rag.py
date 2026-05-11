"""
Graph RAG - Knowledge graph-aware retrieval.

Builds entity-relationship graphs from document chunks and uses
graph traversal for multi-hop reasoning queries.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.integrations.llm.factory import create_llm_client
from app.integrations.llm.prompts import GRAPH_RAG_ENTITY_PROMPT

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class Entity:
    """A named entity extracted from text."""

    name: str
    entity_type: str = "unknown"
    mentions: int = 1
    chunk_ids: list[str] = field(default_factory=list)


@dataclass
class Relationship:
    """A relationship between two entities."""

    subject: str
    predicate: str
    object: str
    source_chunk_id: str = ""
    confidence: float = 1.0


class KnowledgeGraph:
    """In-memory knowledge graph built from document chunks."""

    def __init__(self):
        self.entities: dict[str, Entity] = {}
        self.relationships: list[Relationship] = []
        self._adjacency: dict[str, list[Relationship]] = {}

    def add_entity(self, name: str, entity_type: str = "unknown", chunk_id: str = "") -> None:
        key = name.lower().strip()
        if key in self.entities:
            self.entities[key].mentions += 1
            if chunk_id:
                self.entities[key].chunk_ids.append(chunk_id)
        else:
            self.entities[key] = Entity(
                name=name,
                entity_type=entity_type,
                chunk_ids=[chunk_id] if chunk_id else [],
            )

    def add_relationship(self, rel: Relationship) -> None:
        self.relationships.append(rel)
        subj_key = rel.subject.lower().strip()
        if subj_key not in self._adjacency:
            self._adjacency[subj_key] = []
        self._adjacency[subj_key].append(rel)

    def get_related_entities(self, entity_name: str, max_hops: int = 2) -> list[str]:
        """BFS traversal to find related entities within N hops."""
        key = entity_name.lower().strip()
        visited = {key}
        queue = [(key, 0)]
        related = []

        while queue:
            current, depth = queue.pop(0)
            if depth >= max_hops:
                continue
            for rel in self._adjacency.get(current, []):
                obj_key = rel.object.lower().strip()
                if obj_key not in visited:
                    visited.add(obj_key)
                    related.append(rel.object)
                    queue.append((obj_key, depth + 1))

        return related

    def get_entity_chunk_ids(self, entity_names: list[str]) -> list[str]:
        """Get all chunk IDs associated with a set of entities."""
        chunk_ids = set()
        for name in entity_names:
            key = name.lower().strip()
            if key in self.entities:
                chunk_ids.update(self.entities[key].chunk_ids)
        return list(chunk_ids)


class GraphRAGEngine:
    """Graph RAG engine that extracts entities and uses graph traversal."""

    def __init__(self):
        # Phase 7 — R2 완전 보강: ``OpenAIClient()`` 직접 호출(anti-patterns.md §1 위반) 제거.
        # ``create_llm_client("chat")`` 가 AgentHubLLMWrapper 를 반환하므로 모든 entity 추출
        # 호출은 AgentHub Gateway 로 위임된다. AgentCode 는 ``docutil-rag-chat`` 자동 매핑.
        self._llm = create_llm_client("chat")
        self._graphs: dict[str, KnowledgeGraph] = {}

    async def build_graph_from_chunks(
        self,
        org_id: str,
        chunks: list[dict],
    ) -> KnowledgeGraph:
        """Extract entities and relationships from chunks to build a knowledge graph."""
        graph = KnowledgeGraph()

        for chunk in chunks:
            chunk_id = chunk.get("id", "")
            content = chunk.get("content", "")
            if not content or len(content) < 50:
                continue

            try:
                prompt = GRAPH_RAG_ENTITY_PROMPT.format(content=content[:2000])
                response = await self._llm.generate(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=1000,
                )
                triples = json.loads(response)

                for triple in triples:
                    if len(triple) >= 3:
                        subject, predicate, obj = triple[0], triple[1], triple[2]
                        graph.add_entity(subject, chunk_id=chunk_id)
                        graph.add_entity(obj, chunk_id=chunk_id)
                        graph.add_relationship(
                            Relationship(
                                subject=subject,
                                predicate=predicate,
                                object=obj,
                                source_chunk_id=chunk_id,
                            )
                        )
            except (json.JSONDecodeError, Exception) as exc:
                logger.debug("Entity extraction failed for chunk %s: %s", chunk_id, exc)
                continue

        self._graphs[org_id] = graph
        return graph

    async def graph_enhanced_retrieval(
        self,
        query: str,
        org_id: str,
        chunks: list[dict],
        max_hops: int = 2,
    ) -> list[dict]:
        """Enhance retrieval by finding graph-connected chunks."""
        # Build graph if not cached
        if org_id not in self._graphs:
            await self.build_graph_from_chunks(org_id, chunks)

        graph = self._graphs[org_id]

        # Extract entities from query
        try:
            prompt = GRAPH_RAG_ENTITY_PROMPT.format(content=query)
            response = await self._llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500,
            )
            query_triples = json.loads(response)
            query_entities = set()
            for triple in query_triples:
                if len(triple) >= 1:
                    query_entities.add(triple[0])
                if len(triple) >= 3:
                    query_entities.add(triple[2])
        except (json.JSONDecodeError, Exception):
            query_entities = set()

        # Find related entities via graph traversal
        related_entities = set()
        for entity in query_entities:
            related = graph.get_related_entities(entity, max_hops=max_hops)
            related_entities.update(related)

        # Get chunk IDs from related entities
        all_entities = list(query_entities | related_entities)
        related_chunk_ids = set(graph.get_entity_chunk_ids(all_entities))

        # Boost scores for graph-connected chunks
        for chunk in chunks:
            if chunk.get("id") in related_chunk_ids:
                chunk["score"] = chunk.get("score", 0) * 1.3  # 30% boost
                chunk["graph_connected"] = True

        chunks.sort(key=lambda c: c.get("score", 0), reverse=True)
        return chunks
