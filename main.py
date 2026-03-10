from fastapi import FastAPI, Request, status
from redis_client import r


app = FastAPI()

@app.get("/")
async def root(request: Request):
    return {"message": status.HTTP_200_OK}

@app.get("/proxy")
async def proxy(request: Request):
    script = """
    local key = KEYS[1]
    local count = redis.call('INCR', key)
    if count == 1 then
        redis.call('EXPIRE', key, 60)
    end
    return count
    """
    r.incr
    count = await r.eval(script, 1, "gateway:minute_counter")
    response = dummy_backend()
    response["request_count"] = count
    return response

def dummy_backend():
    return {"message": "backend response"}
