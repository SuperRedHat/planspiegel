import os

from dotenv import load_dotenv

load_dotenv()

# region Chat
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# endregion

# region Checks
MXTOOLBOX_KEY = os.getenv("MXTOOLBOX_KEY")
# endregion

# region Other
RUNNING_IN_DOCKER = os.getenv("RUNNING_IN_DOCKER")
# endregion

# region Auth & Tokens
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 3
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8000/api/docs")
# endregion

# region Databases
REDIS_URL = os.getenv("REDIS_URL", "redis://planspiegel_redis:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "db")
DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
DATABASE_URL_MIGRATIONS = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_ENDPOINT_URL = os.getenv("MINIO_ENDPOINT_URL")
# endregion
