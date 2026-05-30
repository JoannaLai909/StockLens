"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type RankingRow } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { fmtPct, fmtNum, pctColor, cn } from "@/lib/utils";

const TABS = [
  { key: "return_20d",     label: "20日報酬", order: "desc" },
  { key: "return_60d",     label: "60日報酬", order: "desc" },
  { key: "health_score",   label: "健康分數", order: "desc" },
  { key: "volatility_20d", label: "波動率",   order: "asc"  },
  { key: "max_drawdown",   label: "最大回撤", order: "asc"  },
] as const;

function fmt(row: RankingRow, metric: string): string {
  switch (metric) {
    case "return_20d":     return fmtPct(row.return_20d_pct);
    case "return_60d":     return fmtPct(row.return_60d_pct);
    case "health_score":   return fmtNum(row.health_score);
    case "volatility_20d": return `${row.volatility_pct?.toFixed(2)}%`;
    case "max_drawdown":   return fmtPct(row.max_drawdown_pct);
    default:               return "—";
  }
}

function valueColor(row: RankingRow, metric: string): string {
  switch (metric) {
    case "return_20d":     return pctColor(row.return_20d_pct);
    case "return_60d":     return pctColor(row.return_60d_pct);
    case "health_score":   return "text-green-600";
    case "volatility_20d": return "text-blue-600";
    case "max_drawdown":   return "text-red-500";
    default:               return "text-slate-700";
  }
}

export default function RankingSection() {
  const [active, setActive] = useState(0);
  const tab = TABS[active];

  const { data = [], isLoading } = useQuery({
    queryKey: ["rankings", tab.key, tab.order],
    queryFn:  () => api.rankings({ metric: tab.key, order: tab.order, limit: 10 }),
  });

  const top5 = data.slice(0, 5);
  const bot5 = data.slice(5, 10);

  return (
    <Card title="因子排行 Top 10">
      <div className="flex gap-1 mb-4 border-b border-slate-100">
        {TABS.map((t, i) => (
          <button key={t.key} onClick={() => setActive(i)}
            className={cn(
              "px-4 py-2 text-sm font-semibold rounded-t-lg transition-colors border-b-2",
              active === i
                ? "text-blue-600 border-blue-600"
                : "text-slate-500 border-transparent hover:text-slate-700",
            )}>
            {t.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="text-sm text-slate-400 text-center py-8">載入中…</div>
      ) : (
        <div className="grid grid-cols-2 border-t border-slate-100">
          {[top5, bot5].map((half, hi) => (
            <table key={hi} className={cn("w-full text-sm", hi === 1 && "border-l border-slate-100")}>
              <thead>
                <tr className="bg-slate-50 text-xs text-slate-500">
                  <th className="w-9 py-2 px-2 text-center font-semibold">排名</th>
                  <th className="w-16 py-2 px-2 text-left font-semibold">代號</th>
                  <th className="py-2 px-2 text-left font-semibold">名稱</th>
                  <th className="w-28 py-2 px-2" />
                  <th className="w-20 py-2 px-2 text-right font-semibold">{tab.label}</th>
                </tr>
              </thead>
              <tbody>
                {half.map((row, i) => {
                  const rank = hi * 5 + i + 1;
                  const maxVal = Math.abs((data[0] as any)?.[tab.key] ?? 1);
                  const val    = Math.abs((row as any)[tab.key] ?? 0);
                  const width  = Math.max(5, Math.min(100, (val / (maxVal || 1)) * 100));
                  return (
                    <tr key={row.stock_id} className="border-b border-slate-50 hover:bg-slate-50/50">
                      <td className="py-2 px-2 text-center text-xs text-slate-400 font-bold">{rank}</td>
                      <td className="py-2 px-2 text-xs font-mono text-slate-600">{row.stock_id}</td>
                      <td className="py-2 px-2 text-xs text-slate-700 truncate max-w-[80px]">{row.name}</td>
                      <td className="py-2 px-2">
                        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-green-400 to-green-500 rounded-full"
                               style={{ width: `${width}%` }} />
                        </div>
                      </td>
                      <td className={cn("py-2 px-2 text-right text-xs font-bold", valueColor(row, tab.key))}>
                        {fmt(row, tab.key)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ))}
        </div>
      )}
    </Card>
  );
}
