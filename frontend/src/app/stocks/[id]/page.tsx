import { api } from "@/lib/api";
import { notFound } from "next/navigation";
import {
  fmtPct, fmtNum, CATEGORY_LABELS,
  healthColor, healthLabel, pctColor, riskLevel, riskRatio, cn,
} from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import CandleChart from "@/components/charts/CandleChart";
import PriceRangeTabs from "./PriceRangeTabs";
import DownloadReportButton from "./DownloadReportButton";
import dayjs from "dayjs";

export const revalidate = 60;

export default async function StockDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ days?: string }>;
}) {
  const { id } = await params;
  const { days: daysParam } = await searchParams;
  const days = Number(daysParam ?? 126);

  const [info, prices] = await Promise.all([
    api.stockInfo(id, true).catch((err) => {
      console.error("stockInfo error:", err);
      return null;
    }),
    fetch(`${process.env.API_INTERNAL_URL ?? "http://localhost:8000"}/api/stocks/${id}/prices-with-ma?days=${days}`)
      .then((r) => r.json())
      .catch((err) => {
        console.error("prices-with-ma error:", err);
        return [];
      }),
  ]);

  console.log("stock info =", info);

  if (!info) notFound();

  const risk = riskLevel(info.volatility_pct, info.max_drawdown_pct, info.health_score);
  const ratio = riskRatio(info.volume_ratio, info.max_drawdown_pct);
  const metrics = [
    { label: "20日報酬", value: fmtPct(info.return_20d_pct), color: pctColor(info.return_20d_pct) },
    { label: "60日報酬", value: fmtPct(info.return_60d_pct), color: pctColor(info.return_60d_pct) },
    { label: "波動率", value: `${info.volatility_pct?.toFixed(2)}%`, color: "text-blue-600" },
    { label: "最大回撤", value: fmtPct(info.max_drawdown_pct), color: "text-red-500" },
    { label: "成交量倍率", value: fmtNum(info.volume_ratio, 2), color: "text-amber-500" },
    { label: "健康分數", value: `${fmtNum(info.health_score)} / 100`, color: "text-green-600" },
  ];

  return (
    <div className="space-y-5">

      {/* 頁首：股票名稱 + 最新收盤 */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono bg-blue-50 text-blue-600
                             px-2 py-0.5 rounded-md font-bold">{info.stock_id}</span>
            <span className="text-xs text-slate-400">
              {CATEGORY_LABELS[info.category] ?? info.category} · {info.market}
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900">{info.name}</h1>
        </div>
        <div className="text-right">
          <div className="text-3xl font-black text-slate-900">{info.latest_close?.toLocaleString()}</div>
          <div className="text-xs text-slate-400 mt-0.5">資料日期：{dayjs(info.date).format("YYYY-MM-DD")}</div>
          <div className="mt-3">
            <DownloadReportButton info={info} prices={prices} />
          </div>
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

      {/* K 線圖 + 成交量 */}
      <Card title="股價走勢（K 線圖）">
        <PriceRangeTabs currentDays={days} stockId={id} />
        <CandleChart data={prices} />
      </Card>

      {/* 量化因子表 */}
      <div className="grid grid-cols-3 gap-4">
        {/* 左：6 個指標卡 */}
        <div className="col-span-2">
          <Card title={`量化因子表（${dayjs(info.date).format("YYYY-MM-DD")}）`}>
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "20日報酬率", value: fmtPct(info.return_20d_pct),
                  color: pctColor(info.return_20d_pct) },
                { label: "60日報酬率", value: fmtPct(info.return_60d_pct),
                  color: pctColor(info.return_60d_pct) },
                { label: "波動率",     value: `${info.volatility_pct?.toFixed(2)}%`,
                  color: "text-blue-600" },
                { label: "最大回撤",   value: fmtPct(info.max_drawdown_pct),
                  color: "text-red-500" },
                { label: "成交量倍率", value: fmtNum(info.volume_ratio, 2),
                  color: "text-amber-500" },
                { label: "健康分數",   value: `${fmtNum(info.health_score)} / 100`,
                  color: "text-green-600" },
              ].map(({ label, value, color }) => (
                <div key={label} className="bg-slate-50 rounded-xl p-3 text-center">
                  <div className="text-xs text-slate-400 font-semibold mb-1.5">{label}</div>
                  <div className={cn("text-base font-black", color)}>{value}</div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* 右：風險評估 */}
        <Card title="風險評估">
          <div className="space-y-3">
            <RiskRow label="波動率等級" value={risk.vol} />
            <RiskRow label="最大回撤等級" value={risk.dd}
                     good={risk.dd === "低"} />
            <div className="pt-2 border-t border-slate-100">
              <div className="text-xs text-slate-400 mb-1">風險報酬比</div>
              <div className="text-xl font-black text-slate-800">{ratio}</div>
              <a href="#" className="text-xs text-blue-500 hover:underline mt-0.5 block">
                風險報酬比計算說明
              </a>
            </div>
          </div>
        </Card>
        <Card title="K-means 分群">
          <div className="space-y-4">
            <div>
              <div className="text-xs font-bold text-slate-400 mb-1">
                {info.cluster_label !== null ? `Cluster ${info.cluster_label}` : "尚未分群"}
                {info.cluster_stock_count ? ` · 同群 ${info.cluster_stock_count} 檔` : ""}
              </div>
              <div className="text-2xl font-black text-blue-600">
                {info.cluster_name ?? "尚未分類"}
              </div>
              <p className="text-sm text-slate-500 mt-2 leading-relaxed">
                {info.cluster_description}
              </p>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-xl bg-slate-50 px-3 py-2">
                <div className="text-[11px] font-bold text-slate-400">群組健康</div>
                <div className="text-sm font-black text-green-600">
                  {info.cluster_avg_health_score !== null ? fmtNum(info.cluster_avg_health_score, 1) : "—"}
                </div>
              </div>
              <div className="rounded-xl bg-slate-50 px-3 py-2">
                <div className="text-[11px] font-bold text-slate-400">60日報酬</div>
                <div className="text-sm font-black text-blue-600">
                  {info.cluster_avg_return_60d_pct !== null ? fmtPct(info.cluster_avg_return_60d_pct) : "—"}
                </div>
              </div>
              <div className="rounded-xl bg-slate-50 px-3 py-2">
                <div className="text-[11px] font-bold text-slate-400">群組波動</div>
                <div className="text-sm font-black text-amber-600">
                  {info.cluster_avg_volatility_pct !== null ? `${fmtNum(info.cluster_avg_volatility_pct, 2)}%` : "—"}
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

    </div>
  );
}

function RiskRow({ label, value, good }: {
  label: string; value: string; good?: boolean;
}) {
  const color = value === "低" ? "text-green-600"
    : value === "中等" ? "text-amber-500"
    : value === "高" ? "text-red-500"
    : "text-slate-400";
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-slate-400">{label}</span>
      <span className={cn("text-sm font-bold", color)}>{value}</span>
    </div>
  );
}
