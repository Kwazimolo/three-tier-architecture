variable "security_group_ids" {
  description = "Map of security group IDs for app and bastion instances"
  type = object({
    app     = string
    bastion = string
  })
}

variable "app_subnet_ids" {
  description = "Map of subnet IDs for app and bastion instances"
  type = object({
    app     = map(string)
    bastion = map(string)
  })
}