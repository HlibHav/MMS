"""
ORM models aligned with docs/DATABASE_SCHEMA.md (critical tables).
"""

from datetime import datetime
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
    Computed,
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
    margin_pct = Column(
        Numeric(5, 2),
        Computed(
            "CASE WHEN sales_value > 0 THEN (margin_value / sales_value * 100) ELSE 0 END",
            persisted=True,
        ),
        nullable=True,
    )
    units = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("date", "channel", "department", "promo_flag", name="uq_sales_record"),
        CheckConstraint("channel IN ('online','offline')", name="ck_sales_channel"),
    )


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

    __table_args__ = (
        CheckConstraint("date_range_end >= date_range_start", name="ck_scenario_dates"),
    )


class ScenarioKPI(Base):
    __tablename__ = "scenario_kpis"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String, ForeignKey("promo_scenarios.id"), nullable=False)
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
    kpi_breakdown = Column(JSON, nullable=False)  # by_channel, by_department, by_segment
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("period_end >= period_start", name="ck_kpi_dates"),
        Index("idx_kpis_scenario", "scenario_id"),
        Index("idx_kpis_period", "period_start", "period_end"),
    )


class ValidationReport(Base):
    __tablename__ = "validation_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String, ForeignKey("promo_scenarios.id"), nullable=False)
    status = Column(String(20), nullable=False)  # PASS | WARN | BLOCK
    issues = Column(JSON, nullable=True)
    overall_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("scenario_id", name="uq_validation_scenario"),
        CheckConstraint("status IN ('PASS','WARN','BLOCK')", name="ck_validation_status"),
    )


class PostMortemReport(Base):
    __tablename__ = "post_mortem_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String, ForeignKey("promo_scenarios.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    forecast_kpi_id = Column(String, ForeignKey("scenario_kpis.id"), nullable=True)
    actual_kpi = Column(JSON, nullable=False)
    vs_forecast = Column(JSON, nullable=True)
    post_promo_dip = Column(JSON, nullable=True)
    cannibalization_signals = Column(JSON, nullable=True)
    insights = Column(JSON, nullable=True)
    learning_points = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("period_end >= period_start", name="ck_postmortem_dates"),
    )


class CreativeBrief(Base):
    __tablename__ = "creative_briefs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String, ForeignKey("promo_scenarios.id"), nullable=False)
    brief = Column(JSON, nullable=False)
    assets = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_creative_scenario", "scenario_id"),)


class Segment(Base):
    __tablename__ = "segments"

    segment_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    share_of_customers = Column(Numeric(5, 4), nullable=False)
    share_of_revenue = Column(Numeric(5, 4), nullable=False)
    avg_basket_value = Column(Numeric(10, 2), nullable=False)
    fav_categories = Column(JSON, nullable=True)
    discount_sensitivity = Column(String(20), nullable=True)
    purchase_frequency = Column(Numeric(5, 2), nullable=True)
    last_purchase_days_ago = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


class UpliftCoefficient(Base):
    __tablename__ = "uplift_coefficients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    department = Column(String(50), nullable=False)
    channel = Column(String(20), nullable=False)
    discount_band = Column(String(20), nullable=False)
    uplift_sales_pct = Column(Numeric(6, 2), nullable=False)
    uplift_units_pct = Column(Numeric(6, 2), nullable=False)
    margin_impact_pct = Column(Numeric(6, 2), nullable=False)
    confidence = Column(Numeric(3, 2), nullable=True)
    sample_size = Column(Integer, nullable=True)
    model_version = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("department", "channel", "discount_band", "model_version", name="uq_uplift_version"),
        CheckConstraint("channel IN ('online','offline')", name="ck_uplift_channel"),
    )


class DataProcessingJob(Base):
    __tablename__ = "data_processing_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), nullable=False)
    files_queued = Column(Integer, nullable=False)
    files_processed = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    result = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("status IN ('queued','processing','completed','failed')", name="ck_job_status"),
        Index("idx_jobs_status", "status"),
    )


class Target(Base):
    __tablename__ = "targets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    month = Column(String(7), nullable=False)
    geo = Column(String(10), nullable=False)
    sales_value_target = Column(Numeric(15, 2), nullable=False)
    margin_pct_target = Column(Numeric(5, 2), nullable=False)
    units_target = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("month", "geo", name="uq_targets_month_geo"),
        Index("idx_targets_month", "month"),
        Index("idx_targets_geo", "geo"),
    )


class PromoCatalog(Base):
    __tablename__ = "promo_catalog"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    promo_name = Column(String(200), nullable=True)
    date_start = Column(Date, nullable=False)
    date_end = Column(Date, nullable=False)
    departments = Column(JSON, nullable=True)
    channels = Column(JSON, nullable=True)
    avg_discount_pct = Column(Numeric(5, 2), nullable=True)
    mechanics = Column(JSON, nullable=True)
    source_file = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("date_end >= date_start", name="ck_promo_dates"),
        Index("idx_promo_dates", "date_start", "date_end"),
    )


# Legacy/utility models retained for compatibility
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


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    meta = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
