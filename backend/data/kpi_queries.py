"""
KPI query functions — operational and business (CXO-grade).
Each function queries DuckDB and returns structured results.
All support optional filters: category, sku, time range.
"""

from datetime import datetime, date
from typing import Optional
from . import duckdb_client as db


def _where_clause(
    category: Optional[str] = None,
    sku: Optional[str] = None,
    from_dt: Optional[str] = None,
    to_dt: Optional[str] = None,
    table_alias: str = "e",
    catalog_alias: str = "c",
) -> str:
    """Build a WHERE clause from optional filters."""
    conditions = []
    if category:
        conditions.append(f"{catalog_alias}.category = '{category}'")
    if sku:
        conditions.append(f"{table_alias}.sku_id = '{sku}'")
    if from_dt:
        conditions.append(f"{table_alias}.timestamp >= '{from_dt}'")
    if to_dt:
        conditions.append(f"{table_alias}.timestamp <= '{to_dt}'")
    if conditions:
        return "AND " + " AND ".join(conditions)
    return ""


# ─── Operational KPIs ────────────────────────────────────────────────────────

def get_summary_kpis(
    category: Optional[str] = None,
    from_dt: Optional[str] = None,
    to_dt: Optional[str] = None,
) -> dict:
    """Six headline operational KPIs."""
    wc = _where_clause(category=category, from_dt=from_dt, to_dt=to_dt)

    result = db.query(f"""
        WITH filtered AS (
            SELECT e.*, c.category
            FROM events e
            JOIN catalog c ON e.sku_id = c.sku_id
            WHERE 1=1 {wc}
        ),
        funnel AS (
            SELECT
                COUNT(*) FILTER (WHERE event_type = 'PICKED_UP') AS pickups,
                COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL') AS trials,
                COUNT(*) FILTER (WHERE event_type IN ('EXITED_TRIAL_PURCHASED', 'SOLD_AT_TILL')) AS purchases,
                COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_REJECTED') AS rejections,
                COUNT(*) FILTER (WHERE event_type = 'MISPLACED') AS misplacements,
                COUNT(DISTINCT CASE WHEN event_type = 'MOVED_TO_FLOOR' THEN sku_id END) AS floor_skus
            FROM filtered
        )
        SELECT
            ROUND(100.0 * purchases / NULLIF(trials + purchases, 0), 1) AS trial_to_buy_pct,
            ROUND(100.0 * pickups / NULLIF(floor_skus * 14, 0), 1) AS floor_to_pickup_pct,
            trials AS trial_count,
            ROUND(100.0 * misplacements / NULLIF(pickups, 0), 1) AS misplacement_rate_pct,
            rejections AS rejection_count,
            pickups AS pickup_count
        FROM funnel
    """)
    return result[0] if result else {}


def get_funnel(
    category: Optional[str] = None,
    sku: Optional[str] = None,
    from_dt: Optional[str] = None,
    to_dt: Optional[str] = None,
) -> list[dict]:
    """Conversion funnel: Floor → Pickup → Trial → Purchase."""
    wc = _where_clause(category=category, sku=sku, from_dt=from_dt, to_dt=to_dt)

    result = db.query(f"""
        WITH filtered AS (
            SELECT e.*, c.category
            FROM events e
            JOIN catalog c ON e.sku_id = c.sku_id
            WHERE 1=1 {wc}
        )
        SELECT
            COUNT(DISTINCT tag_id) FILTER (WHERE event_type = 'MOVED_TO_FLOOR') AS on_floor,
            COUNT(DISTINCT tag_id) FILTER (WHERE event_type = 'PICKED_UP') AS pickups,
            COUNT(DISTINCT tag_id) FILTER (WHERE event_type = 'ENTERED_TRIAL') AS trials,
            COUNT(DISTINCT tag_id) FILTER (WHERE event_type = 'SOLD_AT_TILL') AS total_purchases
        FROM filtered
    """)

    if not result:
        return []

    r = result[0]
    return [
        {"stage": "On Floor", "count": r["on_floor"], "rate": 100.0},
        {"stage": "Picked Up", "count": r["pickups"],
         "rate": round(100.0 * r["pickups"] / max(r["on_floor"], 1), 1)},
        {"stage": "Tried", "count": r["trials"],
         "rate": round(100.0 * r["trials"] / max(r["pickups"], 1), 1)},
        {"stage": "Purchased", "count": r["total_purchases"],
         "rate": round(100.0 * r["total_purchases"] / max(r["trials"], 1), 1)},
    ]


