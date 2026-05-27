variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "cloud-6-terraform"
}

variable "aws_account_id" {
  type = string
}

variable "stage1_state_path" {
  type    = string
  default = "../stage1/terraform.tfstate"
}

variable "rds_password" {
  type      = string
  sensitive = true
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
