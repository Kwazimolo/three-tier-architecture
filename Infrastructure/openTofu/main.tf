module "networking" {
  source = "./modules/networking"
}

module "security" {
  source         = "./modules/security"
  vpc_id         = module.networking.vpc_id
  app_subnet_ids = module.networking.private_app_subnet_ids

  depends_on = [module.networking]
}

module "compute" {
  source = "./modules/compute"
  security_group_ids = {
    app     = module.security.app_security_group_id
    bastion = module.security.bastion_security_group_id
  }
  app_subnet_ids            = {
    app     = module.networking.private_app_subnet_ids
    bastion = module.networking.public_subnet_ids
  }
  
  depends_on = [
    module.networking,
    module.security
  ]
}

module "load_balancing" {
  source = "./modules/load_balancer"

  security_group_ids = {
    alb = module.security.alb_security_group_id
  }
  vpc_id = module.networking.vpc_id
  public_subnet_ids = module.networking.public_subnet_ids
  app_instance_ids = module.compute.app_instance_ids

  depends_on = [ 
    module.networking,
    module.security,
    module.compute
   ]
}

module "database" {
  source = "./modules/database"
  security_group_ids = {
    db = module.security.db_security_group_id
  }
  database_subnet_ids = module.networking.private_db_subnet_ids

  depends_on = [ 
    module.networking
   ]
}