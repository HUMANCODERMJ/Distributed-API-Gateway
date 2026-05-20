"""
User Service - Downstream service for user management.
Runs on port 8001.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="User Service", version="1.0.0")


@app.get("/users")
async def list_users():
    """Get all users."""
    return JSONResponse(content={
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
        ]
    })


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get a specific user by ID."""
    users = {
        1: {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin"},
        2: {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user"},
        3: {"id": 3, "name": "Charlie", "email": "charlie@example.com", "role": "user"}
    }
    
    user = users.get(user_id)
    if not user:
        return JSONResponse(
            status_code=404,
            content={"error": f"User {user_id} not found"}
        )
    
    return JSONResponse(content=user)


@app.post("/users")
async def create_user(name: str, email: str):
    """Create a new user."""
    return JSONResponse(
        status_code=201,
        content={
            "id": 4,
            "name": name,
            "email": email,
            "created": True
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
