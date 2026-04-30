# Design — In-Store Product Journey Tracker

## 1. Architecture Overview

### 1.1 High-Level Architecture

The system is a three-layer stack designed for solo build speed without sacrificing the production-shape narrative. The lightweight choice (DuckDB + FastAPI + Next.js) is deliberate — every component has a one-line swap to the production equivalent on Trent's existing Azure/Databricks stack, which is the credibility moment for a CXO audience.

```
┌─────────────────────────────────────────────────────────────────┐
│                  FRONTEND (Next.js + React)                     │
│  ┌─────────────────────┐    ┌─────────────────────────────┐    │
│  │  Living Store Map   │    │  Coordinated Chart Grid     │    │
│  │  (SVG + Framer      │    │  (Funnel, bars, heatmap,    │    │
│  │  Motion, ~55%       │◄──►│  hourly trend, alerts —     │    │
│  │  width)             │    │  cross-filtered, ~45%)      │    │
│  └─────────────────────┘    └─────────────────────────────┘    │
│     ┌──────────────────────────────────────────┐                │
│     │   AI Chat Panel (floating, expandable)   │                │
│     └──────────────────────────────────────────┘                │
│              Shared State (Zustand store)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP + SSE (streaming)
┌────────────────────────────▼────────────────────────────────────┐
│                    BACKEND (FastAPI)                            │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐     │
│  │ KPI API      │  │ Event Stream  │  │ AI Agent         │     │
│  │ (REST)       │  │ (SSE for demo │  │ (Gemini function │     │
│  │              │  │ mode replay)  │  │ calling)         │     │
│  └──────┬───────┘  └───────┬───────┘  └────────┬─────────┘     │
│         │                  │                   │                │
│         └──────────────────┼───────────────────┘                │
│                            │                                    │
│                  ┌─────────▼──────────┐                         │
│                  │ DuckDB / Parquet   │                         │
│                  │ (events + KPIs)    │                         │
│                  └────────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                             ▲
                             │
┌────────────────────────────┴────────────────────────────────────┐
│              SYNTHETIC DATA GENERATOR (Python)                  │
│  Store layout → Catalog → Tags → Journey simulation →           │
│  Event stream with planted insight stories + light-touch        │
│  after-hours activity → Parquet files                           │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Production-Shape Mapping (The CXO Slide)

The same architecture, with the prototype layer swapped for Trent's existing stack:

| Prototype Layer | Production Equivalent (Trent) |
|---|---|
| Python synth generator | Real RFID readers + Impinj/Zebra middleware |
| Local Parquet files | Delta Lake on Azure Data Lake Gen2 |
| DuckDB queries | Databricks SQL warehouse |
| FastAPI on laptop | FastAPI on Azure App Service or AKS |
| Google AI Studio Gemini API | Vertex AI Gemini in `asia-south1` (Mumbai region) — data sovereignty per India DPDP Act 2023; or self-hosted open-weight LLM via vLLM if offline inference is required |
| Single store, 14 days | All Westside/Zudio stores, full history |
| Single dashboard | Persona dashboards (Store Mgr, Cat, HO) |

**This table is the slide.** Every component a developer touches in the prototype has a named production equivalent on Trent's existing stack. The data schema, tool catalog, frontend components, and AI agent design carry forward unchanged.

### 1.3 Key Design Decisions

The architecture deliberately separates the data layer (synthetic generator and DuckDB) from the analytical layer (KPI computation) from the presentation layer (FastAPI + frontend). This separation is the production-shape narrative — in the production system, the synthetic generator is replaced by a real RFID event ingestion service writing to the same Parquet/Delta schema, and everything downstream is identical.

DuckDB is chosen over SQLite because the KPI queries are analytical (group-bys, window functions, aggregations across the full event log) and DuckDB's columnar engine handles them in milliseconds against Parquet files. Crucially, DuckDB's Parquet format is bit-identical to the Parquet that Databricks reads, so the production migration is "point Databricks at the same files" rather than a rewrite.

FastAPI is chosen because it supports streaming responses natively (essential for the AI chat layer), its automatic OpenAPI documentation accelerates frontend integration, and it's the same framework Trent uses elsewhere — frictionless production handoff.

Next.js with the App Router is chosen for the frontend because it provides server-side rendering for the initial dashboard load (fast first paint), and excellent ecosystem support for the visual libraries (Framer Motion, Recharts, shadcn/ui) that drive polish.

Gemini is chosen as the AI layer for several reasons specific to this build's audience and constraints. Its function-calling and streaming capabilities cover the technical needs (tool dispatch, token streaming, structured output). Vertex AI's `asia-south1` region offers a credible production answer to data residency under India's DPDP Act 2023 — a question CXOs will ask. Tata Group has substantial Google Cloud relationships, which makes Gemini a culturally aligned choice for a Trent-internal pitch. The Google AI Studio API tier is generous enough for hackathon-scale usage with a single API key, no GCP project setup required for the prototype.

## 2. Synthetic Data Generator Design

### 2.1 Store Layout Model

The virtual store is defined as a JSON configuration. The same JSON drives both the simulator's spatial logic and the frontend's Living Store Map rendering — single source of truth for layout.

```json
{
  "store_id": "STORE_001",
  "name": "Demo Westside, Mumbai",
  "trading_hours": {"open": "10:00", "close": "22:00"},
  "zones": [
    {"id": "BACKROOM", "type": "backroom", "x": 50, "y": 50, "w": 200, "h": 100},
    {"id": "F_WT_A1", "type": "fixture", "category": "Women_Tops", "x": 300, "y": 100, "w": 80, "h": 60, "placement": "front"},
    {"id": "F_WT_A7", "type": "fixture", "category": "Women_Tops", "x": 600, "y": 350, "w": 80, "h": 60, "placement": "back"},
    {"id": "F_WB_B1", "type": "fixture", "category": "Women_Bottoms", "x": 400, "y": 100, "w": 80, "h": 60, "placement": "front"},
    {"id": "F_MS_C1", "type": "fixture", "category": "Men_Shirts", "x": 300, "y": 200, "w": 80, "h": 60, "placement": "front"},
    {"id": "F_MB_D1", "type": "fixture", "category": "Men_Bottoms", "x": 400, "y": 200, "w": 80, "h": 60, "placement": "front"},
    {"id": "F_K_E1",  "type": "fixture", "category": "Kids", "x": 300, "y": 300, "w": 80, "h": 60, "placement": "side"},
    {"id": "F_A_F1",  "type": "fixture", "category": "Accessories", "x": 600, "y": 380, "w": 80, "h": 60, "placement": "near_exit"},
    {"id": "TRIAL",   "type": "trial_room", "x": 550, "y": 100, "w": 100, "h": 150},
    {"id": "TILL_1",  "type": "till", "x": 650, "y": 50, "w": 60, "h": 40},
    {"id": "TILL_2",  "type": "till", "x": 720, "y": 50, "w": 60, "h": 40},
    {"id": "EXIT",    "type": "exit", "x": 700, "y": 430, "w": 80, "h": 30}
  ]
}
```

The `placement` attribute on fixtures (front/back/side/near_exit) drives planted-story logic — front fixtures get higher base pickup rates, accessories near_exit drive the shrinkage cluster.

### 2.2 Catalog & Inventory Schema

```python
# product_catalog.parquet
sku_id: str             # SKU-0001
category: str           # Women_Tops
sub_category: str       # Casual_Tee
color: str              # Navy
size: str               # XS, S, M, L, XL, 28, 30, ...
fit: str                # Slim, Regular, Relaxed
price_inr: float
unit_cost_inr: float    # for working-capital KPI
brand: str

