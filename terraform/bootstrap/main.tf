# Run once, before the main stack. Creates the bucket that holds the main stack's
# remote state (versioned, encrypted, no public access). Its own state stays local
# (bootstrap/terraform.tfstate, gitignored); it is small and rarely changes.

variable "region" {
  description = "Must match the main stack's region."
  type        = string
  default     = "us-east-1"
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "state" {
  bucket = "finlarp-tfstate-${data.aws_caller_identity.current.account_id}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "state_bucket" {
  description = "Use as the bucket in the main stack's terraform init."
  value       = aws_s3_bucket.state.bucket
}
