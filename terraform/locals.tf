locals {
  name_prefix = var.project_name

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }

  vpc_id = var.use_existing_vpc ? var.existing_vpc_id : one(aws_vpc.main[*].id)

  public_subnet_ids = var.use_existing_vpc ? var.existing_public_subnet_ids : aws_subnet.public[*].id
}
