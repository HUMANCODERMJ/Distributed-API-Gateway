"""
AI Service - Downstream service for AI operations.
Runs on port 8003.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="AI Service", version="1.0.0")


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str


@app.get("/ai/test")
async def test_endpoint():
    """Simple test endpoint."""
    return JSONResponse(content={
        "service": "AI Service",
        "status": "operational",
        "version": "1.0.0"
    })


@app.post("/ai/chat")
async def chat(request: ChatRequest):
    """Chat with AI (dummy implementation)."""
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Dummy AI response
    responses = {
        "hello": "Hello! How can I help you?",
        "help": "I'm an AI assistant. Ask me anything!",
        "default": "That's an interesting question. Let me think about that..."
    }
    
    message_lower = request.message.lower().strip()
    response_text = responses.get(message_lower, responses["default"])
    
    return JSONResponse(content={
        "request": request.message,
        "response": response_text,
        "model": "dummy-gpt",
        "tokens": {
            "input": len(request.message.split()),
            "output": len(response_text.split())
        }
    })


@app.get("/ai/models")
async def list_models():
    """List available AI models."""
    return JSONResponse(content={
        "models": [
            {"id": "dummy-gpt", "name": "Dummy GPT", "capabilities": ["chat", "completion"]},
            {"id": "dummy-claude", "name": "Dummy Claude", "capabilities": ["chat", "analysis"]}
        ]
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