def get_category_bars(
    from_dt: Optional[str] = None,
    to_dt: Optional[str] = None,
) -> list[dict]:
    """Per-category trial-to-buy conversion."""
    wc = _where_clause(from_dt=from_dt, to_dt=to_dt)

    return db.query(f"""
        WITH filtered AS (
            SELECT e.*, c.category
            FROM events e
            JOIN catalog c ON e.sku_id = c.sku_id
            WHERE 1=1 {wc}
        )
        SELECT
            category,
            COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL') AS trials,
            COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED') AS purchases,
            ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED')
                / NULLIF(COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL'), 0), 1) AS trial_to_buy_pct
        FROM filtered
        GROUP BY category
        ORDER BY trial_to_buy_pct DESC
    """)


def get_hourly_trend(
    category: Optional[str] = None,
    from_dt: Optional[str] = None,
    to_dt: Optional[str] = None,
) -> list[dict]:
    """Hourly conversion trend."""
    wc = _where_clause(category=category, from_dt=from_dt, to_dt=to_dt)

    return db.query(f"""
        WITH filtered AS (
            SELECT e.*, c.category, EXTRACT(HOUR FROM e.timestamp) AS hr,
                   DATE_TRUNC('day', e.timestamp) AS day
            FROM events e
            JOIN catalog c ON e.sku_id = c.sku_id
            WHERE 1=1 {wc}
              AND EXTRACT(HOUR FROM e.timestamp) BETWEEN 10 AND 21
        )
        SELECT
            day,
            hr AS hour,
            COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL') AS trials,
            COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED') AS purchases,
            ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED')
                / NULLIF(COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL'), 0), 1) AS conversion_pct
        FROM filtered
        GROUP BY day, hr
        ORDER BY day, hr
    """)


def get_fixture_heatmap() -> list[dict]:
    """Per-fixture pickup rates for the store map."""
    return db.query("""
        WITH pickups AS (
            SELECT zone_to AS fixture_id, COUNT(*) AS pickup_count
            FROM events WHERE event_type = 'PICKED_UP'
            GROUP BY 1
        ),
        tags AS (
            SELECT initial_zone, COUNT(*) AS tag_count
            FROM inventory WHERE initial_zone LIKE 'F_%'
            GROUP BY 1
        )
        SELECT
            p.fixture_id,
            p.pickup_count,
            t.tag_count,
            ROUND(1.0 * p.pickup_count / NULLIF(t.tag_count, 0), 2) AS pickups_per_tag
        FROM pickups p
        LEFT JOIN tags t ON p.fixture_id = t.initial_zone
        ORDER BY pickups_per_tag DESC
    """)


def get_size_rejection_heatmap(
    category: Optional[str] = None,
    sku: Optional[str] = None,
) -> list[dict]:
    """Rejection rate by size for the heatmap."""
    wc = _where_clause(category=category, sku=sku)

    return db.query(f"""
        WITH trials AS (
            SELECT e.sku_id, i.size, e.event_type, c.category
            FROM events e
            JOIN inventory i ON e.tag_id = i.tag_id
            JOIN catalog c ON e.sku_id = c.sku_id
            WHERE e.event_type IN ('EXITED_TRIAL_REJECTED', 'EXITED_TRIAL_PURCHASED')
            {wc}
        )
        SELECT
            size,
            COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_REJECTED') AS rejected,
            COUNT(*) AS total_trials,
            ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_REJECTED')
                / NULLIF(COUNT(*), 0), 1) AS rejection_pct
        FROM trials
        GROUP BY size
        ORDER BY rejection_pct DESC
    """)


