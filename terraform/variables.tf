variable "region" {
  description = "AWS region to deploy resources into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for tagging and naming"
  type        = string
  default     = "github-webhook"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "api_stage_name" {
  description = "Stage name for the REST API (alphanumeric, hyphen, underscore)"
  type        = string
  default     = "prod"

  validation {
    condition     = can(regex("^[A-Za-z0-9_-]+$", var.api_stage_name))
    error_message = "api_stage_name must contain only letters, numbers, hyphens, or underscores."
  }
}

variable "container_image" {
  description = "Full container image URI (e.g., ECR URI)"
  type        = string
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8000
}

variable "desired_count" {
  description = "Number of Fargate tasks"
  type        = number
  default     = 1
}

variable "cpu" {
  description = "Fargate task CPU units"
  type        = number
  default     = 512
}

variable "memory" {
  description = "Fargate task memory (MiB)"
  type        = number
  default     = 1024
}

variable "allowed_ip_cidrs" {
  description = "Additional CIDR blocks to allow (manual allowlist). GitHub hook IPs can be auto-added separately."
  type        = list(string)
  default     = []
}

variable "include_github_hook_ips" {
  description = "Automatically include GitHub webhook source IP ranges from https://api.github.com/meta (hooks)."
  type        = bool
  default     = true
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "use_existing_vpc" {
  description = "Set true to use an existing VPC and subnets instead of creating new ones"
  type        = bool
  default     = false
}

variable "existing_vpc_id" {
  description = "ID of the existing VPC to deploy into when use_existing_vpc is true"
  type        = string
  default     = null

  validation {
    condition     = var.use_existing_vpc == false || (var.use_existing_vpc && var.existing_vpc_id != null && trimspace(var.existing_vpc_id) != "")
    error_message = "When use_existing_vpc is true, existing_vpc_id must be provided."
  }
}

variable "existing_public_subnet_ids" {
  description = "List of existing public subnet IDs to use when use_existing_vpc is true"
  type        = list(string)
  default     = []

  validation {
    condition     = var.use_existing_vpc == false || (var.use_existing_vpc && length(var.existing_public_subnet_ids) > 0)
    error_message = "When use_existing_vpc is true, provide at least one subnet ID in existing_public_subnet_ids."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default = [
    "10.0.1.0/24",
    "10.0.2.0/24"
  ]
}

variable "health_check_path" {
  description = "Path ALB uses for health checks"
  type        = string
  default     = "/health"
}
