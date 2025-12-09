"""
Maintenance Policy model.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, func

from ..database import Base


class MaintenancePolicy(Base):
    """Maintenance policy defining rules for alert generation."""
    
    __tablename__ = "maintenance_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_type = Column(String(20), nullable=False, index=True)
    metric = Column(String(50), nullable=False)
    rule_type = Column(String(20), nullable=False)
    threshold = Column(Float, nullable=False)
    condition = Column(String(5), nullable=False)
    window_minutes = Column(Integer, nullable=True)
    severity = Column(String(10), nullable=False)
    description = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
