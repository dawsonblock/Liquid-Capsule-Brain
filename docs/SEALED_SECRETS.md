# Sealed Secrets

This repo supports both **plain Secrets** and **SealedSecrets** (Bitnami). Toggle in Helm values.

## Options
```yaml
secrets:
  enabled: true
  stringData:
    OPENAI_API_KEY: "sk-..."
    ADMIN_TOKEN: "cb_admin_..."
sealedSecrets:
  enabled: false
  encryptedData: {}
```

### Use Sealed Secrets
1. Install the controller (via helmfile or your own pipeline):
   ```bash
   helmfile -f deploy/helm/helmfile.yaml apply --selector name=sealed-secrets
   ```
2. Create a Kubernetes Secret manifest from your `.env`:
   ```bash
   kubectl create secret generic cb-env --from-env-file=.env -n capsule-brain --dry-run=client -o yaml > cb-secret.yaml
   ```
3. Seal it:
   ```bash
   # fetch public cert (one-time) if needed
   kubeseal --controller-namespace sealed-secrets --controller-name sealed-secrets -o yaml < cb-secret.yaml > cb-sealed.yaml
   ```
4. Copy the `encryptedData` map into `deploy/helm/capsule-brain/values-prod.yaml`:
   ```yaml
   sealedSecrets:
     enabled: true
     encryptedData:
       OPENAI_API_KEY: AgB....
       ADMIN_TOKEN: AgC....
   secrets:
     enabled: true  # keep true so the template renders (as SealedSecret)
   ```
5. Deploy:
   ```bash
   helm upgrade --install cb deploy/helm/capsule-brain -n capsule-brain --create-namespace -f deploy/helm/capsule-brain/values-prod.yaml
   ```
