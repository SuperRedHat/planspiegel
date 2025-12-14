import redis.asyncio as aioredis

from constants import ACCESS_TOKEN_EXPIRE_MINUTES, REDIS_URL, REDIS_PASSWORD

# from redis import RedisError


redis_for_token_cancellation = aioredis.from_url(REDIS_URL+"/0",
                          password=REDIS_PASSWORD,
                          decode_responses=True)

redis_for_session = aioredis.from_url(REDIS_URL+"/1",
                          password=REDIS_PASSWORD,
                          decode_responses=True)


# TODO: async def check_redis():
#     try:
#         await redis.ping()
#         return True
#     except RedisError as redis_error:
#         return False

async def revoke_token(token: str):
    await redis_for_token_cancellation.set(name=token, value="revoked", ex=ACCESS_TOKEN_EXPIRE_MINUTES)

async def check_token_revoked(token: str):
    result = await redis_for_token_cancellation.get(token)
    return result is not None
