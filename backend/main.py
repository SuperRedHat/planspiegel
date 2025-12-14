from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.exceptions import RedisError
from sqlalchemy.sql import text
from starlette.middleware.sessions import SessionMiddleware

from ai.chat import router as chat_router
# routers
from auth import router as auth_router
from checks.cookies import router as cookies_router
from checks.lighthouse import router as lighthouse_router
from checks.network import router as network_router
from checks.scan_ports import router as scan_ports_router
from checks.technologies import router as technologies_router
from constants import SESSION_SECRET_KEY
# from lib.minio_storage import setup_minio
# dbs
from lib.postgres_db import yield_db
from lib.redis_db import redis_for_token_cancellation, redis_for_session


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Start-up
    # setup_minio()
    yield
    # Shutdown


app = FastAPI(
    title="Planspiegel API",
    description="API for webapp with chat that guide user through the website security checkups",
    version="1.0.0",
    contact={
        "name": "Popov Vitalii",
        "url": "https://linktr.ee/mskVitalii",
        "email": "vitalii.popov@s2023.tu-chemnitz.de",
    },
    docs_url="/docs",
    openapi_url="/api/openapi.json",
    root_path="/api",
    lifespan=lifespan
)

origins = [
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://134.109.116.232/",
    "http://134.109.116.232:80/",
    "http://172.18.0.1",
    "http://172.18.0.1:41622",
    "https://planspiegel.com/",
    "https://planspiegel.com:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "HEAD", "PUT", "PATCH", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

if not SESSION_SECRET_KEY:
    raise ValueError("SESSION_SECRET_KEY environment variable is not set.")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)


@app.get("/")
def read_root():
    return {"message": "planspiegel_contacts API is running"}


@app.get("/healthz")
async def healthz():
    try:
        # Check connection for PostgreSQL
        async for session in yield_db():
            await session.execute(text("SELECT 1"))
            break

        # Check connection for Redis
        await redis_for_session.ping()
        await redis_for_token_cancellation.ping()

        return {"status": "ok"}
    except RedisError as redis_error:
        return {"status": "error", "service": "redis", "details": str(redis_error)}
    except Exception as postgres_error:
        return {"status": "error", "service": "postgres", "details": str(postgres_error)}


app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(cookies_router, prefix="/checks", tags=["checks"])
app.include_router(scan_ports_router, prefix="/checks", tags=["checks"])
app.include_router(lighthouse_router, prefix="/checks", tags=["checks"])
app.include_router(technologies_router, prefix="/checks", tags=["checks"])
app.include_router(network_router, prefix="/checks", tags=["checks"])
app.include_router(chat_router, tags=["chat"])
