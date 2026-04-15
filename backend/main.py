"""FusionDex API — FastAPI entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all models so SQLAlchemy registers them with Base
import backend.db.models  # noqa: F401

from backend.routes import (
    ability_route,
    ai_route,
    creator_route,
    fusion_route,
    generation_route,
    move_route,
    pokemon_route,
    sprite_route,
    stats_route,
    triple_fusion_route,
    type_route,
)

app = FastAPI(
    title="FusionDex API",
    description="Pokédex API for Pokémon Infinite Fusion — EN/FR",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",          # Next.js dev (host)
        "http://fusiondex_frontend:3000", # Docker internal
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def healthcheck():
    return {"status": "healthy"}


app.include_router(pokemon_route.router)
app.include_router(move_route.router)
app.include_router(ability_route.router)
app.include_router(type_route.router)
app.include_router(fusion_route.router)
app.include_router(fusion_route.plural_router)
app.include_router(generation_route.router)
app.include_router(creator_route.router)
app.include_router(sprite_route.router)
app.include_router(triple_fusion_route.router)
app.include_router(stats_route.router)
app.include_router(ai_route.router)