def get_category_hour_heatmap(
    from_dt: Optional[str] = None,
    to_dt: Optional[str] = None,
) -> list[dict]:
    """Category x hour-of-day conversion heatmap."""
    wc = _where_clause(from_dt=from_dt, to_dt=to_dt)

    return db.query(f"""
        WITH filtered AS (
            SELECT e.*, c.category, EXTRACT(HOUR FROM e.timestamp) AS hr
            FROM events e
            JOIN catalog c ON e.sku_id = c.sku_id
            WHERE 1=1 {wc}
              AND EXTRACT(HOUR FROM e.timestamp) BETWEEN 10 AND 21
        )
        SELECT
            category,
            hr AS hour,
            COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL') AS trials,
            COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED') AS purchases,
            ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED')
                / NULLIF(COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL'), 0), 1) AS conversion_pct
        FROM filtered
        GROUP BY category, hr
        ORDER BY category, hr
    """)


def get_sku_journey(sku_id: str) -> list[dict]:
    """Per-tag journey timeline for a SKU."""
    return db.query(f"""
        SELECT
            e.tag_id,
            e.event_type,
            e.zone_from,
            e.zone_to,
            e.timestamp,
            i.size
        FROM events e
        JOIN inventory i ON e.tag_id = i.tag_id
        WHERE e.sku_id = '{sku_id}'
        ORDER BY e.timestamp
        LIMIT 500
    """)


def get_replenishment_sla() -> list[dict]:
    """Overnight replenishment SLA adherence."""
    return db.query("""
        WITH replenish AS (
            SELECT
                DATE_TRUNC('day', timestamp) AS night_date,
                COUNT(*) AS replenish_count
            FROM events
            WHERE event_type = 'OPS_REPLENISHED'
            GROUP BY 1
        )
        SELECT
            night_date,
            replenish_count,
            CASE
                WHEN replenish_count < (SELECT AVG(replenish_count) * 0.5 FROM replenish)
                THEN 'BREACH'
                ELSE 'OK'
            END AS sla_status
        FROM replenish
        ORDER BY night_date
    """)


# ─── Anomaly Detection ───────────────────────────────────────────────────────

