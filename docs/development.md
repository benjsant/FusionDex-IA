# Développement

Guide pour installer, lancer et contribuer au projet.

## Prérequis

- **Docker** + Docker Compose v2
- **Node.js** ≥ 20 (pour le dev frontend hors Docker)
- **Python** ≥ 3.12 + [`uv`](https://github.com/astral-sh/uv) (pour l'ETL et la doc)

## Premier lancement

```bash
git clone <repo-url>
cd FusionDex-IA
cp .env.example .env               # ajuste POSTGRES_PASSWORD si besoin
docker compose up -d               # db + backend + sprites + frontend
```

Services accessibles :

- Frontend : [http://localhost:53000](http://localhost:53000)
- Backend / Swagger : [http://localhost:58000/docs](http://localhost:58000/docs)
- Sprites (direct, debug) : [http://localhost:58080/sprites/](http://localhost:58080/sprites/)
- Postgres : `localhost:55432` (user/db dans `.env`)

!!! tip "Base vide au premier démarrage"
    Le schéma se crée automatiquement via `docker/init_postgres.sql`, mais **les données ne sont pas incluses**. Lance le pipeline ETL pour peupler la base (voir plus bas).

## Peupler la base

```bash
cd etl
uv sync
uv run python -m etl.scripts.load_db
```

Durée : ~5–15 min selon ton réseau (beaucoup de fetch MediaWiki + PokeAPI).

## Dev sans Docker

### Backend

```bash
cd backend
uv sync
uv run uvicorn backend.main:app --reload --port 58000
```

### Frontend

```bash
cd frontend
npm install
npm run dev       # http://localhost:3000
```

En dev hors Docker, le proxy `/api/*` cible `BACKEND_INTERNAL_URL=http://localhost:58000` (cf. `frontend/.env.local.example`).

### Documentation

Voie principale — Docker, cohérent avec le reste du projet :

```bash
docker compose --profile docs up docs     # http://localhost:58100
```

Le service est sous profil `docs` → il ne démarre **pas** avec un simple `docker compose up`. Les fichiers `docs/`, `mkdocs.yml`, `pyproject.toml`, `uv.lock` sont montés en volume, donc le hot-reload fonctionne dès qu'on édite une page.

Premier lancement : `--build` pour construire l'image.

```bash
docker compose --profile docs up --build docs
```

Fallback host (sans Docker) :

```bash
uv sync --group docs
uv run mkdocs serve     # http://127.0.0.1:58100
```

## Configuration

### Ports (convention préfixe 5)

Les ports hôte sont tous configurables via `.env` pour éviter les collisions avec d'autres projets locaux.

```dotenv
FUSIONDEX_FRONTEND_PORT=53000
FUSIONDEX_BACKEND_PORT=58000
FUSIONDEX_SPRITES_PORT=58080
FUSIONDEX_DB_PORT=55432
```

Le serveur MkDocs (dev-tooling) est fixé à `58100` dans `mkdocs.yml`.

### CORS

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:53000,http://localhost:58000
```

En prod, lister uniquement le domaine public.

### Proxy Next.js

```dotenv
BACKEND_INTERNAL_URL=http://backend:8000     # Docker interne
SPRITES_INTERNAL_URL=http://sprites:80       # Docker interne
```

Ces variables sont lues **à runtime** par les route handlers — pas besoin de rebuild pour les changer.

## Mode prod / démo

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

En prod, seul `frontend` est exposé publiquement. Prérequis : `.env.prod` avec `POSTGRES_PASSWORD`, `CORS_ALLOWED_ORIGINS=https://<domaine>`, `FUSIONDEX_FRONTEND_PORT=<public>`.

## Tests

### Backend

```bash
cd backend
uv run pytest
```

53 tests. **Ils nécessitent un dump SQL** sous `backend/tests/fixtures/` (non committé). La CI actuelle ne lance que `test_ai.py` (smoke test DeepSeek). Cf. [Roadmap](roadmap.md).

### Frontend

Pas encore de suite de tests (Playwright prévu).

## Commits

Le projet suit [Conventional Commits](https://www.conventionalcommits.org/) :

- `feat(backend):` / `feat(frontend):` / `feat(etl):`
- `fix(frontend):` — bugs UI
- `refactor(infra):` — Docker, CI, proxy
- `test(backend):` — pytest
- `docs:` — cette doc

Les commits générés par l'assistant incluent :

```
Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

## Structure du repo

```
backend/        # FastAPI + SQLAlchemy + tests
etl/            # pipeline Python + uv
frontend/       # Next.js 15 App Router
docker/         # Dockerfiles + init_postgres.sql
docs/           # cette documentation (MkDocs)
data/           # dumps + caches (gitignored)
.github/        # CI workflows
```

## Voir aussi

- [Architecture](architecture.md)
- [ETL](etl.md)
- [API backend](api.md)
