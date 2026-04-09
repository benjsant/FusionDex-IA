import { statColor, statBarWidth, formatStatName } from "@/lib/utils";

interface StatBarProps {
  stat: string;   // key matching backend field (hp, attack, sp_attack…)
  value: number;
  max?: number;
}

export function StatBar({ stat, value, max = 255 }: StatBarProps) {
  const width = statBarWidth(value, max);
  const color = statColor(value);

  return (
    <div className="flex items-center gap-3">
      <span className="w-24 text-right text-xs text-[rgb(120,120,140)] shrink-0">
        {formatStatName(stat)}
      </span>
      <span className="w-8 text-right text-sm font-mono font-semibold text-[rgb(220,220,255)] shrink-0">
        {value}
      </span>
      <div className="flex-1 h-2 rounded-full bg-[rgb(40,40,55)]">
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{ width: `${width}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
