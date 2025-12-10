"""
Database package

Provides SQLAlchemy engine/session helpers and ORM models that mirror the schema
outlined in `docs/DATABASE_SCHEMA.md`. For local development we default to
DuckDB (file-backed) to keep setup lightweight while staying SQL-compliant; in
production, set DATABASE_URL to a PostgreSQL connection string.
"""

from .session import get_engine, get_session
from .models import (
    Base,
    SalesAggregated,
    PromoScenario,
    ScenarioKPI,
    ValidationReport,
    PostMortemReport,
    CreativeBrief,
    Segment,
    UpliftCoefficient,
    DataProcessingJob,
    Target,
    PromoCatalog,
    Opportunity,
    ModelVersion,
)

__all__ = [
    "Base",
    "get_engine",
    "get_session",
    "SalesAggregated",
    "PromoScenario",
    "ScenarioKPI",
    "ValidationReport",
    "PostMortemReport",
    "CreativeBrief",
    "Segment",
    "UpliftCoefficient",
    "DataProcessingJob",
    "Target",
    "PromoCatalog",
    "Opportunity",
    "ModelVersion",
]
