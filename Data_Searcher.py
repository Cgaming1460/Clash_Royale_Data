
# 1. This is the actual logic for connecting with the Clash API and
#    getting that data, we import this into the main.py file, you can
#    see that in 'from Data_Searcher import initialize' this file is
#    Data_Searcher.py

# IMPORTANT NOTE, any flashy code separations and the _extract_items
# function is done with the help of AI, as a backend developer I still
# need to go over such concepts and consolidate my understanding - I apologise.

"""
Data_Searcher
~~~~~~~~~~~~~

Async helper for talking to the Clash Royale official API.

Public entrypoint:
    async initialize(api_key: str, tag: str, choice: int = 1, clan_tag: str = "")

`choice` decides what we fetch:

    1 -> Player profile by player tag (`tag`)
    2 -> Recent battles for a player (`tag`)
    3 -> Clan info by clan tag (uses `clan_tag` if given, otherwise `tag`)
    4 -> All cards in the game (no tag needed)
    5 -> Top players globally (no tag needed)
    6 -> Top clans globally (no tag needed)

Return value:
    - On success: the object / list returned by the API (often a list of dicts)
    - On failure: a human-readable error string
"""

# 2. Importing foreign code to help with the process, you can see
#    the clash royale related code that's being imported
from __future__ import annotations

from typing import Any, List

import aiohttp
from clashroyale.official_api import Client
from clashroyale.errors import NotFoundError, Unauthorized, RatelimitError


def _extract_items(result: Any) -> List[Any]:
    """
    Normalise Clash Royale API results that contain lists.

    The wrapper is a bit inconsistent:
      * Sometimes result.raw_data is a dict: {"items": [...], "paging": {...}}
      * Sometimes result.raw_data is already a list: [...]
      * Sometimes result itself is already the list

    This helper always returns a plain Python list.
    """
    # Prefer raw_data if it exists
    raw = getattr(result, "raw_data", result)

    # Case 1: {"items": [...]} style
    if isinstance(raw, dict):
        items = raw.get("items")
        if isinstance(items, list):
            return items
        # If "items" exists but isn't a list, best effort:
        if items is not None:
            try:
                return list(items)
            except TypeError:
                return [items]
        return []

    # Case 2: already a list
    if isinstance(raw, list):
        return raw

    # Fallback: single object → wrap in a list (better than crashing)
    return [raw] if raw is not None else []


async def initialize(  # 3. You can see initialize being used in main.py
    api_key: str,
    tag: str,
    choice: int = 1,
    clan_tag: str = "",
    battle_limit=None,
    limit: int=10,
):
    """
    Main async entrypoint used by Flask via asyncio.run().

    Parameters
    ----------
    api_key : str
        Clash Royale API token.
    tag : str
        For choices 1 & 2: player tag.
        For choice 3 (clan): used as the clan tag if `clan_tag` is not provided.
        Ignored for choices 4–6.
    choice : int
        Selects which kind of data to fetch (see module docstring).
    clan_tag : str, optional
        Alternative way to pass the clan tag for choice 3. If this is a
        non-empty string, it takes priority over `tag`.

    Returns
    -------
    - On success: API object / list
    - On failure: error string
    """
    async with aiohttp.ClientSession() as session: # 4. Starting the 
        client = Client(                           #    connection
            token=api_key,                         #    session
            is_async=True,
            session=session,
            error_debug=False,
            timeout=15,
            cache_fp="clash_cache.db",
            cache_expires=60,
            table_name="cr_cache",
            user_agent="MyClashApp/2.0",
            camel_case=False,
        )

        # Decide which clan identifier to use (for choice 3)
        clan_identifier = clan_tag or tag

        # ------------------------------------------------------------------ #
        # Player profile
        # ------------------------------------------------------------------ #
        if choice == 1:
            try:
                return await client.get_player(tag)
            except NotFoundError:
                return "No such player tag."
            except Unauthorized:
                return "Check your API token."
            except RatelimitError:
                return "You hit the rate limit. Slow down."

        # ------------------------------------------------------------------ #
        # Player battles
        # ------------------------------------------------------------------ #
        if choice == 2:
            try:
                return await client.get_player_battles(tag)
            except NotFoundError:
                return "No such player tag."
            except Unauthorized:
                return "Check your API token."
            except RatelimitError:
                return "You hit the rate limit. Slow down."

        # ------------------------------------------------------------------ #
        # Clan by tag
        # ------------------------------------------------------------------ #
        if choice == 3:
            try:
                return await client.get_clan(clan_identifier)
            except NotFoundError:
                return "No such clan tag."
            except Unauthorized:
                return "Check your API token."
            except RatelimitError:
                return "You hit the rate limit. Slow down."

        # ------------------------------------------------------------------ #
        # All cards
        # ------------------------------------------------------------------ #
        if choice == 4:
            try:
                result = await client.get_all_cards()
                items = _extract_items(result)
                # For cards we just return [] if empty (could also turn into error string
                # if you want similar behaviour to choices 5 & 6)
                return items
            except Unauthorized:
                return "Check your API token."
            except RatelimitError:
                return "You hit the rate limit. Slow down."

        # ------------------------------------------------------------------ #
        # Top players (global)
        # ------------------------------------------------------------------ #
        if choice == 5:
            try:
                result = await client.get_top_players("global", limit=limit)
                # We only care about the first page → no async iteration
                items = _extract_items(result)
                if not items:
                    # Turn "empty items" into an error string so Flask can show it
                    return "API: no top players data returned (items was empty)."
                return items
            except Unauthorized:
                return "Check your API token."
            except RatelimitError:
                return "You hit the rate limit. Slow down."

        # ------------------------------------------------------------------ #
        # Top clans (global)
        # ------------------------------------------------------------------ #
        if choice == 6:
            try:
                result = await client.get_top_clans(limit=limit)
                # First page only; avoids buggy async generator path
                items = _extract_items(result)
                if not items:
                    return "API: no top clans data returned (items was empty)."
                return items
            except Unauthorized:
                return "Check your API token."
            except RatelimitError:
                return "You hit the rate limit. Slow down."

        # ------------------------------------------------------------------ #
        # Unknown choice
        # ------------------------------------------------------------------ #
        raise ValueError("Choice must be an integer between 1 and 6.")
