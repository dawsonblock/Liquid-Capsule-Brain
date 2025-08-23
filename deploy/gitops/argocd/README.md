# Argo CD GitOps

## Bootstrap Argo CD (Helmfile option)
```bash
cd deploy/helm
helmfile apply --selector name=argo-cd
```

## Register your repo
- Push this repo to GitHub/GitLab.
- Update `repoURL` in `deploy/gitops/argocd/appset.yaml` to your git HTTPS URL.

## Apply project + appset
```bash
kubectl apply -n argocd -f deploy/gitops/argocd/project.yaml
kubectl apply -n argocd -f deploy/gitops/argocd/appset.yaml
```

Argo CD will create two Applications: `cb-staging` and `cb-prod`, each deploying the Helm chart with its values file.
