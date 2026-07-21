import { AlertTriangle, CalendarDays, CheckCircle2, Database, LineChart, ShieldCheck } from "lucide-react";
import dayjs from "dayjs";
import { api, type DataHealthCategory, type StaleStock } from "@/lib/api";
import { Card, KpiCard } from "@/components/ui/Card";
import { CATEGORY_LABELS, cn, fmtNum } from "@/lib/utils";

export const dynamic = "force-dynamic";
export const revalidate = 60;

const STATUS_LABELS: Record<StaleStock["status"], string> = {
  missing_price: "缺股價",
  missing_factor: "缺因子",
  stale_price: "股價落後",
  stale_factor: "因子落後",
  ok: "正常",
};

const QUALITY_LABELS = [
  ["missing_return_20d", "20日報酬"],
  ["missing_return_60d", "60日報酬"],
  ["missing_volatility_20d", "波動率"],
  ["missing_max_drawdown", "最大回撤"],
  ["missing_volume_ratio", "成交量倍率"],
  ["missing_health_score", "健康分數"],
  ["missing_cluster_label", "K-means 分群"],
] as const;

function dateText(date: string | null) {
  return date ? dayjs(date).format("YYYY-MM-DD") : "-";
}

function healthTone(priceStale: number, factorStale: number) {
  if (priceStale === 0 && factorStale === 0) {
    return {
      label: "資料同步正常",
      color: "text-green-600",
      bg: "bg-green-50",
      icon: <CheckCircle2 size={18} />,
    };
  }

  return {
    label: "需要補資料",
    color: "text-amber-600",
    bg: "bg-amber-50",
    icon: <AlertTriangle size={18} />,
  };
}

function CoverageBar({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "blue" | "green";
}) {
  const color = tone === "green" ? "bg-green-500" : "bg-blue-500";

  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-xs">
        <span className="font-bold text-slate-500">{label}</span>
        <span className="font-black text-slate-800">{fmtNum(value, 1)}%</span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
        <div className={cn("h-full rounded-full", color)} style={{ width: `${Math.min(100, value ?? 0)}%` }} />
      </div>
    </div>
  );
}

