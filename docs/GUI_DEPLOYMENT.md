# Capsule Brain GUI Deployment Guide

This guide provides comprehensive instructions for deploying the Capsule Brain GUI in production environments.

## 🚀 Overview

The Capsule Brain GUI is a modern, responsive web interface built with FastAPI and WebSocket technology. It provides real-time interaction with the AI system, file upload capabilities, and comprehensive monitoring dashboards.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.11 or higher
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Storage**: 1GB free space
- **Network**: HTTPS support for production deployments

### Dependencies
- FastAPI with WebSocket support
- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+)
- JavaScript enabled in browser

## 🔧 Configuration

### Environment Variables

```bash
# Application Environment
APP_ENV=production                    # production, staging, development
APP_PROFILE=production               # Application profile

# Security Configuration
ADMIN_TOKEN=your-secure-admin-token  # Required for production
CORS_ORIGINS=https://yourdomain.com  # Restrict CORS origins

# File Upload Limits
UPLOAD_MAX_BYTES=10485760           # 10MB default

# Performance Settings
UVICORN_WORKERS=2                   # Number of workers
HOST=0.0.0.0                       # Bind address
PORT=8000                          # Port number
```

### Production Configuration

```bash
# .env.production
APP_ENV=production
APP_PROFILE=production
ADMIN_TOKEN=your-super-secure-admin-token-here
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
UPLOAD_MAX_BYTES=10485760
UVICORN_WORKERS=4
HOST=0.0.0.0
PORT=8000
```

## 🐳 Docker Deployment

### Dockerfile Configuration

The GUI is automatically included in the main Docker image. No additional configuration required.

```dockerfile
# GUI static files are included in the main image
COPY capsule_brain/gui/static/ /app/capsule_brain/gui/static/
```

### Docker Compose

```yaml
version: '3.8'
services:
  capsule-brain:
    image: capsule-brain:latest
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - ADMIN_TOKEN=${ADMIN_TOKEN}
      - CORS_ORIGINS=https://yourdomain.com
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped
```

## ☸️ Kubernetes Deployment

### Helm Chart Configuration

```yaml
# values.yaml
gui:
  enabled: true
  ingress:
    enabled: true
    hosts:
      - host: yourdomain.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: capsule-brain-tls
        hosts:
          - yourdomain.com
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"
```

### Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: capsule-brain-gui
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  tls:
  - hosts:
    - yourdomain.com
    secretName: capsule-brain-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: capsule-brain-service
            port:
              number: 8000
```

## 🔒 Security Configuration

### HTTPS Setup

For production deployments, HTTPS is required:

```nginx
# Nginx configuration
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Security Headers

The GUI automatically includes security headers:

- **Content Security Policy**: Restricts resource loading
- **X-Frame-Options**: Prevents clickjacking
- **X-Content-Type-Options**: Prevents MIME sniffing
- **X-XSS-Protection**: Enables XSS filtering
- **Referrer-Policy**: Controls referrer information

### Rate Limiting

Built-in rate limiting protects against abuse:

- **60 requests per minute** per IP address
- **Automatic IP blocking** for violations
- **Configurable limits** via environment variables

## 📱 Mobile Support

### Responsive Design

The GUI includes mobile-optimized features:

- **Responsive layout** for all screen sizes
- **Touch-optimized** controls
- **Mobile-specific** route at `/mobile`
- **Progressive Web App** capabilities

### Mobile Configuration

```javascript
// Mobile detection and optimization
const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

if (isMobile) {
    // Apply mobile optimizations
    document.body.classList.add('mobile-optimized');
}
```

## 📊 Performance Optimization

### Caching Strategy

```nginx
# Static file caching
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary "Accept-Encoding";
}

# HTML caching
location / {
    expires 1h;
    add_header Cache-Control "public";
}
```

### Compression

Enable gzip compression for better performance:

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

## 🔍 Monitoring and Observability

### Health Checks

The GUI provides health check endpoints:

```bash
# Basic health check
curl https://yourdomain.com/deployment/health

# Detailed deployment info
curl https://yourdomain.com/deployment/info

# Configuration details
curl https://yourdomain.com/deployment/config
```

