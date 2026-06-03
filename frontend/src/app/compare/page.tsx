"use client";

import { useMemo, useState } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Plus, X } from "lucide-react";
import dayjs from "dayjs";
import { api, type PriceBar, type RankingRow, type StockBasic } from "@/lib/api";
import FactorRadarChart from "@/components/charts/RadarChart";
import { CATEGORY_LABELS, cn, healthColor } from "@/lib/utils";

const PALETTE = ["#0f6fe8", "#149b55", "#f59e0b", "#ef4444", "#8b5cf6"];
const DEFAULT_SELECTED = ["2330", "2454"];

function formatPct(value: number | null | undefined) {
  if (value == null) return "-";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatNum(value: number | null | undefined, digits = 1) {
  if (value == null) return "-";
  return value.toFixed(digits);
}

function StockSelector({
  allStocks,
  selectedIds,
  onChange,
  colorMap,
}: {
  allStocks: StockBasic[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  colorMap: Record<string, string>;
}) {
  const [draftId, setDraftId] = useState("");
  const selectedStocks = selectedIds
    .map((id) => allStocks.find((stock) => stock.stock_id === id))
    .filter((stock): stock is StockBasic => Boolean(stock));
  const availableStocks = allStocks.filter((stock) => !selectedIds.includes(stock.stock_id));

  const addStock = () => {
    if (!draftId || selectedIds.includes(draftId) || selectedIds.length >= 5) return;
    onChange([...selectedIds, draftId]);
    setDraftId("");
  };

  const removeStock = (id: string) => {
    onChange(selectedIds.filter((stockId) => stockId !== id));
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
      <div className="flex flex-wrap items-center gap-3">
        {selectedStocks.map((stock) => (
          <div
            key={stock.stock_id}
            className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 shadow-sm"
          >
            <span
              className="h-2.5 w-2.5 rounded-full shrink-0"
              style={{ background: colorMap[stock.stock_id] }}
            />
            <span>{stock.stock_id} {stock.name}</span>
            <button
              onClick={() => removeStock(stock.stock_id)}
              className="text-slate-300 transition-colors hover:text-red-500"
              aria-label={`移除 ${stock.stock_id}`}
            >
              <X size={14} />
            </button>
          </div>
        ))}

        <select
          value={draftId}
          onChange={(event) => setDraftId(event.target.value)}
          className="h-10 min-w-48 rounded-xl border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-600 outline-none transition-colors focus:border-blue-300"
          disabled={selectedIds.length >= 5}
        >
          <option value="">新增股票</option>
          {availableStocks.map((stock) => (
            <option key={stock.stock_id} value={stock.stock_id}>
              {stock.stock_id} {stock.name}
            </option>
          ))}
        </select>

        <button
          onClick={addStock}
          disabled={!draftId || selectedIds.length >= 5}
          className="inline-flex h-10 items-center gap-1.5 rounded-xl border border-slate-200 px-3 text-sm font-bold text-slate-600 transition-colors hover:border-blue-200 hover:bg-blue-50 hover:text-blue-600 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Plus size={15} />
          新增
        </button>
      </div>
    </div>
  );
}

function SummaryCards({
  selected,
  colorMap,
}: {
  selected: RankingRow[];
  colorMap: Record<string, string>;
}) {
  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${selected.length}, minmax(0, 1fr))` }}>
      {selected.map((row) => (
        <div
          key={row.stock_id}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
        >
          <div className="h-1.5" style={{ background: colorMap[row.stock_id] }} />
          <div className="p-4">
            <div className="text-xs text-slate-400 font-mono mb-0.5">{row.stock_id}</div>
            <div className="text-base font-bold text-slate-800">{row.name}</div>
            <div className="text-2xl font-black text-slate-900 mt-1">
              {row.latest_close?.toLocaleString()}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              {CATEGORY_LABELS[row.category] ?? row.category}
            </div>
            <div className="mt-2 text-xs text-slate-400">Health Score</div>
            <div className="text-lg font-black" style={{ color: healthColor(row.health_score) }}>
              {row.health_score?.toFixed(1)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function buildChartData(allPrices: { id: string; prices: PriceBar[] }[]) {
  if (allPrices.some((item) => !item.prices.length)) return [];

  const commonStart = allPrices.reduce((latest, item) => {
    const first = item.prices[0]?.date ?? "";
    return first > latest ? first : latest;
  }, "");

  const normalized = allPrices.map(({ id, prices }) => {
    const filtered = prices.filter((price) => price.date >= commonStart);
    const base = filtered[0]?.close ?? 1;
    return {
      id,
      data: filtered.map((price) => ({
        date: price.date,
        norm: (price.close / base) * 100,
      })),
    };
  });

  const allDates = Array.from(
    new Set(normalized.flatMap((item) => item.data.map((point) => point.date))),
  ).sort();

  return allDates.map((date) => {
    const row: Record<string, string | number> = { date };
    normalized.forEach(({ id, data }) => {
      const match = data.find((point) => point.date === date);
      if (match) row[id] = Number(match.norm.toFixed(2));
    });
    return row;
  });
}

function TrendChart({
  selectedIds,
  selected,
  priceData,
  colorMap,
}: {
  selectedIds: string[];
  selected: RankingRow[];
  priceData: Record<string, PriceBar[]>;
  colorMap: Record<string, string>;
}) {
  const allPrices = selectedIds.map((id) => ({
    id,
    prices: priceData[id] ?? [],
  }));
  const chartData = buildChartData(allPrices);

  if (!chartData.length) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
        <h3 className="text-sm font-bold text-slate-700 mb-1">相對走勢比較（已標準化）</h3>
        <div className="py-16 text-center text-sm text-slate-400">價格資料載入中...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
      <h3 className="text-sm font-bold text-slate-700 mb-1">相對走勢比較（已標準化）</h3>
      <p className="text-xs text-slate-400 mb-3">以共同起始日為基準設為 100</p>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="date"
            tickFormatter={(date) => dayjs(date).format("MM/DD")}
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} domain={["auto", "auto"]} tickLine={false} />
          <ReferenceLine y={100} stroke="#94a3b8" strokeDasharray="4 3" />
          <Tooltip
            formatter={(value: number, name: string) => [`${value.toFixed(2)}`, name]}
            labelFormatter={(date) => dayjs(date).format("YYYY-MM-DD")}
            contentStyle={{
              borderRadius: 12,
              borderColor: "#e2e8f0",
              boxShadow: "0 10px 30px rgb(15 23 42 / 0.08)",
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {selectedIds.map((id) => {
            const stock = selected.find((row) => row.stock_id === id);
            return (
              <Line
                key={id}
                dataKey={id}
                name={stock ? `${stock.stock_id} ${stock.name}` : id}
                stroke={colorMap[id]}
                dot={false}
                strokeWidth={2}
                connectNulls
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function RadarSection({
  selected,
  colors,
}: {
  selected: RankingRow[];
  colors: string[];
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
      <h3 className="text-sm font-bold text-slate-700 mb-1">因子雷達圖（最新日）</h3>
      <p className="text-xs text-slate-400 mb-3">報酬與健康分數越高越好，波動率與回撤已反向處理</p>
      <FactorRadarChart stocks={selected} colors={colors} />
    </div>
  );
}

function MetricsTable({
  selected,
  colorMap,
}: {
  selected: RankingRow[];
  colorMap: Record<string, string>;
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
      <h3 className="text-sm font-bold text-slate-700 mb-3">關鍵指標比較（最新日）</h3>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-sm">
          <thead>
            <tr className="bg-slate-50 text-xs text-slate-500">
              <th className="py-2 px-3 text-left">股票</th>
              <th className="py-2 px-3 text-right">20日報酬</th>
              <th className="py-2 px-3 text-right">60日報酬</th>
              <th className="py-2 px-3 text-right">健康分數</th>
              <th className="py-2 px-3 text-right">波動率</th>
              <th className="py-2 px-3 text-right">最大回撤</th>
              <th className="py-2 px-3 text-right">成交量倍率</th>
            </tr>
          </thead>
          <tbody>
            {selected.map((row) => (
              <tr key={row.stock_id} className="border-t border-slate-50">
                <td className="py-2.5 px-3">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ background: colorMap[row.stock_id] }}
                    />
                    <span className="font-mono text-xs text-slate-500">{row.stock_id}</span>
                    <span className="font-semibold text-slate-800">{row.name}</span>
                  </div>
                </td>
                <td className={cn(
                  "py-2.5 px-3 text-right font-bold text-xs",
                  (row.return_20d_pct ?? 0) >= 0 ? "text-green-600" : "text-red-500",
                )}>
                  {formatPct(row.return_20d_pct)}
                </td>
                <td className={cn(
                  "py-2.5 px-3 text-right font-bold text-xs",
                  (row.return_60d_pct ?? 0) >= 0 ? "text-green-600" : "text-red-500",
                )}>
                  {formatPct(row.return_60d_pct)}
                </td>
                <td className="py-2.5 px-3 text-right font-bold text-xs text-green-600">
                  {formatNum(row.health_score)}
                </td>
                <td className="py-2.5 px-3 text-right font-bold text-xs text-blue-600">
                  {formatPct(row.volatility_pct)}
                </td>
                <td className="py-2.5 px-3 text-right font-bold text-xs text-red-500">
                  {formatPct(row.max_drawdown_pct)}
                </td>
                <td className="py-2.5 px-3 text-right font-bold text-xs text-amber-500">
                  {formatNum(row.volume_ratio, 2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RankingList({
  selected,
  colorMap,
}: {
  selected: RankingRow[];
  colorMap: Record<string, string>;
}) {
  const sorted = [...selected].sort((a, b) => (b.health_score ?? 0) - (a.health_score ?? 0));

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
      <h3 className="text-sm font-bold text-slate-700 mb-3">綜合名次（健康分數排序）</h3>
      <div className="space-y-2">
        {sorted.map((row, index) => (
          <div key={row.stock_id} className="flex items-center gap-3">
            <div className="text-lg font-black text-slate-300 w-6 text-center">{index + 1}</div>
            <div
              className="w-2.5 h-2.5 rounded-full shrink-0"
              style={{ background: colorMap[row.stock_id] }}
            />
            <div className="flex-1 text-sm font-semibold text-slate-700">
              {row.stock_id} {row.name}
            </div>
            <div className="w-32 h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${row.health_score ?? 0}%`,
                  background: colorMap[row.stock_id],
                }}
              />
            </div>
            <div className="text-sm font-black text-slate-800 w-12 text-right">
              {row.health_score?.toFixed(1)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ComparePage() {
  const [selectedIds, setSelectedIds] = useState<string[]>(DEFAULT_SELECTED);

  const { data: allStocks = [] } = useQuery({
    queryKey: ["stocks-list"],
    queryFn: () => api.listStocks(),
  });

  const { data: allFactors = [], isLoading } = useQuery({
    queryKey: ["rankings-compare"],
    queryFn: () => api.rankings({ limit: 30 }),
  });

  const selected = useMemo(
    () => selectedIds
      .map((id) => allFactors.find((row) => row.stock_id === id))
      .filter((row): row is RankingRow => Boolean(row)),
    [allFactors, selectedIds],
  );

  const colorMap = useMemo(
    () => Object.fromEntries(selectedIds.map((id, index) => [id, PALETTE[index]])),
    [selectedIds],
  );
  const selectedColors = selectedIds.map((id) => colorMap[id]);

  const priceQueries = useQueries({
    queries: selectedIds.map((id) => ({
      queryKey: ["prices", id],
      queryFn: () => api.stockPrices(id, 365),
      enabled: selectedIds.length >= 2,
    })),
  });

  const priceData = useMemo(
    () => Object.fromEntries(selectedIds.map((id, index) => [id, priceQueries[index]?.data ?? []])),
    [priceQueries, selectedIds],
  );

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">股票比較</h1>
          <p className="text-sm text-slate-400 mt-1">
            選擇 2-5 檔股票，比較報酬、風險與量能表現
          </p>
        </div>
        <button
          onClick={() => setSelectedIds([])}
          className="text-xs text-slate-400 hover:text-slate-600 border border-slate-200 rounded-lg px-3 py-1.5"
        >
          清除全部
        </button>
      </div>

      <StockSelector
        allStocks={allStocks}
        selectedIds={selectedIds}
        onChange={setSelectedIds}
        colorMap={colorMap}
      />

      {selectedIds.length < 2 && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-700">
          請至少選擇 <strong>2 檔</strong>股票，最多 5 檔。
        </div>
      )}

      {isLoading && selectedIds.length >= 2 && (
        <div className="py-16 text-center text-sm text-slate-400">載入股票資料中...</div>
      )}

      {!isLoading && selectedIds.length >= 2 && (
        <>
          <SummaryCards selected={selected} colorMap={colorMap} />

          <div className="grid grid-cols-[1.1fr_0.9fr] gap-4">
            <TrendChart
              selectedIds={selectedIds}
              selected={selected}
              priceData={priceData}
              colorMap={colorMap}
            />
            <RadarSection selected={selected} colors={selectedColors} />
          </div>

          <MetricsTable selected={selected} colorMap={colorMap} />
          <RankingList selected={selected} colorMap={colorMap} />
        </>
      )}
    </div>
  );
}
