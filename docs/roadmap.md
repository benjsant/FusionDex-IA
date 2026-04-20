# Roadmap

Version live du suivi : [ROADMAP.md](https://github.com/) à la racine du repo. Cette page reprend l'état au moment de la dernière mise à jour de la doc et liste les pistes ouvertes.

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
- [ ] Mega-évolutions (pas couvertes)
- [ ] Scheduler (Prefect ou n8n) pour automatiser les refresh

### Backend — ✅ base solide

30+ endpoints + 53 tests pytest verts. Couvre pokémon, moves, abilities, types, fusions, sprites, triple-fusions, générations, créateurs, stats, IA.

**Pistes ouvertes :**

- [ ] **E2E DeepSeek** — tester `/ai/ask` bout-à-bout avec vraie clé
- [ ] **CI full pytest** — actuellement seul `test_ai.py` tourne. Le reste nécessite un dump SQL fixture à committer sous `backend/tests/fixtures/`
- [ ] Endpoints de recherche avancée (full-text sur moves/abilities ?)

### Frontend — 🚧 en cours

Fondations posées : Pokédex (liste + fiche), Fusion (sélecteur + résultat), composants (EvolutionChain, MovesetTable, PokemonCard, FusionSprite…), hooks typés.

**Pistes ouvertes :**

- [ ] Page triple-fusions (tab dédié)
- [ ] Galerie sprites + crédits (par créateur)
- [ ] Chat IA (intégration `useAiChat`)
- [ ] Toggle EN/FR global persistent
- [ ] Tests Playwright

### IA / DeepSeek — 🚧 à valider

Code en place (`ai_route.py` + `ai_service.py`) mais jamais testé bout-à-bout.

**Pistes ouvertes :**

- [ ] Tester l'intégration DeepSeek (clés, quotas, parsing)
- [ ] Définir le use-case principal : recommandations de fusion ? team-building ? recherche NL ?
- [ ] Garde-fous (coût, abus)

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

### Documentation — 🚧 en cours

Cette page fait partie du MVP documentaire (9 pages MkDocs Material).

**Pistes ouvertes :**

- [ ] Diagrammes Mermaid enrichis (séquences, ERD complet)
- [ ] Guide contributeur (`CONTRIBUTING.md` + pointeur depuis ici)
- [ ] Captures d'écran frontend
- [ ] Tutoriel "première fusion personnalisée" pas à pas

## Cap v1.0

Les critères pour désarchiver les plans initiaux et considérer l'app complète :

- Frontend stable (toutes les pages principales en place, pas de bugs bloquants)
- IA validée bout-à-bout avec use-case clair
- CI full verte (dump fixture committé)
- Déploiement public accessible
- Documentation à jour sur chaque page

Avant cette étape, les docs historiques restent figées sous [Archive](archive/index.md).
