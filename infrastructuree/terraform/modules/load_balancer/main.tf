# Loadbalancer facing the application tier where users will hit connections to. 
# In this project, it serves as the web tier entry point

resource "aws_lb" "app_alb" {
  name               = "App-Tier-LB"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.security_group_ids.alb]
  subnets            = values(var.public_subnet_ids)
  
  tags = {
    Name        = "App-Tier-LB"
    Environment = "Production"
    Tier        = "Web"
    ManagedBy   = "Terraform"
  }
}

# Load balancer target group

resource "aws_lb_target_group" "app_lb_tg" {
  name        = "App-Tier-tg"
  port        = 80
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = var.vpc_id

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }

  stickiness {
    enabled = false
    type    = "app_cookie"
  }
  
  tags = {
    Name        = "App-Tier-tg"
    Environment = "Production"
    Tier        = "Web"
    ManagedBy   = "Terraform"
  }
}

# Load balancer Listener to target group

resource "aws_lb_listener" "app_listener" {
  load_balancer_arn = aws_lb.app_alb.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_lb_tg.arn
  }
  
  tags = {
    Name        = "App-Tier-HTTP-Listener"
    Environment = "Production"
    Tier        = "Web"
    ManagedBy   = "Terraform"
  }
}

# Target group attachment to EC2 instances

resource "aws_lb_target_group_attachment" "app_tg_att" {
  count            = length(var.app_instance_ids)
  target_group_arn = aws_lb_target_group.app_lb_tg.arn
  target_id        = var.app_instance_ids[count.index]
  port             = 80
}