function CategoryCoverage({ rows }: { rows: DataHealthCategory[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] text-sm">
        <thead>
          <tr className="bg-slate-50 text-xs text-slate-500">
            <th className="px-3 py-2 text-left">產業</th>
            <th className="px-3 py-2 text-right">股票數</th>
            <th className="px-3 py-2 text-right">股價覆蓋</th>
            <th className="px-3 py-2 text-right">因子覆蓋</th>
            <th className="px-3 py-2 text-right">平均股價天數</th>
            <th className="px-3 py-2 text-right">平均因子天數</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const pricePct = row.stock_count ? (row.price_stock_count / row.stock_count) * 100 : 0;
            const factorPct = row.stock_count ? (row.factor_stock_count / row.stock_count) * 100 : 0;

            return (
              <tr key={row.category} className="border-t border-slate-50">
                <td className="px-3 py-3 font-semibold text-slate-800">
                  {CATEGORY_LABELS[row.category] ?? row.category}
                </td>
                <td className="px-3 py-3 text-right font-bold text-slate-600">{row.stock_count}</td>
                <td className="px-3 py-3 text-right">
                  <span className="font-black text-blue-600">{fmtNum(pricePct, 1)}%</span>
                  <span className="ml-1 text-xs text-slate-400">({row.price_stock_count})</span>
                </td>
                <td className="px-3 py-3 text-right">
                  <span className="font-black text-green-600">{fmtNum(factorPct, 1)}%</span>
                  <span className="ml-1 text-xs text-slate-400">({row.factor_stock_count})</span>
                </td>
                <td className="px-3 py-3 text-right font-bold text-slate-600">{fmtNum(row.avg_price_days, 1)}</td>
                <td className="px-3 py-3 text-right font-bold text-slate-600">{fmtNum(row.avg_factor_days, 1)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function StaleStockTable({ rows }: { rows: StaleStock[] }) {
  if (!rows.length) {
    return (
      <div className="flex items-center justify-center rounded-xl bg-green-50 py-12 text-sm font-semibold text-green-700">
        目前沒有落後或缺漏的股票資料
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[820px] text-sm">
        <thead>
          <tr className="bg-slate-50 text-xs text-slate-500">
            <th className="px-3 py-2 text-left">股票</th>
            <th className="px-3 py-2 text-left">產業</th>
            <th className="px-3 py-2 text-right">狀態</th>
            <th className="px-3 py-2 text-right">最新股價日</th>
            <th className="px-3 py-2 text-right">最新因子日</th>
            <th className="px-3 py-2 text-right">股價天數</th>
            <th className="px-3 py-2 text-right">因子天數</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.stock_id} className="border-t border-slate-50">
              <td className="px-3 py-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-slate-400">{row.stock_id}</span>
                  <span className="font-semibold text-slate-800">{row.name}</span>
                </div>
              </td>
              <td className="px-3 py-3 text-slate-500">{CATEGORY_LABELS[row.category] ?? row.category}</td>
              <td className="px-3 py-3 text-right">
                <span className="rounded-md bg-amber-50 px-2 py-1 text-xs font-black text-amber-600">
                  {STATUS_LABELS[row.status]}
                </span>
              </td>
              <td className="px-3 py-3 text-right font-bold text-slate-600">{dateText(row.latest_price_date)}</td>
              <td className="px-3 py-3 text-right font-bold text-slate-600">{dateText(row.latest_factor_date)}</td>
              <td className="px-3 py-3 text-right font-bold text-slate-600">{row.price_days}</td>
              <td className="px-3 py-3 text-right font-bold text-slate-600">{row.factor_days}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default async function HealthPage() {
  const data = await api.dataHealth(true);
  const { summary, by_category: byCategory, stale_stocks: staleStocks, factor_quality: factorQuality } = data;
  const tone = healthTone(summary.stale_price_count, summary.stale_factor_count);
  const missingFactorFields = QUALITY_LABELS.reduce(
    (total, [key]) => total + (factorQuality[key] ?? 0),
    0,
  );

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">資料健康</h1>
          <p className="mt-1 text-sm text-slate-400">檢查股價、量化因子與分群資料是否完整同步</p>
        </div>
        <div className={cn("flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-black", tone.bg, tone.color)}>
          {tone.icon}
          {tone.label}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          icon={<Database size={18} />}
          label="資料列數"
          value={summary.price_rows.toLocaleString()}
          sub={`${summary.factor_rows.toLocaleString()} 筆因子`}
          tone="blue"
        />
        <KpiCard
          icon={<LineChart size={18} />}
          label="追蹤覆蓋率"
          value={`${fmtNum(summary.price_coverage_pct, 1)}%`}
          sub={`${summary.stock_count} 檔股票`}
          tone="green"
        />
        <KpiCard
          icon={<CalendarDays size={18} />}
          label="最新股價日"
          value={dateText(summary.latest_price_date)}
          sub={`起始 ${dateText(summary.earliest_price_date)}`}
          tone="blue"
        />
        <KpiCard
          icon={<ShieldCheck size={18} />}
          label="最新因子日"
          value={dateText(summary.latest_factor_date)}
          sub={`缺漏欄位 ${missingFactorFields}`}
          tone="green"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <Card title="整體覆蓋率">
          <div className="space-y-5">
            <CoverageBar label="股價資料覆蓋" value={summary.price_coverage_pct} tone="blue" />
            <CoverageBar label="因子資料覆蓋" value={summary.factor_coverage_pct} tone="green" />
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div className="rounded-xl bg-slate-50 p-3">
                <div className="text-xs font-bold text-slate-400">股價落後股票</div>
                <div className="mt-1 text-2xl font-black text-amber-600">{summary.stale_price_count}</div>
              </div>
              <div className="rounded-xl bg-slate-50 p-3">
                <div className="text-xs font-bold text-slate-400">因子落後股票</div>
                <div className="mt-1 text-2xl font-black text-amber-600">{summary.stale_factor_count}</div>
              </div>
              <div className="rounded-xl bg-slate-50 p-3">
                <div className="text-xs font-bold text-slate-400">平均股價天數</div>
                <div className="mt-1 text-2xl font-black text-blue-600">{fmtNum(summary.avg_price_days, 1)}</div>
              </div>
              <div className="rounded-xl bg-slate-50 p-3">
                <div className="text-xs font-bold text-slate-400">平均因子天數</div>
                <div className="mt-1 text-2xl font-black text-green-600">{fmtNum(summary.avg_factor_days, 1)}</div>
              </div>
            </div>
          </div>
        </Card>

        <Card title="最新因子欄位缺漏">
          <div className="grid grid-cols-2 gap-2 md:grid-cols-4 xl:grid-cols-7">
            {QUALITY_LABELS.map(([key, label]) => {
              const value = factorQuality[key] ?? 0;

              return (
                <div key={key} className="rounded-xl bg-slate-50 px-2 py-3 text-center">
                  <div className={cn("text-lg font-black", value ? "text-amber-600" : "text-green-600")}>
                    {value}
                  </div>
                  <div className="mt-1 text-[11px] font-bold leading-tight text-slate-400">{label}</div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      <Card title="產業資料覆蓋">
        <CategoryCoverage rows={byCategory} />
      </Card>

      <Card title="需要處理的股票">
        <StaleStockTable rows={staleStocks} />
      </Card>
    </div>
  );
}
