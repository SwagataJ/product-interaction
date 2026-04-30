"use client";

import { useStore } from "@/lib/store";
import { X } from "lucide-react";
import ConversionFunnel from "./ConversionFunnel";
import CategoryBars from "./CategoryBars";
import HourlyTrend from "./HourlyTrend";
import SizeRejectionHeatmap from "./SizeRejectionHeatmap";
import CategoryHourHeatmap from "./CategoryHourHeatmap";
import AlertFeed from "./AlertFeed";
import BrandBars from "./BrandBars";
import PriceTierChart from "./PriceTierChart";
import FitAnalysisChart from "./FitAnalysisChart";
import SubcategoryBars from "./SubcategoryBars";
import ColorPerformance from "./ColorPerformance";

const CATEGORY_LABELS: Record<string, string> = {
  Women_Western: "Women's Western",
  Women_Ethnic: "Women's Ethnic",
  Men_Casual: "Men's Casual",
  Men_Formal: "Men's Formal",
  Kids: "Kids",
  Accessories: "Accessories",
};

export default function ChartGrid() {
  const { gridFilter, clearGridFilter } = useStore();

  return (
    <div className="flex flex-col gap-2">
      {gridFilter.category && (
        <div className="flex items-center gap-2 px-1">
          <span className="text-xs text-[var(--text-muted)]">Showing:</span>
          <button
            onClick={clearGridFilter}
            className="flex items-center gap-1 text-xs bg-[var(--accent-cyan)] text-[var(--bg-deep)] px-2 py-0.5 rounded-full font-medium"
          >
            {CATEGORY_LABELS[gridFilter.category] || gridFilter.category}
            <X size={12} />
          </button>
        </div>
      )}
      <div className="grid grid-cols-3 gap-2">
        <ConversionFunnel />
        <CategoryBars />
        <HourlyTrend />
      </div>
      <div className="grid grid-cols-3 gap-2">
        <BrandBars />
        <SubcategoryBars />
        <FitAnalysisChart />
      </div>
      <div className="grid grid-cols-3 gap-2" style={{ maxHeight: "260px" }}>
        <ColorPerformance />
        <PriceTierChart />
        <AlertFeed compact />
      </div>
      <div className="grid grid-cols-2 gap-2" style={{ maxHeight: "260px" }}>
        <SizeRejectionHeatmap />
        <CategoryHourHeatmap />
      </div>
    </div>
  );
}
