# Security group for web/application tier servers

data "aws_region" "current" {}

# Securtiy group for Bastion Host

resource "aws_security_group" "bastion_sg" {
  name        = "OT-bastion_sg"
  description = "Security group for Bastion Host on the presentation tier"
  vpc_id      = var.vpc_id

  ingress {
    description = "SSH into the instance"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["209.35.86.151/32"]
  }

  egress {
    description = "Allow Outbound connectivity"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "OT-bastion_sg"
    Environment = "Production"
    Tier        = "Presentation"
    ManagedBy   = "OpenTofu"
    Role        = "Bastion"
  }
}

# Securtiy group for App Host

resource "aws_security_group" "app_sg" {
  name        = "OT-app-sg"
  description = "Security group for application servers on the application tier"
  vpc_id      = var.vpc_id

  ingress {
    description     = "SSH into the instance from bastion host"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion_sg.id]
  }

  ingress {
    description     = "Allow connectivity from ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    description = "Allow Outbound connectivity"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "OT-app-sg"
    Environment = "Production"
    Tier        = "Application"
    ManagedBy   = "OpenTofu"
    Role        = "WebServer"
  }
}

# Security group for Load balancer facing the application tier

resource "aws_security_group" "alb_sg" {
  name        = "OT-alb-sg"
  description = "Security group for load balancer on the web tier"
  vpc_id      = var.vpc_id

  ingress {
    description = "Access to webpage"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all Outbound connectivity"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "OT-alb-sg"
    Environment = "Production"
    Tier        = "Web"
    ManagedBy   = "OpenTofu"
    Role        = "LoadBalancer"
  }
}

# Security group for data tier database

resource "aws_security_group" "db_sg" {
  name        = "OT-db-sg"
  description = "Allow application tier to communicate to database tier"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Allow connection to database"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  tags = {
    Name        = "OT-db-sg"
    Environment = "Production"
    Tier        = "Data"
    ManagedBy   = "OpenTofu"
    Role        = "Database"
  }
}

resource "aws_security_group" "vpc_endpoints_sg" {
  name        = "OT-vpce-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
    description     = "Allow HTTPS from EC2 instances"
  }

  tags = {
    Name        = "OT-vnet-sg"
    Environment = "Production"
    Tier        = "Network"
    ManagedBy   = "OpenTofu"
    Role        = "VPCEndpoint"
  }
}