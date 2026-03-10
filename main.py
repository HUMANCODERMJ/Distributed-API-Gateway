from fastapi import FastAPI, Request, status, HTTPException
from redis_client import r


app = FastAPI()

@app.get("/")
async def root(request: Request):
    return {"message": status.HTTP_200_OK}

@app.get("/proxy")
async def proxy(request: Request):
    script = """
    local key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local count = redis.call('INCR', key)
    if count == 1 then
        redis.call('EXPIRE', key, 60)
    end
    local allowed = 1
    if count > limit then
        allowed = 0
    end
    return {count, allowed}
    """

    limit = 10
    result = await r.eval(script, 1, "gateway:minute_counter", limit)
    count, allowed = result[0], result[1]

    if allowed == 0:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    response = final_response()
    response["request_count"] = count
    return response

def final_response():
    return {"message": "backend response"}