### Metrics Integration

GUI metrics are automatically collected:

- **WebSocket connections**
- **Message processing times**
- **Error rates**
- **Performance statistics**

Access metrics at `/metrics` endpoint.

## 🧪 Testing

### Pre-deployment Testing

```bash
# Run comprehensive GUI tests
pytest tests/test_gui_comprehensive.py -v

# Test security features
pytest tests/test_gui_comprehensive.py::TestGUISecurity -v

# Test performance
pytest tests/test_gui_comprehensive.py::TestGUIPerformance -v
```

### Load Testing

```bash
# Use Locust for load testing
locust -f locustfile.py --host=https://yourdomain.com

# Test WebSocket connections
python -m pytest tests/test_gui_comprehensive.py::TestGUIEndpoints::test_concurrent_connections -v
```

## 🚀 Deployment Steps

### 1. Prepare Environment

```bash
# Set environment variables
export APP_ENV=production
export ADMIN_TOKEN=$(openssl rand -hex 32)
export CORS_ORIGINS=https://yourdomain.com

# Verify configuration
python -c "from capsule_brain.gui.deployment import GUIDeploymentManager; print('Configuration valid')"
```

### 2. Deploy Application

```bash
# Using Docker
docker run -d \
  --name capsule-brain \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e ADMIN_TOKEN=$ADMIN_TOKEN \
  -e CORS_ORIGINS=$CORS_ORIGINS \
  capsule-brain:latest

# Using Kubernetes
kubectl apply -f k8s/
```

### 3. Configure Reverse Proxy

```bash
# Nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/capsule-brain
sudo ln -s /etc/nginx/sites-available/capsule-brain /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 4. SSL Certificate

```bash
# Using Let's Encrypt
sudo certbot --nginx -d yourdomain.com
```

### 5. Verify Deployment

```bash
# Check health
curl https://yourdomain.com/deployment/health

# Test GUI access
curl -I https://yourdomain.com/

# Verify WebSocket
wscat -c wss://yourdomain.com/ws
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Static Files Not Loading

```bash
# Check file permissions
ls -la capsule_brain/gui/static/

# Verify file paths
python -c "from pathlib import Path; print(Path('capsule_brain/gui/static/index.html').exists())"
```

#### 2. WebSocket Connection Issues

```bash
# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" https://yourdomain.com/ws
```

#### 3. CORS Issues

```bash
# Verify CORS configuration
curl -H "Origin: https://yourdomain.com" -I https://yourdomain.com/
```

#### 4. Rate Limiting

```bash
# Check rate limit status
curl -H "X-Forwarded-For: 192.168.1.1" https://yourdomain.com/deployment/info
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
export APP_ENV=development
export DEBUG=true

# Access debug endpoints
curl https://yourdomain.com/dev/gui-debug
```

## 📈 Performance Tuning

### Production Optimizations

1. **Enable caching** for static files
2. **Compress responses** with gzip
3. **Use CDN** for static assets
4. **Optimize images** and assets
5. **Monitor performance** metrics

### Scaling Considerations

- **Horizontal scaling**: Multiple application instances
- **Load balancing**: Distribute WebSocket connections
- **Database optimization**: For persistent data
- **CDN integration**: For static file delivery

## 🔄 Updates and Maintenance

### Rolling Updates

```bash
# Update application
docker pull capsule-brain:latest
docker stop capsule-brain
docker rm capsule-brain
docker run -d --name capsule-brain [previous options] capsule-brain:latest
```

### Configuration Updates

```bash
# Update environment variables
kubectl set env deployment/capsule-brain APP_ENV=production

# Restart deployment
kubectl rollout restart deployment/capsule-brain
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebSocket Best Practices](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_client_applications)
- [Security Headers Guide](https://owasp.org/www-project-secure-headers/)
- [Performance Optimization](https://web.dev/performance/)

## 🆘 Support

For deployment issues:

1. Check the troubleshooting section
2. Review application logs
3. Verify configuration
4. Test individual components
5. Contact the development team

---

**Note**: This guide assumes familiarity with web deployment concepts. For production deployments, consider consulting with DevOps professionals for optimal configuration and security practices.
