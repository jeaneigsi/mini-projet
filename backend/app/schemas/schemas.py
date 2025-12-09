"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================
# Site Schemas
# ============================================

class SiteBase(BaseModel):
    """Base schema for Site."""
    code: str
    name: str
    address: Optional[str] = None


class SiteResponse(SiteBase):
    """Response schema for Site."""
    id: int
    created_at: datetime
    total_assets: int = 0
    high_alerts: int = 0
    medium_alerts: int = 0
    low_alerts: int = 0
    
    class Config:
        from_attributes = True


class SiteListResponse(BaseModel):
    """Response schema for list of sites."""
    sites: List[SiteResponse]
    total: int


# ============================================
# Asset Schemas
# ============================================

class AssetBase(BaseModel):
    """Base schema for Asset."""
    code: str
    type: str
    status: str = "OK"


class AssetResponse(AssetBase):
    """Response schema for Asset."""
    id: int
    site_id: int
    site_code: Optional[str] = None
    site_name: Optional[str] = None
    created_at: datetime
    open_alerts: int = 0
    
    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    """Response schema for list of assets."""
    assets: List[AssetResponse]
    total: int


# ============================================
# Alert Schemas
# ============================================

class AlertBase(BaseModel):
    """Base schema for Alert."""
    severity: str
    message: str


class AlertResponse(AlertBase):
    """Response schema for Alert."""
    id: int
    asset_id: int
    policy_id: Optional[int] = None
    triggered_at: datetime
    status: str
    metric_value: Optional[float] = None
    acknowledged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    asset_code: Optional[str] = None
    asset_type: Optional[str] = None
    site_code: Optional[str] = None
    
    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    """Schema for updating an Alert."""
    status: Optional[str] = Field(None, pattern="^(open|ack|closed)$")


class AlertListResponse(BaseModel):
    """Response schema for list of alerts."""
    alerts: List[AlertResponse]
    total: int


# ============================================
# Work Order Schemas
# ============================================

class WorkOrderBase(BaseModel):
    """Base schema for WorkOrder."""
    priority: str = "MEDIUM"
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class WorkOrderResponse(WorkOrderBase):
    """Response schema for WorkOrder."""
    id: int
    alert_id: int
    created_at: datetime
    closed_at: Optional[datetime] = None
    status: str
    alert_message: Optional[str] = None
    alert_severity: Optional[str] = None
    asset_code: Optional[str] = None
    site_code: Optional[str] = None
    
    class Config:
        from_attributes = True


class WorkOrderUpdate(BaseModel):
    """Schema for updating a WorkOrder."""
    status: Optional[str] = Field(None, pattern="^(open|in_progress|done|cancelled)$")
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class WorkOrderListResponse(BaseModel):
    """Response schema for list of work orders."""
    work_orders: List[WorkOrderResponse]
    total: int


# ============================================
# Health Check Schema
# ============================================

class HealthResponse(BaseModel):
    """Response schema for health check."""
    status: str
    version: str
    database: str
    elasticsearch: str
