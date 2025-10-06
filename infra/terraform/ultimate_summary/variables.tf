variable "namespace" {
  type        = string
  description = "Kubernetes namespace for ultimate summary service"
  default     = "ultimate-summary"
}

variable "jwt_signing_secret" {
  type        = string
  description = "JWT signing secret (provide via TF var or external secret store)"
  default     = ""
  sensitive   = true
}
