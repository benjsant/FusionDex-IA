"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/pokedex",    label: "Pokédex" },
  { href: "/fusion",     label: "Fusion" },
  { href: "/moves",      label: "Capacités" },
  { href: "/types",      label: "Types" },
  { href: "/abilities",  label: "Talents" },
  { href: "/ai",         label: "IA" },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-16 bg-[rgb(15,15,20)]/95 backdrop-blur border-b border-[rgb(50,50,70)] flex items-center px-4 gap-6">
      <Link
        href="/"
        className="text-lg font-bold text-indigo-400 hover:text-indigo-300 transition-colors whitespace-nowrap mr-4"
      >
        FusionDex
      </Link>

      <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide">
        {NAV_LINKS.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "px-3 py-1.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap",
              pathname?.startsWith(href)
                ? "bg-indigo-600/30 text-indigo-300"
                : "text-[rgb(160,160,180)] hover:text-white hover:bg-[rgb(30,30,45)]",
            )}
          >
            {label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
