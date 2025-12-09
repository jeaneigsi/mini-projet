"""
API Routes for the Maintenance 4.0 Platform.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.site import Site
from ..models.asset import Asset
from ..models.alert import Alert
from ..models.workorder import WorkOrder
from ..schemas.schemas import (
    SiteResponse, SiteListResponse,
    AssetResponse, AssetListResponse,
    AlertResponse, AlertListResponse, AlertUpdate,
    WorkOrderResponse, WorkOrderListResponse, WorkOrderUpdate
)

router = APIRouter(prefix="/api/v1", tags=["api"])


# ============================================
# Sites Endpoints
# ============================================

@router.get("/sites", response_model=SiteListResponse)
def get_sites(db: Session = Depends(get_db)):
    """Get all sites with alert counts."""
    
    # Query sites with aggregated alert counts
    sites = db.query(Site).all()
    
    result = []
    for site in sites:
        # Count assets
        total_assets = db.query(Asset).filter(Asset.site_id == site.id).count()
        
        # Count open alerts by severity
        asset_ids = [a.id for a in db.query(Asset.id).filter(Asset.site_id == site.id).all()]
        
        high_alerts = db.query(Alert).filter(
            Alert.asset_id.in_(asset_ids),
            Alert.status == "open",
            Alert.severity == "HIGH"
        ).count() if asset_ids else 0
        
        medium_alerts = db.query(Alert).filter(
            Alert.asset_id.in_(asset_ids),
            Alert.status == "open",
            Alert.severity == "MEDIUM"
        ).count() if asset_ids else 0
        
        low_alerts = db.query(Alert).filter(
            Alert.asset_id.in_(asset_ids),
            Alert.status == "open",
            Alert.severity == "LOW"
        ).count() if asset_ids else 0
        
        result.append(SiteResponse(
            id=site.id,
            code=site.code,
            name=site.name,
            address=site.address,
            created_at=site.created_at,
            total_assets=total_assets,
            high_alerts=high_alerts,
            medium_alerts=medium_alerts,
            low_alerts=low_alerts
        ))
    
    return SiteListResponse(sites=result, total=len(result))


@router.get("/sites/{site_id}", response_model=SiteResponse)
def get_site(site_id: int, db: Session = Depends(get_db)):
    """Get a specific site by ID."""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    total_assets = db.query(Asset).filter(Asset.site_id == site.id).count()
    
    return SiteResponse(
        id=site.id,
        code=site.code,
        name=site.name,
        address=site.address,
        created_at=site.created_at,
        total_assets=total_assets,
        high_alerts=0,
        medium_alerts=0,
        low_alerts=0
    )


@router.get("/sites/{site_id}/assets", response_model=AssetListResponse)
def get_site_assets(site_id: int, db: Session = Depends(get_db)):
    """Get all assets for a specific site."""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    assets = db.query(Asset).filter(Asset.site_id == site_id).all()
    
    result = []
    for asset in assets:
        open_alerts = db.query(Alert).filter(
            Alert.asset_id == asset.id,
            Alert.status == "open"
        ).count()
        
        result.append(AssetResponse(
            id=asset.id,
            code=asset.code,
            type=asset.type,
            status=asset.status,
            site_id=asset.site_id,
            site_code=site.code,
            site_name=site.name,
            created_at=asset.created_at,
            open_alerts=open_alerts
        ))
    
    return AssetListResponse(assets=result, total=len(result))


# ============================================
# Assets Endpoints
# ============================================

@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    """Get a specific asset by ID."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    site = db.query(Site).filter(Site.id == asset.site_id).first()
    open_alerts = db.query(Alert).filter(
        Alert.asset_id == asset.id,
        Alert.status == "open"
    ).count()
    
    return AssetResponse(
        id=asset.id,
        code=asset.code,
        type=asset.type,
        status=asset.status,
        site_id=asset.site_id,
        site_code=site.code if site else None,
        site_name=site.name if site else None,
        created_at=asset.created_at,
        open_alerts=open_alerts
    )


# ============================================
# Alerts Endpoints
# ============================================