# tag_inventory.parquet
tag_id: str             # TAG-000001
sku_id: str             # FK to product_catalog
initial_zone: str       # FK to store layout zone
status: str             # active, sold, returned, missing
```

### 2.3 Event Schema

Every reader event is a single row. The schema is intentionally Delta-Lake-compatible so production migration is a one-line storage change.

```python
# events.parquet
event_id: str           # UUID
tag_id: str             # FK to tag_inventory
sku_id: str             # denormalized for query speed
zone_from: str | None   # null for first event
zone_to: str            # the zone the reader detected
event_type: str         # see enum below
timestamp: datetime
event_metadata: dict    # JSON: rejection_reason, basket_id, customer_anon_id, etc.
```

**Trading-hours event types:** `RECEIVED_BACKROOM`, `MOVED_TO_FLOOR`, `PICKED_UP`, `BASKET_DWELL`, `ENTERED_TRIAL`, `EXITED_TRIAL_PURCHASED`, `EXITED_TRIAL_REJECTED`, `RETURNED_TO_FIXTURE`, `MISPLACED`, `SOLD_AT_TILL`, `EXITED_STORE`, `EXITED_WITHOUT_SALE` (shrinkage), `RETURNED_BY_CUSTOMER`.

**After-hours event types (light-touch):** `OPS_REPLENISHED` (backroom-to-fixture), `OPS_STOCKTAKE_SCAN` (read in place), `OPS_VM_RESET` (item moved between fixtures by staff).

### 2.4 Journey Simulation Logic

The generator runs a discrete-event simulation across the 14-day window. For each tag, a journey path is sampled from a probability distribution biased by SKU attributes, fixture placement, and planted-story rules:

```
Path probabilities (baseline):
  Stays on fixture all period:       55%
  Picked up, returned to fixture:    20%
  Picked, tried, rejected:           14%
  Picked, tried, purchased:           7%
  Picked, purchased without trial:    2% (mostly accessories)
  Misplaced on wrong fixture:         1%
  Shrinkage (exits without till):     1%
