#!/bin/bash
# Health check script for Liquid Capsule Brain services

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
ADMIN_TOKEN="${ADMIN_TOKEN:-dev-secure-token-123}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"

echo "🔍 Checking Liquid Capsule Brain services..."

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local name=$2
    local headers=$3
    
    if curl -sf $headers "$url" > /dev/null 2>&1; then
        echo "✅ $name is healthy"
        return 0
    else
        echo "❌ $name is not responding"
        return 1
    fi
}

# Check API health
echo "Checking API health..."
if check_endpoint "$API_URL/healthz" "API Health" "-H 'x-admin-token: $ADMIN_TOKEN'"; then
    # Check API ready state
    check_endpoint "$API_URL/ready" "API Ready" "-H 'x-admin-token: $ADMIN_TOKEN'"
    
    # Check metrics endpoint
    check_endpoint "$API_URL/metrics" "API Metrics" ""
    
    # Test a simple query
    echo "Testing API query..."
    RESPONSE=$(curl -s -X POST "$API_URL/ask?q=health%20check" 2>/dev/null || echo "")
    if [[ $RESPONSE == *"ack"* ]]; then
        echo "✅ API query test passed"
    else
        echo "⚠️  API query test failed"
    fi
else
    echo "❌ API is not available"
fi

# Check Prometheus (if running)
echo "Checking Prometheus..."
if check_endpoint "$PROMETHEUS_URL/-/ready" "Prometheus" ""; then
    check_endpoint "$PROMETHEUS_URL/api/v1/query?query=up" "Prometheus Query API" ""
else
    echo "ℹ️  Prometheus not running (optional)"
fi

# Check Grafana (if running)
echo "Checking Grafana..."
if check_endpoint "$GRAFANA_URL/api/health" "Grafana" ""; then
    echo "✅ Grafana is healthy"
else
    echo "ℹ️  Grafana not running (optional)"
fi

# Check Docker containers (if Docker is available)
if command -v docker &> /dev/null; then
    echo "Checking Docker containers..."
    CONTAINERS=$(docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "")
    if [ -n "$CONTAINERS" ]; then
        echo "$CONTAINERS"
    else
        echo "ℹ️  No Docker containers running"
    fi
fi

echo ""
echo "🏥 Health check complete!"
echo "📊 Access points:"
echo "   API: $API_URL"
echo "   Prometheus: $PROMETHEUS_URL"
echo "   Grafana: $GRAFANA_URL"
