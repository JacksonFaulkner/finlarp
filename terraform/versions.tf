terraform {
  required_version = ">= 1.10"

  # bucket/key/region passed at init (see the init command in the stack README or the
  # bootstrap output). use_lockfile needs no DynamoDB table.
  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}
