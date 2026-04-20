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
    parts.push(evo.item_name_fr ?? evo.item_name_en);
  } else if (evo.trigger_type === "trade") {
    parts.push("Échange");
  } else if (evo.trigger_type === "friendship") {
    parts.push("Amitié");
  }
  if (evo.if_notes) parts.push(evo.if_notes);
  return parts.join(" · ") || evo.trigger_type;
}

function EvolutionRow({
  fromId,
  fromName,
  toId,
  toName,
  condition,
  ifOverride,
}: {
  fromId: number;
  fromName: string;
  toId: number;
  toName: string;
  condition: string;
  ifOverride: boolean;
}) {
  return (
    <div className="flex items-center gap-4 p-3 rounded-lg bg-[rgb(25,25,35)] border border-[rgb(40,40,55)]">
      <Link
        href={`/pokedex/${fromId}`}
        className="text-[rgb(180,180,210)] hover:text-indigo-300 text-sm"
      >
        {fromName} <span className="text-[rgb(100,100,120)]">(#{fromId})</span>
      </Link>
      <span className="text-[rgb(100,100,120)] text-lg">→</span>
      <div className="flex-1">
        <Link
          href={`/pokedex/${toId}`}
          className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          {toName}
        </Link>
        <span className="ml-2 text-xs text-[rgb(100,100,120)]">(#{toId})</span>
        <p className="text-xs text-[rgb(160,160,180)] mt-0.5">{condition}</p>
      </div>
      {ifOverride && (
        <span className="text-xs px-2 py-0.5 rounded bg-indigo-900/40 text-indigo-300 shrink-0">
          IF uniquement
        </span>
      )}
    </div>
  );
}

export function EvolutionChain({ pokemonId, evolutions }: EvolutionChainProps) {
  const preEvos = evolutions.filter((e) => e.evolves_into_id === pokemonId);
  const nextEvos = evolutions.filter((e) => e.pokemon_id === pokemonId);

  if (preEvos.length === 0 && nextEvos.length === 0) {
    return (
      <p className="text-[rgb(120,120,140)] text-sm">
        Ce Pokémon n&apos;a ni pré-évolution ni évolution dans Infinite Fusion.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {preEvos.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-[rgb(160,160,180)] uppercase tracking-wider">
            Pré-évolution
          </h4>
          <div className="space-y-2">
            {preEvos.map((evo) => (
              <EvolutionRow
                key={`pre-${evo.id}`}
                fromId={evo.pokemon_id}
                fromName={evo.pokemon_name_fr ?? evo.pokemon_name_en ?? `#${evo.pokemon_id}`}
                toId={evo.evolves_into_id}
                toName={evo.evolves_into_name_fr ?? evo.evolves_into_name_en}
                condition={evolutionCondition(evo)}
                ifOverride={evo.if_override}
              />
            ))}
          </div>
        </div>
      )}

      {nextEvos.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-[rgb(160,160,180)] uppercase tracking-wider">
            Évolution
          </h4>
          <div className="space-y-2">
            {nextEvos.map((evo) => (
              <EvolutionRow
                key={`next-${evo.id}`}
                fromId={pokemonId}
                fromName={`#${pokemonId}`}
                toId={evo.evolves_into_id}
                toName={evo.evolves_into_name_fr ?? evo.evolves_into_name_en}
                condition={evolutionCondition(evo)}
                ifOverride={evo.if_override}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
