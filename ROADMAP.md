# FusionDex-IA — Roadmap

État d'avancement et prochaines étapes par couche.

## ETL — ✅ stabilisé

Pipeline complet en 12 étapes, factorisé en helpers :
- `etl/utils/sql.py` — `load_id_map`
- `etl/utils/wikitext.py` — fetch MediaWiki + clean
- `etl/utils/io.py` — `load_json` / `save_json`
- Héritage des moves de pré-évolutions (`enrich_evolution_movesets.py`)

**Données finales** : 572 Pokémon · 676 moves · 178 abilities · 40067 pokemon_move · 166090 fusion_sprite · 7081 créateurs · 23 triple_fusion · 1634 pokemon_location

**Pistes restantes**
- Audit DB — Pokémon sans sprites, moves orphelins, cohérence des fusions
- Mega-évolutions (pas couvertes pour l'instant)

## Backend FastAPI — ✅ base solide

**30+ endpoints** couvrant Pokémon, moves, abilities, types, fusions, sprites, triple-fusions, générations, créateurs, stats, IA.

- Pagination + filtres sur `/pokemon/` et `/moves/`
- Sub-endpoints fusion : `/moves`, `/abilities`, `/weaknesses`, `/random`
- `GET /sprites/{h}/{b}/image` sert l'image PNG (default ou `?variant_id=N`)
- `/generations/`, `/generations/{id}/pokemon`
- `/creators/`, `/creators/{id}`, `/creators/{id}/sprites`
- `/fusions/involving/{pokemon_id}` — toutes les paires head/body
- `/stats/coverage` — audit (Pokémon sans sprite/types/moves, moves/abilities orphelins)
- `/ai/ask` renvoie 503 propre si `DEEPSEEK_API_KEY` absent
- **53 tests pytest verts** (voir [backend/tests/](backend/tests/))

**Pistes restantes**
- [ ] **E2E DeepSeek** — tester `/ai/ask` bout-à-bout avec vraie clé
- [ ] **CI full pytest** — le workflow actuel ne lance que `test_ai.py` (les autres ont besoin d'un dump SQL committé sous `backend/tests/fixtures/`)

## Frontend Next.js — 🚧 à démarrer

Rien de commencé côté front. Prévoir :
- Liste Pokédex (avec filtres type/gen)
- Fiche Pokémon (stats, moves, évolutions, faiblesses)
- Calculateur de fusion (drag & drop head/body)
- Galerie sprites + crédits
- Page triple-fusions

## IA / DeepSeek — 🚧 à valider

`ai_route.py` + `ai_service.py` existent mais jamais testés bout-à-bout.

- [ ] Vérifier l'intégration DeepSeek (clés, quotas)
- [ ] Définir le use-case : recommandations de fusion ? assistant de team-building ?

## Infra

- Postgres 5432 exposé sur le host pour DBeaver
- Docker compose : db + backend + sprites sidecar + frontend
- CI GitHub Actions — smoke (import + `test_ai.py`) sur PR backend
- [ ] Dump SQL fixture → full pytest en CI
- [ ] Déploiement (hébergement à choisir)
