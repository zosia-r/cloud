output "order_rds_endpoint" {
  value = aws_db_instance.order.address
}

output "inventory_rds_endpoint" {
  value = aws_db_instance.inventory.address
}

output "payment_rds_endpoint" {
  value = aws_db_instance.payment.address
}

output "rds_port" {
  value = aws_db_instance.order.port
}

output "rds_username" {
  value = var.rds_username
}

output "order_db_name" {
  value = var.order_db_name
}

output "inventory_db_name" {
  value = var.inventory_db_name
}

output "payment_db_name" {
  value = var.payment_db_name
}

output "dynamodb_design_table" {
  value = aws_dynamodb_table.designs.name
}

output "dynamodb_design_table_arn" {
  value = aws_dynamodb_table.designs.arn
}

output "dynamodb_notification_table" {
  value = aws_dynamodb_table.notifications.name
}

output "dynamodb_notification_table_arn" {
  value = aws_dynamodb_table.notifications.arn
}

output "s3_design_bucket" {
  value = aws_s3_bucket.designs.bucket
}

output "s3_design_bucket_arn" {
  value = aws_s3_bucket.designs.arn
}

output "rabbitmq_endpoint" {
  value = try(aws_mq_broker.rabbitmq[0].instances[0].endpoints[0], "")
}
