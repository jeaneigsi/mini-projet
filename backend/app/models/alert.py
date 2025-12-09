"""
Alert model.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from ..database import Base


class Alert(Base):
    """Alert generated when a maintenance policy is triggered."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"))
    policy_id = Column(Integer, ForeignKey("maintenance_policies.id", ondelete="SET NULL"), nullable=True)
    triggered_at = Column(DateTime, default=func.now())
    severity = Column(String(10), nullable=False)
    status = Column(String(10), default="open", index=True)
    message = Column(String, nullable=False)
    metric_value = Column(Float, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Relationships
    asset = relationship("Asset", backref="alerts")
    policy = relationship("MaintenancePolicy", backref="alerts")
