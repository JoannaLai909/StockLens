"use client";

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell,
} from "recharts";
import type { PriceBar } from "@/lib/api";
import dayjs from "dayjs";

export default function PriceChart({ data, showVolume = true }: { data: PriceBar[]; showVolume?: boolean }) {
  if (!data.length) return <div className="text-sm text-slate-400 py-8 text-center">無價格資料</div>;
  return (
    <div className="space-y-1">
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#0f6fe8" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#0f6fe8" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" tickFormatter={(d) => dayjs(d).format("MM/DD")}
                 tick={{ fontSize: 11, fill: "#94a3b8" }} tickLine={false} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} tickLine={false}
                 domain={["auto", "auto"]} width={60} tickFormatter={(v) => v.toLocaleString()} />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0].payload as PriceBar;
              return (
                <div className="bg-white border border-slate-200 rounded-xl shadow-lg p-3 text-xs">
                  <div className="font-bold text-slate-600 mb-1">{dayjs(d.date).format("YYYY-MM-DD")}</div>
                  <div className="grid grid-cols-2 gap-x-3 gap-y-0.5">
                    <span className="text-slate-400">開盤</span><span className="font-semibold">{d.open}</span>
                    <span className="text-slate-400">最高</span><span className="font-semibold text-green-600">{d.high}</span>
                    <span className="text-slate-400">最低</span><span className="font-semibold text-red-500">{d.low}</span>
                    <span className="text-slate-400">收盤</span><span className="font-semibold">{d.close}</span>
                  </div>
                </div>
              );
            }}
          />
          <Area type="monotone" dataKey="close" stroke="#0f6fe8" strokeWidth={2}
                fill="url(#priceGrad)" dot={false} activeDot={{ r: 4 }} />
        </AreaChart>
      </ResponsiveContainer>
      {showVolume && (
        <ResponsiveContainer width="100%" height={70}>
          <BarChart data={data} margin={{ top: 0, right: 4, left: 0, bottom: 0 }}>
            <YAxis tick={false} axisLine={false} tickLine={false} width={60} />
            <XAxis dataKey="date" hide />
            <Bar dataKey="volume" maxBarSize={6} radius={[2, 2, 0, 0]}>
              {data.map((d, i) => {
                const prev = data[i - 1];
                const up = !prev || d.close >= prev.close;
                return <Cell key={d.date} fill={up ? "#149b55" : "#ef4444"} fillOpacity={0.7} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
