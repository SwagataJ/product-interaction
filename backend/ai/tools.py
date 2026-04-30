"""AI tool definitions and handlers for the Gemini function-calling agent."""

import json
from decimal import Decimal
from datetime import datetime, date
from google.genai import types
from ..data import kpi_queries as kpi


def _make_serializable(obj):
    """Recursively convert Decimal/datetime to JSON-safe types."""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(v) for v in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj

# ─── Tool Definitions (Gemini FunctionDeclaration) ────────────────────────────

TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="get_kpi",
        description="Fetch a specific KPI value, optionally filtered by category, SKU, or time range. Use this for any operational metric question.",
        parametersJsonSchema={
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": ["trial_to_buy", "floor_to_pickup", "trial_count", "misplacement_rate", "rejection_count", "pickup_count"],
                    "description": "Which KPI to fetch",
                },
                "category": {"type": "string", "description": "Filter by product category e.g. Women_Western, Men_Casual"},
                "from_dt": {"type": "string", "description": "Start datetime ISO format"},
                "to_dt": {"type": "string", "description": "End datetime ISO format"},
            },
            "required": ["metric"],
        },
    ),
    types.FunctionDeclaration(
        name="get_funnel",
        description="Get the conversion funnel breakdown: Floor → Pickup → Trial → Purchase. Shows where customers drop off.",
        parametersJsonSchema={
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "sku": {"type": "string"},
                "from_dt": {"type": "string"},
                "to_dt": {"type": "string"},
            },
        },
    ),
    types.FunctionDeclaration(
        name="get_anomalies",
        description="Get ranked anomaly/alert list with severity and narrative. Use when looking for what's wrong without a specific hypothesis.",
        parametersJsonSchema={
            "type": "object",
            "properties": {},
        },
    ),
    types.FunctionDeclaration(
        name="get_sku_journey",
        description="Get the full journey event timeline for a specific SKU showing every tag movement.",
        parametersJsonSchema={
            "type": "object",
            "properties": {
                "sku_id": {"type": "string", "description": "The SKU identifier e.g. SKU-4471"},
            },
            "required": ["sku_id"],
        },
    ),
    types.FunctionDeclaration(
        name="compare_periods",
        description="Compare a metric between two time windows. Returns deltas and percentage changes. Use for Saturday-vs-Saturday or week-over-week comparisons.",
        parametersJsonSchema={
            "type": "object",
            "properties": {
                "metric": {"type": "string", "description": "Metric name to compare"},
                "a_from": {"type": "string", "description": "Period A start datetime"},
                "a_to": {"type": "string", "description": "Period A end datetime"},
                "b_from": {"type": "string", "description": "Period B start datetime"},
                "b_to": {"type": "string", "description": "Period B end datetime"},
            },
            "required": ["metric", "a_from", "a_to", "b_from", "b_to"],
        },
    ),
    types.FunctionDeclaration(
        name="estimate_lost_sales",
        description="Estimate revenue lost due to floor stockouts in INR. Use when CXOs ask about financial impact of stockouts.",
        parametersJsonSchema={
            "type": "object",
            "properties": {
                "sku": {"type": "string"},
                "category": {"type": "string"},
                "from_dt": {"type": "string"},
                "to_dt": {"type": "string"},
            },
        },
    ),
    types.FunctionDeclaration(
        name="get_size_rejection_heatmap",
        description="Get rejection rate breakdown by size. Use when investigating fit issues or size-specific problems.",
        parametersJsonSchema={
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "sku": {"type": "string"},
            },
        },
    ),
]

GEMINI_TOOLS = [types.Tool(function_declarations=TOOL_DECLARATIONS)]


# ─── Tool Handlers ────────────────────────────────────────────────────────────

def execute_tool(name: str, args: dict) -> dict:
    """Dispatch a tool call to the corresponding kpi_queries function."""
    result = _execute_tool_inner(name, args)
    return _make_serializable(result)


def _execute_tool_inner(name: str, args: dict) -> dict:
    try:
        if name == "get_kpi":
            result = kpi.get_summary_kpis(
                category=args.get("category"),
                from_dt=args.get("from_dt"),
                to_dt=args.get("to_dt"),
            )
            metric = args.get("metric", "")
            if metric and metric in result:
                return {"metric": metric, "value": result[metric], "all_kpis": result}
            return result

        elif name == "get_funnel":
            return {"funnel": kpi.get_funnel(
                category=args.get("category"),
                sku=args.get("sku"),
                from_dt=args.get("from_dt"),
                to_dt=args.get("to_dt"),
            )}

        elif name == "get_anomalies":
            return {"anomalies": kpi.get_anomalies()}

        elif name == "get_sku_journey":
            sku_id = args.get("sku_id", "")
            events = kpi.get_sku_journey(sku_id)
            return {
                "sku_id": sku_id,
                "event_count": len(events),
                "events": events[:50],
                "note": f"Showing first 50 of {len(events)} events" if len(events) > 50 else None,
            }

        elif name == "compare_periods":
            return kpi.compare_periods(
                metric=args.get("metric", "trial_to_buy_pct"),
                period_a_from=args["a_from"],
                period_a_to=args["a_to"],
                period_b_from=args["b_from"],
                period_b_to=args["b_to"],
            )

        elif name == "estimate_lost_sales":
            return kpi.estimate_lost_sales(
                sku=args.get("sku"),
                category=args.get("category"),
                from_dt=args.get("from_dt"),
                to_dt=args.get("to_dt"),
            )

        elif name == "get_size_rejection_heatmap":
            return {"sizes": kpi.get_size_rejection_heatmap(
                category=args.get("category"),
                sku=args.get("sku"),
            )}

        else:
            return {"error": f"Unknown tool: {name}"}

    except Exception as e:
        return {"error": str(e)}
