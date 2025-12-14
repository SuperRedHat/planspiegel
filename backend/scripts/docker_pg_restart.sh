#!/bin/bash

# chmod +x ./scripts/docker_pg_restart.sh

docker stop planspiegel_postgres
docker rm -v planspiegel_postgres
docker volume rm backend_planspiegel_postgres_data
docker compose up -d planspiegel_postgres