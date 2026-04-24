"""DeepSeek AI service — tool-calling agent avec cascade BDD + fail-closed.

Phase 1 de l'assistant agentique (cf. ROADMAP.md § IA) :
  1. Le LLM reçoit la question + la liste de tools (specs JSON Schema)
  2. Il peut choisir d'appeler 1+ tools → on les exécute, on renvoie les
     résultats, on reboucle
  3. Quand le LLM rend une réponse textuelle → on la stream à l'UI
  4. Si aucune réponse après MAX_ITERATIONS → refus explicite
     (*« Je n'ai pas trouvé cette information. »*)

La boucle est non-streamée ; seul le texte final est streamé en SSE.
Cela permet d'inspecter `tool_calls` avant de décider quoi envoyer à
l'utilisateur.

Environnement : `DEEPSEEK_API_KEY` requis. Le service est fail-closed :
sans clé, `/ai/ask` répond 503 (non géré ici, mais côté route).
"""

from __future__ import annotations

import json
import logging
import os
from typing import AsyncIterator

from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from backend.services.ai_tools import TOOL_SPECS, dispatch_tool

LOGGER = logging.getLogger(__name__)

# ─── Configuration ───────────────────────────────────────────────────────────

MODEL            = "deepseek-chat"
BASE_URL         = "https://api.deepseek.com"
MAX_ITERATIONS   = 5       # circuit breaker : 5 tours d'appels tools max
MAX_TOKENS       = 1024
TEMPERATURE      = 0.3     # basse pour réponses factuelles
FAILURE_MESSAGE  = "Je n'ai pas trouvé cette information."

SYSTEM_PROMPT = """Tu es FusionDex AI, assistant spécialisé du jeu Pokémon Infinite Fusion (fan-game basé sur les Gen 1-2 avec système de fusions, Move Experts, TMs, etc.).

Règles STRICTES à respecter :

1. Utilise toujours les outils (tools) mis à ta disposition pour répondre aux questions sur les Pokémon, fusions, moves, items et Move Tutors. Ne réponds JAMAIS à partir de ta mémoire de Pokémon générale.

2. N'invente JAMAIS aucune information. Toute affirmation factuelle doit provenir d'un résultat de tool.

3. Si aucun tool ne retourne d'information pertinente à la question, réponds EXACTEMENT :
   "Je n'ai pas trouvé cette information."
   Ne tente pas de deviner ou de compléter.

4. Tu peux enchaîner plusieurs tool calls (ex: résoudre un Pokémon puis consulter sa fusion) mais reste efficace.

5. Réponds en français par défaut ; en anglais si l'utilisateur écrit en anglais.

6. Sois concis, précis, et cite les valeurs concrètes retournées par les tools (stats, prix, localisations)."""


def _get_client() -> AsyncOpenAI:
    """Factory — lève RuntimeError si `DEEPSEEK_API_KEY` est absente."""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY environment variable not set")
    return AsyncOpenAI(api_key=api_key, base_url=BASE_URL)


# ─── Boucle tool-calling ─────────────────────────────────────────────────────

async def stream_ai_response(
    db: Session,
    message: str,
    context: str | None = None,
) -> AsyncIterator[str]:
    """Agent loop : tool calls → résultats → boucle → streaming de la réponse finale.

    Args:
        db: Session SQLAlchemy (passée aux handlers de tools).
        message: Question de l'utilisateur.
        context: Contexte optionnel injecté par l'UI (sélection courante).

    Yields:
        Chunks de texte (réponse finale OU message de refus fail-closed).
    """
    client = _get_client()

    user_content = message
    if context:
        user_content = f"[Contexte: {context}]\n\n{message}"

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_content},
    ]

    for iteration in range(MAX_ITERATIONS):
        LOGGER.debug("AI loop iteration %d/%d", iteration + 1, MAX_ITERATIONS)

        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SPECS,
            tool_choice="auto",
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            # Ajoute le message assistant (avec tool_calls) avant les résultats.
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id":   tc.id,
                        "type": "function",
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })
            # Exécute chaque tool call, append son résultat en tant que
            # message "tool" référencé par tool_call_id.
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError as exc:
                    result = {"error": f"Invalid JSON arguments: {exc}"}
                else:
                    result = dispatch_tool(db, tc.function.name, args)

                LOGGER.debug("Tool %s → %s", tc.function.name,
                             "error" if "error" in result else "ok")

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      json.dumps(result, ensure_ascii=False),
                })
            # Reboucle pour laisser le LLM raisonner sur les résultats.
            continue

        # Pas de tool_calls → réponse textuelle finale.
        content = (msg.content or "").strip()
        if not content:
            yield FAILURE_MESSAGE
            return
        yield content
        return

    # Max iterations atteintes sans réponse finale → fail-closed.
    LOGGER.warning("Max iterations (%d) reached without final response", MAX_ITERATIONS)
    yield FAILURE_MESSAGE
