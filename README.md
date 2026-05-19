# Cukiernia Microservices (Cloud)

A compact microservices project containing several FastAPI services, a simple message-broker example, and Docker / AWS integration.

### Structure
- `1-message-broker/`: lightweight message broker examples (publisher, consumer, events).
- `2-five-microservices/`: a working set of five FastAPI microservices (design, inventory, notification, order, payment) used for local development and Postman testing.
- `3-aws-s3/`: the same services configured to use AWS S3 for uploads.
- `4-aws-db/`: the same services configured to use AWS RDS (PostgreSQL)  and AWS DynamoDB for data storage.
- `5-docker/`: Docker for containerizing and running the services together.

### Technologies
- Python 3
- FastAPI
- AWS: S3, RDS (PostgreSQL), DynamoDB
- Docker