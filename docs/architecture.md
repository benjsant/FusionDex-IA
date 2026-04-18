# Architecture

Vue d'ensemble des couches du projet et de la façon dont elles communiquent.

## Schéma global

```mermaid
flowchart LR
    subgraph Sources
        A[PokeAPI]
        B[Wiki Infinite Fusion]
        C[Poképédia]
        D[PokeAPI sprites repo]
    end

    subgraph ETL["ETL (Python + uv)"]
        E[load_db.py<br/>orchestration]
        F[fix_*.py<br/>corrections canoniques]
    end

    subgraph DB[(PostgreSQL 16)]
        G[pokemon, move, type,<br/>ability, evolution…]
        H[fusion_sprite,<br/>triple_fusion]
        I[move_expert_move]
    end

    subgraph Backend["FastAPI"]
        J[routes/]
        K[services/]
        L[schemas/]
    end

    subgraph Frontend["Next.js 15 App Router"]
        M[pages /pokedex /fusion…]
        N[proxy /api/* /sprites-cdn/*]
    end

    Sprites[Sidecar nginx<br/>sprites PNG]

    A --> E
    B --> E
    C --> E
    D --> Sprites
    E --> DB
    F --> DB
    DB --> K
    K --> J
    J --> L
    L --> N
    Sprites --> N
    N --> M
```

## Services Docker

Quatre services, tous sur le réseau interne Docker. Seul le frontend est exposé publiquement en prod.

| Service    | Port interne | Port hôte (dev) | Rôle                                |
| ---------- | ------------ | --------------- | ----------------------------------- |
| `db`       | 5432         | 55432           | PostgreSQL 16                       |
| `backend`  | 8000         | 58000           | FastAPI                             |
| `sprites`  | 80           | 58080           | nginx statique pour sprites PNG     |
| `frontend` | 3000         | 53000           | Next.js (standalone)                |

Les ports hôte suivent une convention **préfixe 5** pour éviter les collisions avec d'autres projets locaux.

!!! tip "Override prod"
    `docker-compose.prod.yml` remet `ports: !reset []` sur db/backend/sprites — plus rien n'est exposé sauf le frontend. Le navigateur passe toujours par le proxy Next.js.

## Flux de requêtes

### En dev

```
Navigateur → http://localhost:53000/pokedex
           → Next.js SSR → fetch http://localhost:53000/api/pokemon/
           → Route handler Next.js (/app/api/[...path]/route.ts)
           → fetch http://backend:8000/pokemon/ (réseau Docker interne)
           → FastAPI → SQLAlchemy → Postgres
           ← JSON
```

### En prod

Identique, sauf que `http://backend:8000` n'est joignable que depuis le conteneur `frontend`. Le navigateur ne voit jamais l'URL réelle du backend, uniquement `/api/*` sur le domaine public.

## Pourquoi ce découpage ?

- **ETL séparé du backend** : le pipeline de données tourne en one-shot (ou via Prefect plus tard), indépendamment du serveur web. Pas de couplage.
- **Sprites servis par nginx plutôt que FastAPI** : 166k fichiers PNG statiques, nginx est 10× plus efficace que Python pour ça.
- **Proxy Next.js plutôt qu'appels directs au backend** : masque les URLs internes, évite CORS côté navigateur, permet de changer la cible backend sans rebuild frontend (env runtime).
- **`INTEGER[]` PostgreSQL pour Move Experts** : contraintes multi-valeurs (required_pokemon_ids, etc.) naturellement représentées sans table de jonction supplémentaire.

## Références

- [backend/main.py](https://github.com/) — wiring FastAPI + CORS
- [docker-compose.yml](https://github.com/) — services dev
- [docker-compose.prod.yml](https://github.com/) — override prod
- [frontend/app/api/[...path]/route.ts](https://github.com/) — proxy catch-all
