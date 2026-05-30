"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, BarChart3, LineChart, GitCompare, ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/",         icon: LayoutDashboard, label: "市場總覽" },
  { href: "/rankings", icon: BarChart3,        label: "因子排行" },
  { href: "/stocks",   icon: LineChart,        label: "個股分析" },
  { href: "/compare",  icon: GitCompare,       label: "股票比較" },
  { href: "/health",   icon: ShieldCheck,      label: "資料健康" },
];

export default function Sidebar() {
  const path = usePathname();

  return (
    <aside className="w-56 shrink-0 h-screen sticky top-0 flex flex-col
                      bg-white border-r border-slate-200 shadow-sm">
      <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-100">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-50 to-green-50
                        flex items-center justify-center text-blue-600 font-black text-sm">
          SL
        </div>
        <div>
          <div className="text-sm font-black text-slate-800 leading-tight">StockLens</div>
          <div className="text-xs text-slate-400">台股量化分析</div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = href === "/" ? path === "/" : path.startsWith(href);
          return (
            <Link key={href} href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                active
                  ? "bg-blue-50 text-blue-600 font-semibold"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
              )}>
              <Icon size={17} className={active ? "text-blue-600" : "text-slate-400"} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-4 py-4 border-t border-slate-100 text-xs text-slate-400 space-y-0.5">
        <div>資料來源：FinMind</div>
        <div>追蹤股票：30 檔</div>
        <div className="mt-2 text-[11px] text-slate-300">
          ⚠️ 僅供研究參考，不構成投資建議
        </div>
      </div>
    </aside>
  );
}
