import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { notFound } from "next/navigation";
import { fmtPct, fmtNum, CATEGORY_LABELS, healthColor, healthLabel, pctColor, cn } from "@/lib/utils";
import PriceChart from "@/components/charts/PriceChart";
import PriceRangeTabs from "./PriceRangeTabs";
import dayjs from "dayjs";

// 個股頁在執行時才依股票代號抓 API 資料。
export const dynamic = "force-dynamic";
export const revalidate = 60;

export default async function StockDetailPage({
  params, searchParams,
}: {
  params: { id: string };
  searchParams: { days?: string };
}) {
  const days = Number(searchParams.days ?? 126);
  const id   = params.id;

  const [info, prices] = await Promise.all([
    api.stockInfo(id, true).catch(() => null),
    api.stockPrices(id, days, true).catch(() => []),
  ]);
  if (!info) notFound();

  const metrics = [
    { label: "20日報酬率", value: fmtPct(info.return_20d_pct),             color: pctColor(info.return_20d_pct) },
    { label: "60日報酬率", value: fmtPct(info.return_60d_pct),             color: pctColor(info.return_60d_pct) },
    { label: "波動率",     value: `${info.volatility_pct?.toFixed(2)}%`,   color: "text-blue-600"  },
    { label: "最大回撤",   value: fmtPct(info.max_drawdown_pct),           color: "text-red-500"   },
    { label: "成交量倍率", value: fmtNum(info.volume_ratio, 2),            color: "text-amber-500" },
    { label: "健康分數",   value: `${fmtNum(info.health_score)} / 100`,    color: "text-green-600" },
  ];

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono bg-blue-50 text-blue-600 px-2 py-0.5 rounded-md font-bold">
              {info.stock_id}
            </span>
            <span className="text-xs text-slate-400">
              {CATEGORY_LABELS[info.category] ?? info.category} · {info.market}
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900">{info.name}</h1>
        </div>
        <div className="text-right">
          <div className="text-3xl font-black text-slate-900">{info.latest_close?.toLocaleString()}</div>
          <div className="text-xs text-slate-400 mt-0.5">資料日期：{dayjs(info.date).format("YYYY-MM-DD")}</div>
        </div>
      </div>

      <div className="grid grid-cols-6 gap-3">
        {metrics.map(({ label, value, color }) => (
          <div key={label} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-3.5 text-center">
            <div className="text-xs text-slate-400 font-semibold mb-1.5">{label}</div>
            <div className={cn("text-base font-black", color)}>{value}</div>
          </div>
        ))}
      </div>

      <Card title="收盤價走勢 ＋ 成交量">
        <PriceRangeTabs currentDays={days} stockId={id} />
        <PriceChart data={prices} showVolume />
      </Card>

      <div className="grid grid-cols-2 gap-4">
        <Card title="健康狀態">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-black text-white"
                 style={{ background: healthColor(info.health_score) }}>
              {fmtNum(info.health_score, 0)}
            </div>
            <div>
              <div className="text-base font-bold text-slate-800">{healthLabel(info.health_score)}</div>
              <div className="text-sm text-slate-400 mt-1 leading-relaxed">
                請搭配報酬率、波動率、最大回撤與<br />成交量變化一起判斷。
              </div>
            </div>
          </div>
        </Card>
        <Card title="K-means 分群">
          <div className="flex items-center gap-4">
            <div className="text-3xl font-black text-blue-600">
              {info.cluster_label !== null ? `Cluster ${info.cluster_label}` : "—"}
            </div>
            <div className="text-sm text-slate-400 leading-relaxed">
              依 health_score、報酬率、波動率等<br />6 個因子做 K-means 分群（3 群）。
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
