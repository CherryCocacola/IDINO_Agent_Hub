"""
SQL Query Loader
- Load SQL queries from YAML files
- Support for parameterized queries
- Easy query management without code changes
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache


class QueryLoader:
    """
    Load and manage SQL queries from YAML files

    Usage:
        loader = QueryLoader("student")
        query = loader.get("get_student_by_id", student_id="STU001")
    """

    _instances: Dict[str, "QueryLoader"] = {}
    _base_path: Optional[Path] = None

    def __new__(cls, domain: str):
        """Singleton per domain"""
        if domain not in cls._instances:
            instance = super().__new__(cls)
            instance._domain = domain
            instance._queries = {}
            instance._load_queries()
            cls._instances[domain] = instance
        return cls._instances[domain]

    @classmethod
    def set_base_path(cls, path: str):
        """Set base path for query files"""
        cls._base_path = Path(path)

    @classmethod
    def get_base_path(cls) -> Path:
        """Get base path for query files"""
        if cls._base_path is None:
            # Default: shared/database/queries
            cls._base_path = Path(__file__).parent / "queries"
        return cls._base_path

    def _load_queries(self):
        """Load queries from YAML file"""
        query_file = self.get_base_path() / f"{self._domain}.yaml"

        if not query_file.exists():
            raise FileNotFoundError(f"Query file not found: {query_file}")

        with open(query_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            self._queries = data.get("queries", {})

    def reload(self):
        """Reload queries from file (for development)"""
        self._queries = {}
        self._load_queries()

    def get(self, query_name: str, **params) -> str:
        """
        Get SQL query by name with parameter substitution

        Args:
            query_name: Name of the query in YAML
            **params: Parameters to substitute

        Returns:
            SQL query string
        """
        if query_name not in self._queries:
            raise KeyError(f"Query not found: {query_name}")

        query = self._queries[query_name]

        # Handle nested query structure
        if isinstance(query, dict):
            query = query.get("sql", "")

        # Substitute parameters
        if params:
            query = query.format(**params)

        return query

    def get_raw(self, query_name: str) -> str:
        """Get raw query without parameter substitution"""
        if query_name not in self._queries:
            raise KeyError(f"Query not found: {query_name}")

        query = self._queries[query_name]
        if isinstance(query, dict):
            return query.get("sql", "")
        return query

    def list_queries(self) -> list:
        """List all available query names"""
        return list(self._queries.keys())

    @classmethod
    def clear_cache(cls):
        """Clear all cached instances"""
        cls._instances.clear()


# Convenience functions
@lru_cache(maxsize=10)
def load_queries(domain: str) -> QueryLoader:
    """Load queries for a domain (cached)"""
    return QueryLoader(domain)


def get_query(domain: str, query_name: str, **params) -> str:
    """Get a query directly"""
    return load_queries(domain).get(query_name, **params)
