"""
Site model.
"""

from sqlalchemy import Column, Integer, String, DateTime, func

from ..database import Base


class Site(Base):
    """Site model representing a building/location."""
    
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
