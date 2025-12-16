region           = "eu-central-1"
container_image  = "ghcr.io/joeri-abbo/git-webhook-scanner:latest"
allowed_ip_cidrs = ["203.0.113.0/24", "198.51.100.1/32"]
use_existing_vpc = true
existing_vpc_id  = "vpc-029f758b9bfe412c8"
existing_public_subnet_ids = [
  "subnet-04cf9fedd0ac97327",
  "subnet-047ba44e3c1910b21"
]