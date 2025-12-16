output "api_gateway_url" {
  description = "Invoke URL for the REST API"
  value       = "https://${aws_api_gateway_rest_api.this.id}.execute-api.${var.region}.amazonaws.com/${var.api_stage_name}"
}

output "load_balancer_dns" {
  description = "Public DNS name of the application load balancer"
  value       = aws_lb.app.dns_name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.app.name
}
