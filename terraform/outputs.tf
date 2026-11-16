output "worker_instance_id" {
  description = "EC2 instance id of the worker."
  value       = aws_instance.worker.id
}

output "connect" {
  description = "Open a shell on the worker (needs the AWS CLI and the session-manager-plugin)."
  value       = "aws ssm start-session --target ${aws_instance.worker.id} --region ${var.region}"
}

output "secret_parameters" {
  description = "SSM parameter names created from var.secrets (values are not shown)."
  value       = [for p in aws_ssm_parameter.secret : p.name]
}
