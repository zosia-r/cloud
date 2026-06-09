# Deployment - AWS Application Deployment Guide

Deployment consists of **2 stages**:
1. **Stage 1**: Creating databases and storage services (RDS PostgreSQL, DynamoDB, S3, RabbitMQ)
2. **Stage 2**: Deploying services (Order, Design, Inventory, Payment, Notification) to AWS

---

## Stage 1 - Creating Databases on AWS

Terraform will create the following AWS resources:
- 3 PostgreSQL databases (order, inventory, payment)
- 2 DynamoDB tables (design, notification)
- S3 bucket (for project file storage)
- RabbitMQ (for inter-service communication)

### Step 1: Navigate to stage1 folder

```bash
cd 6-terraform/terraform/stage1
```

### Step 2: Configure terraform.tfvars


### Step 3: Authenticate with AWS

```bash
aws configure
```

### Step 4: Initialize and deploy infrastructure

Initialize Terraform (run once):

```bash
terraform init
```

Create the infrastructure:

```bash
terraform apply
```

Confirm the plan by entering `yes`.

Expected output after 5-15 minutes:
```
Apply complete! Resources: XX added, 0 changed, 0 destroyed.
```

Stage 1 is now complete. Databases have been created successfully.

---

## Stage 2 - Deploying Services

In this stage, you will:
1. Build Docker images for each service
2. Push images to AWS ECR (Elastic Container Registry)
3. Deploy services to AWS using Terraform

### Step 1: Build Docker images

Navigate to the docker folder:

```bash
cd 5-docker
```

Build each service image sequentially:

```bash
docker build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/order_service -t order:latest .
docker build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/design_service -t design:latest .
docker build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/inventory_service -t inventory:latest .
docker build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/payment_service -t payment:latest .
docker build -f docker/base/Dockerfile --build-arg SERVICE_DIR=services/notification_service -t notification:latest .
```

Verify all images were built successfully:

```bash
docker images | grep -E "order|design|inventory|payment|notification"
```

You should see 5 images listed.

### Step 2: Prepare AWS ECR (image repository)

Retrieve your AWS Account ID:

```bash
aws sts get-caller-identity --query Account --output text
```

Save this value (format: 123456789012). You will need it for the next steps.

Create ECR repositories for each service:

```bash
aws ecr create-repository --repository-name order --region us-east-1
aws ecr create-repository --repository-name design --region us-east-1
aws ecr create-repository --repository-name inventory --region us-east-1
aws ecr create-repository --repository-name payment --region us-east-1
aws ecr create-repository --repository-name notification --region us-east-1
```

### Step 3: Authenticate Docker with AWS ECR

Configure docker to push images to AWS:

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 265068570806.dkr.ecr.us-east-1.amazonaws.com
```

Expected output: `Login Succeeded`

### Step 4: Tag and push images to AWS ECR

For each service, tag the local image and push to AWS:

For each service, tag the local image and push to AWS:

```bash
docker tag order:latest 265068570806.dkr.ecr.us-east-1.amazonaws.com/order:latest
docker push 265068570806.dkr.ecr.us-east-1.amazonaws.com/order:latest

docker tag design:latest 265068570806.dkr.ecr.us-east-1.amazonaws.com/design:latest
docker push 265068570806.dkr.ecr.us-east-1.amazonaws.com/design:latest

docker tag inventory:latest 265068570806.dkr.ecr.us-east-1.amazonaws.com/inventory:latest
docker push 265068570806.dkr.ecr.us-east-1.amazonaws.com/inventory:latest

docker tag payment:latest 265068570806.dkr.ecr.us-east-1.amazonaws.com/payment:latest
docker push 265068570806.dkr.ecr.us-east-1.amazonaws.com/payment:latest

docker tag notification:latest 265068570806.dkr.ecr.us-east-1.amazonaws.com/notification:latest
docker push 265068570806.dkr.ecr.us-east-1.amazonaws.com/notification:latest
```

Expected output for each service: `Pushed`

### Step 5: Configure Terraform for stage2

Navigate to the stage2 folder:

```bash
cd 6-terraform/terraform/stage2
```

Configure the `terraform.tfvars` file.

### Step 6: Deploy services to AWS

Initialize Terraform:

```bash
terraform init
```

Deploy the services:

```bash
terraform apply
```

Confirm by entering `yes`.

Expected output after 10-20 minutes:
```
Apply complete! Resources: XX added, 0 changed, 0 destroyed.
```

### Step 7: Retrieve service endpoints

Display all outputs:

```bash
terraform output
```

Or retrieve only service URLs:

```bash
terraform output service_urls
```

Output will be similar to:
```
service_urls = {
  "design"       = "http://cukiernia-alb-12345.us-east-1.elb.amazonaws.com:8002"
  "inventory"    = "http://cukiernia-alb-12345.us-east-1.elb.amazonaws.com:8003"
  "notification" = "http://cukiernia-alb-12345.us-east-1.elb.amazonaws.com:8005"
  "order"        = "http://cukiernia-alb-12345.us-east-1.elb.amazonaws.com:8001"
  "payment"      = "http://cukiernia-alb-12345.us-east-1.elb.amazonaws.com:8004"
}
```

Test service health by accessing the `/health` endpoint:
```
http://cukiernia-alb-12345.us-east-1.elb.amazonaws.com:8001/health
```

Update Postman collection variables with the new service URLs.

---

## Cleanup

After testing is complete, remove all AWS resources:

```bash
cd 6-terraform/terraform/stage2
terraform destroy
cd ../stage1
terraform destroy
```

Confirm by entering `yes` when prompted.

All AWS resources will be deleted.
