output "app_instance_ids" {
  description = "IDs of the EC2 instances in the app tier"
  value       = aws_instance.app_tier_ec2[*].id
}