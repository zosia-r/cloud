variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "cloud-6-terraform"
}

variable "stage1_state_path" {
  type    = string
  default = "../stage1/terraform.tfstate"
}

variable "order_image" {
  type = string
}

variable "design_image" {
  type = string
}

variable "inventory_image" {
  type = string
}

variable "payment_image" {
  type = string
}

variable "notification_image" {
  type = string
}

variable "rds_password" {
  type      = string
  sensitive = true
}

variable "create_iam_roles" {
  type    = bool
  default = true
}

variable "ecs_execution_role_arn" {
  type    = string
  default = ""
  validation {
    condition     = var.create_iam_roles || var.ecs_execution_role_arn != ""
    error_message = "ecs_execution_role_arn must be set when create_iam_roles is false."
  }
}

variable "ecs_task_role_arn" {
  type    = string
  default = ""
  validation {
    condition     = var.create_iam_roles || var.ecs_task_role_arn != ""
    error_message = "ecs_task_role_arn must be set when create_iam_roles is false."
  }
}

variable "service_cpu" {
  type    = number
  default = 256
}

variable "service_memory" {
  type    = number
  default = 512
}

variable "rabbitmq_url" {
  type    = string
  default = ""
}


variable "aws_access_key_id" {
  type    = string
  default = ""
}


variable "aws_secret_access_key" {
  type    = string
  default = ""
}

variable "aws_session_token" {
  type    = string
  default = ""
}
