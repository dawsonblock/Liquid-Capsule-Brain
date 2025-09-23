# Capsule Brain Monitoring Setup

This directory contains monitoring configurations and dashboards for the Capsule Brain system.

## 📊 Monitoring Stack

### Components
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert management and routing
- **Node Exporter**: System metrics collection

### Metrics Available

#### Application Metrics
- `http_requests_total`: Total HTTP requests by method and endpoint
- `http_request_duration_seconds`: Request duration histogram
- `http_connections_active`: Active HTTP connections
- `debug_operations_total`: Debug operations counter
- `memory_objects_count`: Memory object count
- `memory_gc_collections_total`: Garbage collection events

#### System Metrics
- `process_cpu_seconds_total`: CPU usage
- `process_resident_memory_bytes`: Resident memory usage
- `process_virtual_memory_bytes`: Virtual memory usage
- `node_memory_MemAvailable_bytes`: Available system memory
- `node_cpu_seconds_total`: System CPU usage

## 🚀 Quick Start

### 1. Start Monitoring Stack
```bash
# Start Prometheus and Grafana
docker-compose -f monitoring/docker-compose.yml up -d

# Check status
docker-compose -f monitoring/docker-compose.yml ps
```

### 2. Access Dashboards
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Capsule Brain**: http://localhost:8000

### 3. Import Dashboard
1. Open Grafana at http://localhost:3000
2. Go to "Dashboards" → "Import"
3. Upload `monitoring/grafana/dashboards/capsule-brain.json`
4. Configure Prometheus as data source

## 📈 Dashboard Features

### System Overview
- **API Response Time**: 95th and 50th percentile response times
- **Request Rate**: Requests per second by endpoint
- **Error Rate**: 4xx and 5xx error rates
- **Memory Usage**: Resident and virtual memory consumption
- **CPU Usage**: Process CPU utilization
- **Active Connections**: Current HTTP connections

### Debug Operations
- **Debug Operations**: Rate of debug operations
- **Memory Leaks**: Object count and GC collections
- **Performance Metrics**: Custom performance indicators

### Alerting
- **High Response Time**: >1 second response time
- **High Error Rate**: >5% error rate
- **Memory Leaks**: Increasing object count
- **High CPU Usage**: >80% CPU utilization

## 🔧 Configuration

### Environment Variables
```bash
# Prometheus configuration
PROMETHEUS_RETENTION=15d
PROMETHEUS_STORAGE_PATH=/prometheus

# Grafana configuration
GF_SECURITY_ADMIN_PASSWORD=admin
GF_USERS_ALLOW_SIGN_UP=false

# Capsule Brain metrics
METRICS_ENABLED=true
METRICS_PORT=8000
```

### Custom Metrics
Add custom metrics to your application:
```python
from prometheus_client import Counter, Histogram, Gauge

# Custom counters
debug_operations = Counter('debug_operations_total', 'Debug operations', ['operation'])
memory_objects = Gauge('memory_objects_count', 'Memory object count')
request_duration = Histogram('http_request_duration_seconds', 'Request duration')

# Use in your code
debug_operations.labels(operation='memory_check').inc()
memory_objects.set(len(gc.get_objects()))
```

## 📊 Performance Monitoring

### Key Metrics to Watch
1. **Response Time**: Should be <100ms for most endpoints
2. **Error Rate**: Should be <1% for production
3. **Memory Usage**: Should be stable over time
4. **CPU Usage**: Should be <70% under normal load
5. **Active Connections**: Should not exceed connection limits

### Alerting Rules
```yaml
# High response time alert
- alert: HighResponseTime
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "High response time detected"

# High error rate alert
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
```

## 🔍 Troubleshooting

### Common Issues
1. **Metrics not appearing**: Check if Capsule Brain is running and metrics endpoint is accessible
2. **Dashboard not loading**: Verify Prometheus data source configuration
3. **High memory usage**: Check for memory leaks in debug operations
4. **Slow queries**: Optimize Prometheus queries and increase retention

### Debug Commands
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check metrics endpoint
curl http://localhost:8000/metrics

# Check Grafana health
curl http://localhost:3000/api/health

# View logs
docker-compose -f monitoring/docker-compose.yml logs -f
```

## 📚 Advanced Configuration

### Custom Dashboards
Create custom dashboards by:
1. Copying existing dashboard JSON
2. Modifying panels and queries
3. Importing into Grafana
4. Sharing with team

### Alert Channels
Configure alert channels in AlertManager:
- **Email**: SMTP configuration
- **Slack**: Webhook integration
- **PagerDuty**: Incident management
- **Webhook**: Custom integrations

### Data Retention
Configure data retention policies:
```yaml
# prometheus.yml
global:
  retention: 15d

# Grafana data source
{
  "retention": "15d",
  "maxDataPoints": 1000
}
```

## 🎯 Best Practices

### Monitoring Strategy
1. **Start Simple**: Begin with basic metrics and dashboards
2. **Iterate**: Add more detailed metrics as needed
3. **Alert Wisely**: Set up meaningful alerts, not noise
4. **Review Regularly**: Check dashboards and adjust thresholds
5. **Document**: Keep monitoring documentation up to date

### Performance Optimization
1. **Query Optimization**: Use efficient Prometheus queries
2. **Dashboard Optimization**: Limit data points and time ranges
3. **Resource Management**: Monitor monitoring stack resources
4. **Backup**: Regular backup of Grafana dashboards and configs

## 📞 Support

For monitoring-related issues:
1. Check the troubleshooting section
2. Review Prometheus and Grafana logs
3. Verify configuration files
4. Test metrics endpoints manually
5. Contact the development team

## 🔄 Updates

### Version Compatibility
- **Prometheus**: 2.40+
- **Grafana**: 9.0+
- **Node Exporter**: 1.5+
- **Capsule Brain**: 1.0.1+

### Migration Notes
When updating monitoring components:
1. Backup existing dashboards
2. Test new versions in development
3. Update configuration files
4. Verify all metrics are working
5. Update documentation
