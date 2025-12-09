# Maintenance 4.0 Platform

Plateforme de maintenance predictive multi-sites pour Exprom FM - Casanearshore.

## Architecture

```
Simulator -> MQTT (Mosquitto) -> Bridge -> Kafka -> Logstash -> Elasticsearch -> Kibana
                                                                      |
                                                               Backend (FastAPI)
                                                                      |
                                                               PostgreSQL
```

## Quick Start

### Prerequisites

- Docker Desktop
- Docker Compose v2+

### Setup

1. Copy environment file:
```bash
cp .env.example .env
```

2. Start all services:
```bash
docker-compose up -d
```

3. Wait for services to be ready (about 2-3 minutes for first startup)

4. Access the dashboards:
   - Kibana: http://localhost:5601
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Verify Installation

```bash
# Check all services are running
docker-compose ps

# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Check API health
curl http://localhost:8000/health

# View telemetry in Kafka
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic telemetry \
  --max-messages 5
```
docker exec -it kafka kafka-console-consumer  --bootstrap-server localhost:9092 --topic telemetry --max-messages 5
## Services

| Service | Port | Description |
|---------|------|-------------|
| Mosquitto | 1883 | MQTT Broker |
| Kafka | 9092 | Event Bus |
| Elasticsearch | 9200 | Analytics Storage |
| Kibana | 5601 | Dashboards |
| PostgreSQL | 5432 | Business Database |
| Backend | 8000 | FastAPI Application |
| Simulator | - | Sensor Data Generator |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| GET | /api/v1/sites | List all sites |
| GET | /api/v1/sites/{id}/assets | List assets for a site |
| GET | /api/v1/assets/{id} | Get asset details |
| GET | /api/v1/alerts | List alerts |
| PATCH | /api/v1/alerts/{id} | Update alert status |
| GET | /api/v1/workorders | List work orders |
| PATCH | /api/v1/workorders/{id} | Update work order |

## Simulate Anomaly

To trigger an alert:

```bash
# Restart simulator with anomaly mode
docker-compose stop simulator
SIMULATE_ANOMALY=true docker-compose up -d simulator
```

This will cause metrics to exceed thresholds, triggering alerts and work orders.

## Project Structure

```
industrie-4.0/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/           # FastAPI application
├── simulator/         # Sensor data generator
├── mqtt-bridge/       # MQTT to Kafka bridge
├── mosquitto/         # MQTT broker config
├── logstash/          # Logstash pipeline
├── elasticsearch/     # ES index templates
├── kibana/            # Kibana dashboards
└── database/          # PostgreSQL init scripts
```

## License

MIT
