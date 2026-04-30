# Requirements — In-Store Product Journey Tracker

## 1. Project Overview

### 1.1 Purpose
Build a production-shape prototype that tracks the journey of every product unit through a fashion retail store — from backroom receipt to final outcome (sale, rejection, return, or shrinkage) — and surfaces this through a polished dashboard combining a live Living Store Map and a coordinated analytical chart grid, augmented by a conversational AI layer that lets users interrogate the data in natural language.

### 1.2 Context
The production system would run on UHF passive RFID infrastructure with readers at every journey checkpoint. For this build, all RFID events are simulated through a synthetic data generator that bakes in discoverable patterns (stockouts, fit issues, shrinkage clusters, fixture-placement gaps, replenishment failures) which the analytics and AI layers surface as headline insights. The simulation also includes a light-touch model of after-hours operational activity so the dashboard remains alive outside trading hours.

### 1.3 Target Audience
The primary demo audience is internal Trent leadership at CXO level. The dashboard primarily serves Store Managers, with secondary lenses for Category/Buying teams and Operations accessible through the AI conversation layer rather than separate views. The pitch positions this as a working prototype with a credible production path on Trent's existing Azure/Databricks stack.

### 1.4 Success Criteria
- A CXO viewer landing on the Live Store tab understands "this is what's happening in our store right now" within ten seconds
- The Executive Summary tab communicates the day's three biggest business issues without any narration
- The six planted insight stories surface convincingly during a 7-minute demo loop
- The AI responds to any of five planted CXO-relevant questions (lost sales, conversion drivers, fit issues, shrinkage, replenishment lag) with narrative insight plus a contextual visualization, auto-switching tabs when its answer references entities on a non-active tab
- The dashboard reacts to AI responses by highlighting and animating relevant elements
- The architecture slide shows a one-line swap from synthetic events to real RFID events on Trent's existing Databricks/Azure infrastructure
- Investment ask and ROI framing are quantified (lost-sales recovery, conversion uplift, working capital release)

### 1.5 Build Constraints
Solo build across approximately seven calendar days, roughly 50–60 productive hours. Single laptop, no required cloud infrastructure beyond LLM API access. Lightweight stack (Python + DuckDB + FastAPI + Next.js). The build pace is sustainable — burnout is a tracked risk, not a heroic assumption.

## 2. Functional Requirements

### 2.1 Synthetic Data Generation

**FR-1.1** The system shall generate synthetic RFID reader events for a virtual fashion retail store covering at least fourteen days of operating hours plus light-touch after-hours operational activity.

**FR-1.2** The virtual store shall contain at least eleven distinct zones: one backroom, six fixture zones spanning Women's Tops, Women's Bottoms, Men's Shirts, Men's Bottoms, Kids, and Accessories, one trial room cluster, two till zones, and one exit.

**FR-1.3** The product catalog shall contain between three hundred and five hundred SKUs with attributes including category, sub-category, color, size, fit, price tier, and brand. Catalog skews toward mid-price fashion retail typical of Westside/Zudio formats.

**FR-1.4** The tag inventory shall contain between five thousand and ten thousand individual units, each mapped to a SKU and assigned a unique tag identifier.

**FR-1.5** The generator shall produce events covering all defined journey stages: backroom-to-floor, fixture-to-pickup, basket dwell, floor-to-trial-room, trial-to-till, trial-to-fixture rejection, fixture-to-fixture misplacement, basket-to-floor abandonment, floor-to-backroom returns, till-to-exit, return journeys, and shrinkage exits.

**FR-1.6** The generator shall bake in at least six planted insight stories that the dashboard and AI layer can discover and narrate, each chosen for direct CXO relevance:

- A high-rejection SKU concentrated in one size — a fit issue worth a buying-team escalation
- A chronic stockout-on-floor while backroom holds inventory — a working-capital and lost-sales story
- A Saturday-versus-Saturday conversion drop with a traceable root cause — an operational-failure story
- A fixture-placement performance gap — a visual-merchandising ROI story
- A shrinkage cluster on specific SKUs near the exit — a loss-prevention story
- A replenishment SLA failure pattern where overnight replenishment misses cause next-day immediate stockouts — a cross-temporal operational story that closes the loop with after-hours data

**FR-1.7** Event timestamps shall follow realistic distributions: backroom dwell sampled from a gamma distribution roughly twenty-four to seventy-two hours, fixture dwell highly variable, trial dwell three to eight minutes, till-to-exit thirty to one hundred twenty seconds. Pickup and trial events follow realistic intra-day patterns including lunch and evening peaks plus weekend surges.

