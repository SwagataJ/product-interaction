const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(path, API_BASE);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v) url.searchParams.set(k, v);
    });
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// Types
export interface SummaryKpis {
  trial_to_buy_pct: number;
  floor_to_pickup_pct: number;
  trial_count: number;
  misplacement_rate_pct: number;
  rejection_count: number;
  pickup_count: number;
}

export interface BusinessKpis {
  lost_sales_inr: number;
  working_capital_inr: number;
  conversion_uplift_inr: number;
  conversion_delta_pct: number;
}

export interface FunnelStage {
  stage: string;
  count: number;
  rate: number;
}

export interface CategoryBar {
  category: string;
  trials: number;
  purchases: number;
  trial_to_buy_pct: number;
}

export interface HourlyPoint {
  day: string;
  hour: number;
  trials: number;
  purchases: number;
  conversion_pct: number;
}

export interface FixtureHeat {
  fixture_id: string;
  pickup_count: number;
  tag_count: number;
  pickups_per_tag: number;
}

export interface SizeRejection {
  size: string;
  rejected: number;
  total_trials: number;
  rejection_pct: number;
}

export interface Alert {
  type: string;
  severity: string;
  title: string;
  narrative: string;
  sku_id?: string;
  category?: string;
  fixture_id?: string;
}

export interface StoreLayout {
  store_id: string;
  name: string;
  trading_hours: { open: string; close: string };
  zones: Array<{
    id: string;
    type: string;
    category?: string;
    x: number;
    y: number;
    w: number;
    h: number;
    placement?: string;
    label: string;
  }>;
}

export interface BrandPerf {
  brand: string;
  category: string;
  pickups: number;
  trials: number;
  purchases: number;
  trial_to_buy_pct: number;
  revenue_inr: number;
}

export interface PriceTier {
  price_tier: string;
  tier_order: number;
  pickups: number;
  trials: number;
  purchases: number;
  trial_to_buy_pct: number;
  pickup_rate_pct: number;
}

export interface FitAnalysis {
  fit: string;
  total_trials: number;
  rejected: number;
  purchased: number;
  rejection_pct: number;
  conversion_pct: number;
}

export interface SubcategoryPerf {
  sub_category: string;
  category: string;
  pickups: number;
  trials: number;
  purchases: number;
  trial_to_buy_pct: number;
  revenue_inr: number;
}

export interface ColorPerf {
  color: string;
  pickups: number;
  trials: number;
  purchases: number;
  rejections: number;
  trial_to_buy_pct: number;
  rejection_pct: number;
}

export interface LostSales {
  total_estimated_lost_sales_inr: number;
  by_category: Array<{
    category: string;
    unsold_units: number;
    total_retail_value_inr: number;
    estimated_lost_sales_inr: number;
  }>;
  methodology: string;
}

// API functions
export const getKpiSummary = (params?: Record<string, string>) =>
  fetchApi<SummaryKpis>("/api/kpis/summary", params);

export const getBusinessKpis = (params?: Record<string, string>) =>
  fetchApi<BusinessKpis>("/api/kpis/business", params);

export const getFunnel = (params?: Record<string, string>) =>
  fetchApi<FunnelStage[]>("/api/kpis/funnel", params);

export const getCategories = (params?: Record<string, string>) =>
  fetchApi<CategoryBar[]>("/api/kpis/categories", params);

export const getHourlyTrend = (params?: Record<string, string>) =>
  fetchApi<HourlyPoint[]>("/api/kpis/hourly", params);

export const getFixtureHeatmap = () =>
  fetchApi<FixtureHeat[]>("/api/kpis/heatmap/fixtures");

export const getSizeRejectionHeatmap = (params?: Record<string, string>) =>
  fetchApi<SizeRejection[]>("/api/kpis/heatmap/sizes", params);

export const getCategoryHourHeatmap = (params?: Record<string, string>) =>
  fetchApi<Array<{ category: string; hour: number; conversion_pct: number }>>(
    "/api/kpis/heatmap/category-hour", params
  );

export const getAnomalies = () =>
  fetchApi<Alert[]>("/api/kpis/anomalies");

export const getBrandPerformance = (params?: Record<string, string>) =>
  fetchApi<BrandPerf[]>("/api/kpis/brands", params);

export const getPriceTierConversion = (params?: Record<string, string>) =>
  fetchApi<PriceTier[]>("/api/kpis/price-tiers", params);

export const getFitAnalysis = (params?: Record<string, string>) =>
  fetchApi<FitAnalysis[]>("/api/kpis/fit-analysis", params);

export const getSubcategoryPerformance = (params?: Record<string, string>) =>
  fetchApi<SubcategoryPerf[]>("/api/kpis/subcategories", params);

export const getColorPerformance = (params?: Record<string, string>) =>
  fetchApi<ColorPerf[]>("/api/kpis/colors", params);

export const getLostSales = () =>
  fetchApi<LostSales>("/api/kpis/lost-sales");

export const getStoreLayout = () =>
  fetchApi<StoreLayout>("/api/store/layout");
