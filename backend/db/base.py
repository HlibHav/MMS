"""
Database Base Models

SQLAlchemy models for database tables.
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class SalesAggregated(Base):
    """Sales aggregated data table."""
    __tablename__ = "sales_aggregated"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    channel = Column(String(20), nullable=False, index=True)
    department = Column(String(50), nullable=False, index=True)
    promo_flag = Column(Boolean, default=False, index=True)
    discount_pct = Column(Float)
    sales_value = Column(Float, nullable=False)
    margin_value = Column(Float, nullable=False)
    margin_pct = Column(Float)
    units = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        {"unique_constraint": ("date", "channel", "department", "promo_flag")},
    )


class PromoCampaign(Base):
    """Promotional campaign table."""
    __tablename__ = "promo_campaigns"
    
    id = Column(String, primary_key=True)
    promo_name = Column(String(200), nullable=False)
    date_start = Column(Date, nullable=False, index=True)
    date_end = Column(Date, nullable=False, index=True)
    departments = Column(Text)  # JSON array as string
    channels = Column(Text)  # JSON array as string
    avg_discount_pct = Column(Float)
    mechanics = Column(Text)  # JSON object as string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProcessingJob(Base):
    """Data processing job tracking."""
    __tablename__ = "processing_jobs"
    
    id = Column(String, primary_key=True)
    job_type = Column(String(50), nullable=False)  # "xlsb", "promo"
    status = Column(String(20), nullable=False, index=True)  # "queued", "processing", "completed", "failed"
    files_processed = Column(Integer, default=0)
    total_files = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    result = Column(Text)  # JSON result
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)
    created_by = Column(String(100))


class Scenario(Base):
    """Stored promotional scenarios."""
    __tablename__ = "scenarios"
    
    id = Column(String, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    date_start = Column(Date, nullable=False, index=True)
    date_end = Column(Date, nullable=False, index=True)
    departments = Column(Text)  # JSON array
    channels = Column(Text)  # JSON array
    discount_percentage = Column(Float, nullable=False)
    segments = Column(Text)  # JSON array
    metadata = Column(Text)  # JSON object
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))


class ScenarioKPI(Base):
    """Stored scenario KPIs."""
    __tablename__ = "scenario_kpis"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=False, index=True)
    total_sales = Column(Float, nullable=False)
    total_margin = Column(Float, nullable=False)
    total_ebit = Column(Float, nullable=False)
    total_units = Column(Integer, nullable=False)
    breakdown_by_channel = Column(Text)  # JSON
    breakdown_by_department = Column(Text)  # JSON
    comparison_vs_baseline = Column(Text)  # JSON
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    scenario = relationship("Scenario", backref="kpis")
