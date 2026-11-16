# One SSM Parameter Store SecureString per non-empty entry in var.secrets.
# Standard tier is free. Read at /finlarp/<ENV_VAR_NAME>.
resource "aws_ssm_parameter" "secret" {
  # keys are env var names (not sensitive), so unwrap them for for_each.
  for_each = nonsensitive(toset([for k, v in var.secrets : k if v != ""]))

  name  = "/finlarp/${each.key}"
  type  = "SecureString"
  tier  = "Standard"
  value = var.secrets[each.key]
}
