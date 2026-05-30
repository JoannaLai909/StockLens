import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
}

export function Card({ title, children, className, ...props }: CardProps) {
  return (
    <div className={cn("bg-white rounded-2xl border border-slate-200 shadow-sm", className)} {...props}>
      {title && (
        <div className="px-5 pt-4 pb-0">
          <h3 className="text-sm font-bold text-slate-700">{title}</h3>
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}

export function KpiCard({
  icon, label, value, sub, tone = "blue", badge,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  tone?: "blue" | "green";
  badge?: string;
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 flex items-center gap-3.5">
      <div className={cn(
        "w-11 h-11 rounded-xl flex items-center justify-center text-lg shrink-0",
        tone === "green" ? "bg-green-50 text-green-600" : "bg-blue-50 text-blue-600",
      )}>
        {icon}
      </div>
      <div>
        <div className="text-xs font-semibold text-slate-400 mb-0.5">{label}</div>
        <div className={cn(
          "text-xl font-black leading-none",
          tone === "green" ? "text-green-600" : "text-blue-600",
        )}>
          {value}
          {badge && (
            <span className="ml-2 text-xs font-bold bg-green-50 text-green-600 px-2 py-0.5 rounded-md">
              {badge}
            </span>
          )}
        </div>
        {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
      </div>
    </div>
  );
}