@router.get("/alerts", response_model=AlertListResponse)
def get_alerts(
    status: Optional[str] = Query(None, description="Filter by status (open, ack, closed)"),
    severity: Optional[str] = Query(None, description="Filter by severity (LOW, MEDIUM, HIGH)"),
    site_id: Optional[int] = Query(None, description="Filter by site ID"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get alerts with optional filters."""
    query = db.query(Alert)
    
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if site_id:
        asset_ids = [a.id for a in db.query(Asset.id).filter(Asset.site_id == site_id).all()]
        query = query.filter(Alert.asset_id.in_(asset_ids))
    
    total = query.count()
    alerts = query.order_by(Alert.triggered_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for alert in alerts:
        asset = db.query(Asset).filter(Asset.id == alert.asset_id).first()
        site = db.query(Site).filter(Site.id == asset.site_id).first() if asset else None
        
        result.append(AlertResponse(
            id=alert.id,
            asset_id=alert.asset_id,
            policy_id=alert.policy_id,
            triggered_at=alert.triggered_at,
            severity=alert.severity,
            status=alert.status,
            message=alert.message,
            metric_value=alert.metric_value,
            acknowledged_at=alert.acknowledged_at,
            closed_at=alert.closed_at,
            asset_code=asset.code if asset else None,
            asset_type=asset.type if asset else None,
            site_code=site.code if site else None
        ))
    
    return AlertListResponse(alerts=result, total=total)


@router.patch("/alerts/{alert_id}", response_model=AlertResponse)
def update_alert(alert_id: int, update: AlertUpdate, db: Session = Depends(get_db)):
    """Update an alert status."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if update.status:
        alert.status = update.status
        if update.status == "ack":
            alert.acknowledged_at = datetime.utcnow()
        elif update.status == "closed":
            alert.closed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alert)
    
    asset = db.query(Asset).filter(Asset.id == alert.asset_id).first()
    site = db.query(Site).filter(Site.id == asset.site_id).first() if asset else None
    
    return AlertResponse(
        id=alert.id,
        asset_id=alert.asset_id,
        policy_id=alert.policy_id,
        triggered_at=alert.triggered_at,
        severity=alert.severity,
        status=alert.status,
        message=alert.message,
        metric_value=alert.metric_value,
        acknowledged_at=alert.acknowledged_at,
        closed_at=alert.closed_at,
        asset_code=asset.code if asset else None,
        asset_type=asset.type if asset else None,
        site_code=site.code if site else None
    )


# ============================================
# Work Orders Endpoints
# ============================================

@router.get("/workorders", response_model=WorkOrderListResponse)
def get_work_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get work orders with optional filters."""
    query = db.query(WorkOrder)
    
    if status:
        query = query.filter(WorkOrder.status == status)
    
    total = query.count()
    work_orders = query.order_by(WorkOrder.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for wo in work_orders:
        alert = db.query(Alert).filter(Alert.id == wo.alert_id).first()
        asset = db.query(Asset).filter(Asset.id == alert.asset_id).first() if alert else None
        site = db.query(Site).filter(Site.id == asset.site_id).first() if asset else None
        
        result.append(WorkOrderResponse(
            id=wo.id,
            alert_id=wo.alert_id,
            created_at=wo.created_at,
            closed_at=wo.closed_at,
            status=wo.status,
            priority=wo.priority,
            assigned_to=wo.assigned_to,
            notes=wo.notes,
            alert_message=alert.message if alert else None,
            alert_severity=alert.severity if alert else None,
            asset_code=asset.code if asset else None,
            site_code=site.code if site else None
        ))
    
    return WorkOrderListResponse(work_orders=result, total=total)


@router.patch("/workorders/{wo_id}", response_model=WorkOrderResponse)
def update_work_order(wo_id: int, update: WorkOrderUpdate, db: Session = Depends(get_db)):
    """Update a work order."""
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if update.status:
        wo.status = update.status
        if update.status == "done":
            wo.closed_at = datetime.utcnow()
    if update.assigned_to is not None:
        wo.assigned_to = update.assigned_to
    if update.notes is not None:
        wo.notes = update.notes
    
    db.commit()
    db.refresh(wo)
    
    alert = db.query(Alert).filter(Alert.id == wo.alert_id).first()
    asset = db.query(Asset).filter(Asset.id == alert.asset_id).first() if alert else None
    site = db.query(Site).filter(Site.id == asset.site_id).first() if asset else None
    
    return WorkOrderResponse(
        id=wo.id,
        alert_id=wo.alert_id,
        created_at=wo.created_at,
        closed_at=wo.closed_at,
        status=wo.status,
        priority=wo.priority,
        assigned_to=wo.assigned_to,
        notes=wo.notes,
        alert_message=alert.message if alert else None,
        alert_severity=alert.severity if alert else None,
        asset_code=asset.code if asset else None,
        site_code=site.code if site else None
    )