def get_anomalies() -> list[dict]:
    """Ranked alert list with severity and narrative text."""
    alerts = []

    # 1. Stockout-while-stocked: aggregate by category+size to avoid duplicates
    stockout = db.query("""
        WITH backroom_agg AS (
            SELECT
                c.category, i.size, c.brand,
                COUNT(*) AS backroom_count,
                ROUND(AVG(c.price_inr), 0) AS avg_price_inr
            FROM inventory i
            JOIN catalog c ON i.sku_id = c.sku_id AND i.size = c.size
            WHERE i.initial_zone = 'BACKROOM'
              AND i.tag_id NOT IN (
                  SELECT DISTINCT tag_id FROM events WHERE event_type = 'SOLD_AT_TILL'
              )
            GROUP BY 1, 2, 3
            HAVING COUNT(*) > 15
        )
        SELECT *, ROUND(backroom_count * avg_price_inr, 0) AS stuck_value_inr
        FROM backroom_agg
        ORDER BY stuck_value_inr DESC
        LIMIT 3
    """)
    for s in stockout:
        alerts.append({
            "type": "stockout_while_stocked",
            "severity": "critical",
            "title": f"Stockout: {s['brand']} {s['category']} size {s['size']}",
            "narrative": f"{s['backroom_count']} units sitting in backroom unsold. "
                         f"₹{s['stuck_value_inr']:,.0f} of inventory not reaching the floor when customers want it.",
            "category": s["category"],
        })

    # 2. High rejection SKUs (fit issues)
    rejections = db.query("""
        WITH trials AS (
            SELECT
                e.sku_id, i.size, c.category, c.brand,
                COUNT(*) FILTER (WHERE e.event_type = 'EXITED_TRIAL_REJECTED') AS rejected,
                COUNT(*) AS total_trials
            FROM events e
            JOIN inventory i ON e.tag_id = i.tag_id
            JOIN catalog c ON e.sku_id = c.sku_id
            WHERE e.event_type IN ('EXITED_TRIAL_REJECTED', 'EXITED_TRIAL_PURCHASED')
            GROUP BY 1, 2, 3, 4
            HAVING COUNT(*) >= 10
        )
        SELECT *, ROUND(100.0 * rejected / total_trials, 1) AS rejection_pct
        FROM trials
        WHERE rejected * 1.0 / total_trials > 0.6
        ORDER BY rejection_pct DESC
        LIMIT 5
    """)
    for r in rejections:
        alerts.append({
            "type": "high_rejection",
            "severity": "high",
            "title": f"Fit issue: {r['brand']} {r['sku_id']} size {r['size']}",
            "narrative": f"{r['rejection_pct']}% trial rejection rate ({r['rejected']}/{r['total_trials']} trials). "
                         f"Likely fit issue — escalate to buying team.",
            "sku_id": r["sku_id"],
            "category": r["category"],
        })

    # 3. Fixture placement performance gap
    fixture_gap = db.query("""
        WITH pickups AS (
            SELECT zone_to AS fixture_id, COUNT(*) AS pickup_count
            FROM events WHERE event_type = 'PICKED_UP'
            GROUP BY 1
        ),
        tags AS (
            SELECT initial_zone, COUNT(*) AS tag_count
            FROM inventory WHERE initial_zone LIKE 'F_%'
            GROUP BY 1
        )
        SELECT
            p.fixture_id, p.pickup_count, t.tag_count,
            ROUND(1.0 * p.pickup_count / NULLIF(t.tag_count, 0), 2) AS pickups_per_tag
        FROM pickups p
        JOIN tags t ON p.fixture_id = t.initial_zone
        ORDER BY pickups_per_tag DESC
    """)
    if len(fixture_gap) >= 2:
        top = fixture_gap[0]
        bottom = fixture_gap[-1]
        ratio = round(top["pickups_per_tag"] / max(bottom["pickups_per_tag"], 0.01), 1)
        if ratio >= 1.5:
            alerts.append({
                "type": "fixture_placement_gap",
                "severity": "medium",
                "title": f"VM opportunity: {top['fixture_id']} outperforms {bottom['fixture_id']} by {ratio}x",
                "narrative": f"Front fixture {top['fixture_id']} has {top['pickups_per_tag']} pickups/tag vs "
                             f"{bottom['fixture_id']} at {bottom['pickups_per_tag']}. Same products, {ratio}x engagement gap. "
                             f"Visual merchandising ROI is significant.",
                "fixture_id": top["fixture_id"],
            })

    # 4. Shrinkage cluster
    shrinkage = db.query("""
        SELECT
            c.category,
            COUNT(*) AS shrinkage_events,
            COUNT(DISTINCT e.sku_id) AS affected_skus
        FROM events e
        JOIN catalog c ON e.sku_id = c.sku_id
        WHERE e.event_type = 'EXITED_WITHOUT_SALE'
        GROUP BY 1
        ORDER BY shrinkage_events DESC
    """)
    for s in shrinkage:
        avg_shrinkage = sum(x["shrinkage_events"] for x in shrinkage) / len(shrinkage)
        if s["shrinkage_events"] > avg_shrinkage * 2:
            alerts.append({
                "type": "shrinkage_cluster",
                "severity": "high",
                "title": f"Shrinkage alert: {s['category']}",
                "narrative": f"{s['shrinkage_events']} exit-without-sale events across {s['affected_skus']} SKUs. "
                             f"Concentrated near exit — loss prevention should investigate.",
                "category": s["category"],
            })

    # 5. Replenishment SLA breaches
    replenish = db.query("""
        WITH nightly AS (
            SELECT
                DATE_TRUNC('day', timestamp) AS night,
                COUNT(*) AS replenish_count
            FROM events
            WHERE event_type = 'OPS_REPLENISHED'
            GROUP BY 1
        )
        SELECT night, replenish_count
        FROM nightly
        WHERE replenish_count < (SELECT AVG(replenish_count) * 0.6 FROM nightly)
        ORDER BY night
    """)
    for r in replenish:
        alerts.append({
            "type": "replenishment_sla_breach",
            "severity": "medium",
            "title": f"Replenishment SLA breach: {r['night']}",
            "narrative": f"Only {r['replenish_count']} items replenished overnight — "
                         f"below SLA threshold. Check if size-28 Women's Western was missed.",
            "night": str(r["night"]),
        })

    # 6. Saturday-vs-Saturday drop
    sat_data = db.query("""
        SELECT
            DATE_TRUNC('day', timestamp) AS day,
            COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL') AS trial_entries
        FROM events
        WHERE DAYNAME(timestamp) = 'Saturday'
        GROUP BY 1
        ORDER BY 1
    """)
    if len(sat_data) >= 2:
        vals = [(s["day"], s["trial_entries"]) for s in sat_data]
        max_val = max(v[1] for v in vals)
        min_entry = min(vals, key=lambda v: v[1])
        delta = round(100 * (max_val - min_entry[1]) / max_val, 1)
        if delta > 20:
            alerts.append({
                "type": "saturday_drop",
                "severity": "high",
                "title": f"Saturday conversion drop: {delta}% fewer trials on {min_entry[0]}",
                "narrative": f"Trial room entries dropped {delta}% compared to the previous Saturday. "
                             f"Root cause appears operational, not commercial — check trial room availability.",
            })

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 99))

    return alerts


