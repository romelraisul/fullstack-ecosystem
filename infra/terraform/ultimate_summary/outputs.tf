output "namespace" {
  value       = kubernetes_namespace.ultimate.metadata[0].name
  description = "Namespace created for the ultimate summary service"
}
