"""
Asset model.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from ..database import Base


class Asset(Base):
    """Asset model representing equipment (HVAC, CHILLER, ELEVATOR)."""
    
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    type = Column(String(20), nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"))
    status = Column(String(20), default="OK")
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    site = relationship("Site", backref="assets")
