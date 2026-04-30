# Tasks — In-Store Product Journey Tracker (7-Day Solo Build)

## How To Read This Document

Tasks are organized by **calendar day** rather than abstract phases — solo work over a week is paced by daily energy, not Gantt charts. Each day has:

- A **target** stated in plain language so you know what "done for the day" looks like
- A **time budget** (most days are 7–9 productive hours; one day is a deliberate rest/buffer day)
- Numbered tasks (`D1.1`, `D1.2` …) with estimates and acceptance criteria
- An **end-of-day checkpoint** — if this is true, you're on track; if not, decide whether to push or cut

Total budget: ~50–60 productive hours across 7 days. Day 5 is a half-day rest/buffer by design — solo builds that skip rest days hit Day 7 with broken code and no demo.

The critical principle: **the chart grid carries the dashboard if the map under-delivers**. Build the grid first. The map is the wow but the grid is the floor.

---

## Day 1 — Foundations & Synthetic Data Generator

**Target:** By end of day, `events.parquet` exists with all six planted stories statistically detectable. Backend FastAPI skeleton runs and serves a health check.

**Time budget:** 8 hours

### D1.1 Repo & environment setup `[1h]`
Create the monorepo with three top-level folders: `generator/`, `backend/`, `frontend/`. Add root `README.md`, `.gitignore`, `.env.example` files. Install Python 3.11+, Node 20+. Verify Google AI Studio API key with a smoke-test Python call.
**Acceptance:** A smoke test using `google-genai` SDK to call `gemini-2.5-pro` returns a real response.

### D1.2 Store layout JSON `[30m]`
Author `generator/store_layout.json` per design section 2.1. Eleven zones with realistic coordinates. Include `placement` attribute on fixtures. Mirror to `frontend/public/store-layout.json` (for later).
**Acceptance:** Load JSON in a Python REPL; zone count and types match spec.

### D1.3 Product catalog generation `[1h]`
Write `generator/build_catalog.py` producing `product_catalog.parquet` with 350 SKUs. Realistic size curves per category. Price tiers in INR aligned with mid-price fashion retail. Include `unit_cost_inr` for the working-capital KPI. Plant SKU-4471 as the Men's Slim Fit Shirt with full size range.
**Acceptance:** Parquet loads in DuckDB; counts per category balanced; SKU-4471 exists with sizes XS–XL.

### D1.4 Tag inventory generation `[45m]`
Write `generator/build_inventory.py` producing `tag_inventory.parquet` with ~7000 tags. 70% on appropriate fixture, 30% in BACKROOM. Size-28 Women's Bottoms gets 60+ backroom tags to support the stockout-while-stocked story.
**Acceptance:** Per-fixture tag counts reasonable; size-28 backroom inventory present.

### D1.5 Journey path sampler `[1.5h]`
Write `generator/journey_paths.py`. Define path probability distributions from design section 2.4. Implement planted-story modifiers for SKUs and zones. Function: `sample_path(tag_record) → list[(event_type, zone_to)]`.
**Acceptance:** 10,000 sampled paths show aggregate distributions matching design (within 2 percentage points). SKU-4471 size M paths show ~71% trial rejection.

### D1.6 Timestamp sampler `[45m]`
Write `generator/timestamps.py`. Sample timestamps for events using gamma/exponential/normal distributions. Apply intra-day weighting (lunch peak, evening peak). Enforce trading hours for customer events.
**Acceptance:** Sampled day's events have realistic hour-of-day histogram (peak 18:00–21:00); no customer events 22:00–10:00.

