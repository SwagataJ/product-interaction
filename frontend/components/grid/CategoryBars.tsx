"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getCategories, type CategoryBar } from "@/lib/api";
import { useStore } from "@/lib/store";

const CATEGORY_LABELS: Record<string, string> = {
  Women_Western: "Women's Western",
  Women_Ethnic: "Women's Ethnic",
  Men_Casual: "Men's Casual",
  Men_Formal: "Men's Formal",
  Kids: "Kids",
  Accessories: "Accessories",
};

export default function CategoryBars() {
  const [data, setData] = useState<CategoryBar[]>([]);
  const { gridFilter, setGridFilter } = useStore();

  useEffect(() => {
    getCategories().then(setData).catch(console.error);
  }, []);

  if (!data.length) {
    return <div className="glass-card p-4 h-48 animate-pulse" />;
  }

  const maxPct = Math.max(...data.map((d) => d.trial_to_buy_pct));

  return (
    <div className="glass-card p-4">
      <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] mb-3">
        Trial-to-Buy by Category
      </h3>
      <div className="flex flex-col gap-1.5">
        {data.map((cat, i) => {
          const isSelected = gridFilter.category === cat.category;
          const widthPct = (cat.trial_to_buy_pct / maxPct) * 100;
          return (
            <button
              key={cat.category}
              onClick={() =>
                setGridFilter(isSelected ? {} : { category: cat.category })
              }
              className={`flex items-center gap-2 text-left rounded px-1 py-0.5 transition-all ${
                isSelected
                  ? "ring-1 ring-[var(--accent-cyan)]"
                  : "hover:bg-[var(--bg-deep)]"
              }`}
            >
              <span className="text-xs text-[var(--text-muted)] w-28 shrink-0 truncate">
                {CATEGORY_LABELS[cat.category] || cat.category}
              </span>
              <div className="flex-1 relative h-5 bg-[var(--bg-deep)] rounded overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${widthPct}%` }}
                  transition={{ duration: 0.6, delay: i * 0.1 }}
                  className="h-full rounded bg-[var(--accent-amber)]"
                  style={{ opacity: isSelected ? 1 : 0.7 }}
                />
              </div>
              <span className="text-xs font-tabular text-[var(--text-primary)] w-12 text-right">
                {cat.trial_to_buy_pct}%
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
