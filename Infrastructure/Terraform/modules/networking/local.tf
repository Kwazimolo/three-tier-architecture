locals {
  public_subnets = [
    { cidr_block = "10.0.1.0/24", availability_zone = "eu-west-2a", name = "terraform-public-subnet-1" },
    { cidr_block = "10.0.2.0/24", availability_zone = "eu-west-2b", name = "terraform-public-subnet-2" }
  ]
  private_second_layer_subnets = [
    { cidr_block = "10.0.3.0/24", availability_zone = "eu-west-2a", name = "terraform-private-subnet-1" },
    { cidr_block = "10.0.4.0/24", availability_zone = "eu-west-2b", name = "terraform-private-subnet-2" }
  ]

  private_third_layer_subnets = [
    { cidr_block = "10.0.5.0/24", availability_zone = "eu-west-2a", name = "terraform-private-storage-subnet-1" },
    { cidr_block = "10.0.6.0/24", availability_zone = "eu-west-2b", name = "terraform-private-storage-subnet-2" }
  ]
}