```

Planted-story modifiers override the baseline for specific SKUs or zones. For example, the SKU planted with a fit issue has a trial-to-rejection probability of 71% concentrated entirely in size M.

Timestamps within a path are sampled from realistic distributions:
- Backroom dwell: Gamma(shape=2, scale=12) hours, clipped to [4, 96]
- Time on floor before pickup: Exponential(scale=8) hours, clipped to [0.1, 168]
- Basket dwell: Normal(mean=4, std=2) minutes, clipped to [0.5, 20]
- Trial dwell: Normal(mean=5, std=2) minutes, clipped to [1, 15]
- Till-to-exit: Normal(mean=60, std=20) seconds, clipped to [10, 300]

Pickup events are biased to occur during trading hours with intra-day weighting: lunchtime micro-peak (12:00–14:00), strong evening peak (18:00–21:00), weekend amplification.

### 2.5 Light-Touch After-Hours Simulation

After trading close (22:00–10:00), the generator emits a deliberately small volume of operational events:

- **Replenishment**: For fixtures whose end-of-day on-floor count dropped below a threshold while backroom holds stock, generate an `OPS_REPLENISHED` event between 03:00 and 09:00 with stochastic timing. Replenishment lag (close-to-replenishment delta) is the metric the planted story #6 leans on. On 2 of 14 nights, suppress replenishment for the size-28 stockout SKU to plant the SLA-failure story.
- **Stocktake**: 2-3 fixtures per night get a batch of `OPS_STOCKTAKE_SCAN` events between 23:00 and 02:00 with no zone change, simulating cycle counts.
- **VM Reset**: 1-2 events per night between 06:00 and 09:00, moving a few tags between fixtures of the same category.

Total after-hours volume: roughly 50-100 events per night versus thousands during trading hours. Visually distinct on the map, narratively meaningful in the data.

### 2.6 Planted Insight Stories

Six stories are baked into the simulation, each surfaceable by both the dashboard's anomaly detection and the AI agent. Each story is framed for direct CXO relevance:

1. **Fit issue SKU** — SKU-4471 (Men's Slim Fit Shirt). Size M units have a 71% trial rejection rate; other sizes track baseline (~20%). Framing: "This SKU is responsible for an estimated ₹X lakh in lost sales from fit-driven rejections — flag to buying."

2. **Stockout-while-stocked** — Women's Bottoms size 28 sells through floor inventory by ~14:00 daily. Backroom holds 40+ units throughout. No replenishment events fire for 3+ hours after stockout. Framing: "We have inventory; we just don't have it on the floor when customers want it."

3. **Saturday-vs-Saturday drop** — One Saturday in the 14-day window has Trial Room utilization 50% lower than the prior Saturday (planted as TRIAL zone reader emitting fewer events for a 2-hour window — simulating maintenance closure). Framing: "Conversion fell 18% this Saturday — root cause is operational, not commercial."

4. **Fixture placement gap** — Two fixtures hold identical SKU mixes; the front-of-store fixture has a 4x pickup rate vs the back-wall fixture. Framing: "Same product, four times the engagement based on placement — VM ROI is enormous and we're underestimating it."

5. **Shrinkage cluster** — Three Accessories SKUs near the EXIT zone have abnormally high `EXITED_WITHOUT_SALE` rates (5x baseline shrinkage). Pattern is concentrated in evening hours. Framing: "Shrinkage is concentrated in three SKUs near the exit during evening hours — loss prevention should investigate."

6. **Replenishment SLA failure** — On 2 of 14 overnight cycles, the size-28 Women's Bottoms replenishment doesn't happen. On those days, the next-day stockout fires immediately at store open (10:00) instead of the usual 14:00. Framing: "Two of fourteen nights, our replenishment process broke. We lost roughly ₹Y in same-day sales because of it."

### 2.7 Generator Output

The generator writes to a known directory:
- `store_layout.json`
- `product_catalog.parquet`
- `tag_inventory.parquet`
- `events.parquet`

DuckDB loads these directly via `read_parquet` — no ingestion step required. The same Parquet files are readable by Databricks SQL or Spark in production with zero transformation.

## 3. Backend Design (FastAPI)

### 3.1 Service Structure

```
backend/
├── main.py                  # FastAPI app, CORS, route registration
├── config.py                # paths, model names, demo speed defaults
├── data/
│   ├── duckdb_client.py     # connection + parameterized queries
│   └── kpi_queries.py       # SQL strings for each KPI
├── api/
│   ├── kpis.py              # GET /api/kpis/* endpoints
│   ├── events.py            # SSE stream for demo mode replay
│   ├── chat.py              # POST /api/chat (streaming)
│   └── store.py             # GET /api/store/layout
├── ai/
│   ├── agent.py             # Gemini client + function-calling loop
│   ├── tools.py             # tool definitions + handlers
│   ├── prompts.py           # system prompt for the agent
│   └── schemas.py           # response payload models (Pydantic)
└── generator/
    └── synth.py             # entry point to (re)generate data
