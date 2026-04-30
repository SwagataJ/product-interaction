/** Format number in Indian numbering system (e.g., ₹2,30,000) */
export function formatINR(value: number): string {
  if (value >= 10000000) {
    return `₹${(value / 10000000).toFixed(1)} Cr`;
  }
  if (value >= 100000) {
    return `₹${(value / 100000).toFixed(1)} L`;
  }
  const formatted = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
  return formatted;
}

/** Format percentage */
export function formatPct(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${value.toFixed(1)}%`;
}

/** Format large numbers with Indian notation */
export function formatCount(value: number): string {
  return new Intl.NumberFormat("en-IN").format(value);
}
