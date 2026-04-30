"""Streaming chat endpoint — POST /api/chat via SSE."""

import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ..ai.agent import run_agent_stream_real

router = APIRouter(prefix="/api", tags=["Chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    context: str | None = None


@router.post("/chat")
async def chat(req: ChatRequest):
    """Stream AI agent response as Server-Sent Events."""

    async def event_generator():
        history = [{"role": m.role, "content": m.content} for m in req.history]
        async for event in run_agent_stream_real(
            message=req.message,
            history=history,
            context=req.context,
        ):
            event_type = event["event"]
            data = json.dumps(event["data"], default=str)
            yield f"event: {event_type}\ndata: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
