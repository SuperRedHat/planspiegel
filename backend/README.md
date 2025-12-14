# Planspiegel Backend

## How to start on Mac / WSL with Python

Download Python from [official website](https://www.python.org/downloads) or 
```shell
brew install python
```

Give the permission to the file to run or run it with `sudo`
```shell
chmod +x ./scripts/setup.sh && chmod +x ./scripts/run.sh
```

Active venv -> install dependencies -> run migrations

```shell
./scripts/setup.sh
```

Start the server
```shell
./scripts/run.sh
```

Go to Swagger and enjoy hacking!

--- 

## How to start with Docker

1. Install Docker and run
2. `docker compose up -d --build`

## How to start migrations?

`alembic revision --autogenerate -m "Chat and Messages"`

### In case of the problems ask [Vitalii Popov](mailto:vitalii.popov@s2023.tu-chemnitz.de)

## How to start GPT agent?

`cd chat && python ./generate_checks_embeddings.py`

## Storage

Download google service account to
planspiegel_google_service_account_key.json