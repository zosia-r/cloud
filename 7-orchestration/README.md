# 7-Orchestration

In this section, we orchestrate our microservices using Docker Swarm.

## Create a Docker Swarm Cluster
```docker swarm init
```

## Deploy the Stack
```docker deploy -c docker-compose.yml cukiernia
```

## Verify the Deployment
```docker stack service ls
```

## Verify the Services
```docker service ps cukiernia_order_service
```

## Scale the Services
```docker service scale cukiernia_payment_service=5
```

## Monitor resource usage
```docker stats
```

## Cleanup
```docker stack rm cukiernia
```
