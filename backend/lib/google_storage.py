from io import BytesIO

from fastapi import FastAPI
from google.cloud import storage

app = FastAPI()

storage_client = storage.Client.from_service_account_json('planspiegel_google_service_account_key.json')

bucket_name = "planspiegel-attachments"


def upload_attachment(filename: str, content_type: str, file: bytes) -> str:
    bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob(filename)
    blob.upload_from_file(BytesIO(file), content_type=content_type)

    return f"https://storage.googleapis.com/{bucket_name}/{filename}"
