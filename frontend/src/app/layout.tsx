import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "StockLens | 台股量化分析",
  description: "整合股價資料、量化因子與互動式圖表，快速掌握股票表現與風險",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW">
      <body className="bg-surface text-slate-800 antialiased">
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 overflow-auto">
              <div className="max-w-[1300px] mx-auto px-6 py-6">
                {children}
              </div>
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
