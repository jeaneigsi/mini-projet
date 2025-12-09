"""
Elasticsearch client for querying telemetry data.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from elasticsearch import Elasticsearch

from .config import settings

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Client for interacting with Elasticsearch."""
    
    def __init__(self):
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to Elasticsearch."""
        try:
            self.client = Elasticsearch(
                [settings.elasticsearch_url],
                verify_certs=False,
                request_timeout=30
            )
            if self.client.ping():
                logger.info(f"Connected to Elasticsearch at {settings.elasticsearch_url}")
            else:
                logger.warning("Elasticsearch ping failed")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            self.client = None
    
    def get_metric_aggregation(
        self,
        asset_code: str,
        metric: str,
        window_minutes: int,
        agg_type: str = "avg"
    ) -> Optional[float]:
        """
        Get aggregated metric value for an asset over a time window.
        
        Args:
            asset_code: The asset code to query
            metric: The metric name (e.g., 'temp_supply_air')
            window_minutes: Time window in minutes
            agg_type: Aggregation type ('avg', 'max', 'min', 'count')
        
        Returns:
            Aggregated value or None if no data
        """
        if not self.client:
            logger.warning("Elasticsearch client not available")
            return None
        
        try:
            # Build the query
            now = datetime.utcnow()
            start_time = now - timedelta(minutes=window_minutes)
            
            metric_field = f"metric_{metric}"
            
            query = {
                "size": 0,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"asset_code": asset_code}},
                            {"range": {"@timestamp": {"gte": start_time.isoformat(), "lte": now.isoformat()}}}
                        ],
                        "filter": [
                            {"exists": {"field": metric_field}}
                        ]
                    }
                },
                "aggs": {
                    "metric_agg": {
                        agg_type: {"field": metric_field}
                    }
                }
            }
            
            response = self.client.search(
                index=settings.elasticsearch_index,
                body=query
            )
            
            agg_value = response.get("aggregations", {}).get("metric_agg", {}).get("value")
            return agg_value
            
        except Exception as e:
            logger.error(f"Error querying Elasticsearch: {e}")
            return None
    
    def get_recent_metric_values(
        self,
        asset_code: str,
        metric: str,
        count: int = 5
    ) -> List[float]:
        """
        Get the most recent metric values for an asset.
        
        Args:
            asset_code: The asset code to query
            metric: The metric name
            count: Number of recent values to retrieve
        
        Returns:
            List of recent values
        """
        if not self.client:
            return []
        
        try:
            metric_field = f"metric_{metric}"
            
            query = {
                "size": count,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"asset_code": asset_code}}
                        ],
                        "filter": [
                            {"exists": {"field": metric_field}}
                        ]
                    }
                },
                "sort": [{"@timestamp": {"order": "desc"}}],
                "_source": [metric_field]
            }
            
            response = self.client.search(
                index=settings.elasticsearch_index,
                body=query
            )
            
            values = []
            for hit in response.get("hits", {}).get("hits", []):
                value = hit.get("_source", {}).get(metric_field)
                if value is not None:
                    values.append(value)
            
            return values
            
        except Exception as e:
            logger.error(f"Error querying Elasticsearch: {e}")
            return []
    
    def get_latest_metric(self, asset_code: str, metric: str) -> Optional[float]:
        """Get the latest value of a metric for an asset."""
        values = self.get_recent_metric_values(asset_code, metric, count=1)
        return values[0] if values else None


# Singleton instance
es_client = ElasticsearchClient()
