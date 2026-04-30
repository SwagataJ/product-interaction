"""SSE event stream for demo mode replay."""

import asyncio
import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from ..data import duckdb_client as db

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.get("/stream")
async def stream(
    speed: int = Query(100, ge=10, le=1000),
    day: str = Query(None),
    start_hour: int = Query(10, ge=0, le=23),
):
    """Stream events as SSE at configurable speed.

    Defaults to starting at 10:00 (store opening) for immediate action.
    """

    async def event_generator():
        # Pick the busiest day if no day specified
        if day:
            day_filter = f"DATE_TRUNC('day', timestamp) = '{day}'"
        else:
            # Use the first Saturday (busiest) in the dataset
            best = db.query("""
                SELECT DATE_TRUNC('day', timestamp) AS d, COUNT(*) AS cnt
                FROM events
                WHERE EXTRACT(HOUR FROM timestamp) BETWEEN 10 AND 21
                GROUP BY 1 ORDER BY cnt DESC LIMIT 1
            """)
            best_day = str(best[0]["d"])[:10] if best else None
            day_filter = f"DATE_TRUNC('day', timestamp) = '{best_day}'" if best_day else "1=1"

        events = db.query(f"""
            SELECT event_id, tag_id, sku_id, zone_from, zone_to,
                   event_type, timestamp, event_metadata
            FROM events
            WHERE {day_filter}
              AND EXTRACT(HOUR FROM timestamp) >= {start_hour}
            ORDER BY timestamp
        """)

        if not events:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No events found'})}\n\n"
            return

        prev_ts = None
        for evt in events:
            ts = evt["timestamp"]

            # Compute delay based on speed multiplier
            if prev_ts is not None:
                real_delta = (ts - prev_ts).total_seconds()
                delay = max(real_delta / speed, 0.01)
                # Cap delay to prevent long pauses
                delay = min(delay, 2.0)
                await asyncio.sleep(delay)

            prev_ts = ts

            payload = {
                "event_id": evt["event_id"],
                "tag_id": evt["tag_id"],
                "sku_id": evt["sku_id"],
                "zone_from": evt["zone_from"],
                "zone_to": evt["zone_to"],
                "event_type": evt["event_type"],
                "timestamp": str(evt["timestamp"]),
                "event_metadata": evt["event_metadata"],
            }

            yield f"data: {json.dumps(payload)}\n\n"

        # Signal end and loop
        yield f"data: {json.dumps({'type': 'loop', 'message': 'Restarting from beginning'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
