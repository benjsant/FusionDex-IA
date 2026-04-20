# Schemas Pydantic

Modèles d'I/O — auto-généré depuis `backend/schemas/`.

Chaque endpoint accepte et retourne des **schemas Pydantic**, ce qui permet :

- Validation des payloads entrants (FastAPI lève `422` sur payload invalide)
- Sérialisation typée des réponses
- Génération automatique du schéma OpenAPI (`/docs`, `/redoc`)

## Pokémon

::: backend.schemas.pokemon

## Fusion

::: backend.schemas.fusion

## Triple fusion

::: backend.schemas.triple_fusion

## Moves

::: backend.schemas.move

## Abilities

::: backend.schemas.ability

## Types

::: backend.schemas.type_

## Générations

::: backend.schemas.generation

## Évolutions

::: backend.schemas.evolution

## Locations

::: backend.schemas.location

## Faiblesses

::: backend.schemas.weakness

## Créateurs de sprites

::: backend.schemas.creator

## Sprites

::: backend.schemas.sprite

## Stats d'audit

::: backend.schemas.stats

## IA (DeepSeek)

::: backend.schemas.ai
