"use client";

import {
  ComposedChart, Bar, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, Legend,
} from "recharts";
import dayjs from "dayjs";

interface PriceWithMA {
  date: string;
  open: number; high: number; low: number; close: number;
  volume: number; trade_value: number;
  ma5: number | null; ma20: number | null; ma60: number | null;
}

export default function CandleChart({ data }: { data: PriceWithMA[] }) {
  return (
    <div>
      {/* K 線圖 */}
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date"
                 tickFormatter={d => dayjs(d).format("MM/DD")}
                 tick={{ fontSize: 11, fill: "#94a3b8" }} tickLine={false}
                 interval="preserveStartEnd" />
          <YAxis domain={["auto","auto"]} tick={{ fontSize: 11, fill: "#94a3b8" }}
                 tickLine={false} width={60}
                 tickFormatter={v => v.toLocaleString()} />
          <Tooltip content={<CandleTooltip />} />
          <Legend
            payload={[
              { value: "MA5",  type: "line", color: "#f59e0b" },
              { value: "MA20", type: "line", color: "#0f6fe8" },
              { value: "MA60", type: "line", color: "#8b5cf6" },
            ]}
          />

          {/* K 棒本體（用 Bar 模擬漲跌顏色）*/}
          <Bar dataKey="close" barSize={5}>
            {data.map(d => (
              <Cell key={d.date}
                    fill={d.close >= d.open ? "#149b55" : "#ef4444"} />
            ))}
          </Bar>

          {/* MA 線 */}
          <Line dataKey="ma5"  stroke="#f59e0b" dot={false} strokeWidth={1.2}
                connectNulls name="MA5" />
          <Line dataKey="ma20" stroke="#0f6fe8" dot={false} strokeWidth={1.2}
                connectNulls name="MA20" />
          <Line dataKey="ma60" stroke="#8b5cf6" dot={false} strokeWidth={1.2}
                connectNulls name="MA60" />
        </ComposedChart>
      </ResponsiveContainer>

      {/* 成交量圖 */}
      <ResponsiveContainer width="100%" height={80}>
        <ComposedChart data={data} margin={{ top: 0, right: 4, left: 0, bottom: 0 }}>
          <YAxis tick={false} axisLine={false} tickLine={false} width={60} />
          <XAxis dataKey="date" hide />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0].payload as PriceWithMA;
              const tv = d.trade_value ? (d.trade_value / 1e8).toFixed(2) : "—";
              return (
                <div className="bg-white border border-slate-200 rounded-lg shadow p-2 text-xs">
                  <div className="text-slate-400">{dayjs(d.date).format("MM/DD")}</div>
                  <div>成交量：{(d.volume / 1e6).toFixed(1)}M 股</div>
                  <div>成交金額：{tv} 億</div>
                </div>
              );
            }}
          />
          <Bar dataKey="volume" maxBarSize={6} radius={[2, 2, 0, 0]}>
            {data.map((d, i) => {
              const prev = data[i - 1];
              const up = !prev || d.close >= prev.close;
              return <Cell key={d.date} fill={up ? "#149b55" : "#ef4444"} fillOpacity={0.7} />;
            })}
          </Bar>
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function CandleTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload as PriceWithMA;
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-lg p-3 text-xs">
      <div className="font-bold text-slate-600 mb-1.5">
        {dayjs(d.date).format("YYYY-MM-DD")}
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
        <span className="text-slate-400">開盤</span>
        <span className="font-semibold">{d.open?.toLocaleString()}</span>
        <span className="text-slate-400">最高</span>
        <span className="font-semibold text-green-600">{d.high?.toLocaleString()}</span>
        <span className="text-slate-400">最低</span>
        <span className="font-semibold text-red-500">{d.low?.toLocaleString()}</span>
        <span className="text-slate-400">收盤</span>
        <span className="font-semibold">{d.close?.toLocaleString()}</span>
      </div>
      {d.ma5 && (
        <div className="mt-1.5 pt-1.5 border-t border-slate-100 grid grid-cols-2 gap-x-4 gap-y-0.5">
          <span className="text-amber-500">MA5</span>
          <span className="font-semibold">{d.ma5?.toLocaleString()}</span>
          <span className="text-blue-500">MA20</span>
          <span className="font-semibold">{d.ma20?.toLocaleString()}</span>
          <span className="text-purple-500">MA60</span>
          <span className="font-semibold">{d.ma60?.toLocaleString()}</span>
        </div>
      )}
    </div>
  );
}