"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, LabelList,
} from "recharts";
import type { IndustryAvg } from "@/lib/api";
import { CATEGORY_LABELS, healthColor } from "@/lib/utils";

export default function IndustryBarChart({ data }: { data: IndustryAvg[] }) {
  const sorted = [...data].sort((a, b) => b.avg_health_score - a.avg_health_score);
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={sorted} layout="vertical" margin={{ top: 4, right: 48, bottom: 20, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
        <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: "#64748b" }}
               label={{ value: "健康分數 (0–100)", position: "insideBottom", offset: -10, fontSize: 11, fill: "#94a3b8" }} />
        <YAxis type="category" dataKey="category" width={52}
               tickFormatter={(v) => CATEGORY_LABELS[v] ?? v}
               tick={{ fontSize: 12, fill: "#334155" }} />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const d = payload[0].payload as IndustryAvg;
            return (
              <div className="bg-white border border-slate-200 rounded-xl shadow-lg p-3 text-xs">
                <div className="font-bold text-slate-800 mb-1">{CATEGORY_LABELS[d.category] ?? d.category}</div>
                <div>健康分數：<span className="font-semibold">{d.avg_health_score}</span></div>
                <div>20日報酬：<span className="font-semibold">{d.avg_return_20d_pct > 0 ? "+" : ""}{d.avg_return_20d_pct}%</span></div>
                <div>股票數：<span className="font-semibold">{d.stock_count}</span></div>
              </div>
            );
          }}
        />
        <Bar dataKey="avg_health_score" radius={[0, 4, 4, 0]} maxBarSize={22}>
          {sorted.map((d) => (
            <Cell key={d.category} fill={healthColor(d.avg_health_score)} />
          ))}
          <LabelList dataKey="avg_health_score" position="right"
                     formatter={(v: number) => v.toFixed(1)}
                     style={{ fontSize: 11, fontWeight: 700, fill: "#475569" }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
