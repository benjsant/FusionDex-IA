import type { EvolutionOut } from "@/types/api";
import Link from "next/link";

interface EvolutionChainProps {
  pokemonId: number;
  evolutions: EvolutionOut[];
}

function evolutionCondition(evo: EvolutionOut): string {
  const parts: string[] = [];
  if (evo.trigger_type === "level_up" && evo.min_level) {
    parts.push(`Niveau ${evo.min_level}`);
  } else if (evo.trigger_type === "use_item" && evo.item_name_en) {
    parts.push(evo.item_name_en);
  } else if (evo.trigger_type === "trade") {
    parts.push("Échange");
  } else if (evo.trigger_type === "friendship") {
    parts.push("Amitié");
  }
  if (evo.if_notes) parts.push(evo.if_notes);
  return parts.join(" · ") || evo.trigger_type;
}

export function EvolutionChain({ pokemonId, evolutions }: EvolutionChainProps) {
  if (evolutions.length === 0) {
    return (
      <p className="text-[rgb(120,120,140)] text-sm">
        Ce Pokémon n&apos;a pas d&apos;évolution dans Infinite Fusion.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {evolutions.map((evo) => (
        <div
          key={`${evo.evolves_into_id}-${evo.trigger_type}`}
          className="flex items-center gap-4 p-3 rounded-lg bg-[rgb(25,25,35)] border border-[rgb(40,40,55)]"
        >
          <span className="text-[rgb(120,120,140)] text-sm">#{pokemonId}</span>
          <span className="text-[rgb(100,100,120)] text-lg">→</span>

          <div className="flex-1">
            <Link
              href={`/pokedex/${evo.evolves_into_id}`}
              className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              {evo.evolves_into_name_fr ?? evo.evolves_into_name_en}
            </Link>
            <span className="ml-2 text-xs text-[rgb(100,100,120)]">
              (#{evo.evolves_into_id})
            </span>
            <p className="text-xs text-[rgb(160,160,180)] mt-0.5">
              {evolutionCondition(evo)}
            </p>
          </div>

          {evo.if_override && (
            <span className="text-xs px-2 py-0.5 rounded bg-indigo-900/40 text-indigo-300 shrink-0">
              IF uniquement
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
