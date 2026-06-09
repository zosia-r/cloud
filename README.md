# Cloud

A microservices project demonstrating message-broker patterns, FastAPI services, containerization, infrastructure as code, and serverless computing with AWS integration.

### Structure
- `1-message-broker/`: Message broker implementation with publisher and consumer patterns.
- `2-five-microservices/`: Five FastAPI microservices (design, inventory, notification, order, payment) for local development.
- `3-aws-s3/`: Services configured with AWS S3 for file storage.
- `4-aws-db/`: Services configured with AWS RDS (PostgreSQL) and AWS DynamoDB.
- `5-docker/`: Docker containerization for all services.
- `6-terraform/`: Infrastructure as Code deployment using Terraform for automated AWS provisioning (RDS, DynamoDB, S3, ECR, ECS).
- `7-orchestration/`: Docker Compose orchestration and deployment configuration.
- `8-serverless/`: AWS Lambda function for serverless computing.

### Technologies
- Python 3
- FastAPI
- AWS: S3, RDS (PostgreSQL), DynamoDB, ECR, ECS, Lambda
- Docker
- Terraform
- Docker Compose
- RabbitMQ
