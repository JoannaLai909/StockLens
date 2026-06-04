"use client";

import { Download } from "lucide-react";
import type { PriceBar, StockInfo } from "@/lib/api";
import { CATEGORY_LABELS, fmtNum, fmtPct } from "@/lib/utils";

function esc(value: unknown) {
  return String(value ?? "—")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function latestVolumeInYi(prices: PriceBar[]) {
  const latest = prices.at(-1);
  if (!latest?.volume) return "—";
  return fmtNum(latest.volume / 100_000_000, 2);
}

export default function DownloadReportButton({
  info,
  prices,
}: {
  info: StockInfo;
  prices: PriceBar[];
}) {
  const handleDownload = () => {
    const latestPrices = prices.slice(-8).reverse();
    const html = `
      <!doctype html>
      <html lang="zh-TW">
      <head>
        <meta charset="utf-8" />
        <title>StockLens ${esc(info.stock_id)} ${esc(info.name)} 分析報告</title>
        <style>
          * { box-sizing: border-box; }
          body {
            margin: 0;
            padding: 36px;
            color: #172033;
            font-family: -apple-system, BlinkMacSystemFont, "Noto Sans TC", "Microsoft JhengHei", sans-serif;
            background: #f5f8fc;
          }
          .page {
            max-width: 900px;
            margin: 0 auto;
            padding: 32px;
            background: white;
            border: 1px solid #dbe4f0;
            border-radius: 18px;
          }
          h1 { margin: 0; font-size: 28px; }
          .sub { margin-top: 8px; color: #64748b; font-size: 13px; }
          .meta {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e2e8f0;
          }
          .price { text-align: right; font-size: 28px; font-weight: 900; }
          .grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin: 22px 0;
          }
          .card {
            padding: 15px;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            background: #fbfdff;
          }
          .label { color: #64748b; font-size: 12px; font-weight: 700; }
          .value { margin-top: 6px; font-size: 20px; font-weight: 900; }
          .green { color: #149b55; }
          .red { color: #ef4444; }
          .blue { color: #0f6fe8; }
          .amber { color: #f59e0b; }
          h2 { margin: 26px 0 10px; font-size: 18px; }
          p { color: #475569; line-height: 1.7; }
          table { width: 100%; border-collapse: collapse; font-size: 13px; }
          th, td { padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: right; }
          th:first-child, td:first-child { text-align: left; }
          th { color: #64748b; background: #f8fafc; }
          .notice {
            margin-top: 28px;
            padding-top: 16px;
            border-top: 1px solid #e2e8f0;
            color: #94a3b8;
            font-size: 12px;
          }
          @media print {
            body { background: white; padding: 0; }
            .page { border: 0; border-radius: 0; max-width: none; }
          }
        </style>
      </head>
      <body>
        <main class="page">
          <section class="meta">
            <div>
              <h1>StockLens 個股分析報告</h1>
              <div class="sub">
                ${esc(info.stock_id)} ${esc(info.name)} ·
                ${esc(CATEGORY_LABELS[info.category] ?? info.category)} ·
                資料日期 ${esc(info.date)}
              </div>
            </div>
            <div>
              <div class="price">${esc(info.latest_close?.toLocaleString())}</div>
              <div class="sub">最新收盤價</div>
            </div>
          </section>

          <section class="grid">
            <div class="card"><div class="label">20日報酬率</div><div class="value green">${esc(fmtPct(info.return_20d_pct))}</div></div>
            <div class="card"><div class="label">60日報酬率</div><div class="value green">${esc(fmtPct(info.return_60d_pct))}</div></div>
            <div class="card"><div class="label">健康分數</div><div class="value green">${esc(fmtNum(info.health_score, 1))} / 100</div></div>
            <div class="card"><div class="label">波動率</div><div class="value blue">${esc(fmtNum(info.volatility_pct, 2))}%</div></div>
            <div class="card"><div class="label">最大回撤</div><div class="value red">${esc(fmtPct(info.max_drawdown_pct))}</div></div>
            <div class="card"><div class="label">成交量倍率</div><div class="value amber">${esc(fmtNum(info.volume_ratio, 2))}</div></div>
          </section>

          <h2>K-means 分群解讀</h2>
          <p>
            此股票目前歸類為 <strong>${esc(info.cluster_name ?? `Cluster ${info.cluster_label ?? "—"}`)}</strong>。
            ${esc(info.cluster_description)}
          </p>

          <section class="grid">
            <div class="card"><div class="label">同群股票數</div><div class="value">${esc(info.cluster_stock_count)}</div></div>
            <div class="card"><div class="label">群組平均健康分數</div><div class="value">${esc(info.cluster_avg_health_score)}</div></div>
            <div class="card"><div class="label">最新成交量（億）</div><div class="value">${esc(latestVolumeInYi(prices))}</div></div>
          </section>

          <h2>近期價格資料</h2>
          <table>
            <thead>
              <tr>
                <th>日期</th><th>開盤</th><th>最高</th><th>最低</th><th>收盤</th><th>成交量</th>
              </tr>
            </thead>
            <tbody>
              ${latestPrices.map((item) => `
                <tr>
                  <td>${esc(item.date)}</td>
                  <td>${esc(item.open)}</td>
                  <td>${esc(item.high)}</td>
                  <td>${esc(item.low)}</td>
                  <td>${esc(item.close)}</td>
                  <td>${esc(item.volume?.toLocaleString())}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>

          <div class="notice">
            本報告由 StockLens 台股量化分析與健康評估平台產生，僅供課程展示與研究參考，不構成投資建議。
          </div>
        </main>
        <script>
          window.addEventListener("load", () => {
            window.print();
          });
        </script>
      </body>
      </html>
    `;

    const win = window.open("", "_blank", "width=960,height=720");
    if (!win) return;
    win.document.open();
    win.document.write(html);
    win.document.close();
  };

  return (
    <button
      onClick={handleDownload}
      className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-bold text-white shadow-sm hover:bg-blue-700"
    >
      <Download size={16} />
      下載分析報告
    </button>
  );
}
