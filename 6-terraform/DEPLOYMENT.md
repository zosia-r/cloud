# Deployment process (AWS / Azure) – 2 stages

This document describes a **two‑stage deployment** using Docker images from `5-docker` and Terraform.

> **Stage 1** creates databases and shared services (RDS / DynamoDB / S3 / RabbitMQ).  
> **Stage 2** deploys microservices (ECS/Fargate on AWS or Container Apps/AKS on Azure).

---

## ✅ Stage 1 (AWS) – data services
Terraform folder: `cloud/6-terraform/infra/stage1`

Creates:
- **RDS PostgreSQL** (3 instances: order/inventory/payment)
- **DynamoDB** tables (designs + notifications)
- **S3** bucket for design uploads
- **Amazon MQ (RabbitMQ)** – optional (`enable_rabbitmq=true`)

### Run
```/dev/null/terraform-stage1.sh#L1-6
cd /home/felix/repo/cloud/6-terraform/infra/stage1
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars (passwords, region)
terraform init
terraform apply
```

### Outputs (used by Stage 2)
- `order_rds_endpoint`, `inventory_rds_endpoint`, `payment_rds_endpoint`
- `rds_port`
- `order_db_name`, `inventory_db_name`, `payment_db_name`
- `dynamodb_design_table`, `dynamodb_notification_table`
- `s3_design_bucket`
- `rabbitmq_endpoint` (if enabled)

> If your DB is **not** in AWS, you can skip Stage 1 and provide external endpoints in Stage 2.

---

## ✅ Stage 2 (AWS) – microservices
Terraform folder: `cloud/6-terraform/infra/stage2`

Deploys:
- **ECS Fargate** services
- **Application Load Balancer** with listeners on ports `8001–8005`
- CloudWatch log groups
- IAM roles for DynamoDB + S3

### 1) Build Docker images (from list #5)
```/dev/null/build-images.sh#L1-8
cd /home/felix/repo/cloud/5-docker

docker build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/order_service -t order:latest .
docker build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/design_service -t design:latest .
docker build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/inventory_service -t inventory:latest .
docker build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/payment_service -t payment:latest .
docker build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/notification_service -t notification:latest .
```

### 2) Push images to a registry (ECR example)
```/dev/null/push-ecr.sh#L1-9
AWS_REGION=us-east-1
ACCOUNT_ID=123456789012

aws ecr create-repository --repository-name order --region $AWS_REGION
aws ecr create-repository --repository-name design --region $AWS_REGION
# ...repeat for inventory/payment/notification

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

docker tag order:latest ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/order:latest
# ...repeat for all services

docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/order:latest
# ...repeat for all services
```

### 3) Deploy with Terraform
```/dev/null/terraform-stage2.sh#L1-6
cd /home/felix/repo/cloud/6-terraform/infra/stage2
cp terraform.tfvars.example terraform.tfvars
# edit image URIs + db password + rabbitmq_url (if used)
# db names and username are taken from stage1 outputs
terraform init
terraform apply
```

### Service URLs
Terraform outputs:
- `alb_dns_name`
- `service_urls` → map of URLs (ports 8001–8005)


## Notes
- Current Terraform uses **local state**. If you need S3 backend + DynamoDB locks, tell me and I’ll add it.
- Services expect env vars:
  - `ORDER_DB_HOST`, `INVENTORY_DB_HOST`, `PAYMENT_DB_HOST`, `RDS_USER`, `RDS_PASSWORD`, `RDS_PORT`
  - `DESIGN_TABLE`, `NOTIFICATION_TABLE`, `S3_BUCKET_NAME`, `AWS_REGION`
  - `RABBITMQ_URL` (optional)
