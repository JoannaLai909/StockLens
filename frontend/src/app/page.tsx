import { Users, Calendar, Heart, TrendingUp } from "lucide-react";
import { api } from "@/lib/api";
import { KpiCard, Card } from "@/components/ui/Card";
import { fmtPct, fmtNum } from "@/lib/utils";
import HealthScatterChart from "@/components/charts/ScatterChart";
import IndustryBarChart from "@/components/charts/IndustryBarChart";
import RankingSection from "./RankingSection";
import dayjs from "dayjs";

// 首頁會在執行時向 FastAPI 抓資料；不要在 Docker build 階段預先抓 API。
export const dynamic = "force-dynamic";
export const revalidate = 60;

export default async function DashboardPage() {
  const [overview, scatter, industry] = await Promise.all([
    api.marketOverview(true),
    api.healthScatter(true),
    api.industryAvg(true),
  ]);

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-black text-slate-900">StockLens 台股量化分析</h1>
          <p className="text-sm text-slate-400 mt-1">整合股價資料、量化因子與互動式圖表，快速掌握股票表現與風險</p>
        </div>
        <div className="text-xs text-slate-400 pt-1 whitespace-nowrap">
          最後更新：{dayjs(overview.latest_date).format("YYYY-MM-DD")}
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <KpiCard icon={<Users size={18} />} label="追蹤股票數"
                 value={`${overview.stock_count}`} sub="檔股票" tone="blue" />
        <KpiCard icon={<Calendar size={18} />} label="最新資料日期"
                 value={dayjs(overview.latest_date).format("YYYY-MM-DD")} sub="每日更新" tone="blue" />
        <KpiCard icon={<Heart size={18} />} label="平均健康分數"
                 value={fmtNum(overview.avg_health_score)} sub="/ 100" tone="green" />
        <KpiCard icon={<TrendingUp size={18} />} label="20日報酬最佳"
                 value={overview.best_return_id} sub={overview.best_return_name}
                 tone="green" badge={fmtPct(overview.best_return_pct, 1)} />
      </div>

      <div className="grid grid-cols-[1fr_1.25fr] gap-4">
        <Card title="市場健康分布"><HealthScatterChart data={scatter} /></Card>
        <Card title="產業平均健康分數"><IndustryBarChart data={industry} /></Card>
      </div>

      <RankingSection />
    </div>
  );
}
