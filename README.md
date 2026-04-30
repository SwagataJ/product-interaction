# In-Store Product Journey Tracker

A real-time RFID-based product journey analytics dashboard for fashion retail, built as a CXO demo for Trent Limited (Westside/Zudio). Tracks every product unit from backroom to final outcome (sale, rejection, misplacement, shrinkage) and surfaces actionable insights through a live store map, coordinated analytics charts, and a conversational AI layer.

## Architecture

```
Frontend (Next.js 14 + React)
  - Live Store Map (SVG + animated flow dots)
  - Analytics Grid (12 cross-filtered charts)
  - Executive Summary (AI headline + KPIs)
  - AI Chat Panel (streaming, context-aware)
  - Shared state via Zustand
        |
        | HTTP + SSE (streaming)
        v
Backend (FastAPI)
  - REST KPI endpoints
  - SSE event stream (demo mode replay)
  - AI Agent (Gemini 2.5 Pro, function calling)
        |
        v
DuckDB + Parquet (events, catalog, inventory)
        ^
        |
Synthetic Data Generator (Python)
  - Store layout, catalog, tag inventory
  - 14-day journey simulation with planted insights
```

### Production-Shape Mapping

| Prototype | Production Equivalent (Trent) |
|---|---|
| Python synth generator | Real RFID readers + Impinj/Zebra middleware |
| Local Parquet files | Delta Lake on Azure Data Lake Gen2 |
| DuckDB queries | Databricks SQL warehouse |
| FastAPI on laptop | FastAPI on Azure App Service / AKS |
| Gemini API (Vertex AI) | Vertex AI Gemini in `asia-south1` (Mumbai) |

## Features

### Live Store Tab
- SVG floor plan with heat-colored fixtures (engagement intensity)
- Animated flow dots showing real-time product movement between zones
- Event types: pickups, trial room entries, purchases, rejections, replenishment
- Category-colored fixtures with brand labels and placement badges
- After-hours mode with dimmed visuals and ops-only activity

### Analytics Tab
- 6 operational KPIs (trial-to-buy, pickups, rejections, misplacement rate)
- 3 business KPIs (lost sales, working capital, conversion uplift)
- Cross-filtered charts: conversion funnel, category bars, hourly trend, brand performance, sub-category, fit analysis, color performance, price tier, size rejection heatmap, category-hour heatmap
- Click a category bar to filter all charts; click an alert to ask AI about it

### Executive Summary Tab
- AI-generated one-sentence headline (streamed from Gemini)
- Large INR-formatted business KPI cards with category breakdowns
- Operational snapshot metrics
- Priority alerts (clickable, opens AI chat)
- "Talk to Your Store" suggested questions

### AI Chat Panel
- Floating panel available on all tabs
- Gemini 2.5 Pro with 7 function-calling tools
- Streams responses with tool execution badges
- Markdown rendering (bold, lists, tables, code)
- Dashboard actions: auto-switches tabs, highlights fixtures, filters charts
- Auto-starts demo mode when redirecting to Live Store

## Project Structure

```
product-interaction/
  generator/              # Synthetic data generation
    store_layout.json     # Zone positions and fixture metadata
    build_catalog.py      # SKU catalog (300-500 SKUs)
    build_inventory.py    # Tag inventory (5K-10K units)
    journey_paths.py      # Journey state machine
    timestamps.py         # Realistic time distributions
    after_hours.py        # Overnight ops simulation
    synth.py              # Main generator orchestrator
    validate_stories.py   # Verify planted insight stories
  data/                   # Generated Parquet files
    events.parquet
    product_catalog.parquet
    tag_inventory.parquet
  backend/
    main.py               # FastAPI app with CORS
    api/
      kpis.py             # 15 KPI/analytics endpoints
      store.py            # Store layout endpoint
      events.py           # SSE event stream for demo mode
      chat.py             # AI chat SSE endpoint
    data/
      duckdb_client.py    # DuckDB connection manager
      kpi_queries.py      # All analytical SQL queries
    ai/
      agent.py            # Gemini chat loop + streaming
      tools.py            # 7 function declarations + dispatcher
      prompts.py          # System prompt
  frontend/
    app/
      page.tsx            # Main page with tab routing
      layout.tsx          # Root layout (dark theme)
      globals.css         # Design tokens + custom styles
    lib/
      store.ts            # Zustand global state
      api.ts              # API types and fetchers
      eventStream.ts      # SSE consumer for demo events
      chatStream.ts       # Chat SSE consumer + action dispatch
    components/
      topbar/TopBar.tsx          # Nav tabs, demo controls, sim clock
      kpi/KpiCard.tsx            # Animated KPI card
      kpi/KpiStrip.tsx           # Operational KPIs
      kpi/BusinessKpiStrip.tsx   # Business KPIs
      store-map/StoreMap.tsx     # SVG floor plan
      store-map/Fixture.tsx      # Individual fixture rendering
      store-map/FlowDots.tsx     # Animated product movement dots
      grid/ChartGrid.tsx         # Analytics chart layout
      grid/ConversionFunnel.tsx
      grid/CategoryBars.tsx
      grid/HourlyTrend.tsx
      grid/BrandBars.tsx
      grid/SubcategoryBars.tsx
      grid/FitAnalysisChart.tsx
      grid/ColorPerformance.tsx
      grid/PriceTierChart.tsx
      grid/SizeRejectionHeatmap.tsx
      grid/CategoryHourHeatmap.tsx
      grid/AlertFeed.tsx
      chat/ChatPanel.tsx         # Floating AI chat
      chat/MessageBubble.tsx     # Markdown message rendering
      exec/ExecutiveSummary.tsx   # Executive summary tab
```

