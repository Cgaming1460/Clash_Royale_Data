import aiohttp
from clashroyale.official_api import Client
from clashroyale.errors import NotFoundError, Unauthorized, RatelimitError


async def initialize(api_key: str, tag: str, choice: int=1, clan_tag: str="",):
    """
    Fetch a Clash Royale player by tag.

    Returns:
        - player object if successful
        - string error message if something goes wrong
    """
    async with aiohttp.ClientSession() as session:
        client = Client(
            token=api_key,
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
        match choice:  # Selection 
			case 1:
				try:
					return await client.get_player(tag)
				except NotFoundError:
					return "No such player tag."
				except Unauthorized:
					return "Check your API token."
				except RatelimitError:
					return "You hit the rate limit. Slow down."
			case 2:
				try:
					return await client.get_player_battles(tag, limit=10)
				except NotFoundError:
					return "No such player tag."
				except Unauthorized:
					return "Check your API token."
				except RatelimitError:
					return "You hit the rate limit. Slow down."
			case 3:
				try:
					return await client.get_clan(clan_tag)
				except NotFoundError:
					return "No such clan tag."
				except Unauthorized:
					return "Check your API token."
				except RatelimitError:
					return "You hit the rate limit. Slow down."
			case 4:
				try:
					return await client.get_clan_members(clan_tag, limit=50)
				except NotFoundError:
					return "No such clan tag."
				except Unauthorized:
					return "Check your API token."
				except RatelimitError:
					return "You hit the rate limit. Slow down."
			case 5:
				try:
					return await client.get_all_cards()
				except Unauthorized:
					return "Check your API token."
				except RatelimitError:
					return "You hit the rate limit. Slow down."
			case 6:
				try:
					return await client.get_top_players("global", limit=10)
				except Unauthorized:
					return "Check your API token."
				except RatelimitError:
					return "You hit the rate limit. Slow down."	
			case _:
				raise ValueError("This value goes outside of the range 1-6")		
				
				

