from fastapi import FastAPI, Request, status
from redis_client import setValue


app = FastAPI()

@app.get("/")
async def root(request: Request):
    await setValue()
    return {"message": status.HTTP_200_OK}

@app.get("/proxy")
async def proxy(request: Request):
    response = dummy_backend()
    return response

def dummy_backend():
    return {"message": "backend response"}
