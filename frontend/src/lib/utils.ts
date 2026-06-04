import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const CATEGORY_LABELS: Record<string, string> = {
  semiconductor: "半導體",
  financial:     "金融",
  etf:           "ETF",
  electronics:   "電子",
  shipping:      "航運",
  telecom:       "電信",
  other:         "其他",
};

export function fmtPct(v: number | null | undefined, digits = 2): string {
  if (v == null) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(digits)}%`;
}

export function fmtNum(v: number | null | undefined, digits = 1): string {
  if (v == null) return "—";
  return v.toFixed(digits);
}

export function healthColor(score: number | null | undefined): string {
  if (score == null) return "#94a3b8";
  if (score >= 65) return "#149b55";
  if (score >= 55) return "#0f6fe8";
  if (score >= 45) return "#f59e0b";
  return "#ef4444";
}

export function healthLabel(score: number | null | undefined): string {
  if (score == null) return "—";
  if (score >= 65) return "健康較佳";
  if (score >= 55) return "中性";
  if (score >= 45) return "需留意";
  return "風險較高";
}

export function pctColor(v: number | null | undefined): string {
  if (v == null) return "text-slate-400";
  return v >= 0 ? "text-success" : "text-danger";
}
