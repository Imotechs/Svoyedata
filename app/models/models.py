from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String, nullable=True)
    federal_district = Column(String, nullable=True)

class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    unit = Column(String, nullable=True)

class MetricValue(Base):
    __tablename__ = "metric_values"

    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("metrics.id"))
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    value = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    source_url = Column(String)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

    metric = relationship("Metric", backref="values")
    region = relationship("Region", backref="values")
