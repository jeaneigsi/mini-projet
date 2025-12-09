"""
Rule Engine for Maintenance 4.0 Platform.

Evaluates maintenance policies against telemetry data from Elasticsearch
and creates alerts and work orders when thresholds are exceeded.
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.site import Site
from ..models.asset import Asset
from ..models.policy import MaintenancePolicy
from ..models.alert import Alert
from ..models.workorder import WorkOrder
from ..elasticsearch_client import es_client

logger = logging.getLogger(__name__)


class RuleEngine:
    """Engine for evaluating maintenance rules."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def evaluate_all_policies(self):
        """Evaluate all active policies for all assets."""
        self.logger.info("Starting rule evaluation cycle...")
        
        db = SessionLocal()
        try:
            # Get all active policies
            policies = db.query(MaintenancePolicy).filter(
                MaintenancePolicy.active == True
            ).all()
            
            self.logger.info(f"Found {len(policies)} active policies")
            
            # Get all assets
            assets = db.query(Asset).all()
            
            alerts_created = 0
            
            for asset in assets:
                # Get policies matching this asset type
                matching_policies = [p for p in policies if p.asset_type == asset.type]
                
                for policy in matching_policies:
                    if self._evaluate_policy(db, asset, policy):
                        alerts_created += 1
            
            self.logger.info(f"Rule evaluation complete. Created {alerts_created} new alerts.")
            
        except Exception as e:
            self.logger.error(f"Error during rule evaluation: {e}")
            db.rollback()
        finally:
            db.close()
    
    def _evaluate_policy(self, db: Session, asset: Asset, policy: MaintenancePolicy) -> bool:
        """
        Evaluate a single policy for an asset.
        
        Returns True if an alert was created, False otherwise.
        """
        try:
            # Check if there's already an open alert for this asset/policy
            existing_alert = db.query(Alert).filter(
                Alert.asset_id == asset.id,
                Alert.policy_id == policy.id,
                Alert.status == "open"
            ).first()
            
            if existing_alert:
                self.logger.debug(f"Skipping {asset.code}/{policy.metric} - alert already open")
                return False
            
            # Get metric value from Elasticsearch
            metric_value = self._get_metric_value(asset, policy)
            
            if metric_value is None:
                self.logger.debug(f"No data for {asset.code}/{policy.metric}")
                return False
            
            # Evaluate the condition
            if not self._check_condition(metric_value, policy.threshold, policy.condition):
                return False
            
            # Condition violated - create alert
            self.logger.warning(
                f"ALERT: {asset.code} - {policy.description} "
                f"(value={metric_value}, threshold={policy.threshold})"
            )
            
            alert = Alert(
                asset_id=asset.id,
                policy_id=policy.id,
                severity=policy.severity,
                status="open",
                message=f"{policy.description} - Valeur: {metric_value:.2f}, Seuil: {policy.threshold}",
                metric_value=metric_value
            )
            db.add(alert)
            db.flush()  # Get alert ID
            
            # Create work order for HIGH and MEDIUM severity
            if policy.severity in ["HIGH", "MEDIUM"]:
                work_order = WorkOrder(
                    alert_id=alert.id,
                    priority=policy.severity,
                    status="open"
                )
                db.add(work_order)
                self.logger.info(f"Created work order for alert {alert.id}")
            
            # Update asset status
            if policy.severity == "HIGH":
                asset.status = "CRITICAL"
            elif policy.severity == "MEDIUM" and asset.status != "CRITICAL":
                asset.status = "WARNING"
            
            db.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error evaluating policy {policy.id} for asset {asset.code}: {e}")
            return False
    
    def _get_metric_value(self, asset: Asset, policy: MaintenancePolicy) -> Optional[float]:
        """Get the metric value for evaluation."""
        
        if policy.rule_type == "threshold":
            # Use average or max depending on window
            if policy.window_minutes and policy.window_minutes > 0:
                # For threshold rules with time window, use average
                return es_client.get_metric_aggregation(
                    asset_code=asset.code,
                    metric=policy.metric,
                    window_minutes=policy.window_minutes,
                    agg_type="avg"
                )
            else:
                # No window - get latest value
                return es_client.get_latest_metric(asset.code, policy.metric)
        
        elif policy.rule_type == "runtime":
            # For runtime metrics (run_hours, door_cycles), get latest value
            return es_client.get_latest_metric(asset.code, policy.metric)
        
        elif policy.rule_type == "rate_of_change":
            # Get values over window and calculate rate
            values = es_client.get_recent_metric_values(
                asset.code,
                policy.metric,
                count=int(policy.window_minutes or 5)
            )
            if len(values) >= 2:
                # Calculate max value in the window
                return max(values)
            return None
        
        return None
    
    def _check_condition(self, value: float, threshold: float, condition: str) -> bool:
        """Check if the condition is violated."""
        if condition == ">":
            return value > threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<":
            return value < threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "=":
            return value == threshold
        return False


# Singleton instance
rule_engine = RuleEngine()
