output "app_security_group_id" {
  description = "The ID of the App security group"
  value       = aws_security_group.app_sg.id
}

output "bastion_security_group_id" {
  description = "The ID of the App security group"
  value       = aws_security_group.bastion_sg.id
}

output "alb_security_group_id" {
  description = "The ID of the ALB security group"
  value       = aws_security_group.alb_sg.id
}

output "db_security_group_id" {
  description = "The ID of the DB security group"
  value       = aws_security_group.db_sg.id
}

# output "instance_profile_name" {
#   description = "Name of the EC2 instance profile for SSM"
#   value       = aws_iam_instance_profile.ec2_ssm_profile.name
# }

# output "instance_profile_arn" {
#   description = "ARN of the EC2 instance profile for SSM"
#   value       = aws_iam_instance_profile.ec2_ssm_profile.arn
# }