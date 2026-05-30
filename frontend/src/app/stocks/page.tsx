import Link from "next/link";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { CATEGORY_LABELS } from "@/lib/utils";
import { ChevronRight } from "lucide-react";

// 股票清單依賴 FastAPI；避免 Next.js build 時因 API 尚未啟動而失敗。
export const dynamic = "force-dynamic";
export const revalidate = 60;

export default async function StocksPage() {
  const stocks = await api.listStocks(true);
  const grouped = stocks.reduce<Record<string, typeof stocks>>((acc, s) => {
    (acc[s.category] ??= []).push(s);
    return acc;
  }, {});
  const order = ["semiconductor","financial","etf","electronics","shipping","telecom","other"];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-black text-slate-900">個股分析</h1>
        <p className="text-sm text-slate-400 mt-1">選擇股票查看完整量化因子與走勢分析</p>
      </div>
      {order.filter(c => grouped[c]).map(cat => (
        <Card key={cat} title={CATEGORY_LABELS[cat] ?? cat}>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
            {grouped[cat].map(s => (
              <Link key={s.stock_id} href={`/stocks/${s.stock_id}`}
                className="flex items-center justify-between px-3 py-2.5 rounded-xl
                           border border-slate-100 hover:border-blue-200 hover:bg-blue-50/50
                           transition-colors group">
                <div>
                  <div className="text-xs font-mono text-slate-400">{s.stock_id}</div>
                  <div className="text-sm font-semibold text-slate-700 group-hover:text-blue-600">{s.name}</div>
                </div>
                <ChevronRight size={14} className="text-slate-300 group-hover:text-blue-600" />
              </Link>
            ))}
          </div>
        </Card>
      ))}
    </div>
  );
}
