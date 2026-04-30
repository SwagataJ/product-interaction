"""Gemini agent with function-calling loop."""

import json
import os
from google import genai
from google.genai import types
from .tools import GEMINI_TOOLS, execute_tool
from .prompts import SYSTEM_PROMPT

MAX_TOOL_ITERATIONS = 8

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT", "nano-banana-api-test-484205"),
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    return _client


def create_chat(history: list[dict] | None = None):
    """Create a new Gemini chat session with tools configured."""
    client = _get_client()

    gemini_history = []
    if history:
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])],
            ))

    chat = client.chats.create(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-pro"),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=GEMINI_TOOLS,
            temperature=0.3,
        ),
        history=gemini_history if gemini_history else None,
    )
    return chat


async def run_agent_stream(message: str, history: list[dict] | None = None, context: str | None = None):
    """Run the agent loop, yielding SSE events as they occur.

    Yields dicts with 'event' and 'data' keys for SSE serialization.
    """
    prompt = message
    if context:
        prompt = f"[Dashboard context: {context}]\n\n{message}"

    chat = create_chat(history)

    for iteration in range(MAX_TOOL_ITERATIONS):
        if iteration == 0:
            response = chat.send_message(prompt)
        else:
            # After feeding tool results, get next response
            response = chat.send_message(tool_response_parts)

        tool_response_parts = []
        has_function_calls = False
        text_parts = []

        for part in response.candidates[0].content.parts:
            if part.function_call:
                has_function_calls = True
                fc = part.function_call
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}

                yield {"event": "tool_call", "data": {"tool": tool_name, "input": tool_args}}

                result = execute_tool(tool_name, tool_args)

                yield {"event": "tool_result", "data": {"tool": tool_name, "summary": _summarize_result(result)}}

                tool_response_parts.append(types.Part.from_function_response(
                    name=tool_name,
                    response=result,
                ))

            elif part.text:
                text_parts.append(part.text)

        if not has_function_calls:
            full_text = "".join(text_parts)
            # Extract dashboard actions before stripping tags
            actions = _extract_dashboard_actions(full_text)
            # Strip XML tags and <br> from displayed text
            full_text = _strip_dashboard_tags(full_text)
            # Stream text in chunks for a more responsive feel
            for chunk in _chunk_text(full_text, 20):
                yield {"event": "token", "data": {"text": chunk}}

            for action in actions:
                yield {"event": "dashboard_action", "data": action}

            yield {"event": "done", "data": {}}
            return

    # Safety: if we hit max iterations, return what we have
    yield {"event": "token", "data": {"text": "I've gathered the data but hit the analysis limit. Here's what I found so far."}}
    yield {"event": "done", "data": {}}


async def run_agent_stream_real(message: str, history: list[dict] | None = None, context: str | None = None):
    """Streaming version using generate_content_stream for token-level streaming."""
    prompt = message
    if context:
        prompt = f"[Dashboard context: {context}]\n\n{message}"

    chat = create_chat(history)

    for iteration in range(MAX_TOOL_ITERATIONS):
        if iteration == 0:
            stream = chat.send_message_stream(prompt)
        else:
            stream = chat.send_message_stream(tool_response_parts)

        tool_response_parts = []
        has_function_calls = False
        accumulated_text = ""

        for chunk in stream:
            if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
                continue
            for part in chunk.candidates[0].content.parts:
                if part.function_call:
                    has_function_calls = True
                    fc = part.function_call
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}

                    yield {"event": "tool_call", "data": {"tool": tool_name, "input": tool_args}}

                    result = execute_tool(tool_name, tool_args)

                    yield {"event": "tool_result", "data": {"tool": tool_name, "summary": _summarize_result(result)}}

                    tool_response_parts.append(types.Part.from_function_response(
                        name=tool_name,
                        response=result,
                    ))

                elif part.text:
                    accumulated_text += part.text

        if not has_function_calls:
            # Strip tags and emit cleaned text
            cleaned = _strip_dashboard_tags(accumulated_text)
            actions = _extract_dashboard_actions(accumulated_text)
            for chunk in _chunk_text(cleaned, 20):
                yield {"event": "token", "data": {"text": chunk}}
            for action in actions:
                yield {"event": "dashboard_action", "data": action}
            yield {"event": "done", "data": {}}
            return

    yield {"event": "token", "data": {"text": "\n\nReached analysis limit."}}
    yield {"event": "done", "data": {}}


