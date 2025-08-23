# EKS Terraform

## Usage
```bash
cd deploy/terraform/eks
terraform init
terraform apply -auto-approve
aws eks update-kubeconfig --name cb-eks --region us-west-2
kubectl get nodes
```
