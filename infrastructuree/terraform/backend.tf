terraform {
  backend "s3" {
    bucket         = "tf-state-3tier-architecture"
    key            = "terraform/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
  }
}