# ─── Business KPIs (CXO-grade) ───────────────────────────────────────────────

def get_business_kpis(
    from_dt: Optional[str] = None,
    to_dt: Optional[str] = None,
) -> dict:
    """Three CXO-grade business KPIs in INR."""

    # 1. Estimated lost sales from floor stockouts
    # Logic: units in backroom with no MOVED_TO_FLOOR event × price × demand factor
    lost_sales = db.query(f"""
        WITH backroom_only AS (
            SELECT i.tag_id, i.sku_id, c.price_inr
            FROM inventory i
            JOIN catalog c ON i.sku_id = c.sku_id AND i.size = c.size
            WHERE i.initial_zone = 'BACKROOM'
              AND i.tag_id NOT IN (
                  SELECT DISTINCT tag_id FROM events
                  WHERE event_type = 'SOLD_AT_TILL'
              )
        )
        SELECT
            COUNT(*) AS unsold_backroom_units,
            ROUND(SUM(price_inr) * 0.15, 0) AS estimated_lost_sales_inr
        FROM backroom_only
    """)
    lost_sales_inr = lost_sales[0]["estimated_lost_sales_inr"] if lost_sales else 0

    # 2. Working capital tied up in slow-moving SKUs
    # Logic: backroom dwell time × unit cost, aggregated
    working_capital = db.query("""
        WITH backroom_dwell AS (
            SELECT
                i.tag_id, i.sku_id, c.unit_cost_inr,
                MIN(e.timestamp) FILTER (WHERE e.event_type = 'RECEIVED_BACKROOM') AS received_at,
                MIN(e.timestamp) FILTER (WHERE e.event_type = 'MOVED_TO_FLOOR') AS moved_at
            FROM inventory i
            JOIN catalog c ON i.sku_id = c.sku_id AND i.size = c.size
            LEFT JOIN events e ON i.tag_id = e.tag_id
            WHERE i.initial_zone = 'BACKROOM'
            GROUP BY 1, 2, 3
        )
        SELECT
            ROUND(SUM(unit_cost_inr), 0) AS total_working_capital_inr,
            ROUND(AVG(EXTRACT(EPOCH FROM (COALESCE(moved_at, CURRENT_TIMESTAMP) - received_at)) / 3600), 1) AS avg_backroom_hours
        FROM backroom_dwell
        WHERE received_at IS NOT NULL
    """)
    working_capital_inr = working_capital[0]["total_working_capital_inr"] if working_capital else 0

    # 3. Conversion uplift opportunity
    # Compare category-level pickup-to-purchase rates
    uplift = db.query("""
        WITH cat_perf AS (
            SELECT
                c.category,
                COUNT(DISTINCT e.tag_id) FILTER (WHERE e.event_type = 'PICKED_UP') AS pickups,
                COUNT(DISTINCT e.tag_id) FILTER (WHERE e.event_type = 'SOLD_AT_TILL') AS purchases
            FROM events e
            JOIN catalog c ON e.sku_id = c.sku_id
            GROUP BY 1
        ),
        ranked AS (
            SELECT *,
                ROUND(100.0 * purchases / NULLIF(pickups, 0), 1) AS conv_rate,
                NTILE(4) OVER (ORDER BY 100.0 * purchases / NULLIF(pickups, 0)) AS quartile
            FROM cat_perf
            WHERE pickups > 20
        )
        SELECT
            ROUND(AVG(conv_rate) FILTER (WHERE quartile >= 3), 1) AS top_half_pct,
            ROUND(AVG(conv_rate) FILTER (WHERE quartile <= 2), 1) AS bottom_half_pct,
            ROUND(AVG(conv_rate) FILTER (WHERE quartile >= 3) - AVG(conv_rate) FILTER (WHERE quartile <= 2), 1) AS delta_pct
        FROM ranked
    """)
    delta_pct = uplift[0]["delta_pct"] if uplift and uplift[0]["delta_pct"] else 0

    avg_price = db.query("SELECT ROUND(AVG(price_inr), 0) AS avg FROM catalog")[0]["avg"]
    # Estimate: if bottom-half categories converted like top-half, additional revenue
    bottom_data = db.query("""
        WITH cat_perf AS (
            SELECT c.category,
                COUNT(DISTINCT e.tag_id) FILTER (WHERE e.event_type = 'PICKED_UP') AS pickups
            FROM events e JOIN catalog c ON e.sku_id = c.sku_id
            GROUP BY 1
        ),
        ranked AS (
            SELECT *, NTILE(4) OVER (ORDER BY pickups DESC) AS q FROM cat_perf
        )
        SELECT SUM(pickups) AS total_pickups FROM ranked WHERE q >= 3
    """)
    bottom_pickups = bottom_data[0]["total_pickups"] if bottom_data and bottom_data[0]["total_pickups"] else 0
    uplift_inr = round(bottom_pickups * (abs(delta_pct) / 100) * avg_price, 0) if delta_pct else 0

    return {
        "lost_sales_inr": lost_sales_inr or 0,
        "working_capital_inr": working_capital_inr or 0,
        "conversion_uplift_inr": uplift_inr,
        "conversion_delta_pct": delta_pct,
    }


