# 6-terraform

This folder contains Terraform scaffolding under `infra/`.
See `DEPLOYMENT.md` for the two‑stage AWS/Azure deployment process.

## Structure
```
infra/
  envs/
    dev/
    prod/
  stage1/
  stage2/
  modules/
```

## Quick start (dev)
```sh
cd infra/envs/dev
terraform init
terraform fmt
terraform validate
terraform plan
```

## Two‑stage deployment
Use `infra/stage1` to provision data services and `infra/stage2` to deploy microservices.
Stage 2 reads DB names/endpoints from stage 1 outputs.
Details are in `DEPLOYMENT.md`.
