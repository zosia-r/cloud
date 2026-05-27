variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "cloud-6-terraform"
}

variable "order_db_name" {
  type    = string
  default = "order_db"
}

variable "inventory_db_name" {
  type    = string
  default = "inventory_db"
}

variable "payment_db_name" {
  type    = string
  default = "payment_db"
}

variable "s3_bucket_name" {
  type    = string
  default = "cloud-6-terraform-bucket"
}

variable "rds_username" {
  type    = string
  default = "postgres"
}

variable "rds_password" {
  type      = string
  sensitive = true
}

variable "rds_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "rds_allocated_storage" {
  type    = number
  default = 20
}

variable "dynamodb_design_table" {
  type    = string
  default = "design_files"
}

variable "dynamodb_notification_table" {
  type    = string
  default = "notifications"
}

variable "aws_access_key_id" {
  type      = string
  sensitive = true
}

variable "aws_secret_access_key" {
  type      = string
  sensitive = true
}

variable "aws_session_token" {
  type      = string
  sensitive = true
  default   = ""
}