```

### 3.2 KPI API Endpoints

All endpoints return JSON; all support optional query parameters `from`, `to`, `category`, `sku`, `store`:

- `GET /api/kpis/summary` — six headline KPI values with deltas (operational)
- `GET /api/kpis/business` — three CXO-grade business KPIs (lost sales, working capital, conversion uplift) in INR
- `GET /api/kpis/funnel` — funnel stages with counts and rates
- `GET /api/kpis/categories` — per-category trial-to-buy bars
- `GET /api/kpis/hourly` — hourly conversion trend
- `GET /api/kpis/heatmap/category-hour` — category × hour conversion heatmap
- `GET /api/kpis/heatmap/fixtures` — per-fixture pickup rates for the map
- `GET /api/kpis/heatmap/sizes` — rejection rate by size, scoped to current category/SKU filter
- `GET /api/kpis/anomalies` — ranked alert list with severity and narrative
- `GET /api/kpis/sku/{sku_id}/journey` — per-tag journey timeline for a SKU
- `GET /api/kpis/replenishment` — overnight replenishment SLA adherence

KPI computation runs as parameterized DuckDB SQL against the events Parquet. Queries are written once in `kpi_queries.py` and reused across direct API calls and AI tool calls.

### 3.3 Event Stream (Demo Mode)

`GET /api/events/stream?speed=100` returns a Server-Sent Events stream. The backend reads `events.parquet` ordered by timestamp and emits each event with a delay of `(real_dt / speed)`. The frontend consumes these to drive Living Store Map dot animations.

The stream supports `?day=YYYY-MM-DD` to start from a specific day and loops automatically when reaching end-of-data. Operational (after-hours) events stream identically, with `event_type` distinguishing them so the frontend can apply the after-hours visual treatment.

### 3.4 AI Agent Design

#### 3.4.1 Single-Phase Agent with Function Calling

The agent runs as a single Gemini conversation with function calling. Gemini itself decides which functions to call based on the user's question. This is simpler than a two-model orchestration and faster to ship while preserving the production-shape pattern.

The implementation uses the `google-genai` Python SDK (the current generation; the older `google-generativeai` SDK works too but is being deprecated). The default model for this build is `gemini-2.5-pro` for analytical reasoning depth; `gemini-2.5-flash` is configured as a fallback for latency-sensitive paths if needed. Model selection lives in `backend/config.py` and is overridable via environment variable.

#### 3.4.2 Tool Catalog

In Gemini's API these are declared as `FunctionDeclaration` objects passed via the `tools` parameter on `generate_content`. The codebase keeps the term "tools" for cross-vendor portability — swapping to a different LLM provider in the future would require changing only the SDK adapter, not the tool definitions themselves.

```python
TOOLS = [
    {
        "name": "get_kpi",
        "description": "Fetch a specific KPI value, optionally filtered by category, SKU, time range.",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {"type": "string", "enum": ["trial_to_buy", "floor_to_pickup", "journey_time", "stockouts", "trial_utilization", "misplacement_rate"]},
                "dimension": {"type": "string", "enum": ["store", "category", "sku", "fixture", "hour"]},
                "time_range": {"type": "object", "properties": {"from": {"type": "string"}, "to": {"type": "string"}}},
                "filters": {"type": "object", "properties": {"category": {"type": "string"}, "sku_id": {"type": "string"}}}
            },
            "required": ["metric"]
        }
    },
    {
        "name": "get_funnel",
        "description": "Get the conversion funnel breakdown by stage, with optional filters.",
        "parameters": {"type": "object", "properties": {"filters": {"type": "object"}, "time_range": {"type": "object"}}}
    },
    {
        "name": "get_anomalies",
        "description": "Get ranked anomaly list. Use to find what's wrong without a specific hypothesis.",
        "parameters": {"type": "object", "properties": {"severity": {"type": "string"}, "time_range": {"type": "object"}}}
    },
    {
        "name": "get_sku_journey",
        "description": "Get the full journey event timeline for a specific SKU.",
        "parameters": {"type": "object", "properties": {"sku_id": {"type": "string"}}, "required": ["sku_id"]}
    },
    {
        "name": "compare_periods",
        "description": "Compare a metric between two time windows; returns deltas and contributing factors.",
        "parameters": {"type": "object", "properties": {"metric": {"type": "string"}, "period_a": {"type": "object"}, "period_b": {"type": "object"}}}
    },
    {
        "name": "estimate_lost_sales",
        "description": "Estimate revenue lost due to floor stockouts in INR. Use when CXOs ask about financial impact.",
        "parameters": {"type": "object", "properties": {"sku": {"type": "string"}, "category": {"type": "string"}, "time_range": {"type": "object"}}}
    },
    {
        "name": "suggest_actions",
        "description": "Given an anomaly or KPI gap, suggest concrete operational actions framed for CXO/store-manager audiences.",
        "parameters": {"type": "object", "properties": {"context": {"type": "string"}}}
    }
]
```

Each function handler executes a DuckDB query (via `kpi_queries.py`) and returns structured JSON. The agent then synthesizes the natural-language narrative. Note that Gemini's parameter schema uses standard JSON Schema syntax (`type`, `properties`, `required`) rather than Anthropic-style flat `input_schema` — the structure above reflects this.

#### 3.4.3 Response Schema

The chat endpoint streams Server-Sent Events with five event types interleaved:

```
event: tool_call
data: {"tool": "get_funnel", "input": {...}}

event: tool_result
data: {"tool": "get_funnel", "summary": "Pulled funnel data"}

event: token
data: {"text": "Trial-to-buy is "}

event: dashboard_action
data: {"type": "highlight_fixture", "id": "F_MS_C1", "target_tab": "live_store"}

event: inline_chart
data: {"type": "bar", "spec": {...recharts config...}}

