# FusionDex-IA

**Pokédex intelligent pour [Pokémon Infinite Fusion](https://infinitefusion.fandom.com/)** — une application complète qui extrait, structure, expose et affiche les données du jeu (501 Pokémon de base, ~176k fusions, movepools, types, fusions triples, créateurs de sprites, Move Experts…) avec une interface bilingue EN/FR.

## Vue rapide

| Couche     | Stack                                       | État       |
| ---------- | ------------------------------------------- | ---------- |
| ETL        | Python 3.12 + `uv` + MediaWiki + PokeAPI    | ✅ stable  |
| Base       | PostgreSQL 16 (tables relationnelles + `INTEGER[]`) | ✅ stable |
| Backend    | FastAPI + SQLAlchemy 2 + Pydantic           | ✅ stable  |
| Frontend   | Next.js 15 App Router + TypeScript          | 🚧 en cours |
| IA         | DeepSeek API via `/ai/ask`                  | 🚧 à valider |
| Infra      | Docker Compose (dev + prod), Next.js proxy  | ✅ stable  |

## Par où commencer

- **Comprendre l'ensemble** → [Architecture](architecture.md)
- **Schéma et données** → [Base de données](database.md)
- **Lancer le projet localement** → [Développement](development.md)
- **Consommer l'API** → [API backend](api.md)
- **Règles de fusion canoniques** → [Règles de fusion](fusion-rules.md)
- **Ce qu'il reste à faire** → [Roadmap](roadmap.md)

## Sources des données

- [PokeAPI](https://pokeapi.co/) — stats canoniques, learnsets TM/tutor, national dex IDs
- [Pokémon Infinite Fusion Wiki](https://infinitefusion.fandom.com/) — fusions, Move Experts, mécaniques spécifiques IF
- [Poképédia](https://www.pokepedia.fr/) — noms FR
- Sprites du dépôt `PokeAPI/sprites` (GitHub)

!!! info "Pourquoi FusionDex-IA ?"
    Pokémon Infinite Fusion a une richesse de données éparpillées sur plusieurs wikis, sans API officielle. Ce projet centralise tout dans une base PostgreSQL interrogeable, avec une API REST propre et un frontend pour explorer les ~176k combinaisons de fusion.
