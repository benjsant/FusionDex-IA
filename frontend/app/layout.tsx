import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Navbar } from "@/components/layout/Navbar";

export const metadata: Metadata = {
  title: "FusionDex — Pokédex Intelligent pour Infinite Fusion",
  description:
    "Explorez les 501 Pokémon de Pokémon Infinite Fusion, calculez les fusions, découvrez les faiblesses et posez vos questions à l'IA DeepSeek.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className="dark">
      <body className="min-h-screen bg-[rgb(15,15,20)] text-[rgb(240,240,255)]">
        <Providers>
          <Navbar />
          <main className="pt-16">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
