terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
  backend "s3" {
    bucket         = "lifelens-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "lifelens-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "lifelens"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ============================================================================
# VPC
# ============================================================================

data "aws_availability_zones" "available" {}

resource "aws_vpc" "lifelens" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "lifelens-vpc" }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.lifelens.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  tags = { Name = "lifelens-public-subnet-${count.index + 1}" }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.lifelens.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = { Name = "lifelens-private-subnet-${count.index + 1}" }
}

resource "aws_internet_gateway" "lifelens" {
  vpc_id = aws_vpc.lifelens.id
  tags   = { Name = "lifelens-igw" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.lifelens.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.lifelens.id
  }
  tags = { Name = "lifelens-public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ============================================================================
# EKS CLUSTER
# ============================================================================

resource "aws_iam_role" "eks_cluster" {
  name = "lifelens-eks-cluster-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_eks_cluster" "lifelens" {
  name     = "lifelens-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  vpc_config {
    subnet_ids = concat(aws_subnet.public[*].id, aws_subnet.private[*].id)
  }
  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy]
}

# ============================================================================
# RDS POSTGRESQL
# ============================================================================

resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "aws_secretsmanager_secret" "db_password" {
  name = "lifelens/db/password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

resource "aws_db_subnet_group" "lifelens" {
  name       = "lifelens-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  tags       = { Name = "lifelens-db-subnet-group" }
}

resource "aws_security_group" "rds" {
  name        = "lifelens-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = aws_vpc.lifelens.id
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "lifelens-rds-sg" }
}

resource "aws_db_instance" "lifelens" {
  identifier        = "lifelens-postgres"
  engine            = "postgres"
  engine_version    = "16.1"
  instance_class    = var.db_instance_class
  allocated_storage = 100
  storage_type      = "gp3"

  db_name  = "lifelens_db"
  username = "lifelens"
  password = random_password.db_password.result

  multi_az               = true
  publicly_accessible    = false
  skip_final_snapshot    = false
  final_snapshot_identifier = "lifelens-final-snapshot"

  db_subnet_group_name   = aws_db_subnet_group.lifelens.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 30
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = { Name = "lifelens-postgres" }
}

# ============================================================================
# ELASTICACHE REDIS
# ============================================================================

resource "aws_elasticache_subnet_group" "lifelens" {
  name       = "lifelens-cache-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_security_group" "redis" {
  name        = "lifelens-redis-sg"
  description = "Security group for Redis"
  vpc_id      = aws_vpc.lifelens.id
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "lifelens-redis-sg" }
}

resource "aws_elasticache_cluster" "lifelens" {
  cluster_id           = "lifelens-redis"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.lifelens.name
  security_group_ids = [aws_security_group.redis.id]

  tags = { Name = "lifelens-redis" }
}

# ============================================================================
# CLOUDWATCH
# ============================================================================

resource "aws_cloudwatch_log_group" "lifelens_api" {
  name              = "/aws/eks/lifelens-api"
  retention_in_days = 30
  tags              = { Name = "lifelens-api-logs" }
}

# ============================================================================
# OUTPUTS
# ============================================================================

output "rds_endpoint" {
  value       = aws_db_instance.lifelens.endpoint
  description = "RDS database endpoint"
}

output "eks_cluster_name" {
  value       = aws_eks_cluster.lifelens.name
  description = "EKS cluster name"
}

output "redis_endpoint" {
  value       = aws_elasticache_cluster.lifelens.cache_nodes[0].address
  description = "Redis endpoint"
}
