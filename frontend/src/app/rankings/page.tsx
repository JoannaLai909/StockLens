"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Download, Search } from "lucide-react";
import { api, type RankingRow } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { CATEGORY_LABELS, cn, fmtNum, fmtPct, pctColor } from "@/lib/utils";

const METRICS = [
  { key: "return_20d", label: "20日報酬", order: "desc", hint: "短期動能高到低" },
  { key: "return_60d", label: "60日報酬", order: "desc", hint: "中期表現高到低" },
  { key: "health_score", label: "健康分數", order: "desc", hint: "綜合分數高到低" },
  { key: "volatility_20d", label: "波動率", order: "asc", hint: "低波動優先" },
  { key: "max_drawdown", label: "最大回撤", order: "asc", hint: "回撤較小優先" },
  { key: "volume_ratio", label: "成交量倍率", order: "desc", hint: "量能放大優先" },
] as const;

const CATEGORIES = [
  { key: "all", label: "全部產業" },
  { key: "semiconductor", label: "半導體" },
  { key: "financial", label: "金融" },
  { key: "etf", label: "ETF" },
  { key: "electronics", label: "電子" },
  { key: "shipping", label: "航運" },
  { key: "telecom", label: "電信" },
] as const;

function metricValue(row: RankingRow, metric: string) {
  switch (metric) {
    case "return_20d":
      return fmtPct(row.return_20d_pct);
    case "return_60d":
      return fmtPct(row.return_60d_pct);
    case "health_score":
      return fmtNum(row.health_score, 1);
    case "volatility_20d":
      return `${fmtNum(row.volatility_pct, 2)}%`;
    case "max_drawdown":
      return fmtPct(row.max_drawdown_pct);
    case "volume_ratio":
      return fmtNum(row.volume_ratio, 2);
    default:
      return "—";
  }
}

function metricColor(row: RankingRow, metric: string) {
  switch (metric) {
    case "return_20d":
      return pctColor(row.return_20d_pct);
    case "return_60d":
      return pctColor(row.return_60d_pct);
    case "max_drawdown":
      return "text-red-500";
    case "health_score":
      return "text-green-600";
    case "volume_ratio":
      return "text-amber-600";
    default:
      return "text-blue-600";
  }
}

function toCsv(rows: RankingRow[]) {
  const header = [
    "rank",
    "stock_id",
    "name",
    "category",
    "return_20d_pct",
    "return_60d_pct",
    "volatility_pct",
    "max_drawdown_pct",
    "volume_ratio",
    "health_score",
    "cluster_label",
    "latest_close",
  ];
  const body = rows.map((row, index) => [
    index + 1,
    row.stock_id,
    row.name,
    CATEGORY_LABELS[row.category] ?? row.category,
    row.return_20d_pct,
    row.return_60d_pct,
    row.volatility_pct,
    row.max_drawdown_pct,
    row.volume_ratio,
    row.health_score,
    row.cluster_label ?? "",
    row.latest_close,
  ]);
  return [header, ...body].map((line) => line.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(",")).join("\n");
}

