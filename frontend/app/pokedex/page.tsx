"use client";

import { useState, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { usePokemonList, usePokemonSearch } from "@/hooks/usePokemon";
import { PokemonCard } from "@/components/pokemon/PokemonCard";
import { SearchBar } from "@/components/layout/SearchBar";
import { primaryType, secondaryType, normalize } from "@/lib/utils";

const PAGE_SIZE = 40;

const TYPES = [
  "Normal","Fire","Water","Electric","Grass","Ice",
  "Fighting","Poison","Ground","Flying","Psychic","Bug",
  "Rock","Ghost","Dragon","Dark","Steel","Fairy",
];

export default function PokedexPage() {
  return (
    <Suspense>
      <PokedexContent />
    </Suspense>
  );
}

function PokedexContent() {
  const searchParams = useSearchParams();
  const [q, setQ] = useState(searchParams.get("q") ?? "");
  const [typeFilter, setTypeFilter] = useState("");
  const [page, setPage] = useState(1);

  const isSearching = q.trim().length >= 2;

  const listQuery   = usePokemonList({ page, page_size: PAGE_SIZE });
  const searchQuery = usePokemonSearch(q);

  const pokemons = isSearching ? searchQuery.data ?? [] : listQuery.data ?? [];
  const isLoading = isSearching ? searchQuery.isLoading : listQuery.isLoading;

  const filtered = useMemo(() => {
    if (!typeFilter) return pokemons;
    const nf = normalize(typeFilter);
    return pokemons.filter((p) => {
      const t1 = primaryType(p.types);
      const t2 = secondaryType(p.types);
      return (
        (t1 && normalize(t1.name_en) === nf) ||
        (t2 && normalize(t2.name_en) === nf)
      );
    });
  }, [pokemons, typeFilter]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6 text-[rgb(220,220,255)]">
        Pokédex — 501 Pokémon Infinite Fusion
      </h1>

      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <SearchBar
          onSearch={setQ}
          className="flex-1"
          placeholder="Rechercher (Bulbasaur, Bulbizarre, pikachu…)"
        />
        <select
          value={typeFilter}
          onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 rounded-lg bg-[rgb(30,30,42)] border border-[rgb(50,50,70)] text-[rgb(220,220,255)] focus:outline-none focus:border-indigo-500"
        >
          <option value="">Tous les types</option>
          {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      {isLoading ? (
        <SkeletonGrid />
      ) : filtered.length === 0 ? (
        <p className="text-center text-[rgb(120,120,140)] py-12">Aucun Pokémon trouvé.</p>
      ) : (
        <>
          <p className="text-sm text-[rgb(120,120,140)] mb-4">
            {filtered.length} Pokémon{isSearching ? ` pour "${q}"` : ""}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
            {filtered.map((p) => <PokemonCard key={p.id} pokemon={p} />)}
          </div>

          {!isSearching && (
            <div className="flex justify-center gap-3 mt-8">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 rounded-lg bg-[rgb(30,30,42)] border border-[rgb(50,50,70)] text-[rgb(160,160,180)] disabled:opacity-40 hover:border-indigo-500 hover:text-white transition-all"
              >
                ← Précédent
              </button>
              <span className="px-4 py-2 text-[rgb(120,120,140)]">Page {page}</span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={pokemons.length < PAGE_SIZE}
                className="px-4 py-2 rounded-lg bg-[rgb(30,30,42)] border border-[rgb(50,50,70)] text-[rgb(160,160,180)] disabled:opacity-40 hover:border-indigo-500 hover:text-white transition-all"
              >
                Suivant →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
      {Array.from({ length: 40 }).map((_, i) => (
        <div key={i} className="h-40 rounded-xl bg-[rgb(25,25,35)] border border-[rgb(40,40,55)] animate-pulse" />
      ))}
    </div>
  );
}
