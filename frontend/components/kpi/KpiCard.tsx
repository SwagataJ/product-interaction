"use client";

import { useEffect, useRef, useState } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: number;
  format?: "pct" | "count" | "inr";
  delta?: number;
  large?: boolean;
}

function formatValue(value: number, format: string): string {
  if (format === "pct") return `${value.toFixed(1)}%`;
  if (format === "inr") {
    if (value >= 10000000) return `₹${(value / 10000000).toFixed(1)} Cr`;
    if (value >= 100000) return `₹${(value / 100000).toFixed(1)} L`;
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(value);
  }
  return new Intl.NumberFormat("en-IN").format(value);
}

export default function KpiCard({ label, value, format = "count", delta, large }: KpiCardProps) {
  const [displayValue, setDisplayValue] = useState(0);
  const animRef = useRef<number | null>(null);

  useEffect(() => {
    const duration = 800;
    const start = performance.now();
    const startVal = displayValue;

    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(startVal + (value - startVal) * eased);
      if (progress < 1) {
        animRef.current = requestAnimationFrame(animate);
      }
    };

    animRef.current = requestAnimationFrame(animate);
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <div className={`glass-card p-${large ? "6" : "3"} flex flex-col gap-1`}>
      <span className={`text-[var(--text-muted)] ${large ? "text-sm" : "text-xs"} uppercase tracking-wider`}>
        {label}
      </span>
      <span className={`font-tabular font-semibold ${large ? "text-3xl" : "text-lg"} text-[var(--text-primary)]`}>
        {formatValue(displayValue, format)}
      </span>
      {delta != null && (
        <div className={`flex items-center gap-1 text-xs ${delta >= 0 ? "text-[var(--accent-mint)]" : "text-[var(--accent-coral)]"}`}>
          {delta >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          <span>{delta >= 0 ? "+" : ""}{delta.toFixed(1)}%</span>
        </div>
      )}
    </div>
  );
}
