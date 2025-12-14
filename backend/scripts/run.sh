#!/bin/bash

# chmod +x ./scripts/run.sh
source .venv/bin/activate

if ! alembic upgrade head; then
    echo "Error during migrations. Exiting."
    exit 1
fi

echo "DB migrations has been ended."
echo "SWAGGER: http://localhost:8000/api/docs"

uvicorn main:app --host 0.0.0.0 --port 8000 --reload