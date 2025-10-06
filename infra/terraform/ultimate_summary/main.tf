terraform {
  required_version = ">= 1.5.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.20.0"
    }
  }
}

provider "kubernetes" {}

# Placeholder: This could manage a namespace + configmap for the service
resource "kubernetes_namespace" "ultimate" {
  metadata { name = var.namespace }
}

# Example (commented) secret manifest placeholder:
# resource "kubernetes_secret" "jwt" {
#   metadata {
#     name      = "ultimate-summary-secret"
#     namespace = var.namespace
#   }
#   data = {
#     SUMMARY_AUTH_SECRET = base64encode(var.jwt_signing_secret)
#   }
# }
