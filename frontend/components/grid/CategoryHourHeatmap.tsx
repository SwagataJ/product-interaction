"use client";

import { useEffect, useState } from "react";
import { getCategoryHourHeatmap } from "@/lib/api";

const CATEGORY_SHORT: Record<string, string> = {
  Women_Western: "W.West",
  Women_Ethnic: "W.Ethnic",
  Men_Casual: "M.Casual",
  Men_Formal: "M.Formal",
  Kids: "Kids",
  Accessories: "Acc.",
};

function heatColor(pct: number | null): string {
  if (pct == null || pct === 0) return "rgba(255,255,255,0.03)";
  const t = Math.min(pct / 55, 1);
  // blue → cyan → green
  const r = Math.round(10 + t * 0);
  const g = Math.round(40 + t * 190);
  const b = Math.round(80 + t * (180 - 80) * (1 - t));
  return `rgba(${r}, ${g}, ${b}, ${0.3 + t * 0.6})`;
}

export default function CategoryHourHeatmap() {
  const [data, setData] = useState<Array<{ category: string; hour: number; conversion_pct: number }>>([]);

  useEffect(() => {
    getCategoryHourHeatmap().then(setData).catch(console.error);
  }, []);

  if (!data.length) return <div className="glass-card p-4 h-48 animate-pulse" />;

  const categories = [...new Set(data.map((d) => d.category))];
  const hours = [...new Set(data.map((d) => d.hour))].sort((a, b) => a - b);

  const lookup = new Map<string, number>();
  data.forEach((d) => lookup.set(`${d.category}-${d.hour}`, d.conversion_pct));

  const CELL = 18;

  return (
    <div className="glass-card p-4 overflow-hidden" style={{ maxHeight: "260px" }}>
      <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] mb-2">
        Category x Hour
      </h3>
      <div className="overflow-x-auto">
        <table className="border-collapse" style={{ width: "100%" }}>
          <thead>
            <tr>
              <th style={{ width: 52 }} />
              {hours.map((h) => (
                <th
                  key={h}
                  className="text-[8px] font-normal text-[var(--text-dim)] text-center"
                  style={{ width: CELL, padding: 0 }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {categories.map((cat) => (
              <tr key={cat}>
                <td className="text-[9px] text-[var(--text-muted)] pr-1 whitespace-nowrap" style={{ padding: "1px 4px 1px 0" }}>
                  {CATEGORY_SHORT[cat] || cat}
                </td>
                {hours.map((h) => {
                  const val = lookup.get(`${cat}-${h}`) ?? null;
                  return (
                    <td key={h} style={{ padding: 1 }}>
                      <div
                        className="rounded-sm relative group"
                        style={{
                          width: "100%",
                          height: CELL,
                          backgroundColor: heatColor(val),
                        }}
                        title={`${CATEGORY_SHORT[cat] || cat} @ ${h}:00 — ${val ?? 0}%`}
                      >
                        {val != null && val > 0 && (
                          <span
                            className="absolute inset-0 flex items-center justify-center text-[7px] font-tabular text-white opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            {val}
                          </span>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* Legend */}
      <div className="flex items-center gap-2 mt-2">
        <span className="text-[8px] text-[var(--text-dim)]">Low</span>
        <div className="flex gap-px">
          {[0, 10, 20, 30, 45].map((v) => (
            <div key={v} className="rounded-sm" style={{ width: 12, height: 8, backgroundColor: heatColor(v) }} />
          ))}
        </div>
        <span className="text-[8px] text-[var(--text-dim)]">High</span>
      </div>
    </div>
  );
}
