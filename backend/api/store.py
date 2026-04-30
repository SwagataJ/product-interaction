"""Store layout endpoint."""

import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/api/store", tags=["Store"])

LAYOUT_PATH = Path(__file__).parent.parent.parent / "generator" / "store_layout.json"


@router.get("/layout")
async def layout():
    with open(LAYOUT_PATH) as f:
        return json.load(f)
