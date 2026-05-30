const SERVER_BASE =
  process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const CLIENT_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function base(isServer = false) {
  return isServer ? SERVER_BASE : CLIENT_BASE;
}

async function get<T>(path: string, isServer = false): Promise<T> {
  const res = await fetch(`${base(isServer)}${path}`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${path}`);
  return res.json();
}

export interface MarketOverview {
  stock_count: number;
  latest_date: string;
  avg_health_score: number;
  best_return_id: string;
  best_return_name: string;
  best_return_pct: number;
}

export interface ScatterPoint {
  stock_id: string;
  name: string;
  category: string;
  return_20d_pct: number;
  volatility_pct: number;
  health_score: number;
}

export interface IndustryAvg {
  category: string;
  stock_count: number;
  avg_return_20d_pct: number;
  avg_return_60d_pct: number;
  avg_health_score: number;
}

export interface RankingRow {
  stock_id: string;
  name: string;
  category: string;
  return_20d_pct: number;
  return_60d_pct: number;
  volatility_pct: number;
  max_drawdown_pct: number;
  volume_ratio: number;
  health_score: number;
  cluster_label: number | null;
  latest_close: number;
}

export interface StockInfo {
  stock_id: string;
  name: string;
  category: string;
  market: string;
  date: string;
  latest_close: number;
  return_20d_pct: number;
  return_60d_pct: number;
  volatility_pct: number;
  max_drawdown_pct: number;
  volume_ratio: number;
  health_score: number;
  cluster_label: number | null;
}

export interface PriceBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface StockBasic {
  stock_id: string;
  name: string;
  category: string;
  market: string;
}

export const api = {
  marketOverview:  (s=false) => get<MarketOverview>("/api/market/overview", s),
  healthScatter:   (s=false) => get<ScatterPoint[]>("/api/market/health-scatter", s),
  industryAvg:     (s=false) => get<IndustryAvg[]>("/api/market/industry-avg", s),

  rankings: (params: {
    metric?: string; order?: string; category?: string; limit?: number;
  } = {}, s=false) => {
    const q = new URLSearchParams({
      metric:   params.metric   ?? "return_20d",
      order:    params.order    ?? "desc",
      category: params.category ?? "all",
      limit:    String(params.limit ?? 30),
    });
    return get<RankingRow[]>(`/api/rankings?${q}`, s);
  },

  listStocks:  (s=false) => get<StockBasic[]>("/api/stocks", s),
  stockInfo:   (id: string, s=false) => get<StockInfo>(`/api/stocks/${id}`, s),
  stockPrices: (id: string, days=126, s=false) =>
    get<PriceBar[]>(`/api/stocks/${id}/prices?days=${days}`, s),
};
