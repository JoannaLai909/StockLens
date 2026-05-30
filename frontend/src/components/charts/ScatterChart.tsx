"use client";

import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Cell,
} from "recharts";
import type { ScatterPoint } from "@/lib/api";
import { healthColor, CATEGORY_LABELS } from "@/lib/utils";

export default function HealthScatterChart({ data }: { data: ScatterPoint[] }) {
  return (
    <div>
      <ResponsiveContainer width="100%" height={260}>
        <ScatterChart margin={{ top: 8, right: 16, bottom: 20, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="return_20d_pct" type="number" name="20日報酬率" unit="%"
                 tick={{ fontSize: 11, fill: "#64748b" }}
                 label={{ value: "報酬率 (%)", position: "insideBottom", offset: -10, fontSize: 11, fill: "#94a3b8" }} />
          <YAxis dataKey="volatility_pct" type="number" name="波動率" unit="%"
                 tick={{ fontSize: 11, fill: "#64748b" }}
                 label={{ value: "波動率 (%)", angle: -90, position: "insideLeft", offset: 12, fontSize: 11, fill: "#94a3b8" }} />
          <ReferenceLine x={0} stroke="#cbd5e1" strokeDasharray="4 3" />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0].payload as ScatterPoint;
              return (
                <div className="bg-white border border-slate-200 rounded-xl shadow-lg p-3 text-xs">
                  <div className="font-bold text-slate-800 mb-1">{d.stock_id} {d.name}</div>
                  <div className="text-slate-500">{CATEGORY_LABELS[d.category] ?? d.category}</div>
                  <div className="mt-1.5 space-y-0.5">
                    <div>報酬率：<span className="font-semibold">{d.return_20d_pct > 0 ? "+" : ""}{d.return_20d_pct}%</span></div>
                    <div>波動率：<span className="font-semibold">{d.volatility_pct}%</span></div>
                    <div>健康分數：<span className="font-semibold">{d.health_score}</span></div>
                  </div>
                </div>
              );
            }}
          />
          <Scatter data={data}>
            {data.map((d) => (
              <Cell key={d.stock_id} fill={healthColor(d.health_score)} fillOpacity={0.85} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      <div className="flex items-center justify-center gap-5 mt-1 text-xs text-slate-500">
        {[
          { label: "健康較佳", color: "#149b55" },
          { label: "中性",     color: "#0f6fe8" },
          { label: "需留意",   color: "#f59e0b" },
          { label: "風險較高", color: "#ef4444" },
        ].map(({ label, color }) => (
          <span key={label} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: color }} />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
