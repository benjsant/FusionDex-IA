"use client";

import Link from "next/link";

interface AiSuggestButtonProps {
  pokemonName: string;
  pokemonId: number;
  context?: string;
}

export function AiSuggestButton({ pokemonName, pokemonId }: AiSuggestButtonProps) {
  const query = encodeURIComponent(
    `Quels sont les meilleurs partenaires de fusion pour ${pokemonName} (#${pokemonId}) dans Pokémon Infinite Fusion ? Donne des conseils stratégiques.`,
  );

  return (
    <Link
      href={`/ai?q=${query}`}
      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-700/30 border border-indigo-600/40 text-indigo-300 hover:bg-indigo-700/50 hover:text-indigo-200 transition-all text-sm font-medium"
    >
      🤖 Demander à l&apos;IA
    </Link>
  );
}
