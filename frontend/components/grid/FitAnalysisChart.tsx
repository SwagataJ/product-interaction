"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getFitAnalysis, type FitAnalysis } from "@/lib/api";
import { useStore } from "@/lib/store";

export default function FitAnalysisChart() {
  const [data, setData] = useState<FitAnalysis[]>([]);
  const { gridFilter } = useStore();

  useEffect(() => {
    const params: Record<string, string> = {};
    if (gridFilter.category) params.category = gridFilter.category;
    getFitAnalysis(params).then(setData).catch(console.error);
  }, [gridFilter.category]);

  if (!data.length) {
    return <div className="glass-card p-4 h-48 animate-pulse" />;
  }

  const maxTrials = Math.max(...data.map((d) => d.total_trials));

  return (
    <div className="glass-card p-4 overflow-y-auto" style={{ maxHeight: "260px" }}>
      <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] mb-3">
        Trial to Buy — Fit Analysis
      </h3>
      <div className="flex flex-col gap-2">
        {data.map((f, i) => {
          const barW = (f.total_trials / maxTrials) * 100;
          const rejW = f.rejection_pct;
          const convW = f.conversion_pct;
          return (
            <div key={f.fit} className="flex flex-col gap-0.5">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-medium text-[var(--text-primary)]">{f.fit}</span>
                <span className="text-[10px] font-tabular text-[var(--text-muted)]">
                  {f.total_trials} trials
                </span>
              </div>
              <div className="relative h-4 bg-[var(--bg-deep)] rounded overflow-hidden flex">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${convW}%` }}
                  transition={{ duration: 0.5, delay: i * 0.05 }}
                  className="h-full bg-[var(--accent-mint)]"
                  style={{ opacity: 0.8 }}
                />
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${rejW}%` }}
                  transition={{ duration: 0.5, delay: i * 0.05 + 0.1 }}
                  className="h-full bg-[var(--accent-coral)]"
                  style={{ opacity: 0.7 }}
                />
              </div>
              <div className="flex gap-3 text-[9px] text-[var(--text-muted)]">
                <span>
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-[var(--accent-mint)] mr-1" />
                  Buy {convW}%
                </span>
                <span>
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-[var(--accent-coral)] mr-1" />
                  Reject {rejW}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
