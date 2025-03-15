# Backbone VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  instance_tenancy     = "default"
  enable_dns_hostnames = true # Required for enabling prviate DNS for SSM
  enable_dns_support   = true # Required for enabling prviate DNS for SSM

  tags = {
    Name        = "OT-main-vpc-3tier"
    Environment = "Production"
    ManagedBy   = "OpenTofu"
    Project     = "3TierArchitecture"
    Owner       = "Infrastructure"
  }
}

# Internet gateway for VPC to have internet connectivity
resource "aws_internet_gateway" "main-igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "OT-main-igw"
    Environment = "Production"
    ManagedBy   = "OpenTofu"
    Tier        = "Network"
    Role        = "InternetGateway"
  }
}

# #### Public Subnets ####

# Public route table for Web tier
resource "aws_route_table" "public_rt_web" {
  count  = 2
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main-igw.id
  }

  tags = {
    Name        = "OT-public-rt-${count.index + 1}"
    AZ          = "az${count.index + 1}"
    Environment = "Production"
    ManagedBy   = "OpenTofu"
    Tier        = "Web"
    Type        = "Public"
  }
}

resource "aws_subnet" "public" {
  for_each = { for idx, subnet in local.public_subnets : idx => subnet }

  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr_block
  availability_zone = each.value.availability_zone

  tags = {
    Name        = "OT-public-subnet-${tonumber(each.key) + 1}"
    AZ          = "az${tonumber(each.key) + 1}"
    Environment = "Production"
    ManagedBy   = "OpenTofu"
    Tier        = "Web"
    Type        = "Public"
  }
}

resource "aws_route_table_association" "public_subnet_association" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public_rt_web[each.key].id
}

# Private Route table for Data/Storage Tier

# Private Route table for Application Tier

resource "aws_route_table" "private_app_rt" {
  count  = 2
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.app_tier_nat[count.index].id
  }

  tags = {
    Name        = "OT-private-app-rt-${count.index + 1}"
    AZ          = "az${count.index + 1}"
    Environment = "Production"
    ManagedBy   = "OpenTofu"
    Tier        = "Application"
    Type        = "Private"
  }
}

resource "aws_route_table" "private_db_rt" {
  count  = 2
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.db_tier_nat[count.index].id
  }

  tags = {
    Name        = "OT-private-db-rt-${count.index + 1}"
    AZ          = "az${count.index + 1}"
    Environment = "Production"
    ManagedBy   = "OpenTofu"
    Tier        = "Data"
    Type        = "Private"
  }
}

# #### Private Subnets ####

resource "aws_route_table_association" "private_app_subnet_association" {
  for_each       = aws_subnet.private_app
  subnet_id      = each.value.id
  route_table_id = aws_route_table.private_app_rt[each.key].id
}

resource "aws_subnet" "private_app" {
  for_each = { for idx, subnet in local.private_second_layer_subnets : idx => subnet }

  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr_block
  availability_zone = each.value.availability_zone

  tags = {
    Name        = "OT-private-app-subnet-${tonumber(each.key) + 1}"
    AZ          = "az${tonumber(each.key) + 1}"
    Environment = "Production"
    ManagedBy   = "OpenTofu"
    Tier        = "Application"
    Type        = "Private"
  }
}

resource "aws_route_table_association" "private_db_subnet_association" {
  for_each       = aws_subnet.private_db
  subnet_id      = each.value.id
  route_table_id = aws_route_table.private_db_rt[each.key].id
}

resource "aws_subnet" "private_db" {
  for_each = { for idx, subnet in local.private_third_layer_subnets : idx => subnet }

  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr_block
  availability_zone = each.value.availability_zone

  tags = {
    Name        = "OT-private-db-subnet-${tonumber(each.key) + 1}"
    AZ          = "az${tonumber(each.key) + 1}"
    Environment = "Production"
    ManagedBy   = "OpenTofu"
    Tier        = "Data"
    Type        = "Private"
  }
}

# NAT gateway for secured internet conncetivity to private subnets (Application Tier)

resource "aws_nat_gateway" "app_tier_nat" {
  count         = 2
  # subnet_id     = aws_subnet.private_app[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  allocation_id = aws_eip.app_nat_eip[count.index].id

  tags = {
    Name        = "OT-application-nat-gw-${count.index + 1}"
    Environment = "Production"
    ManagedBy   = "OpenTofu"
    Tier        = "Application"
    Role        = "NATGateway"
    AZ          = "az${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.main-igw]
}

resource "aws_eip" "app_nat_eip" {
  count  = 2
  domain = "vpc"

  tags = {
    Name        = "OT-application-nat-eip-${count.index + 1}"
    Environment = "Production"
    ManagedBy   = "OpenTofu"
    Tier        = "Application"
    Role        = "EIP-NAT"
    AZ          = "az${count.index + 1}"
  }
}

# NAT gateway for secured internet connectivity to Database tier

resource "aws_nat_gateway" "db_tier_nat" {
  count         = 2
  subnet_id     = aws_subnet.private_db[count.index].id
  allocation_id = aws_eip.db_nat_eip[count.index].id

  tags = {
    Name        = "OT-db-nat-gw-${count.index + 1}"
    Environment = "Production"
    ManagedBy   = "OpenTofu"
    Tier        = "Data"
    Role        = "NATGateway"
    AZ          = "az${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.main-igw]
}

resource "aws_eip" "db_nat_eip" {
  count  = 2
  domain = "vpc"

  tags = {
    Name        = "OT-storage-nat-eip-${count.index + 1}"
    Environment = "Production"
    ManagedBy   = "OpenTofu"
    Tier        = "Data"
    Role        = "EIP-NAT"
    AZ          = "az${count.index + 1}"
  }
}