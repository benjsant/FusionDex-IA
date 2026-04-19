# Référence du code

Cette section est **auto-générée** à partir des docstrings du code Python via [mkdocstrings](https://mkdocstrings.github.io/). Elle reste **synchronisée avec la source** — pas besoin de la maintenir à la main.

## Organisation

| Page | Contenu |
| --- | --- |
| [Routes](routes.md) | Endpoints FastAPI (un par domaine) — signatures, params, docstrings. |
| [Services](services.md) | Couche métier — requêtes DB, règles de fusion, calculs de stats. |
| [Schemas](schemas.md) | Modèles Pydantic utilisés en I/O (validation + documentation OpenAPI). |
| [Modèles DB](models.md) | Tables SQLAlchemy — relations, contraintes, colonnes. |

## Pour contribuer à cette ref

- Ajoute des **docstrings** aux fonctions / classes / modules : elles apparaîtront automatiquement ici.
- Pour aller plus loin : style Google docstrings avec sections `Args:`, `Returns:`, `Raises:`.
- Les symboles préfixés par `_` (privés) sont **exclus** de la ref (cf. `filters` dans `mkdocs.yml`).

Pour la vue narrative des mêmes composants (schémas d'architecture, workflows, décisions), voir plutôt :

- [Architecture](../architecture.md)
- [API backend](../api.md)
- [ETL](../etl.md)
- [Règles de fusion](../fusion-rules.md)