def get_brand_performance(
    category: Optional[str] = None,
    from_dt: Optional[str] = None,
    to_dt: Optional[str] = None,
) -> list[dict]:
    """Per-brand trial-to-buy conversion with revenue."""
    wc = _where_clause(category=category, from_dt=from_dt, to_dt=to_dt)

    return db.query(f"""
        WITH filtered AS (
            SELECT e.*, c.category, c.brand, c.price_inr
            FROM events e
            JOIN catalog c ON e.sku_id = c.sku_id
            WHERE 1=1 {wc}
        )
        SELECT
            brand,
            MODE(category) AS category,
            COUNT(*) FILTER (WHERE event_type = 'PICKED_UP') AS pickups,
            COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL') AS trials,
            COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED') AS purchases,
            ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED')
                / NULLIF(COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL'), 0), 1) AS trial_to_buy_pct,
            ROUND(SUM(price_inr) FILTER (WHERE event_type = 'SOLD_AT_TILL'), 0) AS revenue_inr
        FROM filtered
        GROUP BY brand
        HAVING COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL') >= 5
        ORDER BY trial_to_buy_pct DESC
    """)


def get_price_tier_conversion(
    from_dt: Optional[str] = None,
    to_dt: Optional[str] = None,
) -> list[dict]:
    """Conversion rates by price tier."""
    wc = _where_clause(from_dt=from_dt, to_dt=to_dt)

    return db.query(f"""
        WITH filtered AS (
            SELECT e.*, c.price_inr
            FROM events e
            JOIN catalog c ON e.sku_id = c.sku_id
            WHERE 1=1 {wc}
        ),
        tiered AS (
            SELECT *,
                CASE
                    WHEN price_inr < 500 THEN 'Under ₹500'
                    WHEN price_inr < 1000 THEN '₹500-999'
                    WHEN price_inr < 2000 THEN '₹1000-1999'
                    WHEN price_inr < 3500 THEN '₹2000-3499'
                    ELSE '₹3500+'
                END AS price_tier,
                CASE
                    WHEN price_inr < 500 THEN 1
                    WHEN price_inr < 1000 THEN 2
                    WHEN price_inr < 2000 THEN 3
                    WHEN price_inr < 3500 THEN 4
                    ELSE 5
                END AS tier_order
            FROM filtered
        )
        SELECT
            price_tier,
            tier_order,
            COUNT(*) FILTER (WHERE event_type = 'PICKED_UP') AS pickups,
            COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL') AS trials,
            COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED') AS purchases,
            ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED')
                / NULLIF(COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL'), 0), 1) AS trial_to_buy_pct,
            ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'PICKED_UP')
                / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'MOVED_TO_FLOOR' THEN sku_id END) * 14, 0), 1) AS pickup_rate_pct
        FROM tiered
        GROUP BY price_tier, tier_order
        ORDER BY tier_order
    """)


