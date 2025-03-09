terraform {
  backend "s3" {
    bucket         = "tf-state-3tier-architecture"
    key            = "opentofu/terraform.tfstate"
    region         = "eu-west-2"
    encrypt        = true
  }
}