## Prerequisites

- Python 3.12+
- Node.js 23+
- Google Cloud service account with Vertex AI access (Gemini 2.5 Pro)

## Setup

### 1. Environment

```bash
cp .env.example .env
# Edit .env with your settings:
#   GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
#   GOOGLE_CLOUD_PROJECT=your-project-id
#   GEMINI_MODEL=gemini-2.5-pro
#   DATA_DIR=./data
#   NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Python Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn duckdb pyarrow google-genai pydantic
```

### 3. Generate Synthetic Data (if not already present)

```bash
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)
python -m generator.synth
python -m generator.validate_stories  # verify planted insights
```

### 4. Frontend

```bash
cd frontend
npm install
```

## Running

### Start Backend
```bash
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)
uvicorn backend.main:app --port 8000
```

### Start Frontend
```bash
cd frontend
npm run dev
```

Open http://localhost:3000

## Demo Mode

Click the **Demo** button in the top bar to start the event stream replay. This plays back the busiest day's events starting at store opening (10:00 AM), accelerated by the selected speed multiplier (50x-500x). The Live Store tab shows animated dots traveling between zones as products are picked up, tried on, purchased, or rejected.

## AI Chat

Click **Ask AI** to open the chat panel. The AI agent has access to 7 tools:
- `get_kpi` — Summary metrics (trial-to-buy, pickups, etc.)
- `get_funnel` — Conversion funnel stages
- `get_anomalies` — Alerts (stockouts, fit issues, placement gaps)
- `get_sku_journey` — Full event trace for a specific SKU
- `compare_periods` — Period-over-period comparison
- `estimate_lost_sales` — Revenue impact of backroom stockouts
- `get_size_rejection_heatmap` — Size-level rejection analysis

### Planted Insight Stories
The synthetic data contains 6 discoverable stories:
1. **Size 28 stockout** — Nuon Women's Western, 19 units in backroom, none on floor
2. **High rejection SKU** — ETA Men's Casual SKU-4471, 88% trial rejection (fit issue)
3. **Saturday conversion drop** — Traceable to operational failure
4. **Fixture placement gap** — F_MS_C1 outperforms F_A_F1 by 2.2x
5. **Shrinkage cluster** — Exit-without-sale events on specific SKUs
6. **Replenishment SLA failure** — Overnight replenishment misses causing morning stockouts

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/kpis/summary` | GET | Operational KPIs |
| `/api/kpis/business` | GET | Business KPIs (lost sales, working capital) |
| `/api/kpis/funnel` | GET | Conversion funnel |
| `/api/kpis/categories` | GET | Category performance |
| `/api/kpis/hourly` | GET | Hourly trend data |
| `/api/kpis/brands` | GET | Brand performance |
| `/api/kpis/subcategories` | GET | Sub-category performance |
| `/api/kpis/colors` | GET | Color performance |
| `/api/kpis/price-tiers` | GET | Price tier conversion |
| `/api/kpis/fit-analysis` | GET | Fit type analysis |
| `/api/kpis/anomalies` | GET | Alerts and anomalies |
| `/api/kpis/lost-sales` | GET | Lost sales by category |
| `/api/kpis/heatmap/fixtures` | GET | Fixture engagement heatmap |
| `/api/kpis/heatmap/sizes` | GET | Size rejection heatmap |
| `/api/kpis/heatmap/category-hour` | GET | Category x hour heatmap |
| `/api/store/layout` | GET | Store floor plan zones |
| `/api/events/stream` | GET | SSE event stream (demo) |
| `/api/chat` | POST | AI chat (SSE response) |
| `/health` | GET | Health check |

Most KPI endpoints accept optional `category` query parameter for filtering.

## Tech Stack

- **Frontend:** Next.js 14, React, Zustand, Recharts, Framer Motion, Lucide Icons
- **Backend:** FastAPI, DuckDB, PyArrow
- **AI:** Google Gemini 2.5 Pro via Vertex AI (`google-genai` SDK)
- **Data:** Parquet files, synthetic RFID event simulation
