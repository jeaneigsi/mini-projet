"""
MQTT to Kafka Bridge

Subscribes to all MQTT topics and forwards messages to Kafka.
Enriches messages with metadata extracted from topic structure.

Topic format: {site_code}/{asset_type}/{asset_id}
Example: cas-s1/hvac/1
"""

import os
import json
import logging
from datetime import datetime

import paho.mqtt.client as mqtt
from kafka import KafkaProducer

# Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "telemetry")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mqtt-bridge")

# Kafka producer (initialized on startup)
producer = None


def create_kafka_producer():
    """Create Kafka producer with retry logic."""
    import time
    max_retries = 30
    retry_interval = 5
    
    for attempt in range(max_retries):
        try:
            p = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all'
            )
            logger.info(f"Connected to Kafka at {KAFKA_BROKER}")
            return p
        except Exception as e:
            logger.warning(f"Kafka connection attempt {attempt + 1}/{max_retries} failed: {e}")
            time.sleep(retry_interval)
    
    raise Exception(f"Could not connect to Kafka after {max_retries} attempts")


def on_connect(client, userdata, flags, rc):
    """Callback when MQTT client connects."""
    if rc == 0:
        logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        # Subscribe to all topics with pattern +/+/+
        client.subscribe("+/+/+")
        logger.info("Subscribed to topic pattern: +/+/+")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code: {rc}")


def on_message(client, userdata, msg):
    """Callback when MQTT message is received."""
    global producer
    
    try:
        # Parse topic to extract metadata
        # Expected format: {site_code}/{asset_type}/{asset_id}
        topic_parts = msg.topic.split("/")
        
        if len(topic_parts) != 3:
            logger.warning(f"Unexpected topic format: {msg.topic}")
            return
        
        site_code, asset_type, asset_id = topic_parts
        
        # Parse payload
        payload = json.loads(msg.payload.decode('utf-8'))
        
        # Enrich message with metadata
        enriched_message = {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "site_code": site_code.upper(),
            "asset_type": asset_type.upper(),
            "asset_code": f"{site_code.upper()}-{asset_type.upper()}_{asset_id}",
            "source_topic": msg.topic,
            "metrics": payload.get("metrics", payload)
        }
        
        # Forward to Kafka
        producer.send(KAFKA_TOPIC, value=enriched_message)
        
        logger.debug(f"Forwarded message from {msg.topic} to Kafka topic {KAFKA_TOPIC}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON payload: {e}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")


def on_disconnect(client, userdata, rc):
    """Callback when MQTT client disconnects."""
    if rc != 0:
        logger.warning(f"Unexpected MQTT disconnection, return code: {rc}")


def main():
    global producer
    
    logger.info("Starting MQTT to Kafka bridge...")
    
    # Create Kafka producer
    producer = create_kafka_producer()
    
    # Create MQTT client
    client = mqtt.Client(client_id="mqtt-kafka-bridge")
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Connect to MQTT broker with retry
    import time
    max_retries = 30
    retry_interval = 5
    
    for attempt in range(max_retries):
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except Exception as e:
            logger.warning(f"MQTT connection attempt {attempt + 1}/{max_retries} failed: {e}")
            time.sleep(retry_interval)
    else:
        raise Exception(f"Could not connect to MQTT broker after {max_retries} attempts")
    
    # Start loop
    logger.info("Bridge is running. Press Ctrl+C to stop.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        client.disconnect()
        if producer:
            producer.close()


if __name__ == "__main__":
    main()
