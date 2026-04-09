"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { normalize } from "@/lib/utils";

interface SearchBarProps {
  placeholder?: string;
  onSearch?: (q: string) => void;
  navigateTo?: boolean; // if true, navigate to /pokedex?q=
  className?: string;
}

export function SearchBar({
  placeholder = "Rechercher un Pokémon (EN, FR, accents ok)…",
  onSearch,
  navigateTo = false,
  className,
}: SearchBarProps) {
  const [value, setValue] = useState("");
  const router = useRouter();

  const handleSearch = useCallback(
    (q: string) => {
      if (onSearch) {
        onSearch(normalize(q));
      }
      if (navigateTo && q.trim().length > 0) {
        router.push(`/pokedex?q=${encodeURIComponent(q.trim())}`);
      }
    },
    [onSearch, navigateTo, router],
  );

  // Debounce 300ms
  useEffect(() => {
    const timer = setTimeout(() => handleSearch(value), 300);
    return () => clearTimeout(timer);
  }, [value, handleSearch]);

  return (
    <input
      type="search"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      placeholder={placeholder}
      className={`w-full px-4 py-2 rounded-lg bg-[rgb(30,30,42)] border border-[rgb(50,50,70)] text-[rgb(220,220,255)] placeholder:text-[rgb(100,100,120)] focus:outline-none focus:border-indigo-500 transition-colors ${className ?? ""}`}
    />
  );
}
