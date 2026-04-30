"use client";

import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { getHourlyTrend, type HourlyPoint } from "@/lib/api";
import { useStore } from "@/lib/store";

export default function HourlyTrend() {
  const [data, setData] = useState<HourlyPoint[]>([]);
  const { gridFilter } = useStore();

  useEffect(() => {
    const params: Record<string, string> = {};
    if (gridFilter.category) params.category = gridFilter.category;
    getHourlyTrend(params).then(setData).catch(console.error);
  }, [gridFilter]);

  if (!data.length) return <div className="glass-card p-4 h-48 animate-pulse" />;

  // Aggregate by hour across all days
  const hourAgg = new Map<number, { trials: number; purchases: number }>();
  for (const pt of data) {
    const existing = hourAgg.get(pt.hour) || { trials: 0, purchases: 0 };
    existing.trials += pt.trials;
    existing.purchases += pt.purchases;
    hourAgg.set(pt.hour, existing);
  }

  const chartData = Array.from(hourAgg.entries())
    .sort(([a], [b]) => a - b)
    .map(([hour, vals]) => ({
      hour: `${hour}:00`,
      conversion: vals.trials > 0 ? Math.round((100 * vals.purchases) / vals.trials * 10) / 10 : 0,
    }));

  return (
    <div className="glass-card p-4">
      <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] mb-3">
        Hourly Conversion Trend
      </h3>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={chartData}>
          <XAxis dataKey="hour" tick={{ fontSize: 10, fill: "var(--text-muted)" }} />
          <YAxis tick={{ fontSize: 10, fill: "var(--text-muted)" }} domain={[0, "auto"]} />
          <Tooltip
            contentStyle={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Line
            type="monotone"
            dataKey="conversion"
            stroke="var(--accent-cyan)"
            strokeWidth={2}
            dot={{ r: 3, fill: "var(--accent-cyan)" }}
            activeDot={{ r: 5, fill: "var(--accent-amber)" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
