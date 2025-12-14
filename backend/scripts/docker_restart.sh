#!/bin/bash

# chmod +x ./scripts/docker_restart.sh

docker compose down -v && docker compose up -d
