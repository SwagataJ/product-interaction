"use client";

import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { getPriceTierConversion, type PriceTier } from "@/lib/api";

const COLORS = ["#00D4FF", "#00E5A0", "#FFB800", "#FF7A45", "#FF4D6D"];

export default function PriceTierChart() {
  const [data, setData] = useState<PriceTier[]>([]);

  useEffect(() => {
    getPriceTierConversion().then(setData).catch(console.error);
  }, []);

  if (!data.length) {
    return <div className="glass-card p-4 h-48 animate-pulse" />;
  }

  return (
    <div className="glass-card p-4" style={{ maxHeight: "260px" }}>
      <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] mb-3">
        Conversion by Price
      </h3>
      <ResponsiveContainer width="100%" height={190}>
        <BarChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <XAxis
            dataKey="price_tier"
            tick={{ fontSize: 9, fill: "#7A8497" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 9, fill: "#7A8497" }}
            axisLine={false}
            tickLine={false}
            domain={[0, "auto"]}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip
            contentStyle={{
              background: "#131829",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 8,
              fontSize: 11,
            }}
            formatter={(value: number) => [`${value}%`, "Conversion"]}
          />
          <Bar dataKey="trial_to_buy_pct" radius={[4, 4, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} fillOpacity={0.8} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
