import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] px-4 text-center">
      <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-indigo-400 to-purple-500 bg-clip-text text-transparent">
        FusionDex
      </h1>
      <p className="text-xl text-[rgb(160,160,180)] mb-2 max-w-xl">
        Le Pokédex intelligent pour{" "}
        <span className="text-indigo-400 font-semibold">Pokémon Infinite Fusion</span>
      </p>
      <p className="text-sm text-[rgb(120,120,140)] mb-10 max-w-lg">
        501 Pokémon · Calculateur de fusions · Assistant IA DeepSeek · Types IF
      </p>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 w-full max-w-2xl">
        <NavCard href="/pokedex" emoji="📖" label="Pokédex" desc="501 Pokémon IF" />
        <NavCard href="/fusion" emoji="⚗️" label="Fusion" desc="Calcule n'importe quelle fusion" />
        <NavCard href="/moves" emoji="⚡" label="Capacités" desc="Toutes les attaques IF" />
        <NavCard href="/types" emoji="🔮" label="Types" desc="Tableau d'efficacités Gen 7" />
        <NavCard href="/ai" emoji="🤖" label="Assistant IA" desc="Pose tes questions à DeepSeek" />
        <NavCard href="/abilities" emoji="✨" label="Talents" desc="Tous les talents IF" />
      </div>
    </div>
  );
}

function NavCard({
  href,
  emoji,
  label,
  desc,
}: {
  href: string;
  emoji: string;
  label: string;
  desc: string;
}) {
  return (
    <Link
      href={href}
      className="group flex flex-col items-center gap-2 p-5 rounded-xl bg-[rgb(20,20,28)] border border-[rgb(50,50,70)] hover:border-indigo-500 hover:bg-[rgb(25,25,38)] transition-all duration-200"
    >
      <span className="text-3xl">{emoji}</span>
      <span className="font-semibold text-[rgb(220,220,255)] group-hover:text-indigo-400 transition-colors">
        {label}
      </span>
      <span className="text-xs text-[rgb(120,120,140)] text-center">{desc}</span>
    </Link>
  );
}
