# Backend API

FastAPI server for AI chat integration using OpenAI.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment variables

Create `.env` file in this directory with your OpenAI API key:

```
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Run the server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /api/chat

Send a message to the AI and get a response.

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ]
}
```

**Response:**
```json
{
  "ok": true,
  "content": "I'm doing well, thank you for asking!"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## Notes

- The API accepts a list of messages (conversation history) and returns a single assistant response.
- Each message should have `role` (either "user" or "assistant") and `content` (the message text).
- The backend will automatically call OpenAI's GPT-3.5-turbo model to generate responses.
