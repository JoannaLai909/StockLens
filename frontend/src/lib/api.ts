const SERVER_BASE =
  process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8002";

const CLIENT_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8002";

function base(isServer = false) {
  return isServer ? SERVER_BASE : CLIENT_BASE;
}

async function get<T>(path: string, isServer = false): Promise<T> {
  const res = await fetch(`${base(isServer)}${path}`, {
    cache: "no-store",
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
  cluster_name: string | null;
  cluster_description: string;
  cluster_stock_count: number | null;
  cluster_avg_health_score: number | null;
  cluster_avg_return_60d_pct: number | null;
  cluster_avg_volatility_pct: number | null;
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

export interface DataHealthSummary {
  stock_count: number;
  price_rows: number;
  factor_rows: number;
  earliest_price_date: string | null;
  latest_price_date: string | null;
  earliest_factor_date: string | null;
  latest_factor_date: string | null;
  price_coverage_pct: number;
  factor_coverage_pct: number;
  stale_price_count: number;
  stale_factor_count: number;
  avg_price_days: number;
  avg_factor_days: number;
}

export interface DataHealthCategory {
  category: string;
  stock_count: number;
  price_stock_count: number;
  factor_stock_count: number;
  avg_price_days: number;
  avg_factor_days: number;
}

export interface StaleStock {
  stock_id: string;
  name: string;
  category: string;
  latest_price_date: string | null;
  latest_factor_date: string | null;
  price_days: number;
  factor_days: number;
  status: "missing_price" | "missing_factor" | "stale_price" | "stale_factor" | "ok";
}

export interface FactorQuality {
  missing_return_20d: number;
  missing_return_60d: number;
  missing_volatility_20d: number;
  missing_max_drawdown: number;
  missing_volume_ratio: number;
  missing_health_score: number;
  missing_cluster_label: number;
}

export interface DataHealth {
  summary: DataHealthSummary;
  by_category: DataHealthCategory[];
  stale_stocks: StaleStock[];
  factor_quality: FactorQuality;
}

export const api = {
  marketOverview:  (s=false) => get<MarketOverview>("/api/market/overview", s),
  healthScatter:   (s=false) => get<ScatterPoint[]>("/api/market/health-scatter", s),
  industryAvg:     (s=false) => get<IndustryAvg[]>("/api/market/industry-avg", s),
  dataHealth:      (s=false) => get<DataHealth>("/api/data-health", s),

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
