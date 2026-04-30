"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getAnomalies, type Alert } from "@/lib/api";
import { useStore } from "@/lib/store";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";

const SEVERITY_CONFIG: Record<string, { color: string; icon: typeof AlertTriangle }> = {
  critical: { color: "var(--accent-coral)", icon: AlertTriangle },
  high: { color: "var(--accent-amber)", icon: AlertCircle },
  medium: { color: "var(--accent-cyan)", icon: Info },
  low: { color: "var(--text-muted)", icon: Info },
};

export default function AlertFeed({ compact = false }: { compact?: boolean }) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const { setChatOpen, setChatPendingContext } = useStore();

  useEffect(() => {
    getAnomalies().then(setAlerts).catch(console.error);
  }, []);

  if (!alerts.length) return <div className="glass-card p-4 h-48 animate-pulse" />;

  return (
    <div className={`glass-card ${compact ? "p-3 max-h-[260px]" : "p-4 h-full"} overflow-y-auto`}>
      <h3 className={`text-xs uppercase tracking-wider text-[var(--text-muted)] ${compact ? "mb-2" : "mb-3"}`}>
        Alerts ({alerts.length})
      </h3>
      <AnimatePresence>
        <div className="flex flex-col gap-2">
          {alerts.map((alert, i) => {
            const config = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.low;
            const Icon = config.icon;
            return (
              <motion.div
                key={`${alert.type}-${i}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex gap-2 p-2 rounded-lg bg-[var(--bg-deep)] hover:bg-[var(--secondary)] transition-colors cursor-pointer"
                onClick={() => {
                  setChatPendingContext(`Investigate: ${alert.title}`);
                  setChatOpen(true);
                }}
              >
                <div
                  className="w-1 shrink-0 rounded-full"
                  style={{ backgroundColor: config.color }}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <Icon size={12} style={{ color: config.color }} />
                    <span className="text-xs font-medium text-[var(--text-primary)] truncate">
                      {alert.title}
                    </span>
                  </div>
                  {!compact && (
                    <p className="text-[11px] text-[var(--text-muted)] line-clamp-2">
                      {alert.narrative}
                    </p>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      </AnimatePresence>
    </div>
  );
}
