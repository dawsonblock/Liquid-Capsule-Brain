# GitOps + Terraform

- **Argo CD**: `deploy/gitops/argocd` (AppProject + ApplicationSet).
- **Helmfile**: now includes `argo-cd` release for one-shot bootstrap.
- **Terraform**: EKS and GKE minimal clusters under `deploy/terraform/eks|gke`.

### Flow (EKS example)
```bash
# 1) Create cluster
cd deploy/terraform/eks && terraform init && terraform apply -auto-approve

# 2) Platform deps
cd ../../helm && helmfile apply --selector name=cert-manager && helmfile apply --selector name=ingress-nginx && helmfile apply --selector name=argo-cd

# 3) GitOps
kubectl apply -n argocd -f ../gitops/argocd/project.yaml
# Edit repoURL in appset.yaml to your git repo, then:
kubectl apply -n argocd -f ../gitops/argocd/appset.yaml
```
