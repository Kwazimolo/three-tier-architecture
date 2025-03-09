output "vpc_id" {
  value       = aws_vpc.main.id
  description = "The ID of the VPC created by Terraform."
}

output "public_subnet_ids" {
  value = { for k, v in aws_subnet.public : k => v.id }
}

output "private_app_subnet_ids" {
  value = { for k, v in aws_subnet.private_app : k => v.id }
}

output "private_db_subnet_ids" {
  value = { for k, v in aws_subnet.private_db : k => v.id }
}