export default function RankingsPage() {
  const [metric, setMetric] = useState<(typeof METRICS)[number]["key"]>("return_20d");
  const [category, setCategory] = useState("all");
  const [keyword, setKeyword] = useState("");

  const activeMetric = METRICS.find((item) => item.key === metric) ?? METRICS[0];

  const { data = [], isLoading } = useQuery({
    queryKey: ["rankings-page", metric, category],
    queryFn: () => api.rankings({
      metric,
      order: activeMetric.order,
      category,
      limit: 30,
    }),
  });

  const filtered = useMemo(() => {
    const key = keyword.trim().toLowerCase();
    if (!key) return data;
    return data.filter((row) =>
      row.stock_id.toLowerCase().includes(key) ||
      row.name.toLowerCase().includes(key),
    );
  }, [data, keyword]);

  const downloadCsv = () => {
    const csv = `\ufeff${toCsv(filtered)}`;
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `stocklens-rankings-${metric}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">因子排行</h1>
          <p className="text-sm text-slate-400 mt-1">
            依報酬率、健康分數、波動率與回撤排序，快速比較 30 檔股票表現。
          </p>
        </div>
        <button
          onClick={downloadCsv}
          className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-bold text-white shadow-sm hover:bg-blue-700"
        >
          <Download size={16} />
          匯出 CSV
        </button>
      </div>

      <Card title="排行設定">
        <div className="grid grid-cols-[1.2fr_0.8fr_1fr] gap-3">
          <div>
            <div className="text-xs font-bold text-slate-400 mb-2">指標</div>
            <div className="grid grid-cols-3 gap-2">
              {METRICS.map((item) => (
                <button
                  key={item.key}
                  onClick={() => setMetric(item.key)}
                  className={cn(
                    "rounded-xl border px-3 py-2 text-left transition-colors",
                    metric === item.key
                      ? "border-blue-500 bg-blue-50 text-blue-700"
                      : "border-slate-100 bg-white text-slate-600 hover:border-blue-200",
                  )}
                >
                  <div className="text-sm font-black">{item.label}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{item.hint}</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="text-xs font-bold text-slate-400 mb-2">產業篩選</div>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-700 outline-none focus:border-blue-400"
            >
              {CATEGORIES.map((item) => (
                <option key={item.key} value={item.key}>{item.label}</option>
              ))}
            </select>
          </div>

          <div>
            <div className="text-xs font-bold text-slate-400 mb-2">搜尋股票</div>
            <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2.5">
              <Search size={16} className="text-slate-400" />
              <input
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                placeholder="輸入代號或名稱"
                className="w-full bg-transparent text-sm font-semibold text-slate-700 outline-none placeholder:text-slate-300"
              />
            </div>
          </div>
        </div>
      </Card>

      <Card title={`${activeMetric.label}排行`}>
        {isLoading ? (
          <div className="py-16 text-center text-sm text-slate-400">載入排行資料中…</div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-100">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 text-xs text-slate-500">
                  <th className="w-16 px-4 py-3 text-center font-bold">排名</th>
                  <th className="px-4 py-3 text-left font-bold">股票</th>
                  <th className="px-4 py-3 text-left font-bold">產業</th>
                  <th className="px-4 py-3 text-right font-bold">{activeMetric.label}</th>
                  <th className="px-4 py-3 text-right font-bold">健康分數</th>
                  <th className="px-4 py-3 text-right font-bold">波動率</th>
                  <th className="px-4 py-3 text-right font-bold">最大回撤</th>
                  <th className="px-4 py-3 text-center font-bold">分群</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row, index) => (
                  <tr key={row.stock_id} className="border-t border-slate-100 hover:bg-blue-50/30">
                    <td className="px-4 py-3 text-center font-black text-slate-400">{index + 1}</td>
                    <td className="px-4 py-3">
                      <Link href={`/stocks/${row.stock_id}`} className="group">
                        <div className="font-mono text-xs text-slate-400 group-hover:text-blue-500">{row.stock_id}</div>
                        <div className="font-black text-slate-800 group-hover:text-blue-600">{row.name}</div>
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-500">{CATEGORY_LABELS[row.category] ?? row.category}</td>
                    <td className={cn("px-4 py-3 text-right font-black", metricColor(row, metric))}>
                      {metricValue(row, metric)}
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-green-600">{fmtNum(row.health_score, 1)}</td>
                    <td className="px-4 py-3 text-right font-bold text-blue-600">{fmtNum(row.volatility_pct, 2)}%</td>
                    <td className="px-4 py-3 text-right font-bold text-red-500">{fmtPct(row.max_drawdown_pct)}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-bold text-slate-500">
                        {row.cluster_label !== null ? `Cluster ${row.cluster_label}` : "—"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
