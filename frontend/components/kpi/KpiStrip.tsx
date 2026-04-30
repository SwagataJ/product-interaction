"use client";

import { useEffect, useState } from "react";
import KpiCard from "./KpiCard";
import { getKpiSummary, type SummaryKpis } from "@/lib/api";

export default function KpiStrip() {
  const [data, setData] = useState<SummaryKpis | null>(null);

  useEffect(() => {
    getKpiSummary().then(setData).catch(console.error);
  }, []);

  if (!data) {
    return (
      <div className="grid grid-cols-6 gap-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="glass-card p-3 h-20 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-6 gap-2">
      <KpiCard label="Trial-to-Buy" value={data.trial_to_buy_pct} format="pct" />
      <KpiCard label="Pickup Rate" value={data.floor_to_pickup_pct} format="pct" />
      <KpiCard label="Trial Count" value={data.trial_count} />
      <KpiCard label="Misplacement" value={data.misplacement_rate_pct} format="pct" />
      <KpiCard label="Rejections" value={data.rejection_count} />
      <KpiCard label="Pickups" value={data.pickup_count} />
    </div>
  );
}
