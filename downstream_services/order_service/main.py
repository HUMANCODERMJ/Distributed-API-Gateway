"""
Order Service - Downstream service for order management.
Runs on port 8002.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Order Service", version="1.0.0")


@app.get("/orders")
async def list_orders():
    """Get all orders."""
    return JSONResponse(content={
        "orders": [
            {"id": 101, "user_id": 1, "product": "Laptop", "amount": 999.99},
            {"id": 102, "user_id": 2, "product": "Mouse", "amount": 29.99},
            {"id": 103, "user_id": 3, "product": "Keyboard", "amount": 79.99}
        ]
    })


@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    """Get a specific order by ID."""
    orders = {
        101: {"id": 101, "user_id": 1, "product": "Laptop", "amount": 999.99, "status": "shipped"},
        102: {"id": 102, "user_id": 2, "product": "Mouse", "amount": 29.99, "status": "delivered"},
        103: {"id": 103, "user_id": 3, "product": "Keyboard", "amount": 79.99, "status": "processing"}
    }
    
    order = orders.get(order_id)
    if not order:
        return JSONResponse(
            status_code=404,
            content={"error": f"Order {order_id} not found"}
        )
    
    return JSONResponse(content=order)


@app.post("/orders")
async def create_order(user_id: int, product: str, amount: float):
    """Create a new order."""
    return JSONResponse(
        status_code=201,
        content={
            "id": 104,
            "user_id": user_id,
            "product": product,
            "amount": amount,
            "status": "pending",
            "created": True
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
