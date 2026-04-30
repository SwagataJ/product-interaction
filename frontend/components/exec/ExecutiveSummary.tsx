"use client";

import { useEffect, useState } from "react";
import {
  getBusinessKpis,
  getKpiSummary,
  getAnomalies,
  getLostSales,
  type BusinessKpis,
  type SummaryKpis,
  type Alert,
  type LostSales,
} from "@/lib/api";
import { useStore } from "@/lib/store";
import {
  AlertTriangle,
  TrendingDown,
  IndianRupee,
  ShoppingBag,
  BarChart3,
  Package,
  MessageCircle,
  Sparkles,
  ArrowRight,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SUGGESTED_QUESTIONS = [
  "What are the top 3 actions to improve conversion today?",
  "Which SKUs should be replenished from backroom right now?",
  "Show me the size 28 stockout situation",
];

const SEVERITY_STYLES: Record<string, { border: string; bg: string; icon: string }> = {
  critical: { border: "border-[var(--accent-coral)]", bg: "bg-[var(--accent-coral)]/10", icon: "text-[var(--accent-coral)]" },
  high: { border: "border-[var(--ops-amber)]", bg: "bg-[var(--ops-amber)]/10", icon: "text-[var(--ops-amber)]" },
  medium: { border: "border-[var(--accent-cyan)]", bg: "bg-[var(--accent-cyan)]/10", icon: "text-[var(--accent-cyan)]" },
};

function formatInr(value: number): string {
  if (value >= 10000000) return `₹${(value / 10000000).toFixed(1)} Cr`;
  if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function ExecutiveSummary() {
  const [business, setBusiness] = useState<BusinessKpis | null>(null);
  const [summary, setSummary] = useState<SummaryKpis | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [lostSales, setLostSales] = useState<LostSales | null>(null);
  const [headline, setHeadline] = useState<string>("");
  const [headlineLoading, setHeadlineLoading] = useState(true);
  const { setChatOpen, setChatPendingContext } = useStore();

  useEffect(() => {
    getBusinessKpis().then(setBusiness);
    getKpiSummary().then(setSummary);
    getAnomalies().then(setAlerts);
    getLostSales().then(setLostSales);
    fetchHeadline();
  }, []);

  async function fetchHeadline() {
    setHeadlineLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: "Give me a one-sentence executive headline for today's store performance. Be specific with numbers. No preamble, just the headline.",
          history: [],
          context: null,
        }),
      });
      if (!res.ok || !res.body) throw new Error("Failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let text = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let eventType = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ") && eventType === "token") {
            try {
              const data = JSON.parse(line.slice(6));
              text += data.text || "";
              setHeadline(text);
            } catch { /* ignore */ }
          }
        }
      }
      if (!text) setHeadline("Store performance data loaded. Ask AI for insights.");
    } catch {
      setHeadline("Store performance data loaded. Ask AI for insights.");
    } finally {
      setHeadlineLoading(false);
    }
  }

  function askQuestion(q: string) {
    setChatPendingContext(null);
    setChatOpen(true);
    // Small delay to let chat panel open, then set context which triggers auto-send
    setTimeout(() => {
      setChatPendingContext(q);
    }, 100);
  }

  const criticalCount = alerts.filter((a) => a.severity === "critical").length;
  const highCount = alerts.filter((a) => a.severity === "high").length;
  const mediumCount = alerts.filter((a) => a.severity === "medium").length;

  return (
    <div className="flex flex-col gap-4">
      {/* AI Headline */}
      <div className="glass-card p-5 relative overflow-hidden">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-[var(--accent-cyan)]/20 flex items-center justify-center flex-shrink-0 mt-0.5">
            <Sparkles size={16} className="text-[var(--accent-cyan)]" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[10px] uppercase tracking-wider text-[var(--text-dim)] mb-1">AI Store Insight</p>
            {headlineLoading ? (
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[var(--accent-cyan)] animate-pulse" />
                <span className="text-sm text-[var(--text-muted)] italic">Analyzing store data...</span>
              </div>
            ) : (
              <p className="text-sm text-[var(--text-primary)] leading-relaxed">{headline}</p>
            )}
          </div>
        </div>
      </div>

      {/* Big KPI Cards */}
      <div className="grid grid-cols-3 gap-3">
        {/* Lost Sales */}
        <div className="glass-card p-5 flex flex-col gap-3 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-[var(--accent-coral)]/5 rounded-bl-full" />
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[var(--accent-coral)]/20 flex items-center justify-center">
              <TrendingDown size={14} className="text-[var(--accent-coral)]" />
            </div>
            <span className="text-xs uppercase tracking-wider text-[var(--text-muted)]">Estimated Lost Sales</span>
          </div>
          <span className="text-3xl font-semibold font-tabular text-[var(--accent-coral)]">
            {business ? formatInr(business.lost_sales_inr) : "..."}
          </span>
          {lostSales && (
            <div className="flex flex-wrap gap-1.5 mt-1">
              {lostSales.by_category.slice(0, 3).map((c) => (
                <span key={c.category} className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--bg-deep)] text-[var(--text-muted)]">
                  {c.category.replace("_", " ")}: {formatInr(c.estimated_lost_sales_inr)}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Working Capital */}
        <div className="glass-card p-5 flex flex-col gap-3 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-[var(--ops-amber)]/5 rounded-bl-full" />
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[var(--ops-amber)]/20 flex items-center justify-center">
              <Package size={14} className="text-[var(--ops-amber)]" />
            </div>
            <span className="text-xs uppercase tracking-wider text-[var(--text-muted)]">Working Capital Tied Up</span>
          </div>
          <span className="text-3xl font-semibold font-tabular text-[var(--ops-amber)]">
            {business ? formatInr(business.working_capital_inr) : "..."}
          </span>
          {lostSales && (
            <p className="text-[10px] text-[var(--text-dim)] mt-1">
              {lostSales.by_category.reduce((s, c) => s + c.unsold_units, 0)} unsold units in backroom
            </p>
          )}
        </div>

        {/* Conversion Uplift */}
        <div className="glass-card p-5 flex flex-col gap-3 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-[var(--accent-mint)]/5 rounded-bl-full" />
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[var(--accent-mint)]/20 flex items-center justify-center">
              <IndianRupee size={14} className="text-[var(--accent-mint)]" />
            </div>
            <span className="text-xs uppercase tracking-wider text-[var(--text-muted)]">Conversion Uplift Opportunity</span>
          </div>
          <span className="text-3xl font-semibold font-tabular text-[var(--accent-mint)]">
            {business ? formatInr(business.conversion_uplift_inr) : "..."}
          </span>
          {business && (
            <p className="text-[10px] text-[var(--text-dim)] mt-1">
              +{business.conversion_delta_pct.toFixed(1)}% conversion improvement potential
            </p>
          )}
        </div>
      </div>

      {/* Middle row: Operational Snapshot + Priority Alerts */}
      <div className="grid grid-cols-5 gap-3">
        {/* Operational Snapshot */}
        <div className="col-span-2 glass-card p-4 flex flex-col gap-3">
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 size={14} className="text-[var(--accent-cyan)]" />
            <span className="text-xs font-medium uppercase tracking-wider text-[var(--text-muted)]">Operational Snapshot</span>
          </div>
          {summary ? (
            <div className="grid grid-cols-2 gap-3">
              <MetricRow label="Trial-to-Buy" value={`${summary.trial_to_buy_pct.toFixed(1)}%`} accent="cyan" />
              <MetricRow label="Total Trials" value={summary.trial_count.toLocaleString("en-IN")} accent="cyan" />
              <MetricRow label="Total Pickups" value={summary.pickup_count.toLocaleString("en-IN")} accent="cyan" />
              <MetricRow label="Rejections" value={summary.rejection_count.toLocaleString("en-IN")} accent="coral" />
              <MetricRow label="Misplacement Rate" value={`${summary.misplacement_rate_pct.toFixed(1)}%`} accent={summary.misplacement_rate_pct > 3 ? "coral" : "mint"} />
              <MetricRow
                label="Alerts"
                value={`${alerts.length} total`}
                subValue={`${criticalCount} critical / ${highCount} high / ${mediumCount} medium`}
                accent={criticalCount > 0 ? "coral" : "amber"}
              />
            </div>
          ) : (
            <div className="h-32 animate-pulse bg-[var(--bg-deep)] rounded" />
          )}
        </div>

        {/* Priority Alerts */}
        <div className="col-span-3 glass-card p-4 flex flex-col gap-2">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <AlertTriangle size={14} className="text-[var(--ops-amber)]" />
              <span className="text-xs font-medium uppercase tracking-wider text-[var(--text-muted)]">Priority Alerts</span>
            </div>
            <span className="text-[10px] text-[var(--text-dim)]">{alerts.length} total</span>
          </div>
          <div className="flex flex-col gap-2 overflow-y-auto max-h-[200px]">
            {alerts.map((alert, i) => {
              const style = SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.medium;
              return (
                <button
                  key={i}
                  onClick={() => askQuestion(`Tell me about: ${alert.title}`)}
                  className={`text-left p-3 rounded-lg border ${style.border}/30 ${style.bg} hover:brightness-110 transition-all`}
                >
                  <div className="flex items-start gap-2">
                    <AlertTriangle size={12} className={`${style.icon} mt-0.5 flex-shrink-0`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-[var(--text-primary)] truncate">{alert.title}</p>
                      <p className="text-[10px] text-[var(--text-muted)] mt-0.5 line-clamp-2">{alert.narrative}</p>
                    </div>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${style.bg} ${style.icon} font-medium flex-shrink-0`}>
                      {alert.severity}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Talk to your store */}
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-7 h-7 rounded-lg bg-[var(--accent-cyan)]/20 flex items-center justify-center">
            <MessageCircle size={14} className="text-[var(--accent-cyan)]" />
          </div>
          <div>
            <span className="text-xs font-medium uppercase tracking-wider text-[var(--text-muted)]">Talk to Your Store</span>
            <p className="text-[10px] text-[var(--text-dim)]">Ask AI-powered questions about your store performance</p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {SUGGESTED_QUESTIONS.map((q, i) => (
            <button
              key={i}
              onClick={() => askQuestion(q)}
              className="text-left p-3 rounded-lg border border-[var(--card-border)] bg-[var(--bg-deep)] hover:border-[var(--accent-cyan)]/50 hover:bg-[var(--accent-cyan)]/5 transition-all group"
            >
              <div className="flex items-start gap-2">
                <ShoppingBag size={12} className="text-[var(--text-dim)] mt-0.5 group-hover:text-[var(--accent-cyan)] transition-colors flex-shrink-0" />
                <span className="text-xs text-[var(--text-muted)] group-hover:text-[var(--text-primary)] transition-colors leading-relaxed">{q}</span>
              </div>
              <div className="flex justify-end mt-2">
                <ArrowRight size={12} className="text-[var(--text-dim)] group-hover:text-[var(--accent-cyan)] transition-colors" />
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function MetricRow({ label, value, subValue, accent }: { label: string; value: string; subValue?: string; accent: string }) {
  const colorMap: Record<string, string> = {
    cyan: "text-[var(--accent-cyan)]",
    mint: "text-[var(--accent-mint)]",
    coral: "text-[var(--accent-coral)]",
    amber: "text-[var(--ops-amber)]",
  };
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] text-[var(--text-dim)] uppercase tracking-wider">{label}</span>
      <span className={`text-sm font-semibold font-tabular ${colorMap[accent] || colorMap.cyan}`}>{value}</span>
      {subValue && <span className="text-[9px] text-[var(--text-dim)]">{subValue}</span>}
    </div>
  );
}
