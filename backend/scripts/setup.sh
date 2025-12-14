#!/bin/bash

# chmod +x ./scripts/setup.sh
source .venv/bin/activate

pip install -r requirements.txt

echo "Dependencies has been installed."

alembic upgrade head

echo "DB migrations has been ended."
