variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
  type        = string
}

variable "environment" {
  description = "Environment name"
  default     = "production"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  default     = "10.0.0.0/16"
  type        = string
}

variable "db_instance_class" {
  description = "RDS instance class"
  default     = "db.t3.large"
  type        = string
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  default     = "cache.t3.medium"
  type        = string
}
