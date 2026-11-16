variable "region" {
  description = "AWS region for the worker and its parameters."
  type        = string
  default     = "us-east-1"
}

variable "secrets" {
  description = "App secrets, keyed by the env var name the code reads. Values live in terraform/secrets.tfvars (gitignored)."
  type        = map(string)
  sensitive   = true
  default     = {}
}

variable "instance_type" {
  description = "Worker instance type."
  type        = string
  default     = "m7i.4xlarge"
}

variable "budget_email" {
  description = "Where budget alerts go. Empty disables the budget."
  type        = string
  default     = ""
}

variable "budget_limit_usd" {
  description = "Monthly account-wide cost alert threshold (USD)."
  type        = number
  default     = 200
}
