# Helm Deploy

## Prereqs
- NGINX Ingress Controller
- cert-manager (ClusterIssuer `letsencrypt-prod`)
- Optional: Prometheus Operator (for ServiceMonitor)

## Install
```bash
NAMESPACE=capsule-brain
helm upgrade --install cb deploy/helm/capsule-brain -n $NAMESPACE --create-namespace   --set image.repository=capsule-brain --set image.tag=latest   --set ingress.hosts[0].host=cb.example.com   --set ingress.tls.enabled=true --set ingress.tls.secretName=cb-tls
```

## Verify
```bash
kubectl -n $NAMESPACE get pods,svc,ingress
curl https://cb.example.com/healthz
```


## Overrides
Use environment-specific values files:

### Staging
```bash
helm upgrade --install cb-staging deploy/helm/capsule-brain -n capsule-brain-staging --create-namespace -f deploy/helm/capsule-brain/values-staging.yaml
```

### Production
```bash
helm upgrade --install cb deploy/helm/capsule-brain -n capsule-brain --create-namespace -f deploy/helm/capsule-brain/values-prod.yaml
```

### ClusterIssuers
Apply cert-manager issuers once per cluster:
```bash
kubectl apply -f deploy/cert-manager/cluster-issuers.yaml
```
