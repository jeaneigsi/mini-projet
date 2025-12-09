#!/bin/bash
# Kibana Dashboard Auto-Import Script

KIBANA_URL="${KIBANA_URL:-http://kibana:5601}"
DASHBOARDS_DIR="/dashboards"
MAX_RETRIES=60
RETRY_INTERVAL=5

echo "=========================================="
echo "Kibana Dashboard Auto-Import"
echo "=========================================="
echo "Kibana URL: $KIBANA_URL"
echo "Dashboards directory: $DASHBOARDS_DIR"

# Wait for Kibana to be ready
echo ""
echo "Waiting for Kibana to be ready..."
retry_count=0

while [ $retry_count -lt $MAX_RETRIES ]; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "$KIBANA_URL/api/status")
    
    if [ "$response" = "200" ]; then
        echo "✅ Kibana is ready!"
        break
    fi
    
    retry_count=$((retry_count + 1))
    echo "Attempt $retry_count/$MAX_RETRIES - Kibana not ready (HTTP $response), waiting ${RETRY_INTERVAL}s..."
    sleep $RETRY_INTERVAL
done

if [ $retry_count -eq $MAX_RETRIES ]; then
    echo "❌ Kibana did not become ready in time. Exiting."
    exit 1
fi

# Wait a bit more for Kibana to fully initialize
echo "Waiting 10s for Kibana to fully initialize..."
sleep 10

# Import each dashboard file
echo ""
echo "Importing dashboards..."

for file in $DASHBOARDS_DIR/*.ndjson; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo ""
        echo "Importing: $filename"
        
        response=$(curl -s -w "\n%{http_code}" -X POST "$KIBANA_URL/api/saved_objects/_import?overwrite=true" \
            -H "kbn-xsrf: true" \
            --form file=@"$file")
        
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | sed '$d')
        
        if [ "$http_code" = "200" ]; then
            echo "✅ Successfully imported: $filename"
            echo "   Response: $body"
        else
            echo "⚠️ Import may have issues: $filename (HTTP $http_code)"
            echo "   Response: $body"
        fi
    fi
done

echo ""
echo "=========================================="
echo "Dashboard import complete!"
echo "=========================================="
echo "Access Kibana at: $KIBANA_URL"
echo "Go to: Analytics > Dashboard"

# Keep container running for logs
sleep infinity
