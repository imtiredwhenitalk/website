import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Deepseek API (OpenAI-compatible)
DEEPSEEK_API_KEY = os.getenv("OPENAI_API_KEY", "sk-3e262b03566648a2b48a2cdc68307bd4")
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1",
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@app.get("/info")
async def info():
    """Get API info."""
    return {
        "name": "AI Chat API",
        "version": "1.0.0",
        "status": "ok",
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint that uses Deepseek's API to generate responses.
    """
    try:
        # Convert messages to OpenAI format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Call Deepseek API with new client
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        
        assistant_message = response.choices[0].message.content
        
        return {
            "ok": True,
            "content": assistant_message,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
