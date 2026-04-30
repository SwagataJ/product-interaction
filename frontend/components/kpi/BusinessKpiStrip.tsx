"use client";

import { useEffect, useState } from "react";
import KpiCard from "./KpiCard";
import { getBusinessKpis, type BusinessKpis } from "@/lib/api";

export default function BusinessKpiStrip() {
  const [data, setData] = useState<BusinessKpis | null>(null);

  useEffect(() => {
    getBusinessKpis().then(setData).catch(console.error);
  }, []);

  if (!data) {
    return (
      <div className="grid grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="glass-card p-6 h-32 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-3 gap-4">
      <KpiCard label="Estimated Lost Sales" value={data.lost_sales_inr} format="inr" large />
      <KpiCard label="Working Capital Tied Up" value={data.working_capital_inr} format="inr" large />
      <KpiCard
        label="Conversion Uplift Opportunity"
        value={data.conversion_uplift_inr}
        format="inr"
        delta={data.conversion_delta_pct}
        large
      />
    </div>
  );
}
