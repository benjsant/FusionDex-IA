# Roadmap

Version live du suivi : [ROADMAP.md](https://github.com/benjsant/FusionDex-IA/blob/main/ROADMAP.md) à la racine du repo. Cette page reprend l'état au moment de la dernière mise à jour de la doc et liste les pistes ouvertes.

## État par couche

### ETL — ✅ stabilisé

Pipeline en 12 étapes. Données actuelles :

- **572 Pokémon** (501 IF + 71 formes)
- **676 moves** · **178 abilities** · **40 067** pokemon_move
- **166 090** fusion_sprite · **23** triple_fusion
- **7 081** créateurs · **1 634** pokemon_location
- **65** règles Move Expert (36 Knot + 29 Boon)

**Pistes ouvertes :**

- [ ] Audit DB — Pokémon sans sprites, moves orphelins, cohérence des fusions
- [ ] Scheduler (Prefect ou n8n) pour automatiser les refresh

### Base de données — 🚧 ajouts planifiés

Avant d'exploiter la cascade IA, enrichir les données structurées :

- [ ] **Move tutors** — nouvelle table `move_tutor(move_id, location_id, price, currency, notes)` scrapée depuis le wiki IF
- [ ] **TM location** — nettoyer `tm.location` (texte libre avec bugs de parsing) et la lier via FK à `location(id)`
- [ ] **Endpoint `/moves/{id}` enrichi** — inclure TM number + location + tutors

### Backend — ✅ base solide

36 endpoints (+ `/health`) + 53 tests pytest verts. Couvre pokémon, moves, abilities, types, fusions, sprites, triple-fusions, générations, créateurs, stats, IA.

**Optimisations DB** (PR #9) : `idx_fusion_sprite_body` (seq scan 7.8ms → BitmapOr 2.76ms), contrainte partielle `uq_fusion_sprite_default`, `compute_fusion_abilities` 2→1 query.

**Pistes ouvertes :**

- [ ] **CI full pytest** — actuellement seul `test_ai.py` tourne. Le reste nécessite un dump SQL fixture à committer sous `backend/tests/fixtures/`
- [ ] Endpoints pour les nouveaux ajouts BDD (tutors, TM enrichi)

### Frontend — 🚧 en cours

Fondations posées : Pokédex (liste + fiche), Fusion (sélecteur + résultat), composants (EvolutionChain, MovesetTable, PokemonCard, FusionSprite, AiChat…), hooks typés. Toutes les pages principales livrées : `/pokedex`, `/fusion`, `/moves`, `/types`, `/abilities`, `/ai`.

**Pistes ouvertes :**

- [ ] Page triple-fusions (tab dédié)
- [ ] Galerie sprites + crédits (par créateur)
- [ ] Toggle EN/FR global persistent
- [ ] Tests Playwright
- [ ] UI transparence IA (sources, tokens, prompt envoyé)

### IA — 🎯 cible v1.0 : assistant agentique

L'objectif v1.0 dépasse le chat générique branché sur DeepSeek : c'est un **assistant agentique** qui interroge la BDD, le wiki IF et le web de façon structurée, avec refus explicite quand la donnée manque, et transparence sur ce qui est envoyé au LLM.

**Principes**

1. **Tool calling natif** (DeepSeek function calling, compatible OpenAI)
2. **Cascade retrieval** : DB interne → wiki IF (MediaWiki API) → web (DuckDuckGo)
3. **Fail-closed** : si aucun tool ne remonte d'info pertinente, réponse explicite *« Je n'ai pas trouvé cette information. »* — jamais d'invention
4. **Transparence** : l'UI montre les tools appelés, les sources, les tokens
5. **Privacy first** : couche PII redactor (créateurs, futurs usernames) **avant** envoi au LLM
6. **Provider pluggable** : interface `LLMProvider` abstraite (DeepSeek / OpenAI / Anthropic / Ollama)

**Phases** — chaque phase = une PR + un post *building in public* :

| Phase | Scope |
|-------|-------|
| 1 | Tools DB (4-5) + refus strict + circuit breaker |
| 2 | Tool MediaWiki IF + résumé + cache |
| 3 | Tool DuckDuckGo (fallback) + rate-limit |
| 4 | UI transparence (sources, tokens, prompt) |
| 5 | Privacy layer + provider pluggable |

**Contraintes**

- Latence cascade ≤ 6s (sinon mode `/ai/ask-fast` DB only)
- Max 5 tool calls par tour (circuit breaker)
- Compression des tool results pour éviter blow du context window (64k)
- Compteur tokens par session avec alertes

### Infra — ✅ v1 stable

- Docker Compose dev + override `docker-compose.prod.yml`
- Ports env-driven (préfixe 5)
- Proxy Next.js `/api/*` et `/sprites-cdn/*` (masque les URLs backend)
- CORS defense-in-depth côté FastAPI
- CI GitHub Actions — smoke test sur PR backend

**Pistes ouvertes :**

- [ ] Dump SQL fixture → full pytest en CI
- [ ] Choix de l'hébergement (Fly.io, Railway, VPS ?)
- [ ] TLS + domaine pour la démo publique
- [ ] Déployer la doc MkDocs (GitHub Pages ?)

### Documentation — 🚧 en cours

MVP documentaire livré : 9 pages MkDocs Material + référence auto (PR #8). Build strict vert. Profil Compose `docs` sur `:58100`.

**Pistes ouvertes :**

- [ ] Diagrammes Mermaid enrichis (séquences, ERD complet)
- [ ] Guide contributeur (`CONTRIBUTING.md` + pointeur depuis ici)
- [ ] Captures d'écran frontend
- [ ] Page dédiée à l'architecture IA agentique (après phase 1)

## Cap v1.0

Les critères pour désarchiver les plans initiaux et considérer l'app complète :

- Frontend stable (toutes les pages principales en place, pas de bugs bloquants)
- **IA agentique phases 1-2 livrées** (tool calling DB + wiki IF + refus strict)
- CI full verte (dump fixture committé)
- Déploiement public accessible
- Documentation à jour sur chaque page

Les phases 3-5 IA (DDG, transparence, privacy) sont cibles **v1.1** — amélioration continue post-lancement.

Avant cette étape, les docs historiques restent figées sous [Archive](archive/index.md).
