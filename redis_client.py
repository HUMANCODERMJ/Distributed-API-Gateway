from redis.asyncio import Redis

r = Redis(host='localhost', port=6379, decode_responses=True)

async def setValue():
    await r.set(1, "Hello")