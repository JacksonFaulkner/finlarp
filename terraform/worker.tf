# The worker box: m7i (16 vCPU / 64 GiB default), Ubuntu 24.04, no inbound ports.
# Shell: aws ssm start-session --target <instance id> (see the connect output).

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ssm_parameter" "ubuntu_ami" {
  name = "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id"
}

resource "aws_security_group" "worker" {
  name        = "finlarp-worker"
  description = "No inbound. Shell via SSM Session Manager."
  vpc_id      = data.aws_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "worker" {
  ami                    = data.aws_ssm_parameter.ubuntu_ami.value
  instance_type          = var.instance_type
  subnet_id              = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.worker.id]
  iam_instance_profile   = aws_iam_instance_profile.worker.name

  # Installs AWS CLI and writes /etc/finlarp/env from /finlarp/* parameters on first boot.
  user_data = templatefile("${path.module}/worker_init.sh.tftpl", {
    region   = var.region
    ssm_path = "/finlarp/"
  })
  user_data_replace_on_change = true

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required" # IMDSv2 only
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 200
    encrypted   = true
  }

  tags = {
    Name = "finlarp-worker"
  }

  lifecycle {
    # new Ubuntu AMIs publish constantly; don't replace the box for that
    ignore_changes = [ami]
  }
}