def get_fit_analysis(
    category: Optional[str] = None,
) -> list[dict]:
    """Rejection rates by fit type."""
    wc = _where_clause(category=category)

    return db.query(f"""
        WITH trials AS (
            SELECT e.sku_id, c.fit, c.category, e.event_type
            FROM events e
            JOIN catalog c ON e.sku_id = c.sku_id
            WHERE e.event_type IN ('EXITED_TRIAL_REJECTED', 'EXITED_TRIAL_PURCHASED')
            {wc}
            AND c.fit IS NOT NULL AND c.fit != ''
        )
        SELECT
            fit,
            COUNT(*) AS total_trials,
            COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_REJECTED') AS rejected,
            COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED') AS purchased,
            ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_REJECTED')
                / NULLIF(COUNT(*), 0), 1) AS rejection_pct,
            ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED')
                / NULLIF(COUNT(*), 0), 1) AS conversion_pct
        FROM trials
        GROUP BY fit
        HAVING COUNT(*) >= 10
        ORDER BY rejection_pct DESC
    """)


def get_subcategory_performance(
    category: Optional[str] = None,
    from_dt: Optional[str] = None,
    to_dt: Optional[str] = None,
) -> list[dict]:
    """Per-sub-category conversion and revenue."""
    wc = _where_clause(category=category, from_dt=from_dt, to_dt=to_dt)

    return db.query(f"""
        WITH filtered AS (
            SELECT e.*, c.category, c.sub_category, c.price_inr
            FROM events e
            JOIN catalog c ON e.sku_id = c.sku_id
            WHERE 1=1 {wc}
        )
        SELECT
            sub_category,
            MODE(category) AS category,
            COUNT(*) FILTER (WHERE event_type = 'PICKED_UP') AS pickups,
            COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL') AS trials,
            COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED') AS purchases,
            ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED')
                / NULLIF(COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL'), 0), 1) AS trial_to_buy_pct,
            ROUND(SUM(price_inr) FILTER (WHERE event_type = 'SOLD_AT_TILL'), 0) AS revenue_inr
        FROM filtered
        GROUP BY sub_category
        HAVING COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL') >= 5
        ORDER BY trial_to_buy_pct DESC
    """)


