from fastapi import FastAPI, Request, status
from redis_client import setValue


app = FastAPI()

@app.get("/")
async def root(request: Request):
    setValue()
    return {"message" : status.HTTP_200_OK}
