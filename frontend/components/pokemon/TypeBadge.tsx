import { typeColor, typeTextColor } from "@/lib/constants";

interface TypeBadgeProps {
  typeName: string;       // name_en from API
  size?: "sm" | "md";
  className?: string;
}

export function TypeBadge({ typeName, size = "md", className }: TypeBadgeProps) {
  const bg    = typeColor(typeName);
  const color = typeTextColor(typeName);

  return (
    <span
      className={`inline-flex items-center justify-center rounded font-semibold uppercase tracking-wide ${
        size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs"
      } ${className ?? ""}`}
      style={{ backgroundColor: bg, color }}
    >
      {typeName}
    </span>
  );
}
