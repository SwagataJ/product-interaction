"""KPI REST endpoints."""

from fastapi import APIRouter, Query
from typing import Optional
from ..data import kpi_queries as kpi

router = APIRouter(prefix="/api/kpis", tags=["KPIs"])


@router.get("/summary")
async def summary(
    category: Optional[str] = Query(None),
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
):
    return kpi.get_summary_kpis(category=category, from_dt=from_dt, to_dt=to_dt)


@router.get("/business")
async def business(
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
):
    return kpi.get_business_kpis(from_dt=from_dt, to_dt=to_dt)


@router.get("/funnel")
async def funnel(
    category: Optional[str] = Query(None),
    sku: Optional[str] = Query(None),
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
):
    return kpi.get_funnel(category=category, sku=sku, from_dt=from_dt, to_dt=to_dt)


@router.get("/categories")
async def categories(
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
):
    return kpi.get_category_bars(from_dt=from_dt, to_dt=to_dt)


@router.get("/hourly")
async def hourly(
    category: Optional[str] = Query(None),
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
):
    return kpi.get_hourly_trend(category=category, from_dt=from_dt, to_dt=to_dt)


@router.get("/heatmap/category-hour")
async def category_hour_heatmap(
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
):
    return kpi.get_category_hour_heatmap(from_dt=from_dt, to_dt=to_dt)


@router.get("/heatmap/fixtures")
async def fixture_heatmap():
    return kpi.get_fixture_heatmap()


@router.get("/heatmap/sizes")
async def size_heatmap(
    category: Optional[str] = Query(None),
    sku: Optional[str] = Query(None),
):
    return kpi.get_size_rejection_heatmap(category=category, sku=sku)


@router.get("/anomalies")
async def anomalies():
    return kpi.get_anomalies()


@router.get("/sku/{sku_id}/journey")
async def sku_journey(sku_id: str):
    return kpi.get_sku_journey(sku_id)


@router.get("/replenishment")
async def replenishment():
    return kpi.get_replenishment_sla()


@router.get("/lost-sales")
async def lost_sales(
    sku: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
):
    return kpi.estimate_lost_sales(sku=sku, category=category, from_dt=from_dt, to_dt=to_dt)


@router.get("/brands")
async def brands(
    category: Optional[str] = Query(None),
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
):
    return kpi.get_brand_performance(category=category, from_dt=from_dt, to_dt=to_dt)


@router.get("/price-tiers")
async def price_tiers(
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
):
    return kpi.get_price_tier_conversion(from_dt=from_dt, to_dt=to_dt)


@router.get("/fit-analysis")
async def fit_analysis(
    category: Optional[str] = Query(None),
):
    return kpi.get_fit_analysis(category=category)


@router.get("/subcategories")
async def subcategories(
    category: Optional[str] = Query(None),
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
):
    return kpi.get_subcategory_performance(category=category, from_dt=from_dt, to_dt=to_dt)


@router.get("/colors")
async def colors(
    category: Optional[str] = Query(None),
    from_dt: Optional[str] = Query(None, alias="from"),
    to_dt: Optional[str] = Query(None, alias="to"),
):
    return kpi.get_color_performance(category=category, from_dt=from_dt, to_dt=to_dt)


@router.get("/compare")
async def compare(
    metric: str = Query(...),
    a_from: str = Query(...),
    a_to: str = Query(...),
    b_from: str = Query(...),
    b_to: str = Query(...),
):
    return kpi.compare_periods(metric, a_from, a_to, b_from, b_to)
