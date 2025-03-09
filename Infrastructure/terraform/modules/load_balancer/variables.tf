variable "security_group_ids" {
  description = "Map of security group IDs"
  type        = object({
    alb = string
  })
}

variable "vpc_id" {
  description = "The ID of the VPC"
  type        = string
}

variable "public_subnet_ids" {
  description = "Map of public subnet IDs"
  type        = map(string)
}

variable "app_instance_ids" {
  description = "List of app tier instance IDs"
  type        = list(string)
}