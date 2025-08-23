provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_container_cluster" "cb" {
  name     = var.cluster_name
  location = var.region
  networking_mode = "VPC_NATIVE"
  remove_default_node_pool = true
  initial_node_count       = 1

  release_channel {
    channel = "REGULAR"
  }

  ip_allocation_policy {}
}

resource "google_container_node_pool" "primary" {
  cluster  = google_container_cluster.cb.name
  location = var.region
  name     = "primary"
  node_count = 3

  node_config {
    machine_type = "e2-standard-4"
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.cb.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.cb.master_auth[0].cluster_ca_certificate)
}

data "google_client_config" "default" {}

provider "helm" {
  kubernetes {
    host                   = "https://${google_container_cluster.cb.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.cb.master_auth[0].cluster_ca_certificate)
  }
}

output "cluster_name"     { value = google_container_cluster.cb.name }
output "cluster_endpoint" { value = google_container_cluster.cb.endpoint }