### D1.7 After-hours operational events `[1h]`
Extend `timestamps.py` and add `generator/after_hours.py`. Generate `OPS_REPLENISHED`, `OPS_STOCKTAKE_SCAN`, `OPS_VM_RESET` events at low volume during 22:00–10:00. For 2 of 14 nights, suppress replenishment for the size-28 SKU (planted story #6).
**Acceptance:** ~50–100 ops events per night; 2 nights are missing the size-28 replenishment.

### D1.8 Event stream assembly `[1h]`
Write `generator/synth.py` as the main entry point. Iterates all tags, samples paths, samples timestamps, includes after-hours, writes `events.parquet`. Plant all six insight stories.
**Acceptance:** `python -m generator.synth` completes in under 3 minutes producing ~300,000 events. DuckDB sanity queries return sensible numbers.

### D1.9 Planted-story validation `[45m]`
Write `generator/validate_stories.py`. Six DuckDB queries, one per planted story, asserting each is detectable:
- SKU-4471 size M trial rejection > 65%
- Daily size-28 floor stockout while backroom > 30
- Saturday-vs-Saturday trial event delta > 40%
- Front fixture pickup / back fixture pickup > 3
- Three Accessories SKUs near exit with EXITED_WITHOUT_SALE > 5x baseline
- 2 nights with replenishment SLA breach for size-28 SKU
**Acceptance:** All six assertions pass. Tune until they do.

### D1.10 FastAPI skeleton `[30m]`
Initialize `backend/`. Install fastapi, uvicorn, duckdb, google-genai, pydantic. Create `main.py` with CORS (allow localhost:3000), health endpoint.
**Acceptance:** `uvicorn main:app --reload` runs; `GET /health` returns `{"ok": true}`.

**End of Day 1 checkpoint:** `events.parquet` exists, validate_stories.py passes all six, FastAPI starts. If any of these are red, do not move to Day 2 — stay on Day 1 tasks.

---

## Day 2 — Backend KPI API

**Target:** All KPI endpoints return correct JSON. Anomaly detection surfaces all six planted stories. Event stream endpoint streams events via SSE.

**Time budget:** 8 hours

### D2.1 DuckDB client `[30m]`
Build `backend/data/duckdb_client.py` exposing a singleton DuckDB connection that loads the Parquet files as views.
**Acceptance:** `client.query("SELECT COUNT(*) FROM events")` returns expected count in <1s.

### D2.2 KPI query library — operational `[2h]`
Write `backend/data/kpi_queries.py`. Functions for: summary KPIs, funnel, category bars, hourly trend, fixture heatmap, size-rejection heatmap, category-hour heatmap, SKU journey, replenishment SLA. Each takes filter parameters, returns structured dict.
**Acceptance:** Each function tested in REPL returns sensible output; queries complete <500ms.

### D2.3 KPI query library — business (CXO) `[1h]`
Add functions for the three CXO-grade KPIs: estimated lost sales, working capital tied up, conversion uplift opportunity. Use realistic INR formulas. Document the assumptions clearly in code comments — the CXO will ask "how did you compute this".
**Acceptance:** Each business KPI returns a number in INR with documented derivation. Lost sales for the demo day is a meaningful figure (likely ₹1.5–3 lakh).

### D2.4 Anomaly detection logic `[1.5h]`
Implement `get_anomalies` per design FR-2.6. Detection rules: stockout-while-stocked >30min, SKU rejection >2x category baseline, fixture performance >2x or <0.5x category average, shrinkage rate >3x global baseline, replenishment SLA breach. Return alerts ranked by severity with narrative text.
**Acceptance:** Calling the endpoint surfaces all six planted stories among the top alerts on the demo day.

### D2.5 KPI REST endpoints `[1.5h]`
Build `backend/api/kpis.py` exposing all endpoints from design section 3.2. Each validates query params with Pydantic, calls the corresponding function, returns JSON.
**Acceptance:** Manual curl tests show all endpoints return valid JSON; OpenAPI docs at `/docs` look clean.

### D2.6 Store layout endpoint `[15m]`
`GET /api/store/layout` reads the JSON and returns it.
**Acceptance:** Endpoint returns full layout.

### D2.7 Event stream SSE `[1h]`
Build `backend/api/events.py` per design section 3.3. SSE endpoint streaming events from Parquet at configurable speed. Loops at end-of-data. Handles both customer and ops event types.
**Acceptance:** `curl -N http://localhost:8000/api/events/stream?speed=100` shows events streaming at the right rate; ops events appear during after-hours timestamps.

### D2.8 End-to-end backend smoke test `[15m]`
Walk through every endpoint with curl. Verify everything works as a system, not just individual functions.
**Acceptance:** All endpoints respond correctly; no 500 errors; query performance feels snappy.

**End of Day 2 checkpoint:** Backend is "feature complete" for the data layer. All KPIs computable. Anomalies detected. Stream works. If any of this is broken, fix before moving on — Day 3+ depends on this being solid.

---

## Day 3 — Frontend Foundations & Chart Grid (Part 1)

**Target:** Frontend skeleton runs. Theme system works. Top bar, KPI strips, conversion funnel, and category bars render with real data.

**Time budget:** 9 hours

### D3.1 Next.js project init `[30m]`
`npx create-next-app@latest frontend --typescript --tailwind --app`. Install: framer-motion, zustand, recharts, lucide-react, shadcn/ui CLI + components.
**Acceptance:** `npm run dev` serves a hello-world on port 3000.

### D3.2 Theme & design tokens `[1h]`
Configure Tailwind with the color tokens from design section 4.2 (including ops-amber, ops-purple, dim variants). Add Inter and Geist Mono via `next/font`. Apply dark theme by default. Build base utility classes for glassmorphic cards.
**Acceptance:** A test page using all the color tokens renders correctly with proper typography.

### D3.3 Zustand global store `[45m]`
Build `lib/store.ts` per design section 4.9. Include selectors for derived state (`getActiveAlerts`, `isAfterHoursDerived`).
**Acceptance:** Debug component reads/writes the store; React DevTools shows expected shape.

### D3.4 API client `[45m]`
Build `lib/api.ts` with typed fetchers for all KPI endpoints + layout. Generate TypeScript types from the backend's OpenAPI spec or write them manually.
**Acceptance:** From a debug page, calling `getKpiSummary()` returns parsed data from the backend.

### D3.5 Top bar `[1h]`
Build `components/topbar/TopBar.tsx`: store selector (single store dropdown), simulated time display, demo mode toggle with speed selector, live status pulse indicator. Glassmorphic styling.
**Acceptance:** Top bar renders; demo toggle flips Zustand boolean; speed selector updates Zustand.

### D3.6 Operational KPI strip `[1.5h]`
Build `components/kpi/KpiCard.tsx` (count-up animation, sparkline, delta arrow) and `KpiStrip.tsx` (2x3 grid). Wire to `/api/kpis/summary`.
**Acceptance:** Six cards render with real values, all animate cleanly on load.

### D3.7 Business KPI strip (CXO) `[1h]`
Build `components/kpi/BusinessKpiStrip.tsx` — three larger cards in 1x3 row showing lost sales, working capital, conversion uplift in INR. Use Indian numbering (₹2,30,000 not ₹230,000). Sparklines and deltas. Style for prominence — these are the CXO-scan-first numbers.
**Acceptance:** Three cards display correctly formatted INR values from `/api/kpis/business`.

### D3.8 Conversion funnel `[1.5h]`
Build `components/grid/ConversionFunnel.tsx`. SVG-based horizontal funnel, four stages, animated bar fills with stagger, hover tooltips with category breakdown, dropoff numbers per stage.
**Acceptance:** Funnel renders with real data, animates on mount, tooltips work.

### D3.9 Category bars `[1h]`
Build `components/grid/CategoryBars.tsx`. Horizontal bar chart, trial-to-buy per category. Click handler that writes to `gridFilter.category` in Zustand.
**Acceptance:** Bars render; clicking a bar updates store; visual selected state on the clicked bar.

**End of Day 3 checkpoint:** Top half of the dashboard (top bar, both KPI strips, funnel, category bars) is visually complete with real data. If you stopped here, it would already look like a working dashboard.

---

## Day 4 — Chart Grid (Part 2) + AI Agent Backend

**Target:** Chart grid is fully composed and cross-filters correctly. AI agent answers questions end-to-end via streaming SSE with tool calls.

**Time budget:** 9 hours

### D4.1 Hourly trend chart `[45m]`
Build `components/grid/HourlyTrend.tsx`. Recharts LineChart of hourly conversion. Highlight anomaly points (red dots) where conversion drops sharply.
**Acceptance:** Chart renders; the planted Saturday-drop window shows a visible dip with a red anomaly marker.

### D4.2 Size rejection heatmap `[45m]`
Build `components/grid/SizeRejectionHeatmap.tsx`. Cells colored by rejection rate per size, scoped by `gridFilter`. When filtered to Men's Shirts SKU-4471, size M cell is dramatically darker red.
**Acceptance:** Heatmap renders correctly; filter changes update the data; SKU-4471 size M shows the planted anomaly.

### D4.3 Alert feed `[1h]`
Build `components/grid/AlertFeed.tsx`. Vertically scrolling alert cards, severity color bars, narrative text, "Investigate" buttons. New alerts animate in via `AnimatePresence`.
**Acceptance:** Feed renders alerts from `/api/kpis/anomalies`, ordered by severity, with all six planted stories visible.

### D4.4 Category × hour heatmap `[45m]`
Build `components/grid/CategoryHourHeatmap.tsx`. Categories vertical, hours horizontal, cells colored by conversion rate. Tooltip on hover.
**Acceptance:** Heatmap renders; visible patterns from planted stories show up.

### D4.5 Chart grid composition & cross-filtering `[1h]`
Build `components/grid/ChartGrid.tsx` to compose all six charts. Wire cross-filtering: clicking a category bar updates `gridFilter` and all charts re-fetch with the filter applied. Visual indicator showing active filter ("Showing: Men's Shirts ✕").
**Acceptance:** Click any category bar; funnel, hourly trend, size heatmap all re-scope. Click ✕ clears filter.

### D4.6 AI tool definitions `[45m]`
Build `backend/ai/tools.py` defining the seven tools from design section 3.4.2 as Gemini `FunctionDeclaration` objects (using JSON Schema parameter syntax). Clear descriptions that help Gemini know when to use each.
**Acceptance:** Function list passes a smoke-test `generate_content` call without schema errors; Gemini emits a sensible function call when prompted.

### D4.7 AI tool handlers `[1h]`
Implement handler functions mapping each tool name + input to a `kpi_queries.py` call. Build dispatcher in `backend/ai/agent.py`: `execute_tool(name, input) → result`. Errors return structured error results, not exceptions.
**Acceptance:** `execute_tool("estimate_lost_sales", {...})` returns expected structure with INR values.

### D4.8 System prompt authoring `[1h]`
Draft the agent system prompt in `backend/ai/prompts.py` per design section 3.4.4. Establish role (Trent retail analyst), mandate tool use, enforce response structure, frame in INR/CXO language. Include 2-3 few-shot examples.
**Acceptance:** Manual smoke test — agent answers a planted question coherently with at least one tool call.

### D4.9 Tool-calling loop `[1.5h]`
Implement the loop in `agent.py`: open a Gemini `generate_content` call with system prompt, tools, and message history; on each `function_call` part returned, execute the corresponding handler and feed the `function_response` back via `send_message`; loop until the model returns a final text response with no function calls. Cap at 8 iterations to prevent runaway.
**Acceptance:** End-to-end: agent receives "How much revenue did we lose to stockouts today?", makes 2-3 tool calls, returns coherent INR-framed answer.

### D4.10 Streaming chat endpoint `[1h]`
Build `backend/api/chat.py` exposing `POST /api/chat` as SSE per design section 3.4.3. Stream tool_call, tool_result, token, dashboard_action, inline_chart, done events. Pass dashboard context into the prompt.
**Acceptance:** `curl -N -X POST` shows interleaved SSE events streaming during a chat call.

**End of Day 4 checkpoint:** Chart grid is complete and cross-filters. AI agent answers questions via streaming. The two halves of the dashboard exist independently — Day 5/6 connects them.

---

## Day 5 — Half-Day Rest / Buffer

**Target:** Catch up on anything that slipped from Days 1–4. Otherwise rest.

**Time budget:** 3–4 hours active, rest of day off

This day is non-negotiable. Solo builds without rest days produce broken Day 7 demos. Use this day to:

- Finish anything that fell behind (most likely some chart in the grid, or AI prompt tuning)
- Take a long walk, get outside, sleep properly
- Review what you've built so far with fresh eyes — write down two or three things you'd change
- If everything is on track, do D6.1 (Living Store Map static render) early so Day 6 has more breathing room

**Acceptance:** You feel ready to do the highest-stakes work of the build (the map and the AI integration) on Day 6.

---

## Day 6 — Living Store Map + AI Integration

**Target:** Living Store Map renders, animates flow dots, applies after-hours treatment. AI chat panel works end-to-end with bidirectional dashboard binding. Click-driven context works.

**Time budget:** 9 hours — this is the highest-stakes day; do it rested.

### D6.1 Static store map render `[1.5h]`
Build `components/store-map/StoreMap.tsx`. SVG sized to ~55% viewport. Rectangles for each zone from the layout JSON. Different fill colors per zone type. Labels.
**Acceptance:** Map renders with all eleven zones visibly placed and labeled.

### D6.2 Fixture heat coloring `[45m]`
Build `components/store-map/Fixture.tsx` accepting pickup-rate prop, computing fill color via interpolation. Wire to `/api/kpis/heatmap/fixtures`.
**Acceptance:** Fixtures show varying heat colors; planted high-pickup front fixture is hottest.

### D6.3 Stockout pulse animation `[30m]`
Add CSS keyframe animation `pulse-alert`. Apply via overlay rect when fixture has active stockout alert.
**Acceptance:** Stockout fixtures pulse visibly red.

### D6.4 SSE event stream consumer `[45m]`
Build `lib/eventStream.ts` opening EventSource to `/api/events/stream?speed=100`, dispatching events to Zustand. Trigger only when `demoMode` is true. Track `currentSimTime` and derive `isAfterHours`.
**Acceptance:** Toggling demo mode populates `liveCustomerEvents` and `liveOpsEvents`; sim time advances visibly.

### D6.5 Customer flow dot animation `[1.5h]`
Build `components/store-map/FlowDot.tsx`. `motion.circle` animating from start zone center to end zone center over a duration proportional to the simulated time delta. Pool managed in Zustand. Cap at 100 concurrent.
**Acceptance:** During demo mode, dots flow visibly across the map at a comfortable pace; no frame drops.

### D6.6 After-hours visual treatment `[1h]`
Build `components/store-map/AfterHoursOverlay.tsx`. When `isAfterHours` is true: dim CSS variables on map container, fade out customer dots over 2s, render OpsDot components for ops events (amber for replenishment with backroom-to-fixture trail, purple pulse-in-place for stocktake), show "After-hours · HH:MM" badge.
**Acceptance:** During demo mode, when sim time crosses 22:00, map visibly transitions; ops events render distinctly; badge shows current time.

### D6.7 Chat panel UI `[1h]`
Build `components/chat/ChatPanel.tsx`. Collapsed pill state in bottom-right; expanded panel state with spring transition. Input field, send button, scrollable messages. `MessageBubble.tsx`, `ToolBadge.tsx`, `InlineChart.tsx`.
**Acceptance:** Panel expands/collapses smoothly; bubbles render distinctly.

### D6.8 Chat SSE consumer `[1h]`
Build `lib/chatStream.ts`. POSTs to `/api/chat` using `fetch` + `ReadableStream` (EventSource doesn't support POST). Dispatches event types to handlers. Wire up message rendering.
**Acceptance:** Sending a message produces tokens streaming into the bubble in real time.

### D6.9 Dashboard action dispatcher `[45m]`
Wire `dashboard_action` SSE handler to update Zustand: `highlight_fixture` pushes to `highlightedFixtures` (with 8s expiry), `trace_journey` sets `tracingSkuJourney`. Map components subscribe and react.
**Acceptance:** A test chat message that should highlight fixture F_MS_C1 actually causes the fixture to highlight on the map.

### D6.10 Inline chart rendering `[30m]`
The agent emits `inline_chart` events with Recharts specs. `InlineChart.tsx` renders the spec inside the message bubble.
**Acceptance:** At least one planted question produces a coherent inline chart.

### D6.11 Click-driven chat context `[45m]`
Wire onClick handlers on KPI cards, alerts, fixtures, category bars, funnel stages. Each opens chat panel and auto-sends a context-appropriate message.
**Acceptance:** Clicking each interactive element opens chat with a relevant pre-filled question that streams a useful answer.

**End of Day 6 checkpoint:** Full system works end-to-end. All five planted CXO questions return streaming answers with dashboard reactions. Map animates customer flow during trading hours and ops events at night. The dashboard is functionally complete; Day 7 is polish + pitch.

---

## Day 7 — Polish, CXO Pitch, Demo Rehearsal

**Target:** Three tabs composed and polished. Auto-switch on AI actions works. Pitch deck ready. Three full demo run-throughs under 7 minutes. Backups exist.

**Time budget:** 9.5 hours (the additional Executive Summary tab and auto-switch logic add ~2 hours over the original Day 7 plan; consider pushing some of D7.1–D7.3 into a Day 6 evening if Day 6 finished early)

### D7.1 Tab shell & navigation `[1h]`
Build the three-tab shell in `app/page.tsx` with `TabNav` component. Wire `activeTab` to Zustand. Tab buttons in the top bar with active-state styling. 200ms crossfade on tab switch using Framer Motion's `AnimatePresence`. Lazy-load tab content (each tab fetches its own data on first activation).
**Acceptance:** Three tabs are clickable; switching tabs triggers crossfade; URL hash updates so tab state survives a refresh.

### D7.2 Live Store tab composition `[45m]`
Compose `app/tabs/LiveStoreTab.tsx`: operational KPI strip at top, Living Store Map fills primary area, vertical alert feed sidebar on the right. Tune spacing.
**Acceptance:** Screenshot at 1920×1080 shows a balanced operational view.

### D7.3 Analytics tab composition `[45m]`
Compose `app/tabs/AnalyticsTab.tsx`: compact operational KPI strip at top, chart grid in 2×3 layout below (funnel, category bars, hourly trend, size heatmap, category × hour heatmap, analytical alert feed).
**Acceptance:** All six grid components render in their assigned cells; cross-filtering works.

### D7.4 Executive Summary tab build `[1.5h]`
Compose `app/tabs/ExecutiveSummaryTab.tsx`: large business KPI strip (1×3, ~4× normal card size), AI-generated headline card below, top three priority alerts as expanded cards, "Talk to your store" prompt with three suggested questions as buttons. Build `components/exec/HeadlineCard.tsx` (small, uses the same chat backend with a prompt asking for "today's headline in one sentence") and `components/exec/SuggestedQuestions.tsx` (three buttons that send pre-defined CXO questions into the chat panel on click).
**Acceptance:** Tab loads with three large INR-formatted KPIs prominently displayed, headline appears within 5 seconds of tab activation, suggested question buttons trigger chat panel responses.

### D7.5 Auto-switch behavior wiring `[45m]`
Build `lib/tabRouter.ts` with the auto-switch logic from design section 4.4. AI dashboard actions with `target_tab` mismatching `activeTab` route through the tabRouter: pulse destination indicator, switch tab, apply action after 250ms. Update the AI agent's system prompt to include `target_tab` in dashboard_action emission.
**Acceptance:** Asking "show me the size 28 stockout" from the Executive Summary tab auto-switches to Live Store with the fixture pulsing.

### D7.6 Loading & empty states `[45m]`
Every component handles loading (skeleton shimmer), empty (graceful message), error (subtle banner). No raw "undefined" or zeros.
**Acceptance:** Reload with throttled network; every component degrades gracefully.

### D7.7 Animation choreography pass `[1h]`
Walk through the dashboard across all three tabs. Tune timings: cards stagger their count-ups, funnel bars fill in sequence, map dots have comfortable pace, tab transitions feel snappy not laggy, hover effects snappy. Reduce motion if it feels chaotic.
**Acceptance:** A 30-second screen recording across all tabs feels professional.

### D7.8 Demo mode pre-scripted moments `[45m]`
Tune the synthetic data so the planted-story alerts fire at the demo timestamps from design section 6. Confirm by running demo mode end-to-end and watching the alert feed.
**Acceptance:** During a 14-minute demo loop, the six alerts fire in the planned order with consistent timing.

### D7.9 Planted question rehearsal `[1.5h]`
Run the five planted CXO questions verbatim against the live system:
1. "How much revenue did we lose to stockouts today?"
2. "Why did Men's Shirts under-perform this week?"
3. "Where is shrinkage concentrated?"
4. "Did overnight operations execute correctly?"
5. "Compare this Saturday to last Saturday."

For each: Is the narrative compelling for a CXO? Is the INR framing right? Does the inline chart make sense? Does the dashboard react visibly with auto-tab-switches working as intended? Tune system prompt and tool implementations until all five feel demo-grade.
**Acceptance:** A trusted non-team person, asking the five questions cold, gets impressive answers with seamless tab transitions every time.

### D7.10 CXO pitch deck `[1.5h]`
Build a 5-slide deck per design section 8:
1. The problem in numbers (Indian fashion retail, 8-12% lost sales, fit rejection invisible)
2. The prototype (screenshots from all three tabs)
3. The path to Trent stores (production-shape mapping table from design section 1.2)
4. The investment ask (pilot store cost, ROI framing, payback)
5. Next steps

Match the dashboard's dark theme. Keep the deck minimal — the dashboard does the talking.
**Acceptance:** Deck reads cleanly without narration.

### D7.11 Demo run-throughs `[1h]`
Three full demo run-throughs end-to-end. Time each. Identify dead air, fumbles, awkward transitions. Cut if over 7 minutes.

The 7-minute structure (using the tab flow):
- 0:00–0:30: Frame the problem (slide 1)
- 0:30–1:00: Open dashboard on Executive Summary tab; three INR numbers + headline land the impact
- 1:00–2:30: Switch to Live Store tab, start demo mode; planted alerts fire as the day plays; presenter narrates
- 2:30–4:00: Click an alert → ask AI → AI auto-switches to Analytics for size-rejection heatmap → user sees evidence → presenter narrates the seamless flow
- 4:00–5:00: After-hours transition on Live Store; replenishment closes the loop on the morning stockout
- 5:00–6:00: Architecture slide (production-shape mapping)
- 6:00–7:00: Investment ask, close

**Acceptance:** All three run-throughs come in under 7 minutes with no surprises and the auto-switch behavior lands as intended.

### D7.12 Failure mode backups `[30m]`
Record a screen capture of a clean demo run (covering all three tabs and the auto-switch behavior) as video fallback. Take screenshots of the five planted-question answers and each tab's landing view. Save to a USB drive and a cloud folder.
**Acceptance:** Both video and screenshot backups accessible offline.

### D7.13 README & setup guide `[30m]`
Update root `README.md` with one-command setup, run instructions, demo flow walkthrough, architecture summary, and a section addressing likely CXO questions ("How does this work with our existing Databricks?", "What's the data sovereignty story?", "Why three tabs?").
**Acceptance:** A new developer (or skeptical CXO with technical background) can read it and understand the system.

**End of Day 7 checkpoint:** Dashboard polished. Demo rehearsed. Pitch deck ready. Backups exist. You're ready to present.

---

## Critical Path & Cuttable Items

**The critical path** (the longest dependency chain that gates the demo):

```
D1.5 path sampler → D1.8 events.parquet → D2.4 anomaly detection
                 → D4.7 tool handlers → D4.9 agent loop
                 → D6.8 chat stream → D6.9 dashboard binding
                 → D7.5 auto-switch wiring → D7.9 planted-question rehearsal
                 → D7.11 run-throughs
```

This chain totals ~13 hours of sequential work and cannot be compressed without quality loss.

**If you're behind by Day 4 evening, cut these in order:**

1. **Voice input** — drop entirely (it's already a stretch goal)
2. **D7.4 Executive Summary tab** — collapse to two tabs (Live Store + Analytics); the business KPIs move into a top strip on Live Store. This is the single biggest cut available — saves ~1.5h.
3. **D6.6 after-hours treatment** — replace with a simple "After-hours" badge and dim the whole map; skip distinct ops dot styles
4. **D4.4 category × hour heatmap** — drop one chart from the grid; use the freed space for slightly larger versions of the others
5. **D4.1 hourly trend anomaly markers** — keep the chart, drop the red anomaly dots
6. **D6.10 inline chart rendering** — replace AI-generated charts with text-only responses (less impressive but functional)
7. **Two of six planted stories** (drop #4 fixture placement and #5 shrinkage cluster) — keeps four strong stories which is plenty for a 7-minute demo

**Do not cut:**
- Any of the synthetic data work (Day 1) — the foundation
- Anomaly detection (D2.4) — without this the alert feed is empty
- The AI tool-calling loop (D4.9) — without this the AI doesn't work
- The CXO pitch deck (D7.6) — without this the demo is just a demo, not a proposal

## Risk Triggers & Contingencies

| Trigger | Contingency |
|---|---|
| End of Day 1: synthetic data not validated | Stay on Day 1 tasks; everything depends on this. Push Day 2 to Day 2 evening. |
| End of Day 2: KPI endpoints flaky | Cut the heatmap-by-fixture endpoint; use static data for the map heat coloring. |
| End of Day 4: AI doesn't reliably call tools | Switch to single-turn JSON-output prompting instead of tool-calling. Less elegant but ships. |
| End of Day 6: map drops frames | Reduce concurrent dot cap to 30; replace flow animation with periodic pulse-only mode (dots appear briefly at fixtures rather than tracing paths). |
| End of Day 6: bidirectional binding flaky | Hardcode dashboard reactions for the five planted CXO questions instead of generic dispatch. Less impressive in front of a developer audience but invisible to CXOs. |
| Day 7 morning: live demo unstable | Switch demo to recorded video walkthrough (D7.8). Better a smooth video than a broken live demo for a CXO audience. |

## Final Sanity Check Before The Pitch

Run this checklist 30 minutes before pitching:

- [ ] `events.parquet` exists and validate_stories.py passes
- [ ] Backend health endpoint returns 200
- [ ] Frontend loads on Live Store tab as default
- [ ] Tab switches between all three tabs work smoothly
- [ ] Executive Summary tab loads with three INR-formatted KPIs and AI-generated headline
- [ ] Demo mode toggle starts the event stream
- [ ] After-hours transition occurs at the planned timestamp during demo loop (visible on Live Store tab)
- [ ] Five planted CXO questions each produce streaming answers in <10s
- [ ] Auto-tab-switch fires when AI references entities on a non-active tab
- [ ] Map fixtures pulse on stockout alerts
- [ ] Inline charts render in the chat panel
- [ ] Pitch deck open in another browser tab
- [ ] Backup video queued
- [ ] You've slept and you've eaten
