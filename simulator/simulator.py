"""
Sensor Simulator for Maintenance 4.0 Platform

Generates realistic telemetry data for HVAC, CHILLER, and ELEVATOR equipment.
Publishes data to MQTT broker.
"""

import os
import json
import time
import random
import logging
from datetime import datetime

import paho.mqtt.client as mqtt

# Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", 10))
SIMULATE_ANOMALY = os.getenv("SIMULATE_ANOMALY", "false").lower() == "true"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("simulator")

# Equipment definitions
SITES = ["cas-s1", "cas-s2"]

EQUIPMENT = {
    "hvac": {
        "metrics": {
            "temp_out_air": {"min": 28, "max": 35, "unit": "C"},
            "temp_supply_air": {"min": 14, "max": 18, "unit": "C", "anomaly_min": 22, "anomaly_max": 26},
            "power_kw": {"min": 8, "max": 15, "unit": "kW"},
            "vibration_level": {"min": 1, "max": 5, "unit": "level", "anomaly_min": 8, "anomaly_max": 12}
        }
    },
    "chiller": {
        "metrics": {
            "water_temp_in": {"min": 16, "max": 20, "unit": "C"},
            "water_temp_out": {"min": 8, "max": 12, "unit": "C", "anomaly_min": 15, "anomaly_max": 19},
            "power_kw": {"min": 20, "max": 40, "unit": "kW"},
            "run_hours": {"min": 0, "max": 0, "unit": "hours", "cumulative": True}
        }
    },
    "elevator": {
        "metrics": {
            "motor_temp": {"min": 40, "max": 65, "unit": "C", "anomaly_min": 85, "anomaly_max": 95},
            "power_kw": {"min": 5, "max": 15, "unit": "kW"},
            "door_cycles": {"min": 0, "max": 0, "unit": "cycles", "cumulative": True},
            "speed": {"min": 1.5, "max": 2.0, "unit": "m/s"}
        }
    }
}

# State for cumulative metrics
cumulative_state = {}


def init_cumulative_state():
    """Initialize cumulative metrics with random starting values."""
    global cumulative_state
    for site in SITES:
        cumulative_state[site] = {
            "chiller": {"run_hours": random.uniform(100, 400)},
            "elevator": {"door_cycles": random.randint(50000, 90000)}
        }


def generate_metric_value(metric_config, is_anomaly=False):
    """Generate a realistic metric value."""
    if is_anomaly and "anomaly_min" in metric_config:
        return round(random.uniform(metric_config["anomaly_min"], metric_config["anomaly_max"]), 2)
    return round(random.uniform(metric_config["min"], metric_config["max"]), 2)


def generate_telemetry(site, asset_type, asset_id, is_anomaly=False):
    """Generate telemetry payload for an asset."""
    equipment_config = EQUIPMENT[asset_type]
    metrics = {}
    
    for metric_name, metric_config in equipment_config["metrics"].items():
        if metric_config.get("cumulative"):
            # Update cumulative value
            if asset_type in cumulative_state[site]:
                if metric_name == "run_hours":
                    cumulative_state[site][asset_type][metric_name] += INTERVAL_SECONDS / 3600
                elif metric_name == "door_cycles":
                    cumulative_state[site][asset_type][metric_name] += random.randint(1, 5)
                metrics[metric_name] = round(cumulative_state[site][asset_type][metric_name], 2)
        else:
            metrics[metric_name] = generate_metric_value(metric_config, is_anomaly)
    
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "metrics": metrics
    }


def on_connect(client, userdata, flags, rc):
    """Callback when MQTT client connects."""
    if rc == 0:
        logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code: {rc}")


def on_disconnect(client, userdata, rc):
    """Callback when MQTT client disconnects."""
    if rc != 0:
        logger.warning(f"Unexpected MQTT disconnection, return code: {rc}")


def main():
    global SIMULATE_ANOMALY
    
    logger.info("Starting sensor simulator...")
    logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"Interval: {INTERVAL_SECONDS} seconds")
    logger.info(f"Anomaly mode: {SIMULATE_ANOMALY}")
    
    # Initialize cumulative state
    init_cumulative_state()
    
    # Create MQTT client
    client = mqtt.Client(client_id="sensor-simulator")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    # Connect to MQTT broker with retry
    max_retries = 30
    retry_interval = 5
    
    for attempt in range(max_retries):
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            client.loop_start()
            break
        except Exception as e:
            logger.warning(f"MQTT connection attempt {attempt + 1}/{max_retries} failed: {e}")
            time.sleep(retry_interval)
    else:
        raise Exception(f"Could not connect to MQTT broker after {max_retries} attempts")
    
    # Give time for connection
    time.sleep(2)
    
    logger.info(f"Simulator is running. Generating data for {len(SITES)} sites...")
    
    try:
        while True:
            # Check for anomaly mode change via environment
            current_anomaly = os.getenv("SIMULATE_ANOMALY", "false").lower() == "true"
            if current_anomaly != SIMULATE_ANOMALY:
                SIMULATE_ANOMALY = current_anomaly
                logger.info(f"Anomaly mode changed to: {SIMULATE_ANOMALY}")
            
            for site in SITES:
                for asset_type in EQUIPMENT.keys():
                    # Generate and publish telemetry
                    topic = f"{site}/{asset_type}/1"
                    payload = generate_telemetry(site, asset_type, 1, SIMULATE_ANOMALY)
                    
                    client.publish(topic, json.dumps(payload))
                    logger.debug(f"Published to {topic}: {payload}")
            
            logger.info(f"Published telemetry for all assets (anomaly={SIMULATE_ANOMALY})")
            time.sleep(INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
