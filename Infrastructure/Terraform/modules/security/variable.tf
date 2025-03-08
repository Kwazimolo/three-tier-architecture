variable "vpc_id" {

  description = "The ID of the VPC"
  type        = string
}

variable "app_subnet_ids" {
  description = "List of subnet IDs for the EC2 instances"
  type        = map(string)
}