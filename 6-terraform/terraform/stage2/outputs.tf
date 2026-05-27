output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "service_urls" {
  value = {
    for key, svc in local.services :
    key => "http://${aws_lb.main.dns_name}:${svc.port}"
  }
}
