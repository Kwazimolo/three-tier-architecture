resource "aws_key_pair" "app_key_pair" {
  key_name   = "dissertation_key"
  public_key = file("~/.ssh/id_rsa.pub") # Your public key file
}

resource "aws_instance" "app_tier_ec2" {
  count                  = 2
  ami                    = "ami-0fed63ea358539e44"
  instance_type          = "t2.micro"
  key_name               = "dissertation_key"
  subnet_id              = var.app_subnet_ids.app[count.index]
  vpc_security_group_ids = [var.security_group_ids.app]
  user_data              = file("${path.module}/services.sh")

  tags = {
    Name        = "app-instance-${count.index + 1}"
    AZ          = "az${count.index + 1}"
    Environment = "Production"
    ManagedBy   = "Terraform"
    Tier        = "Application"
    Role        = "WebServer"
    Project     = "3TierArchitecture"
  }
}

resource "aws_instance" "bastion_ec2" {
  count                       = 1
  ami                         = "ami-0fed63ea358539e44"
  instance_type               = "t2.micro"
  key_name                    = "dissertation_key"
  subnet_id                   = var.app_subnet_ids.bastion[0]
  associate_public_ip_address = true
  vpc_security_group_ids      = [var.security_group_ids.bastion]

  tags = {
    Name        = "bastion-instance-${count.index + 1}"
    AZ          = "az${count.index + 1}"
    Environment = "Production"
    ManagedBy   = "Terraform"
    Tier        = "Presentation"
    Role        = "BastionHost"
    Project     = "3TierArchitecture"
  }
}