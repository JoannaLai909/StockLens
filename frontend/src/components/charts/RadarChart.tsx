"use client";

import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { RankingRow } from "@/lib/api";

const AXES = ["20日報酬", "60日報酬", "健康分數", "低波動", "低回撤"];

function clip(value: number) {
  return Math.min(100, Math.max(0, value));
}

function toRadarValues(row: RankingRow): number[] {
  return [
    clip((row.return_20d_pct ?? 0) + 50),
    clip((row.return_60d_pct ?? 0) + 50),
    clip(row.health_score ?? 0),
    Math.max(0, 100 - (row.volatility_pct ?? 0) * 2),
    Math.max(0, 100 + (row.max_drawdown_pct ?? 0)),
  ];
}

export default function FactorRadarChart({
  stocks,
  colors,
}: {
  stocks: RankingRow[];
  colors: string[];
}) {
  const data = AXES.map((axis, index) => {
    const row: Record<string, string | number> = { axis };
    stocks.forEach((stock) => {
      row[stock.name] = toRadarValues(stock)[index];
    });
    return row;
  });

  if (!stocks.length) {
    return <div className="py-16 text-center text-sm text-slate-400">請先選擇股票</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={data} margin={{ top: 8, right: 24, bottom: 8, left: 24 }}>
        <PolarGrid stroke="#e2e8f0" />
        <PolarAngleAxis dataKey="axis" tick={{ fontSize: 12, fill: "#334155" }} />
        <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
        {stocks.map((stock, index) => (
          <Radar
            key={stock.stock_id}
            name={`${stock.stock_id} ${stock.name}`}
            dataKey={stock.name}
            stroke={colors[index]}
            fill={colors[index]}
            fillOpacity={0.15}
            strokeWidth={2}
          />
        ))}
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Tooltip
          formatter={(value: number) => [`${value.toFixed(1)} 分`, "標準化分數"]}
          contentStyle={{
            borderRadius: 12,
            borderColor: "#e2e8f0",
            boxShadow: "0 10px 30px rgb(15 23 42 / 0.08)",
          }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
