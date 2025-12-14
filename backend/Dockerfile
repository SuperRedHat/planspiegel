FROM python:3.13-slim

RUN apt-get update && apt-get install -y curl
RUN apt-get update && apt-get install -y nodejs
RUN apt-get update && apt-get install -y npm

RUN apt-get update --fix-missing  \
    && apt-get install -y chromium

RUN npm install -g lighthouse

RUN npm install -g retire

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_PATH="/usr/bin/chromium"
ENV RUNNING_IN_DOCKER="true"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY .env.docker .env

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/certs/key.pem", "--ssl-certfile", "/certs/cert.pem"]

