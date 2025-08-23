# GKE Terraform

## Prereqs
- `gcloud auth application-default login`
- Set `project_id` var or export `GOOGLE_PROJECT` and use var files.

## Usage
```bash
cd deploy/terraform/gke
terraform init
terraform apply -auto-approve -var project_id=YOUR_PROJECT_ID
gcloud container clusters get-credentials cb-gke --region us-central1 --project YOUR_PROJECT_ID
kubectl get nodes
```
