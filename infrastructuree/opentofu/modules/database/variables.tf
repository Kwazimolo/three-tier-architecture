variable "database_subnet_ids" {
  description = "Map of private DB subnet IDs"
  type        = map(string)
}

variable "security_group_ids" {
  description = "Map of security group IDs"
  type        = object({
    db = string
  })
}