event: done
data: {}
```

The frontend renders tokens to the chat panel, displays tool badges, dispatches dashboard actions to the global state store (which handles tab auto-switching when `target_tab` differs from the current tab), and renders inline charts within the message bubble.

Each `dashboard_action` carries a `target_tab` field with one of: `live_store`, `analytics`, `executive`, or `none` (for tab-agnostic actions like opening a chat thread). The action dispatcher in the frontend's Zustand store inspects this field; if it differs from the current tab, the dispatcher switches tabs first (with the visual cue from FR-3.3), then applies the action after the transition completes.

#### 3.4.4 System Prompt

The agent's system prompt is engineered to:

- Establish the agent as an in-store retail analyst familiar with fashion-retail KPIs and the Trent Westside/Zudio context
- Force function call usage for any data claim (no hallucinated numbers) — Gemini occasionally produces inline reasoning when a function call would be more appropriate, so the prompt is explicit: "for any specific number, percentage, or named entity in your response, you must call a function first; do not produce these from prior knowledge"
- Enforce a response structure: brief observation, specifics from functions, recommended action with business impact
- Frame numbers in INR with appropriate scale (lakhs/crores) and use the language a Trent CXO would
- Bias toward producing dashboard_action events whenever entities are referenced
- Acknowledge uncertainty cleanly when functions return empty results

A first-pass draft of the system prompt lives in `backend/ai/prompts.py` and is treated as a tunable artifact during demo rehearsal on Day 6. Gemini-specific tuning typically centers on increasing the explicit "you must call a function" instruction strength; left implicit, Gemini will sometimes confabulate plausible-looking numbers from world knowledge rather than calling the tool.

## 4. Frontend Design (Next.js)

### 4.1 Project Structure

```
frontend/
├── app/
│   ├── layout.tsx           # global shell, theme provider, font
│   ├── page.tsx             # tab shell + tab routing
│   ├── tabs/
│   │   ├── LiveStoreTab.tsx       # composes StoreMap + ops KPIs + alert feed
│   │   ├── AnalyticsTab.tsx       # composes ChartGrid + ops KPIs strip
│   │   └── ExecutiveSummaryTab.tsx  # composes business KPIs + headline + AI prompts
│   └── api/                 # (proxy if needed; mostly direct backend calls)
├── components/
│   ├── nav/
│   │   └── TabNav.tsx       # three-tab nav with auto-switch indicator
│   ├── store-map/
│   │   ├── StoreMap.tsx     # SVG map shell
│   │   ├── Fixture.tsx      # fixture rect with heat color + pulse
│   │   ├── FlowDot.tsx      # animated product dot (customer)
│   │   ├── OpsDot.tsx       # animated product dot (after-hours)
│   │   ├── PathTracer.tsx   # SKU journey trace overlay
│   │   └── AfterHoursOverlay.tsx  # dimmed treatment + status badge
│   ├── kpi/
│   │   ├── KpiCard.tsx      # animated value + sparkline + delta
│   │   ├── KpiStrip.tsx     # operational KPIs grid
│   │   └── BusinessKpiStrip.tsx   # CXO-grade KPIs (INR), large variant
│   ├── grid/
│   │   ├── ChartGrid.tsx              # cross-filter coordinator
│   │   ├── ConversionFunnel.tsx
│   │   ├── CategoryBars.tsx
│   │   ├── HourlyTrend.tsx
│   │   ├── SizeRejectionHeatmap.tsx
│   │   ├── CategoryHourHeatmap.tsx
│   │   └── AlertFeed.tsx
│   ├── exec/
│   │   ├── HeadlineCard.tsx          # one-line "what changed today" from AI
│   │   └── SuggestedQuestions.tsx    # three CXO-relevant prompt buttons
│   ├── topbar/
│   │   └── TopBar.tsx       # store, time, demo controls
│   └── chat/
│       ├── ChatPanel.tsx    # global, persists across tabs
│       ├── MessageBubble.tsx
│       ├── ToolBadge.tsx
│       └── InlineChart.tsx  # Recharts renderer from spec
├── lib/
│   ├── api.ts               # backend client
│   ├── eventStream.ts       # SSE consumer for demo mode
│   ├── chatStream.ts        # SSE consumer for chat
│   ├── tabRouter.ts         # tab auto-switch logic for AI actions
│   └── store.ts             # Zustand global state (incl. activeTab)
├── styles/
│   └── globals.css          # Tailwind + CSS variables for theme
└── public/
    └── store-layout.json    # mirrored from backend for client-side render
```

The three tabs are composed from the same component library — they're page-level layouts, not separate component trees. This means the build cost of the third tab (Executive Summary) is mostly composition, not new components.

### 4.2 Visual Design System

**Color tokens (CSS custom properties):**
```
--bg-deep:        #0A0E1A
--bg-card:        #131829
--bg-card-dim:    #0F1420  /* after-hours treatment */

--accent-cyan:    #00D4FF
--accent-amber:   #FFB800
--accent-coral:   #FF4D6D
--accent-mint:    #00E5A0

--text-primary:   #E8ECF1
--text-muted:     #7A8497
--text-dim:       #4A5160  /* after-hours treatment */

--heat-cold:      #1B3358
--heat-warm:      #FF7A45
--heat-hot:       #FF2E63

