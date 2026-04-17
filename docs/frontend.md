# Frontend

Next.js 15 (App Router) + TypeScript. Rendu SSR par défaut, déploiement en mode `output: "standalone"` dans Docker.

## Organisation

```
frontend/
  app/
    (routes pages)
    pokedex/            # liste + fiche
    fusion/             # sélecteur + résultat
    api/[...path]/      # proxy catch-all → backend
    sprites-cdn/[...]/  # proxy catch-all → sidecar nginx (PNG)
  components/
    pokemon/            # EvolutionChain, MovesetTable, PokemonCard, StatBar, TypeBadge, WeaknessGrid
    fusion/             # FusionSelector, FusionSprite
    layout/             # Navbar, SearchBar
  hooks/                # useFusion, useMoves, usePokemon, useAiChat
  lib/
    api.ts              # client fetch centralisé
    constants.ts        # API_BASE_URL = "/api"
    utils.ts
  types/
    api.d.ts            # types générés à partir des schémas Pydantic
```

## Pages

| Route                                  | Contenu                                                |
| -------------------------------------- | ------------------------------------------------------ |
| `/`                                    | Landing                                                |
| `/pokedex`                             | Liste paginée + recherche + filtres                    |
| `/pokedex/[id]`                        | Fiche : stats, types, talents, évolutions, movepool    |
| `/fusion`                              | Sélecteur head/body                                    |
| `/fusion/[headId]/[bodyId]`            | Résultat : sprite + stats + moves + faiblesses + experts |
| `/moves`, `/types`, `/abilities`       | Listes référentielles                                  |

## Proxy Next.js

Tous les appels réseau du navigateur passent par Next :

- `GET /api/pokemon/1` → route handler → `fetch(BACKEND_INTERNAL_URL + "/pokemon/1")`
- `GET /sprites-cdn/CustomBattlers/1.1.png` → route handler → sidecar nginx

Deux bénéfices :

1. **Zéro fuite d'URL backend** dans le bundle client. Le navigateur ne voit que `/api/*`.
2. **Config runtime** : `BACKEND_INTERNAL_URL` est lu à chaque requête (pas d'env bakée au build), on peut changer la cible sans rebuild.

Implémentation : [frontend/app/api/[...path]/route.ts](https://github.com/) et [frontend/app/sprites-cdn/[...path]/route.ts](https://github.com/).

!!! note "Pourquoi pas `next.config.ts` rewrites ?"
    Next.js standalone fige les destinations de rewrite dans `.next/required-server-files.json` au build. Les route handlers, eux, évaluent `process.env` à chaque requête — c'est ce qu'on veut.

## Hooks

Les hooks `use*` encapsulent les appels via `lib/api.ts` + état (loading/error/data). Ils sont typés à partir de `types/api.d.ts` pour que chaque changement de schéma backend casse la compilation côté frontend (fail-fast).

## i18n

Le projet est bilingue EN/FR côté données (colonnes `name_en` / `name_fr`). L'UI actuelle affiche les deux ou laisse au navigateur le choix via un toggle (à stabiliser — cf. [Roadmap](roadmap.md)).

## Dev

```bash
cd frontend
npm install
npm run dev    # http://localhost:3000
```

Pour lancer avec le backend dockerisé :

```bash
docker compose up -d            # lance tout
# Le frontend est sur http://localhost:53000
```

## Build

```bash
docker compose build frontend
```

Le Dockerfile multi-stage n'a **aucun** `ARG` pointant vers le backend : tout passe par les env runtime (`BACKEND_INTERNAL_URL`, `SPRITES_INTERNAL_URL`).

## Voir aussi

- [Architecture](architecture.md) — flux de requêtes proxy.
- [API backend](api.md) — endpoints consommés.
