# RDS database instance for the data tier
resource "aws_db_subnet_group" "data_tier_subnet_group" {
  name       = "data-tier-subnet-group"
  subnet_ids = values(var.database_subnet_ids)

  tags = {
    Name        = "Data Tier DB Subnet Group"
    Environment = "Production"
    Tier        = "Data"
    ManagedBy   = "Terraform"
    Role        = "DatabaseSubnetGroup"
  }
}
 
#  Create RDS instances
resource "aws_db_instance" "data_tier_db" {
  count                      = 2
  identifier                 = "data-tier-db-${count.index + 1}"
  allocated_storage          = 10
  db_name                    = "data_tier_db"
  engine                     = "mysql"
  engine_version             = "8.0.32"
  instance_class             = "db.t3.micro"
  username                   = "admin"
  manage_master_user_password = true
  db_subnet_group_name       = aws_db_subnet_group.data_tier_subnet_group.name
  vpc_security_group_ids     = [var.security_group_ids.db]
  multi_az                   = false
  publicly_accessible        = false
  skip_final_snapshot        = true
  
  tags = {
    Name        = "Data-Tier-DB-${count.index + 1}"
    Environment = "Production"
    Tier        = "Data"
    ManagedBy   = "Terraform"
    Role        = "MySQL-Database"
    Replica     = count.index == 0 ? "Primary" : "Secondary"
  }
}