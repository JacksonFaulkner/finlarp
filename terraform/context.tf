# Private bucket for the worker's output: GLB scenes and stills for local agents to read.
# Context is regenerable, so objects expire after 30 days.

resource "aws_s3_bucket" "context" {
  bucket = "finlarp-context-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "context" {
  bucket                  = aws_s3_bucket.context.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "context" {
  bucket = aws_s3_bucket.context.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "context" {
  bucket = aws_s3_bucket.context.id

  rule {
    id     = "expire-context"
    status = "Enabled"

    filter {}

    expiration {
      days = 30
    }
  }
}

data "aws_iam_policy_document" "worker_context" {
  statement {
    sid       = "ListContext"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.context.arn]
  }

  statement {
    sid       = "WriteReadContext"
    actions   = ["s3:PutObject", "s3:GetObject"]
    resources = ["${aws_s3_bucket.context.arn}/*"]
  }
}

resource "aws_iam_role_policy" "worker_context" {
  name   = "write-context-bucket"
  role   = aws_iam_role.worker.id
  policy = data.aws_iam_policy_document.worker_context.json
}

output "context_bucket" {
  description = "Worker output bucket: GLB and stills, keyed by git ref."
  value       = aws_s3_bucket.context.bucket
}
