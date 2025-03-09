terraform {
  backend "s3" {
    bucket         = "tf-state-3tier-architecture"
    key            = "terraform/terraform.tfstate"
    region         = "eu-west-2"
    encrypt        = true
  }
}