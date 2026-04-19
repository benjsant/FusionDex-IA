# Modèles DB (SQLAlchemy)

Tables et relations — auto-généré depuis `backend/db/models/`.

Pour la vue **relationnelle** (ERD, contraintes FK, cascade), voir plutôt
[Base de données](../database.md).

## Entités principales

### Pokémon

::: backend.db.models.pokemon

### Move

::: backend.db.models.move

### Ability

::: backend.db.models.ability

### Type

::: backend.db.models.type_

### Generation

::: backend.db.models.generation

### Location

::: backend.db.models.location

### Creator

::: backend.db.models.creator

## Relations many-to-many (tables de jonction)

### PokemonType

::: backend.db.models.pokemon_type

### PokemonAbility

::: backend.db.models.pokemon_ability

### PokemonMove

::: backend.db.models.pokemon_move

### PokemonLocation

::: backend.db.models.pokemon_location

### PokemonEvolution

::: backend.db.models.pokemon_evolution

### TypeEffectiveness

::: backend.db.models.type_effectiveness

## Fusions

### FusionSprite

::: backend.db.models.fusion_sprite

### TripleFusion

::: backend.db.models.triple_fusion

### MoveExpertMove

::: backend.db.models.move_expert_move

## Divers

### TM

::: backend.db.models.tm
