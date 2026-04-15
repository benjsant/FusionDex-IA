from pydantic import BaseModel


class CoverageOut(BaseModel):
    pokemon_total: int
    pokemon_without_sprite: int
    pokemon_without_types: int
    pokemon_without_abilities: int
    pokemon_without_moves: int
    moves_total: int
    moves_unused: int  # moves never learned by any Pokémon
    abilities_total: int
    abilities_unused: int
    fusion_sprites_total: int
    triple_fusions_total: int
    creators_total: int