**FR-1.8** The generator shall reflect realistic journey-path probabilities: most units never get picked up; of those picked, a meaningful fraction enter the trial room; of those tried, a majority are rejected back to a fixture; only a small fraction complete the happy path to purchase.

**FR-1.9 (Light-touch after-hours)** The generator shall produce a small set of operational events outside trading hours including overnight replenishment moves (backroom to fixture), occasional stocktake scans, and sporadic VM resets. Volume shall be deliberately low — the goal is to make the map feel alive at night rather than to model night operations in depth. The replenishment events shall close the loop with the daytime stockout story (planted stories #2 and #6).

### 2.2 Journey Reconstruction & KPI Computation

**FR-2.1** The system shall reconstruct per-tag journeys by ordering events by timestamp, deriving zone-to-zone transitions, and computing dwell times at each stage.

**FR-2.2** The system shall compute and expose movement KPIs: average backroom dwell time, fixture-to-pickup time, basket dwell time, trial room dwell time, full journey time, and replenishment lag.

**FR-2.3** The system shall compute and expose conversion-funnel KPIs: floor-to-pickup rate, pickup-to-trial rate, trial-to-purchase rate, pickup-to-purchase rate, and overall sell-through.

**FR-2.4** The system shall compute and expose operational health KPIs including misplacement rate, shrinkage rate, replenishment SLA adherence, and stockout duration on floor while backroom holds inventory.

**FR-2.5** The system shall compute and expose merchandising KPIs including fixture-level pickup rate (heatmap), category-level engagement, and rejection patterns broken down by size, color, and fit.

**FR-2.6** The system shall detect and surface anomalies as ranked alerts including stockouts with available backroom stock, SKUs with rejection rates above a threshold, fixtures performing significantly above or below expectation, shrinkage flags on individual SKUs, and replenishment SLA breaches.

**FR-2.7** All KPIs shall be queryable by time range, store, category, and SKU.

**FR-2.8 (CXO-grade business KPIs)** The system shall additionally compute and expose three business-impact KPIs framed for leadership audiences:

- Estimated lost sales from floor stockouts (units stocked out × average price × estimated demand during stockout window)
- Working capital tied up in slow-moving SKUs (backroom dwell time × unit cost, aggregated)
- Conversion uplift opportunity (delta between top-quartile and bottom-quartile fixture or SKU performance)

These shall be expressed in INR with appropriate scale (lakhs, crores).

### 2.3 Visual Dashboard

**FR-3.1** The dashboard shall present a dark-themed executive interface organized as three primary tabs accessible via a persistent top-level navigation: Live Store, Analytics, and Executive Summary. The Live Store tab shall be the default landing view.

**FR-3.2** Tab navigation shall persist the AI chat panel, top bar, and demo mode state across switches; only the main content area changes. Tab transitions shall use a brief crossfade (approximately 200ms) for visual continuity.

**FR-3.3 (Auto-switch behavior)** When the AI dispatches a dashboard action targeting an entity that lives on a non-active tab (for example, a `highlight_fixture` action while the user is viewing the Analytics tab), the system shall automatically switch to the relevant tab before applying the action. A brief visual cue shall indicate the auto-switch occurred (such as a subtle tab-indicator pulse) so the user understands why the view changed.

**FR-3.4 (Live Store tab — Living Store Map)** The Live Store tab shall feature the Living Store Map at full content width, rendering the store layout in a top-down 2D view with fixtures, trial rooms, tills, backroom, and exit clearly demarcated. It shall animate product movement as glowing dots flowing along realistic paths between zones, driven by the synthetic event stream played back in accelerated time. Fixtures shall display heat coloring driven by pickup rate (warm tones for high pickup, cool tones for low). Stockout fixtures shall pulse subtly to draw attention. The tab shall also include an operational KPI strip (small, secondary) and a live alert feed (vertical, sidebar-style).

**FR-3.5 (Live Store tab — after-hours behavior)** When the simulated time is outside trading hours, the map shall transition to a dimmed visual treatment indicating an after-hours state. Customer-flow dots shall stop. A small number of operational dots (replenishment moves, stocktake scans) shall continue moving at low frequency, with a visually distinct color and style from customer-flow dots. A subtle overlay badge shall indicate the operational state and current simulated time.

**FR-3.6 (Analytics tab — Coordinated Chart Grid)** The Analytics tab shall feature a coordinated chart grid at full content width, including the following visualizations:

- A conversion funnel showing Floor Visits → Pickups → Trials → Purchases, animated and showing dropoff at each stage
- A category-level bar chart showing trial-to-buy conversion per category
- An hourly conversion trend line over the last 24–48 simulated hours
- A rejection heatmap showing rejection rate by size for the currently focused category or SKU
- A category × hour-of-day performance heatmap
- A secondary alert feed sized for analytical browsing rather than live monitoring

The tab shall also include a compact operational KPI strip at top.

**FR-3.7 (Cross-filtering within Analytics tab)** Charts in the Analytics grid shall cross-filter: clicking a category bar re-scopes the funnel, hourly trend, and rejection heatmap to that category. Cross-tab filtering shall also work — clicking a fixture on the Live Store tab and switching to Analytics shall carry the filter across.

**FR-3.8 (Executive Summary tab)** The Executive Summary tab shall present a single-page CXO view containing: the three CXO-grade business-impact KPIs from FR-2.8 (lost sales, working capital, conversion uplift opportunity) at large scale; the top three priority alerts of the moment with narrative summaries; a one-line "what changed today" headline generated by the AI; and a prominent prompt to "ask the AI" with three suggested CXO-relevant questions. This tab shall be intentionally sparse — the layout shall communicate "executive briefing" rather than "operational console".

**FR-3.9** The dashboard shall include a top bar (persistent across tabs) with store selector, time scrubber, demo-mode speed toggle, current simulated time, live status indicator, and the tab navigation.

**FR-3.10** Every numeric value that updates shall animate (count-up, bar fill, smooth transitions); motion shall be purposeful rather than decorative.

**FR-3.11** The dashboard shall use a deep navy or charcoal background with electric cyan, amber, coral red, and mint green as semantic accent colors, balancing visual impact with the seriousness expected by a CXO audience.

### 2.4 AI Conversational Layer

**FR-4.1** The dashboard shall include a persistent AI assistant accessible via a floating control in the bottom-right corner, expandable into a chat panel approximately four hundred pixels wide and six hundred pixels tall.

**FR-4.2** The AI assistant shall accept text input. Voice input via the Web Speech API is a stretch goal.

**FR-4.3** The AI assistant shall be capable of answering natural-language questions about store performance with a focus on questions a CXO or store manager would actually ask. Reference questions include: how much revenue did we lose to stockouts today, why did Men's Shirts under-perform this week, which SKU has the worst fit signal, where is shrinkage concentrated, did overnight operations execute correctly, compare this Saturday to last Saturday.

**FR-4.4** AI responses shall stream token-by-token to convey active reasoning rather than appearing as a single delayed block.

**FR-4.5** AI responses shall include narrative explanation, an inline visualization rendered within the chat panel, and a list of dashboard actions that the frontend dispatches against the main view.

**FR-4.6** AI tool calls executing during reasoning shall surface as visible badges in the chat (for example "Pulled funnel data" or "Compared to baseline") so the AI's process is transparent to the viewer.

**FR-4.7** The AI shall use tool calling against a defined set of analytical tools rather than hallucinating from prompt context. Required tools include get_kpi, get_sku_journey, get_anomalies, compare_periods, get_funnel, estimate_lost_sales, and suggest_actions.

**FR-4.8** Clicking any KPI card, alert, fixture on the map, category bar, or funnel stage shall open the AI panel with context pre-loaded about that element, prompting the user toward investigation.

**FR-4.9** When the AI references entities (fixtures, SKUs, categories), the main dashboard shall react by highlighting and animating those entities — pulsing fixtures, tracing SKU journeys across the store map, filtering charts to the relevant scope. If the referenced entity lives on a non-active tab, the system shall auto-switch to the relevant tab per FR-3.3 before applying the highlight or filter.

**FR-4.10** The AI shall recommend concrete actions where applicable, framed in business language a CXO understands. For example: "pull size M from the floor for fit audit; this SKU is responsible for an estimated ₹2.3 lakh in lost sales over the last week" rather than just "rejection rate is high".

### 2.5 Demo Mode

**FR-5.1** The dashboard shall include a demo mode that plays back a designated demo day of simulated events at accelerated speed (default 100x real time, configurable from 50x to 500x).

**FR-5.2** Demo mode shall be triggerable from the top bar via a single click and shall loop continuously when reaching end of period, with a brief crossfade transition.

**FR-5.3** Planted insight stories shall surface visibly during demo mode playback so a viewer watching passively sees anomalies emerge in real time.

**FR-5.4** Demo mode shall include the after-hours window so the viewer experiences both the trading day (full map activity) and the night cycle (operational events, replenishment closing the stockout loop). The transition between modes shall be visually obvious.

## 3. Non-Functional Requirements

### 3.1 Performance
**NFR-1.1** The dashboard shall load and render the initial view within three seconds on a modern laptop browser.

**NFR-1.2** AI response time from question submission to first streamed token shall be under three seconds; full response with chart rendering under ten seconds.

**NFR-1.3** The Living Store Map shall maintain at least thirty frames per second during demo mode playback with up to one hundred concurrent animated dots.

**NFR-1.4** KPI queries against the synthetic dataset (covering fourteen days, up to four hundred thousand events) shall return in under five hundred milliseconds.

### 3.2 Reliability
**NFR-2.1** The system shall handle a continuous one-hour demo session without crashes or memory leaks.

**NFR-2.2** AI responses shall gracefully handle questions outside the system's knowledge by acknowledging the limit rather than fabricating data.

**NFR-2.3** A backup of pre-recorded screenshots and a static demo video shall exist as a fallback if the live demo fails during a CXO presentation.

### 3.3 Usability
**NFR-3.1** The dashboard shall be visually parseable within ten seconds by a CXO viewer with no prior briefing.

**NFR-3.2** No critical insight shall require more than two interactions to reach (one click into a card or alert, one AI follow-up).

**NFR-3.3** All animations shall respect the user's prefers-reduced-motion browser setting where feasible.

### 3.4 Maintainability & Extensibility
**NFR-4.1** The synthetic event generator shall be swappable with a real RFID event ingestion endpoint via a single configuration change; downstream pipeline and dashboard shall remain unchanged.

**NFR-4.2** The data schema (events Parquet) shall be compatible with Delta Lake on Databricks without transformation, supporting the production-shape narrative for the CXO audience.

**NFR-4.3** Adding a new KPI shall require changes only to the analytical pipeline and one frontend component, not architectural changes.

### 3.5 Build Constraints
**NFR-5.1** The full build shall be completable by a single developer in approximately 50–60 productive hours spread across seven calendar days.

**NFR-5.2** The system shall run end-to-end on a single laptop with no required cloud infrastructure beyond LLM API access.

**NFR-5.3** All third-party dependencies shall be installable via standard package managers (pip, npm) with no manual configuration steps.

**NFR-5.4** The build pace shall accommodate sustainable working hours; the schedule shall include explicit rest and avoid the death-march pattern.

## 4. Out of Scope (For This Build)

The following are explicitly excluded from this build and reserved for the production roadmap:

- Real RFID hardware integration, middleware tuning, and read-accuracy calibration
- Multi-store rollout, cross-store benchmarking, or chain-wide aggregation
- Production-grade authentication, role-based access control, and persona-specific dashboard views beyond the single executive view augmented by AI
- Computer vision integration for browse-without-pickup signal capture
- Integration with live POS, WMS, ERP, CDP, or other enterprise systems
- 3D isometric store visualization
- Mobile-native applications (the dashboard is responsive web only)
- Deep modeling of after-hours operations (only light-touch ambient activity is in scope)
- Multi-language support
- Customer-level analytics tying journeys to loyalty profiles
- Live deployment to Databricks/Azure (the production-shape narrative is shown via architecture slide and schema compatibility, not a working deployment)

## 5. Assumptions

A modern laptop with at least 16GB RAM is available for the demo. The CXO audience is comfortable with web-based dashboards and has briefly seen Power BI or similar tools. Synthetic data with planted patterns is acceptable provided the architecture story makes the production path credible. Google AI Studio API access with Gemini 2.5 Pro (or higher) is provisioned. The demo will be presented on the developer's laptop or projected via HDMI; there is no requirement to run on Trent infrastructure during the pitch.

## 6. Risks

The largest risk is solo-build burnout across seven days; mitigation is a sustainable schedule with one full rest day and clear daily targets.

The second risk is the Living Store Map consuming more time than budgeted relative to the chart grid; mitigation is building the chart grid first (it carries the dashboard if the map under-delivers) and treating the map's polish as a Day 6 task.

The third risk is the AI failing to handle CXO-framed questions convincingly; mitigation is rehearsing against the actual built system rather than the design document, with explicit prompt-tuning time allocated on Day 6.

The fourth risk is the production-roadmap narrative not landing with the CXO audience; mitigation is preparing a one-page "from prototype to Trent stores" architecture slide that explicitly maps the synthetic generator to real RFID readers and DuckDB to Databricks SQL.
