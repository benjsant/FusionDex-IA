# Base de données

PostgreSQL 16. Schéma défini dans [docker/init_postgres.sql](https://github.com/), modèles SQLAlchemy dans [backend/db/models/](https://github.com/).

## Tables principales

### Référentiels

| Table          | Contenu                                      | Volume |
| -------------- | -------------------------------------------- | ------ |
| `type`         | 18 types Pokémon (EN + FR)                   | 18     |
| `ability`      | Talents (EN + FR + description)              | 178    |
| `move`         | Capacités (nom, type, puissance, PP, …)      | 676    |
| `generation`   | Générations (1–9)                            | 9      |
| `creator`      | Créateurs de sprites (attribution)           | 7 081  |

### Pokémon & évolutions

| Table                   | Contenu                                               |
| ----------------------- | ----------------------------------------------------- |
| `pokemon`               | 501 Pokémon IF + 71 formes = **572 entrées**          |
| `pokemon_type`          | Types primaires/secondaires (FK vers `type`)          |
| `pokemon_ability`       | Talents disponibles (normaux + cachés)                |
| `pokemon_move`          | Learnset : 40 067 lignes (level-up, TM, tutor, egg)   |
| `pokemon_evolution`     | Arbres d'évolution (pre + post)                       |
| `pokemon_location`      | Zones de capture IF                                   |

### Fusions

| Table              | Contenu                                                       |
| ------------------ | ------------------------------------------------------------- |
| `fusion_sprite`    | 166 090 sprites custom (head_id, body_id, variant, path, crédit) |
| `triple_fusion`    | 23 fusions triples reconnues                                  |
| `move_expert_move` | 65 règles Move Expert (Knot Island + Boon Island)             |

## Focus : `move_expert_move`

Table atypique, introduite pour modéliser les Move Experts sans multiplier les tables de jonction.

```sql
CREATE TABLE move_expert_move (
    id                   SERIAL      PRIMARY KEY,
    move_id              INTEGER     NOT NULL REFERENCES move(id) ON DELETE CASCADE,
    expert_location      VARCHAR(20) NOT NULL CHECK (expert_location IN ('knot_island', 'boon_island')),
    required_pokemon_ids INTEGER[]   NOT NULL DEFAULT '{}',
    required_type_ids    INTEGER[]   NOT NULL DEFAULT '{}',
    required_move_ids    INTEGER[]   NOT NULL DEFAULT '{}'
);
```

Chaque ligne = une règle. Une fusion peut satisfaire plusieurs règles pour le même move (d'où la liste de `locations` dans la réponse API).

**Sémantique** (cf. [Règles de fusion](fusion-rules.md#move-experts)) :

- **Au sein d'une ligne** : AND entre axes (pokémon requis × types requis × moves requis).
- **Axe `required_pokemon_ids`** : OR — head OU body doit être dans la liste.
- **Axe `required_type_ids`** : superset — la fusion doit avoir **tous** les types listés.
- **Axe `required_move_ids`** : intersection — au moins un move en commun.
- **Tableau vide** sur un axe = aucune contrainte sur cet axe.
- **Entre lignes** : OR — une ligne suffit pour débloquer le move à cet emplacement.

## Index utiles

```sql
CREATE INDEX idx_pokemon_move_pokemon ON pokemon_move(pokemon_id);
CREATE INDEX idx_fusion_sprite_head ON fusion_sprite(head_id);
CREATE INDEX idx_fusion_sprite_body ON fusion_sprite(body_id);
CREATE INDEX idx_move_expert_location ON move_expert_move(expert_location);
```

## Conventions

- Noms EN : clé primaire de recherche (sources PokeAPI/wiki).
- Noms FR : colonne `name_fr` nullable (Poképédia, complétion progressive).
- `national_dex_id` : ID officiel PokeAPI (nullable pour les formes IF exclusives).
- Tous les `ON DELETE` utilisent `CASCADE` sur les jointures pour garder la cohérence si on regénère une table référentielle.

## Voir aussi

- [ETL](etl.md) — comment la base est peuplée.
- [docker/init_postgres.sql](https://github.com/) — source de vérité du schéma.
