data "terraform_remote_state" "stage1" {
  backend = "local"
  config = {
    path = var.stage1_state_path
  }
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

locals {
  container_port         = 8000
  lab_role_arn           = "arn:aws:iam::${var.aws_account_id}:role/LabRole"
  ecr_registry           = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
  order_rds_endpoint     = data.terraform_remote_state.stage1.outputs.order_rds_endpoint
  inventory_rds_endpoint = data.terraform_remote_state.stage1.outputs.inventory_rds_endpoint
  payment_rds_endpoint   = data.terraform_remote_state.stage1.outputs.payment_rds_endpoint
  rds_port               = data.terraform_remote_state.stage1.outputs.rds_port
  rds_username           = data.terraform_remote_state.stage1.outputs.rds_username
  order_db_name          = data.terraform_remote_state.stage1.outputs.order_db_name
  inventory_db_name      = data.terraform_remote_state.stage1.outputs.inventory_db_name
  payment_db_name        = data.terraform_remote_state.stage1.outputs.payment_db_name
  s3_bucket              = data.terraform_remote_state.stage1.outputs.s3_design_bucket
  design_table           = data.terraform_remote_state.stage1.outputs.dynamodb_design_table
  notify_table           = data.terraform_remote_state.stage1.outputs.dynamodb_notification_table

  rabbitmq_env = var.rabbitmq_url == "" ? [] : [
    { name = "RABBITMQ_URL", value = var.rabbitmq_url }
  ]

  common_env = concat([
    { name = "AWS_REGION", value = var.aws_region }
  ], local.rabbitmq_env)

  services = {
    order = {
      name  = "order"
      port  = 8001
      image = "${local.ecr_registry}/order:latest"
      env = concat(local.common_env, [
        { name = "ORDER_DB_HOST", value = local.order_rds_endpoint },
        { name = "RDS_PORT", value = tostring(local.rds_port) },
        { name = "ORDER_DB_NAME", value = local.order_db_name },
        { name = "RDS_USER", value = local.rds_username },
        { name = "RDS_PASSWORD", value = var.rds_password }
      ])
    }
    design = {
      name  = "design"
      port  = 8002
      image = "${local.ecr_registry}/design:latest"
      env = concat(local.common_env, [
        { name = "DESIGN_TABLE", value = local.design_table },
        { name = "S3_BUCKET_NAME", value = local.s3_bucket }
      ])
    }
    inventory = {
      name  = "inventory"
      port  = 8003
      image = "${local.ecr_registry}/inventory:latest"
      env = concat(local.common_env, [
        { name = "INVENTORY_DB_HOST", value = local.inventory_rds_endpoint },
        { name = "RDS_PORT", value = tostring(local.rds_port) },
        { name = "INVENTORY_DB_NAME", value = local.inventory_db_name },
        { name = "RDS_USER", value = local.rds_username },
        { name = "RDS_PASSWORD", value = var.rds_password }
      ])
    }
    payment = {
      name  = "payment"
      port  = 8004
      image = "${local.ecr_registry}/payment:latest"
      env = concat(local.common_env, [
        { name = "PAYMENT_DB_HOST", value = local.payment_rds_endpoint },
        { name = "RDS_PORT", value = tostring(local.rds_port) },
        { name = "PAYMENT_DB_NAME", value = local.payment_db_name },
        { name = "RDS_USER", value = local.rds_username },
        { name = "RDS_PASSWORD", value = var.rds_password }
      ])
    }
    notification = {
      name  = "notification"
      port  = 8005
      image = "${local.ecr_registry}/notification:latest"
      env = concat(local.common_env, [
        { name = "NOTIFICATION_TABLE", value = local.notify_table }
      ])
    }
  }
}

resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"
}


resource "aws_cloudwatch_log_group" "service" {
  for_each = local.services
  name     = "/ecs/${var.project_name}/${each.key}"
}

resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-alb-"
  vpc_id      = data.aws_vpc.default.id

  dynamic "ingress" {
    for_each = local.services
    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs" {
  name_prefix = "${var.project_name}-ecs-"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port       = local.container_port
    to_port         = local.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.default.ids
}

resource "aws_lb_target_group" "service" {
  for_each    = local.services
  name        = "${var.project_name}-${each.key}"
  port        = local.container_port
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  health_check {
    path                = "/health"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "service" {
  for_each          = local.services
  load_balancer_arn = aws_lb.main.arn
  port              = each.value.port
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.service[each.key].arn
  }
}

resource "aws_ecs_task_definition" "service" {
  for_each                 = local.services
  family                   = "${var.project_name}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.service_cpu
  memory                   = var.service_memory
  execution_role_arn       = local.lab_role_arn
  task_role_arn            = local.lab_role_arn

  container_definitions = jsonencode([
    {
      name      = each.key
      image     = each.value.image
      essential = true
      portMappings = [
        {
          containerPort = local.container_port
          hostPort      = local.container_port
          protocol      = "tcp"
        }
      ]
      environment = each.value.env
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.service[each.key].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "service" {
  for_each        = local.services
  name            = "${var.project_name}-${each.key}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.service[each.key].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.service[each.key].arn
    container_name   = each.key
    container_port   = local.container_port
  }

  depends_on = [aws_lb_listener.service]
}
