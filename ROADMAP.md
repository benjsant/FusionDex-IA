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
- Scheduler (Prefect ou n8n) pour automatiser les refresh

## Base de données — 🚧 ajouts planifiés

**Ajouts BDD ciblés** (PR en cours) pour enrichir le contexte exploitable par l'IA :
- [ ] **Move tutors** — nouvelle table `move_tutor(move_id, location_id, price, currency, notes)` scrapée depuis le wiki IF
- [ ] **TM location cleanup** — normaliser `tm.location` (actuellement texte libre avec bugs de parsing) et la lier via FK à `location(id)`
- [ ] **Exposition API** — `/moves/{id}` doit retourner TM number + location + tutors

## Backend FastAPI — ✅ base solide

**36 endpoints + `/health`** couvrant Pokémon, moves, abilities, types, fusions, sprites, triple-fusions, générations, créateurs, stats, IA. **53 tests pytest** (voir [backend/tests/](backend/tests/)).

**Optimisations DB** (PR #9 en cours) — index `idx_fusion_sprite_body` (seq scan 7.8ms → BitmapOr 2.76ms sur `/fusions/involving`), contrainte partielle `uq_fusion_sprite_default`, `compute_fusion_abilities` 2→1 query.

**Pistes restantes**
- [ ] **CI full pytest** — le workflow actuel ne lance que `test_ai.py` (les autres ont besoin d'un dump SQL committé sous `backend/tests/fixtures/`)
- [ ] Endpoints pour les nouveaux ajouts BDD (tutors, TM enrichi)

## Frontend Next.js — 🚧 en cours

Pages en place : `/pokedex` + `/pokedex/[id]`, `/fusion` + `/fusion/[headId]/[bodyId]`, `/moves`, `/types`, `/abilities`, `/ai`. Proxy runtime `/api/*` + `/sprites-cdn/*`. Composants : EvolutionChain, MovesetTable, PokemonCard, FusionSprite, AiChat, etc. Hooks typés : useFusion, useMoves, usePokemon, useAiChat.

**Pistes restantes**
- [ ] Page triple-fusions (tab dédié)
- [ ] Galerie sprites + crédits (par créateur)
- [ ] Toggle EN/FR global persistent
- [ ] Tests Playwright
- [ ] UI transparence IA (cf. section IA ci-dessous)

## IA — 🎯 cible v1.0 : assistant agentique avec cascade retrieval

L'objectif n'est plus un simple chat générique branché sur DeepSeek, mais un **assistant agentique** qui interroge la BDD, le wiki IF et le web de façon structurée, avec refus explicite en cas d'absence de donnée et transparence sur ce qui est envoyé au LLM.

### Principes de conception

1. **Tool calling natif** — DeepSeek (OpenAI-compatible function calling) choisit quels tools appeler
2. **Cascade de retrieval** — DB interne → wiki IF (MediaWiki API) → web (DuckDuckGo)
3. **Fail-closed** — si aucun tool ne remonte d'info pertinente, réponse explicite `"Je n'ai pas trouvé cette information."` — jamais d'invention
4. **Transparence** — l'UI montre quels tools ont été appelés, quelles sources, combien de tokens
5. **Privacy first** — couche de redaction PII (noms de créateurs, futurs usernames) **avant** envoi au LLM
6. **Provider pluggable** — interface `LLMProvider` abstraite, implémentations DeepSeek / OpenAI / Anthropic / Ollama

### Phases d'implémentation

Chaque phase = une PR + un post LinkedIn *building in public*.

| Phase | Scope | Livrables clés |
|-------|-------|----------------|
| 1 | **Tools DB + refus strict** | 4-5 tools (`get_pokemon`, `get_fusion`, `search_moves`, `get_locations`, `get_tutors`), JSON schema, boucle tool-call, system prompt anti-hallucination, circuit breaker (max 5 tool calls/turn) |
| 2 | **Tool MediaWiki IF** | Factorisation avec `etl/utils/wikitext.py`, résumé des pages longues, cache TTL, user-agent poli |
| 3 | **Tool DuckDuckGo** | Fallback dernier recours, rate-limit, summarize les résultats avant ré-injection |
| 4 | **UI transparence** | Afficher les sources utilisées, compteur tokens, bouton « voir le prompt envoyé » |
| 5 | **Privacy layer + provider pluggable** | PII redactor (créateurs), `LLMProvider` ABC, config via env |

### Contraintes techniques

- **Latence** : cascade complète ≤ 6s (SLA cible). Si dépassé, un mode `/ai/ask-fast` (DB only) reste disponible.
- **Coûts** : compter tokens par session, alerte si > seuil configurable.
- **Context window** : DeepSeek chat = 64k tokens. Compression/troncation des tool results si besoin.
- **Boucles infinies** : max 5 tool calls/turn, sinon fail-closed.

### Précisions use-case

L'assistant cible 3 usages (par ordre de priorité) :
1. **Expliquer une fusion** — "Pourquoi cette fusion a tel type ?", "Quels moves intéressants ?"
2. **Recommandations stratégiques** — "Donne-moi une fusion anti-Psychic avec Pikachu en head"
3. **Q&A mécaniques IF** — "Comment fonctionnent les Move Experts ?", "Où est le Mystic Water ?"

## Infra — ✅ v1 stable

- Docker Compose dev + override `docker-compose.prod.yml`
- Ports env-driven (préfixe 5)
- Proxy Next.js `/api/*` et `/sprites-cdn/*` (masque les URLs backend)
- CORS defense-in-depth côté FastAPI
- CI GitHub Actions — smoke test sur PR backend

**Pistes restantes**
- [ ] Dump SQL fixture → full pytest en CI
- [ ] Choix de l'hébergement (Fly.io, Railway, VPS ?)
- [ ] TLS + domaine pour la démo publique
- [ ] Déployer la doc MkDocs (GitHub Pages ?)

## Documentation — 🚧 en cours

MVP documentaire livré (PR #8) : 9 pages MkDocs Material + référence auto-générée via `mkdocstrings`. Build strict vert. Hébergée via profil Compose `docs` sur `:58100`.

**Pistes restantes**
- [ ] Diagrammes Mermaid enrichis (séquences, ERD complet)
- [ ] Guide contributeur (`CONTRIBUTING.md`)
- [ ] Captures d'écran frontend
- [ ] Page dédiée à l'architecture IA agentique (après phase 1)

## Cap v1.0

Les critères pour désarchiver les plans initiaux et considérer l'app complète :

- Frontend stable (toutes les pages principales, pas de bugs bloquants)
- **IA agentique phase 1-2 livrée** (tool calling DB + wiki IF + refus strict)
- CI full verte (dump fixture committé)
- Déploiement public accessible
- Documentation à jour sur chaque page

Les phases 3-5 IA (DDG, transparence, privacy) sont cibles **v1.1** — amélioration continue post-lancement.