--ops-amber:      #FFA940  /* after-hours replenishment dots */
--ops-purple:     #9D7EFF  /* after-hours stocktake dots */
```

**Typography:** Inter for UI, Geist Mono for tabular numerics. INR values formatted with Indian numbering conventions (₹2,30,000 not ₹230,000).

**Motion:** Framer Motion's `layout` animations on card resizes; `AnimatePresence` on alert feed entries; SVG `motion.circle` for flow dots; CSS keyframes for stockout pulse.

### 4.3 Tab Composition

The three tabs are page-level layouts that compose the same underlying components in different ways. The chat panel, top bar, and tab navigation persist across tab switches; only the main content area changes.

**Live Store tab (default landing):** The Living Store Map fills the primary content area at full width. A compact operational KPI strip (six small cards in a horizontal row) sits above the map. A vertical alert feed (sized for live monitoring) runs along the right edge of the map area. This tab is the "operational pulse" view — what's happening right now.

**Analytics tab:** The chart grid fills the primary content area at full width, organized as a 2×3 layout: top row with conversion funnel + category bars + hourly trend; bottom row with size rejection heatmap + category × hour heatmap + analytical alert feed. A compact operational KPI strip sits at top. This tab is the "data story" view — what happened and why.

**Executive Summary tab:** A deliberately sparse single-page layout. The three CXO-grade business KPIs (lost sales, working capital, conversion uplift) render at large size in a 1×3 row across the top, each card roughly four times the size of an operational KPI card. Below them, a single AI-generated headline ("Today's biggest issue: ₹1.4 lakh in lost sales from the 14:00 size-28 stockout"). Below that, the top three priority alerts as expanded cards with full narrative text. At the bottom, a "Talk to your store" prompt with three suggested CXO questions as clickable buttons that send the question into the chat panel. This tab is the "executive briefing" view — what should I care about?

### 4.4 Tab Navigation & Auto-Switch

The `TabNav` component renders three tab buttons in the top bar. The currently active tab is tracked in Zustand as `activeTab: 'live_store' | 'analytics' | 'executive'`.

When the AI dispatches a `dashboard_action` with a `target_tab` that differs from `activeTab`, the `tabRouter` module:

1. Updates `activeTab` in Zustand, triggering a tab transition
2. Plays a brief 200ms crossfade on the main content area
3. Pulses the destination tab's nav indicator briefly so the user notices the auto-switch
4. After the transition completes (250ms total), applies the underlying action (highlight, filter, trace)

This means an AI response saying "size M shirts are rejecting at 71%" will auto-switch the user from wherever they are to the Analytics tab and apply the size-rejection heatmap filter — the user sees the chat narrative *and* the visual evidence without having to navigate manually.

The `target_tab` mapping for each action type:

| Action type | Target tab |
|---|---|
| `highlight_fixture` | `live_store` |
| `trace_journey` | `live_store` |
| `filter_category`, `filter_sku` | `analytics` |
| `highlight_alert` | `live_store` (or current — alerts exist on both) |
| `show_business_kpi` | `executive` |
| `none` (chat-only) | does not switch |

### 4.5 Living Store Map Implementation

On the Live Store tab, the map is a single SVG element sized to fill the primary content area at full width. Fixtures, trial rooms, tills, backroom, and exit are rendered as `<rect>` elements positioned from the layout JSON. Each fixture's fill color is computed from its current pickup rate (interpolated between `--heat-cold` and `--heat-hot`).

Active stockout fixtures get an additional `<rect>` overlay with the `pulse-alert` CSS animation, ensuring the pulse is visible on top of the heat color.

Customer flow dots are `motion.circle` elements driven by the demo mode SSE stream. When a `MOVED_TO_FLOOR` event arrives, a dot appears at the BACKROOM zone's center and animates to the destination fixture's center over a duration proportional to the simulated time delta. When `PICKED_UP` fires, the dot animates to TRIAL or TILL based on the next event in the tag's path.

To avoid overwhelming the renderer, the map caps concurrent dots at one hundred. Excess events are batched into "summary pulses" — a single dot representing N units, labeled with a count.

When the user is on the Live Store tab, dots animate visibly. When the user switches away (to Analytics or Executive Summary), the map component unmounts and event consumption pauses. When they switch back, the map resumes from the current simulated time without trying to replay the missed window. This avoids both wasted CPU on hidden tabs and the "frozen catch-up" jankiness that would happen if events queued during absence.

When the AI dispatches a `trace_journey` action, the user is auto-switched to the Live Store tab; a `PathTracer` component overlays the map with a glowing animated path connecting the SKU's zone sequence, persisting for 8 seconds before fading.

### 4.6 After-Hours Map Behavior

When the simulated time crosses outside trading hours (22:00–10:00), the map applies an after-hours treatment (only visible while the user is on the Live Store tab):

- The map's CSS variables shift to dim equivalents (`--bg-card-dim`, `--text-dim`)
- All in-flight customer flow dots fade out over 2 seconds and stop being rendered
- The `AfterHoursOverlay` component appears in the map's top-left corner with a subtle badge: "After-hours · 03:42"
- Operational events (`OPS_REPLENISHED`, `OPS_STOCKTAKE_SCAN`, `OPS_VM_RESET`) render as `OpsDot` components — visually distinct from customer dots: amber for replenishment (backroom-to-fixture trail), purple pulse-in-place for stocktake, single muted dot for VM resets
- When trading hours resume (10:00), the treatment fades back over 2 seconds and customer dots resume

This satisfies the "light touch" intent — the map stays alive at night without requiring deep operational simulation.

### 4.7 Coordinated Chart Grid

On the Analytics tab, the chart grid fills the primary content area. Its components share a Zustand-backed filter state: `gridFilter = { category?, sku?, timeRange? }`.

**Conversion Funnel:** A horizontal funnel rendered with SVG paths. Stage widths animate from zero on mount with staggered delay. Each stage shows count, percentage of previous stage, and dropoff number. Hovering a stage highlights it.

**Category Bars:** Horizontal bar chart showing trial-to-buy conversion per category. Clicking a bar sets `gridFilter.category` — funnel and other charts re-scope.

**Hourly Trend:** Line chart of hourly conversion over the last 24-48 simulated hours. Anomaly points (e.g., the planted Saturday drop window) are highlighted as red dots.

**Size Rejection Heatmap:** Cells colored by rejection rate per size, scoped to the currently filtered category or SKU. The planted SKU-4471 size M cell will dominate visually.

**Category × Hour Heatmap:** Categories on y-axis, hours on x-axis, cells colored by conversion rate. Lets viewers see daypart patterns instantly.

**Analytical Alert Feed:** A version of the alert feed sized for browsing rather than live monitoring — wider cards, fuller narrative, more historical alerts visible.

### 4.8 Cross-Filtering Behavior

Cross-filtering is the choreography that makes the analytics tab feel like a cockpit:

- Click a category bar → all grid charts re-scope to that category
- Click an alert in the analytical feed → AI panel opens with context; auto-switches to Live Store tab; map highlights the affected fixture; grid filter persists across tab switch
- Click a funnel stage → AI panel opens with a contextual question about that stage's drop-off
- On the Live Store tab, clicking a fixture filters the (off-screen) chart grid to that fixture's category — visible when the user next switches to Analytics

All of this is mediated through the single Zustand store; components subscribe to the slices they care about.

### 4.9 KPI Strips

**Operational KPI strip (Live Store and Analytics tabs):** Six small cards in a horizontal row — trial-to-buy conversion, floor-to-pickup rate, average journey time, current stockout count, trial room utilization, misplacement rate. Each with count-up animation, sparkline, delta.

**Business KPI strip (Executive Summary tab only):** Three large cards in 1×3 row — estimated lost sales today (INR), working capital tied up (INR), conversion uplift opportunity (INR). Roughly 4× the size of operational cards. These are the headline numbers a CXO scans first when landing on the Executive Summary tab.

### 4.10 AI Chat Panel

The chat panel is fixed-position bottom-right, persists across all tabs, with a collapsed pill state and an expanded panel state. Expansion is animated with a spring transition.

The panel consumes the chat SSE stream and renders four block types: user message (right-aligned bubble), tool badge (small inline pill), assistant message (left-aligned bubble with streamed text and inline chart slot), inline chart (Recharts component rendered from spec).

When AI responses include `dashboard_action` events with `target_tab` set, the panel cooperates with the `tabRouter` to auto-switch tabs as described in section 4.4.

Voice input (stretch goal) uses the Web Speech API; the mic icon toggles `SpeechRecognition` and pipes transcribed text into the input field.

### 4.11 Global State (Zustand)

```typescript
type TabId = 'live_store' | 'analytics' | 'executive';

