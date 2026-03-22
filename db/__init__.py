"""Database package for Peru Elecciones 2026."""
from db.connection import get_connection, get_engine

__all__ = ["get_connection", "get_engine"]