def _summarize_result(result: dict) -> str:
    """Create a brief summary of a tool result for the UI badge."""
    if "error" in result:
        return f"Error: {result['error']}"
    if "funnel" in result:
        return f"Fetched funnel data ({len(result['funnel'])} stages)"
    if "anomalies" in result:
        return f"Found {len(result['anomalies'])} anomalies"
    if "event_count" in result:
        return f"Traced {result['event_count']} events for {result.get('sku_id', 'SKU')}"
    if "total_estimated_lost_sales_inr" in result:
        return f"Lost sales: ₹{result['total_estimated_lost_sales_inr']:,.0f}"
    if "sizes" in result:
        return f"Size rejection data ({len(result['sizes'])} sizes)"
    if "metric" in result:
        return f"{result['metric']}: {result.get('value', 'N/A')}"
    return "Data fetched"


def _chunk_text(text: str, words_per_chunk: int = 20) -> list[str]:
    """Split text into chunks for progressive rendering."""
    words = text.split(" ")
    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunk = " ".join(words[i:i + words_per_chunk])
        if i > 0:
            chunk = " " + chunk
        chunks.append(chunk)
    return chunks if chunks else [text]


def _extract_dashboard_actions(text: str) -> list[dict]:
    """Extract dashboard action hints from the response text.

    Parses <reference_dashboard .../> XML tags and also does keyword matching.
    """
    import re
    actions = []

    # Parse any XML-style dashboard tags the model may emit
    for match in re.finditer(r'<(?:reference_dashboard|dashboard_action)\s+([^>]*)/?\s*>', text):
        attrs = match.group(1)
        target_tab = re.search(r'target_tab=["\']?(\w+)', attrs)
        tab = target_tab.group(1) if target_tab else "analytics"

        # Match filter="key: value" or filters={'key': 'value', ...}
        for fmatch in re.finditer(r"(?:category_id|category|sku_id|sku)['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9_-]+)", attrs):
            fval = fmatch.group(1)
            ftype = "filter_category" if "categor" in fmatch.group(0).lower() else "filter_sku"
            actions.append({"type": ftype, "id": fval, "target_tab": tab})

    # Keyword fallbacks only if no XML tags were found
    if actions:
        return actions

    text_lower = text.lower()

    if "sku-4471" in text_lower or "men's slim fit" in text_lower:
        actions.append({
            "type": "filter_sku",
            "id": "SKU-4471",
            "target_tab": "analytics",
        })
    if "size 28" in text_lower or "size-28" in text_lower:
        actions.append({
            "type": "highlight_fixture",
            "id": "F_WB_B1",
            "target_tab": "live_store",
        })
    if "stockout" in text_lower and "backroom" in text_lower:
        actions.append({
            "type": "highlight_alert",
            "id": "stockout_while_stocked",
            "target_tab": "live_store",
        })
    if "lost sales" in text_lower or "revenue lost" in text_lower:
        actions.append({
            "type": "show_business_kpi",
            "id": "lost_sales",
            "target_tab": "executive",
        })

    return actions


def _strip_dashboard_tags(text: str) -> str:
    """Remove <reference_dashboard .../> and <br> tags from response text."""
    import re
    # Strip any XML/HTML-like tags the model invents for dashboard actions
    text = re.sub(r'</?d>\s*', '', text)
    text = re.sub(r'<dashboard_action[^>]*/?\s*>', '', text)
    text = re.sub(r'<reference_dashboard[^>]*/?\s*>', '', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'\[?"?target_tab\([^)]*\)"?\]?', '', text)
    # Catch any remaining XML-like tags with dashboard/action/reference in them
    text = re.sub(r'</?[a-z_]*(?:dashboard|action|reference)[^>]*>', '', text, flags=re.IGNORECASE)
    return text.strip()
