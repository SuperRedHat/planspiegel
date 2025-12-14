# Kubernetes Deployment for Planspiegel Backend

## Overview
This repository contains Kubernetes configurations for deploying the Planspiegel backend. The setup includes PostgreSQL, Redis, and the backend API service, all running on a Kubernetes cluster.

## Architecture
The deployment consists of the following Kubernetes components:

- **Deployments**
  - `planspiegel-backend`: Runs the backend API.
  - `planspiegel-postgres`: Runs PostgreSQL as the database.
  - `planspiegel-redis`: Runs Redis for caching and session storage.
  - `planspiegel-migrations`: Runs database migrations using Alembic.
- **Services**
  - `planspiegel_backend`: Exposes the backend API.
  - `planspiegel_postgres`: Exposes PostgreSQL internally.
  - `planspiegel_redis`: Exposes Redis internally.
- **ConfigMaps**
  - `env-docker-configmap.yaml`: Stores environment variables.
- **Persistent Volume Claims (PVCs)**
  - `planspiegel-postgres-data`: Stores PostgreSQL data.
  - `planspiegel-redis-data`: Stores Redis data.

## Prerequisites
Ensure you have the following installed:

- Kubernetes cluster (Minikube, Kind, or a cloud provider cluster)
- `kubectl` CLI tool
- `Helm` (if using Helm charts)

## Deployment Instructions

### 1. Apply ConfigMaps and Secrets
```sh
kubectl apply -f env-docker-configmap.yaml
```

### 2. Deploy PostgreSQL
```sh
kubectl apply -f planspiegel-postgres-deployment.yaml
kubectl apply -f planspiegel_postgres-service.yaml
```

### 3. Deploy Redis
```sh
kubectl apply -f planspiegel-redis-deployment.yaml
kubectl apply -f planspiegel_redis-service.yaml
```

### 4. Deploy Backend API
```sh
kubectl apply -f planspiegel-backend-deployment.yaml
kubectl apply -f planspiegel_backend-service.yaml
```

### 5. Deploy Database Migrations
```sh
kubectl apply -f planspiegel-migrations-deployment.yaml
```

## Accessing the Backend API
To access the backend service locally, use `kubectl port-forward`:
```sh
kubectl port-forward svc/planspiegel_backend 8000:8000
```
Then, open your browser and go to:
```
http://localhost:8000
```

If using an Ingress Controller, update `ingress.yaml` and apply it:
```sh
kubectl apply -f ingress.yaml
```

## Environment Variables
Environment variables are managed using `ConfigMap`. Key variables include:

- `FRONTEND_URL`: URL of the frontend application
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Database credentials
- `REDIS_URL`, `REDIS_PASSWORD`: Redis configuration
- `SESSION_SECRET_KEY`: Secret key for authentication sessions

## Storage Management
Persistent storage is configured using PVCs:
- `planspiegel-postgres-data` (mounted at `/var/lib/postgresql/data`)
- `planspiegel-redis-data` (mounted at `/data`)

## Troubleshooting
- Check logs for a pod:
  ```sh
  kubectl logs -f <pod-name>
  ```
- Describe a pod for error details:
  ```sh
  kubectl describe pod <pod-name>
  ```
- Restart a pod:
  ```sh
  kubectl delete pod <pod-name>
  ```

## Cleanup
To delete all deployed resources:
```sh
kubectl delete -f .
```

