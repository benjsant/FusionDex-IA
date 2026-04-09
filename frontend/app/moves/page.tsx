"use client";

import { useState, useMemo } from "react";
import { useMoves } from "@/hooks/useMoves";
import { TypeBadge } from "@/components/pokemon/TypeBadge";
import { SearchBar } from "@/components/layout/SearchBar";
import { normalize, formatPower, formatAccuracy, formatCategory } from "@/lib/utils";

const TYPES_LIST = [
  "Normal","Fire","Water","Electric","Grass","Ice",
  "Fighting","Poison","Ground","Flying","Psychic","Bug",
  "Rock","Ghost","Dragon","Dark","Steel","Fairy",
];

export default function MovesPage() {
  const { data: moves = [], isLoading } = useMoves();
  const [q, setQ] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [catFilter, setCatFilter] = useState("");

  const filtered = useMemo(() => {
    return moves.filter((m) => {
      if (typeFilter && m.type.name_en !== typeFilter) return false;
      if (catFilter && m.category !== catFilter) return false;
      if (q.trim().length >= 2) {
        const nq = normalize(q);
        if (!normalize(m.name_en).includes(nq) && !(m.name_fr && normalize(m.name_fr).includes(nq)))
          return false;
      }
      return true;
    });
  }, [moves, q, typeFilter, catFilter]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6 text-[rgb(220,220,255)]">Capacités</h1>

      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <SearchBar onSearch={setQ} placeholder="Rechercher une capacité…" className="flex-1" />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 rounded-lg bg-[rgb(30,30,42)] border border-[rgb(50,50,70)] text-[rgb(220,220,255)] focus:outline-none focus:border-indigo-500"
        >
          <option value="">Tous types</option>
          {TYPES_LIST.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select
          value={catFilter}
          onChange={(e) => setCatFilter(e.target.value)}
          className="px-3 py-2 rounded-lg bg-[rgb(30,30,42)] border border-[rgb(50,50,70)] text-[rgb(220,220,255)] focus:outline-none focus:border-indigo-500"
        >
          <option value="">Toutes catégories</option>
          <option value="Physical">Physique</option>
          <option value="Special">Spéciale</option>
          <option value="Status">Statut</option>
        </select>
      </div>

      <p className="text-sm text-[rgb(120,120,140)] mb-3">{filtered.length} capacités</p>

      {isLoading ? (
        <div className="animate-pulse space-y-2">
          {Array.from({ length: 20 }).map((_, i) => (
            <div key={i} className="h-10 bg-[rgb(25,25,35)] rounded" />
          ))}
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-[rgb(40,40,55)]">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[rgb(25,25,35)] text-[rgb(120,120,140)] text-xs">
                <th className="px-3 py-2 text-left">Nom EN</th>
                <th className="px-3 py-2 text-left">Nom FR</th>
                <th className="px-3 py-2 text-left">Type</th>
                <th className="px-3 py-2 text-left">Cat.</th>
                <th className="px-3 py-2 text-right">Puiss.</th>
                <th className="px-3 py-2 text-right">Préc.</th>
                <th className="px-3 py-2 text-right">PP</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((mv) => (
                <tr
                  key={mv.id}
                  className="border-t border-[rgb(35,35,48)] hover:bg-[rgb(25,25,38)] transition-colors"
                >
                  <td className="px-3 py-2 font-medium text-[rgb(220,220,255)]">{mv.name_en}</td>
                  <td className="px-3 py-2 text-[rgb(160,160,180)]">{mv.name_fr ?? "—"}</td>
                  <td className="px-3 py-2">
                    <TypeBadge typeName={mv.type.name_en} size="sm" />
                  </td>
                  <td className="px-3 py-2 text-[rgb(160,160,180)] text-xs">
                    {formatCategory(mv.category)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-[rgb(200,200,220)]">
                    {formatPower(mv.power)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-[rgb(200,200,220)]">
                    {formatAccuracy(mv.accuracy)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-[rgb(200,200,220)]">
                    {mv.pp ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
