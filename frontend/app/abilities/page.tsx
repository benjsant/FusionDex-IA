"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getAbilities, getAbility } from "@/lib/api";
import { SearchBar } from "@/components/layout/SearchBar";
import { normalize } from "@/lib/utils";
import type { AbilityDetail } from "@/types/api";

export default function AbilitiesPage() {
  const { data: abilities = [], isLoading } = useQuery({
    queryKey: ["abilities"],
    queryFn: getAbilities,
  });

  const [q, setQ] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data: detail } = useQuery({
    queryKey: ["ability", selectedId],
    queryFn: () => getAbility(selectedId!),
    enabled: selectedId != null,
  });

  const filtered = useMemo(() => {
    if (q.trim().length < 2) return abilities;
    const nq = normalize(q);
    return abilities.filter(
      (a) =>
        normalize(a.name_en).includes(nq) ||
        (a.name_fr && normalize(a.name_fr).includes(nq)),
    );
  }, [abilities, q]);

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6 text-[rgb(220,220,255)]">Talents</h1>

      <SearchBar
        onSearch={setQ}
        placeholder="Rechercher un talent…"
        className="mb-4"
      />

      <p className="text-sm text-[rgb(120,120,140)] mb-3">{filtered.length} talents</p>

      <div className="flex gap-4">
        {/* List */}
        <div className="flex-1 overflow-y-auto max-h-[70vh] rounded-lg border border-[rgb(40,40,55)]">
          {isLoading ? (
            <div className="animate-pulse p-4 space-y-2">
              {Array.from({ length: 15 }).map((_, i) => (
                <div key={i} className="h-10 bg-[rgb(30,30,42)] rounded" />
              ))}
            </div>
          ) : (
            filtered.map((a) => (
              <button
                key={a.id}
                onClick={() => setSelectedId(selectedId === a.id ? null : a.id)}
                className={`w-full flex items-center justify-between px-4 py-3 border-b border-[rgb(35,35,48)] hover:bg-[rgb(25,25,38)] transition-colors text-left ${
                  selectedId === a.id
                    ? "bg-[rgb(25,25,45)] border-l-2 border-l-indigo-500"
                    : ""
                }`}
              >
                <div>
                  <p className="text-sm font-medium text-[rgb(220,220,255)]">
                    {a.name_en}
                  </p>
                  {a.name_fr && (
                    <p className="text-xs text-[rgb(120,120,140)]">{a.name_fr}</p>
                  )}
                </div>
              </button>
            ))
          )}
        </div>

        {/* Detail panel */}
        {detail && (
          <div className="w-72 shrink-0 rounded-lg bg-[rgb(20,20,28)] border border-[rgb(50,50,70)] p-4 h-fit sticky top-20">
            <h2 className="font-bold text-[rgb(220,220,255)] mb-0.5">{detail.name_en}</h2>
            {detail.name_fr && (
              <p className="text-sm text-[rgb(160,160,180)] mb-3">{detail.name_fr}</p>
            )}
            {detail.description_en && (
              <p className="text-sm text-[rgb(180,180,200)] mb-2">{detail.description_en}</p>
            )}
            {detail.description_fr && (
              <p className="text-sm text-[rgb(160,160,180)] border-t border-[rgb(40,40,55)] pt-2 mt-2">
                {detail.description_fr}
              </p>
            )}
            {detail.if_modified && (
              <div className="mt-3 px-2 py-1.5 rounded bg-indigo-900/30 border border-indigo-700/30">
                <p className="text-xs text-indigo-300 font-semibold">Modifié dans IF</p>
                {detail.if_notes && (
                  <p className="text-xs text-indigo-200/70 mt-0.5">{detail.if_notes}</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
