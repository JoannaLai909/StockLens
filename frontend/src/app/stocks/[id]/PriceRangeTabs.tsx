"use client";

import { useRouter, usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const RANGES = [
  { label: "1M", days: 21  },
  { label: "3M", days: 63  },
  { label: "6M", days: 126 },
  { label: "1Y", days: 252 },
];

export default function PriceRangeTabs({ currentDays, stockId }: { currentDays: number; stockId: string }) {
  const router   = useRouter();
  const pathname = usePathname();
  return (
    <div className="flex gap-1 mb-3">
      {RANGES.map(({ label, days }) => (
        <button key={label} onClick={() => router.push(`${pathname}?days=${days}`)}
          className={cn(
            "px-3 py-1 text-xs font-semibold rounded-lg transition-colors",
            currentDays === days
              ? "bg-blue-600 text-white"
              : "bg-slate-100 text-slate-500 hover:bg-slate-200",
          )}>
          {label}
        </button>
      ))}
    </div>
  );
}
