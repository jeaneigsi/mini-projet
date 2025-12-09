"""
WorkOrder model.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from ..database import Base


class WorkOrder(Base):
    """Work order created when an alert requires intervention."""
    
    __tablename__ = "work_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=func.now())
    closed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="open", index=True)
    priority = Column(String(10), default="MEDIUM")
    assigned_to = Column(String(100), nullable=True)
    notes = Column(String, nullable=True)
    
    # Relationships
    alert = relationship("Alert", backref="work_orders")