interface DashboardState {
  // tab navigation
  activeTab: TabId;
  pendingAutoSwitch: TabId | null;  // for the auto-switch indicator pulse

  // selection & filters
  selectedStoreId: string;
  selectedTimeRange: { from: Date; to: Date };
  gridFilter: { category?: string; sku?: string; fixture?: string };

  // chat (persists across tabs)
  chatOpen: boolean;
  chatMessages: Message[];
  chatPendingContext: string | null;

  // dashboard reactions to AI
  highlightedFixtures: string[];
  tracingSkuJourney: string | null;

  // demo mode (persists across tabs)
  demoMode: boolean;
  demoSpeed: number;
  currentSimTime: Date;
  isAfterHours: boolean;
  liveCustomerEvents: Event[];
  liveOpsEvents: Event[];
}
```

All tab-specific components read from and write to this single store. The `tabRouter` module (in `lib/tabRouter.ts`) is the only writer for `activeTab` and `pendingAutoSwitch` — it ensures auto-switch transitions happen in the correct sequence (switch → pulse → apply action). AI dashboard actions translate to store updates routed through `tabRouter` when they target a non-active tab.

## 5. Data Flow Walkthroughs

### 5.1 Cold Start — Dashboard Load

1. User navigates to the dashboard URL
2. Next.js server-renders the shell with the top bar, tab navigation, and Live Store tab as the default active tab
3. Client mounts; Zustand store initializes with default selections (today, all categories, store_001) and `activeTab = 'live_store'`
4. The Live Store tab fetches its data:
   - `GET /api/store/layout` → renders the store map outline
   - `GET /api/kpis/summary` → populates the operational KPI strip
   - `GET /api/kpis/heatmap/fixtures` → colors fixtures by pickup rate
   - `GET /api/kpis/anomalies` → populates the alert feed
5. The Analytics and Executive Summary tabs do not fetch data until first activated (lazy loading)
6. User toggles demo mode → frontend opens SSE connection to `/api/events/stream?speed=100`
7. Flow dots begin animating across the map; trading-hours treatment is active

### 5.2 Tab Switch — User Manual

1. User clicks the Analytics tab button
2. Zustand `activeTab` updates to `'analytics'`
3. Live Store tab content unmounts; Analytics tab content mounts with a 200ms crossfade
4. If first activation, Analytics tab fetches:
   - `GET /api/kpis/funnel`
   - `GET /api/kpis/categories`
   - `GET /api/kpis/hourly`
   - `GET /api/kpis/heatmap/category-hour`
   - `GET /api/kpis/heatmap/sizes`
5. Charts animate in with staggered count-ups
6. Demo mode SSE stream is still consumed but no map animation runs while Live Store is unmounted; KPI strips and alert feed continue updating

### 5.3 After-Hours Transition (while on Live Store tab)

1. Demo mode advances simulated time past 22:00
2. SSE stream begins emitting `OPS_*` event types instead of customer events
3. Frontend detects state change; `isAfterHours` flips to true in Zustand
4. Map components apply after-hours treatment: dim CSS variables, fade out customer dots, render ops dots in distinct styles, show AfterHoursOverlay badge
5. Operational KPI strip values continue to update from streaming aggregates
6. Alert feed shows the planted overnight-replenishment alerts as they fire
7. At 10:00 sim-time, transition reverses; customer dots resume

### 5.4 Conversational Drill — User Asks a Question (with auto-tab-switch)

This walkthrough demonstrates the auto-switch behavior central to the multi-tab design.

1. User is on Executive Summary tab; sees "Today's biggest issue: ₹1.4 lakh in lost sales"
2. User clicks the suggested question button "Why did we lose ₹1.4 lakh today?"
3. The question routes into the chat panel (which is open and persistent across tabs)
4. Frontend POSTs to `/api/chat` with the message and current dashboard context (`activeTab='executive'`)
5. Backend opens a streaming Gemini call with the system prompt, function catalog, and message history
6. Gemini returns a `function_call` part requesting `estimate_lost_sales` for today's window — frontend renders a tool badge in the chat bubble
7. Gemini returns a `function_call` for `get_anomalies` — second tool badge appears
8. Gemini streams narrative tokens: "We lost an estimated ₹2.3 lakh today, concentrated in size-28 Women's Bottoms (₹1.4 lakh) and SKU-4471 fit-rejection (₹0.6 lakh)..."
9. Mid-stream, Gemini emits a `dashboard_action`: `{type: "highlight_fixture", id: "F_WB_B1", target_tab: "live_store"}`
10. The `tabRouter` detects `target_tab` differs from `activeTab`; pulses the Live Store tab indicator; switches `activeTab` to `'live_store'` with a 200ms crossfade; then applies the highlight after the transition completes
11. User now sees the Live Store tab with the size-28 fixture pulsing red, while the chat narrative continues streaming in the persistent chat panel
12. Gemini emits an `inline_chart` event with a Recharts spec for lost sales by SKU; chart renders in the chat bubble
13. Gemini finishes with "Recommendation: address the 14:00 replenishment lag — that's ₹1.4 lakh of recoverable revenue" and `done`

The user experiences a seamless flow: question on Executive Summary → narrative starts → automatic transition to the visual evidence on Live Store → chart rendering inline. They never had to think about navigation.

### 5.5 Click-Driven Drill — User Clicks an Alert

1. User on the Live Store tab clicks the "Size 28 Women's Bottoms stocked out" alert in the feed
2. Frontend updates Zustand: `chatOpen = true`, `chatPendingContext = "alert_id_XYZ"`
3. Chat panel opens (already on the active tab, no switch needed); the context auto-sends a message: "Investigate the size 28 stockout alert"
4. From step 4 of section 5.4, the flow continues; in this case `target_tab` matches `activeTab` so no auto-switch occurs

## 6. Demo Mode Choreography

Demo mode is the playback engine that lets the CXO viewer see the store come to life. When enabled:

1. Backend resets to the start of a designated demo day (a chosen Saturday from the 14-day window — the one with the planted Trial Room utilization drop)
2. Events stream at 100x real time, so a 24-hour day plays in ~14 minutes; trading hours alone are ~7 minutes
3. The frontend animates flow dots on the Live Store tab, updates KPI sparklines as values shift, fires alerts as anomalies cross thresholds
4. Pre-scripted moments hit at known timestamps:
   - ~01:30 of demo: stockout alert fires (Women's Bottoms size 28) — fixture pulses on Live Store map
   - ~02:30 of demo: high-rejection SKU (Men's Shirt 4471) accumulates enough trial events to trip the rejection-rate alert
   - ~03:30 of demo: Trial Room utilization drop becomes visible (the Saturday-vs-Saturday story)
   - ~04:30 of demo: shrinkage cluster fires
   - ~07:00 of demo: trading day ends; Live Store map transitions to after-hours treatment
   - ~07:30 of demo: replenishment events flow from backroom to size-28 fixture, closing the stockout loop
   - ~13:00 of demo: trading day resumes
5. After end-of-day, demo mode loops with a brief fade-and-reset transition

The presenter typically narrates from the Live Store tab during the trading-day window and the after-hours sequence (the visual story). Switches to the Analytics tab happen during AI-driven drill-downs (auto-switched by the system) or explicit presenter actions when discussing historical patterns. The Executive Summary tab is the opening shot — what a CXO sees first when landing on the dashboard before demo mode begins.

The pre-scripted moments give the demo a reliable narrative arc even if the presenter doesn't intervene with chat questions. The CXO sees the store live, the night cycle, and the morning recovery — the full operational rhythm in 14 minutes.

## 7. Technology & Library Choices

| Layer | Choice | Rationale |
|---|---|---|
| Synthetic data | Python (numpy, pandas, scipy) | Familiar; right tools for distribution sampling and tabular ops |
| Storage | Parquet + DuckDB | Zero-config analytical queries; schema-compatible with Databricks/Delta |
| Backend | FastAPI + Pydantic | Streaming support, auto-docs, production-handoff friendly |
| AI | Gemini via Google AI Studio API (or Vertex AI in production) | Function calling, streaming, India-region data residency option, strong fit for Tata Group's Google Cloud relationships |
| Frontend framework | Next.js 14 (App Router) | SSR, ecosystem, deployment speed |
| Styling | Tailwind CSS + shadcn/ui | Looks designed out of the box; rapid iteration |
| Animation | Framer Motion | Declarative, layout-aware, polish-grade |
| Charts | Recharts | Composable, Tailwind-friendly, AI-spec-renderable |
| State | Zustand | Minimal boilerplate, perfect for dashboard-scale state |
| Streaming | Native EventSource (SSE) | Simpler than WebSockets for one-way streams; works with FastAPI |

## 8. The CXO Pitch Frame

The pitch lands these four points in order:

1. **The problem in numbers**: Indian fashion retail loses 8–12% of potential sales to floor stockouts while backroom inventory sits idle. Fit-driven trial rejection is a major hidden cost no current system surfaces.

2. **The prototype**: A live store dashboard showing every product unit's journey, with AI-driven explanation. Demonstrate it. Let it speak.

3. **The path to Trent stores**: One slide showing the production-shape mapping (section 1.2 of this design). Same architecture, swap the prototype layer for Trent's existing Azure/Databricks/RFID infrastructure.

4. **The investment ask**: Pilot in one Westside store (~₹25-30 lakh hardware + ₹1-1.5 cr software/team for 6-9 months). Quantify the ROI from recovered lost sales and conversion uplift across that store; extrapolate to format-level rollout.

This is the structure the pitch deck should follow. The dashboard is the substance; the CXO frame is what makes it a business proposal rather than a tech demo.
