from minio import Minio
from minio.error import S3Error

import constants

minio_client = Minio(constants.MINIO_ENDPOINT_URL,
                     access_key=constants.MINIO_ACCESS_KEY,
                     secret_key=constants.MINIO_SECRET_KEY,
                     secure=False)


def create_bucket(bucket_name: str):
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' created.")
        else:
            print(f"Bucket '{bucket_name}' already exists.")
    except S3Error as e:
        if e.code == "BucketAlreadyOwnedByYou":
            print(f"Bucket '{bucket_name}' is already owned by you.")
        else:
            print(f"Error occurred: {e}")


def setup_minio():
    create_bucket('pdfs')
