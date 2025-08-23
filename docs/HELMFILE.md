# Helmfile Bootstrap

Install platform dependencies + app in order using Helmfile.

```bash
cd deploy/helm
# Install cert-manager, ingress-nginx, sealed-secrets
helmfile apply --selector name=cert-manager
helmfile apply --selector name=ingress-nginx
helmfile apply --selector name=sealed-secrets

# Deploy app
helmfile apply --selector name=cb
```