def get_color_performance(
    category: Optional[str] = None,
    from_dt: Optional[str] = None,
    to_dt: Optional[str] = None,
) -> list[dict]:
    """Per-color conversion rates and rejection analysis."""
    wc = _where_clause(category=category, from_dt=from_dt, to_dt=to_dt)

    return db.query(f"""
        WITH filtered AS (
            SELECT e.*, c.category, c.color
            FROM events e
            JOIN catalog c ON e.sku_id = c.sku_id
            WHERE 1=1 {wc}
        )
        SELECT
            color,
            COUNT(*) FILTER (WHERE event_type = 'PICKED_UP') AS pickups,
            COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL') AS trials,
            COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED') AS purchases,
            COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_REJECTED') AS rejections,
            ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_PURCHASED')
                / NULLIF(COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL'), 0), 1) AS trial_to_buy_pct,
            ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'EXITED_TRIAL_REJECTED')
                / NULLIF(COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL'), 0), 1) AS rejection_pct
        FROM filtered
        GROUP BY color
        HAVING COUNT(*) FILTER (WHERE event_type = 'ENTERED_TRIAL') >= 10
        ORDER BY trial_to_buy_pct DESC
    """)


def compare_periods(
    metric: str,
    period_a_from: str,
    period_a_to: str,
    period_b_from: str,
    period_b_to: str,
) -> dict:
    """Compare a metric between two time periods."""
    a = get_summary_kpis(from_dt=period_a_from, to_dt=period_a_to)
    b = get_summary_kpis(from_dt=period_b_from, to_dt=period_b_to)

    if not a or not b:
        return {"error": "No data for one or both periods"}

    result = {}
    for key in a:
        val_a = a.get(key, 0) or 0
        val_b = b.get(key, 0) or 0
        delta = val_b - val_a
        result[key] = {
            "period_a": val_a,
            "period_b": val_b,
            "delta": delta,
            "delta_pct": round(100 * delta / max(abs(val_a), 1), 1),
        }

    return result


def estimate_lost_sales(
    sku: Optional[str] = None,
    category: Optional[str] = None,
    from_dt: Optional[str] = None,
    to_dt: Optional[str] = None,
) -> dict:
    """Estimate revenue lost to floor stockouts in INR."""
    wc_parts = []
    if category:
        wc_parts.append(f"c.category = '{category}'")
    if sku:
        wc_parts.append(f"i.sku_id = '{sku}'")
    wc = ("AND " + " AND ".join(wc_parts)) if wc_parts else ""

    result = db.query(f"""
        WITH backroom_unsold AS (
            SELECT
                i.tag_id, i.sku_id, c.price_inr, c.category, c.brand, i.size
            FROM inventory i
            JOIN catalog c ON i.sku_id = c.sku_id AND i.size = c.size
            WHERE i.initial_zone = 'BACKROOM'
              AND i.tag_id NOT IN (
                  SELECT DISTINCT tag_id FROM events WHERE event_type = 'SOLD_AT_TILL'
              )
              {wc}
        )
        SELECT
            category,
            COUNT(*) AS unsold_units,
            ROUND(SUM(price_inr), 0) AS total_retail_value_inr,
            ROUND(SUM(price_inr) * 0.15, 0) AS estimated_lost_sales_inr
        FROM backroom_unsold
        GROUP BY category
        ORDER BY estimated_lost_sales_inr DESC
    """)

    total_lost = sum(r["estimated_lost_sales_inr"] for r in result) if result else 0

    return {
        "total_estimated_lost_sales_inr": total_lost,
        "by_category": result,
        "methodology": "Unsold backroom units × retail price × 15% estimated demand conversion"
    }
