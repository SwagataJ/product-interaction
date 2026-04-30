"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getFunnel, type FunnelStage } from "@/lib/api";
import { useStore } from "@/lib/store";
import { formatCount } from "@/lib/format";

const COLORS = ["var(--accent-cyan)", "var(--accent-amber)", "var(--accent-coral)", "var(--accent-mint)"];

export default function ConversionFunnel() {
  const [data, setData] = useState<FunnelStage[]>([]);
  const { gridFilter } = useStore();

  useEffect(() => {
    const params: Record<string, string> = {};
    if (gridFilter.category) params.category = gridFilter.category;
    if (gridFilter.sku) params.sku = gridFilter.sku;
    getFunnel(params).then(setData).catch(console.error);
  }, [gridFilter]);

  if (!data.length) {
    return <div className="glass-card p-4 h-48 animate-pulse" />;
  }

  const maxCount = Math.max(...data.map((d) => d.count));

  return (
    <div className="glass-card p-4">
      <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] mb-3">
        Conversion Funnel
      </h3>
      <div className="flex flex-col gap-2">
        {data.map((stage, i) => {
          const widthPct = (stage.count / maxCount) * 100;
          return (
            <div key={stage.stage} className="flex items-center gap-3">
              <span className="text-xs text-[var(--text-muted)] w-20 shrink-0">
                {stage.stage}
              </span>
              <div className="flex-1 relative h-7 bg-[var(--bg-deep)] rounded overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${widthPct}%` }}
                  transition={{ duration: 0.8, delay: i * 0.15, ease: "easeOut" }}
                  className="h-full rounded"
                  style={{ backgroundColor: COLORS[i] }}
                />
                <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-tabular text-[var(--text-primary)]">
                  {formatCount(stage.count)}
                </span>
              </div>
              <span className="text-xs font-tabular text-[var(--text-muted)] w-12 text-right">
                {stage.rate}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
