"""
ORM models aligned with docs/DATABASE_SCHEMA.md.
"""

from datetime import date, datetime
import uuid

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    DateTime,
    Numeric,
    JSON,
    Float,
    UniqueConstraint,
    Identity,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SalesAggregated(Base):
    __tablename__ = "sales_aggregated"

    id = Column(Integer, Identity(start=1), primary_key=True)
    date = Column(Date, nullable=False, index=True)
    channel = Column(String(20), nullable=False)
    department = Column(String(50), nullable=False)
    promo_flag = Column(Boolean, default=False)
    discount_pct = Column(Numeric(5, 2))
    sales_value = Column(Numeric(15, 2), nullable=False)
    margin_value = Column(Numeric(15, 2), nullable=False)
    units = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = ()


class PromoScenario(Base):
    __tablename__ = "promo_scenarios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    label = Column(String(100), nullable=False)
    source_opportunity_id = Column(String, nullable=True)
    date_range_start = Column(Date, nullable=False)
    date_range_end = Column(Date, nullable=False)
    scenario_type = Column(String(50), nullable=True)
    mechanics = Column(JSON, nullable=False)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScenarioKPI(Base):
    __tablename__ = "scenario_kpis"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    total_sales_value = Column(Numeric(15, 2), nullable=False)
    total_margin_value = Column(Numeric(15, 2), nullable=False)
    total_margin_pct = Column(Numeric(5, 2), nullable=False)
    total_ebit = Column(Numeric(15, 2), nullable=False)
    total_units = Column(Integer, nullable=False)
    sales_value_delta = Column(Numeric(15, 2), nullable=False)
    margin_value_delta = Column(Numeric(15, 2), nullable=False)
    ebit_delta = Column(Numeric(15, 2), nullable=False)
    units_delta = Column(Integer, nullable=False)
    kpi_breakdown = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    month = Column(String(7), nullable=False)
    department = Column(String(50), nullable=False)
    channel = Column(String(20), nullable=False)
    estimated_potential = Column(Float, nullable=False)
    rationale = Column(String(255), nullable=True)
    priority = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class CreativeBrief(Base):
    __tablename__ = "creative_briefs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String, nullable=False)
    objectives = Column(JSON, nullable=False)
    messaging = Column(String, nullable=False)
    target_audience = Column(String, nullable=False)
    tone = Column(String, nullable=False)
    style = Column(String, nullable=False)
    mandatory_elements = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PostMortem(Base):
    __tablename__ = "post_mortems"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String, nullable=False)
    forecast_accuracy = Column(JSON, nullable=False)
    uplift_analysis = Column(JSON, nullable=False)
    post_promo_dip = Column(Float, nullable=True)
    cannibalization_signals = Column(JSON, nullable=True)
    insights = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    meta = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
