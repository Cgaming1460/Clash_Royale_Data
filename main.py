# 1. Importing the external code we need
import asyncio
import os

from flask import Flask, render_template, request
from Data_Searcher import initialize


# 2. Basically what happens to find the api key, ignore this if you
#    don't have the environment variable set up, look to step 3
def get_api_key_or_500():
    """
    Try to read the Clash Royale API key from the environment.

    Returns:
        (api_key, error_response)
        - api_key: the string key, or None if missing
        - error_response: a (message, status_code) tuple suitable for
          returning from a Flask view, or None if everything is OK.
    """
    # 3. Take away the hashtags from with open... and api_key ...,
    #    then ADD a hashtag to api_key = os.getenv("CR_API_KEY").
    #    you will need to have extracted the file using the password
    
    #with open("API_KEY.txt", "r") as f:
       #api_key = f.read().strip()
    
    api_key = os.getenv("CR_API_KEY")
    if not api_key:
        return None, (
            "Server configuration error: CR_API_KEY is not set.",
            500,
        )
    return api_key, None  # 4. We are basically getting back the 
                          #    key and/or an error message


# 5. Kinda like pressing start to the system
app = Flask(__name__)


# 6. Every @app.route() is a different section of webpage ( / = start)
@app.route("/")
@app.route("/home")
def main_page():
    # 7. The homepage is this file
    return render_template("Main_page.html")


# 8. This is a section of the website that deals with the player
#    data lookup, try read through the code if you understand any
@app.route("/player", methods=["GET", "POST"])
def player_data():
    """
    Player lookup page.

    - Only calls the API for the data the user actually requested.
    - Allows partial success: e.g. battles work even if player profile fails.
    - Gives a clearer message when league statistics are missing.
    """
    if request.method == "GET":
        return render_template("Player_ds.html")

    api_key, error_response = get_api_key_or_500()
    if error_response:
        return error_response

    user_tag = request.form["tag"].strip()

    # What does the user want?
    player_fields_keys = (
        "fetch_trophies",
        "fetch_exp_level",
        "fetch_cards",
        "fetch_arena_name",
        "fetch_arena_id",
        "fetch_current_deck",
        "fetch_badges",
        "fetch_league_statistics",
    )

    want_any_player_field = any(key in request.form for key in player_fields_keys)
    want_battles = "fetch_battle_data" in request.form

    # If they didn't tick anything, bail early (no API calls)
    if not (want_any_player_field or want_battles):
        return render_template(
            "Player_dp.html",
            tag=user_tag,
            trophies=None,
            exp_level=None,
            cards=None,
            placeholder="You didn't select any data to fetch.",
            arena_name=None,
            arena_id=None,
            current_deck=None,
            league_statistics=None,
            battle_data=None,
            badges=None,
            battle_limit=None,
        )

    player = None
    battle_data = None
    player_error_msg = None
    battle_error_msg = None

    # 9. player info
    if want_any_player_field:
        player = asyncio.run(initialize(api_key, user_tag, 1))
        if isinstance(player, str):
            player_error_msg = player
            player = None  # ensure we don't try to read attributes from a string

    # 10. battles
    if want_battles:
        battle_data = asyncio.run(initialize(api_key, user_tag, 2))
        if isinstance(battle_data, str):
            battle_error_msg = battle_data
            battle_data = None

    # 11. Seeing what the user has ticked
    if player is not None:
        trophies = player.trophies if "fetch_trophies" in request.form else None
        exp_level = player.exp_level if "fetch_exp_level" in request.form else None
        cards = player.cards if "fetch_cards" in request.form else None
        arena_name = player.arena.name if "fetch_arena_name" in request.form else None
        arena_id = player.arena.id if "fetch_arena_id" in request.form else None
        current_deck = (
            player.current_deck if "fetch_current_deck" in request.form else None
        )
        badges = player.badges if "fetch_badges" in request.form else None
        league_statistics = (
            player.league_statistics
            if "fetch_league_statistics" in request.form
            else None
        )
    else:
        # Either they didn't ask for player fields, or player lookup failed
        trophies = None
        exp_level = None
        cards = None
        arena_name = None
        arena_id = None
        current_deck = None
        badges = None
        league_statistics = None

    # Battle data: only if requested and not errored
    battle_data_render = (
        battle_data if (want_battles and battle_data is not None) else None
    )

    # Build placeholder from error messages, if any
    placeholder_parts = []
    if player_error_msg:
        placeholder_parts.append(player_error_msg)
    if battle_error_msg:
        placeholder_parts.append(battle_error_msg)

    # If they explicitly asked for league stats and none exist, say that
    if (
        "fetch_league_statistics" in request.form
        and league_statistics is None
        and player is not None
    ):
        placeholder_parts.append("This player has no league statistics available.")

    # If no errors/messages yet and no data at all came back, use the generic message
    if not placeholder_parts and not any(
        (
            trophies,
            exp_level,
            cards,
            arena_name,
            arena_id,
            current_deck,
            badges,
            league_statistics,
            battle_data_render,
        )
    ):
        placeholder_parts.append("No data was returned for your selection.")

    placeholder = " | ".join(placeholder_parts) if placeholder_parts else ""

    # --------- SAFE BATTLE LIMIT PARSING ----------
    # Treat empty/invalid input as "no limit" (None)
    raw_battle_limit = request.form.get("fetch_battle_limit", "").strip()
    if raw_battle_limit.isdigit():
        battle_limit = int(raw_battle_limit)
    else:
        battle_limit = None

    return render_template( #12. This is all that should be returned
        "Player_dp.html",   #    at the end
        tag=user_tag,
        trophies=trophies,
        exp_level=exp_level,
        cards=cards,
        placeholder=placeholder,
        arena_name=arena_name,
        arena_id=arena_id,
        current_deck=current_deck,
        league_statistics=league_statistics,
        battle_data=battle_data_render,
        badges=badges,
        battle_limit=battle_limit,
    )


# 13. This is the section that deals with the clan data, the procress
#     is basically the same as player's
@app.route("/clan", methods=["GET", "POST"])
def clan_data():
    if request.method == "GET":
        return render_template("Clan_ds.html")

    api_key, error_response = get_api_key_or_500()
    if error_response:
        return error_response

    clan_tag = request.form["clan_tag"].strip()

    # 3 = clan data (your initialize() design)
    clan = asyncio.run(initialize(api_key, clan_tag, 3))
    clan_error = isinstance(clan, str)

    # ---------- CASE 1: clan lookup failed ----------
    if clan_error:
        return render_template(
            "Clan_dp.html",
            clan_tag=clan_tag if clan != "No such clan tag." else None,
            clan_name=None,
            clan_score=None,
            clan_member_data=None,
            placeholder=clan,
        )

    # ---------- CASE 2: clan OK ----------
    clan_name = clan.name if "fetch_clan_name" in request.form else None
    clan_score = clan.clan_score if "fetch_clan_score" in request.form else None

    # Use the *list* of members if available
    if "fetch_clan_member_data" in request.form:
        raw_members = getattr(clan, "member_list", None)
        if isinstance(raw_members, (list, tuple)):
            clan_member_data = raw_members
        else:
            clan_member_data = None
    else:
        clan_member_data = None

    if not any((clan_name, clan_score, clan_member_data)):
        placeholder = "You didn't select any data to fetch."
    else:
        placeholder = ""

    return render_template(
        "Clan_dp.html",
        clan_tag=clan_tag,
        clan_name=clan_name,
        clan_score=clan_score,
        clan_member_data=clan_member_data,
        placeholder=placeholder,
    )


# 14. This is the section that deals with game data
@app.route("/game", methods=["GET", "POST"])
def game_data():
    """
    Overall game data page.

    - Only calls each endpoint if its checkbox was ticked.
    - Allows partial success and shows API "empty items" as messages.
    """
    if request.method == "GET":
        return render_template("Game_ds.html")

    api_key, error_response = get_api_key_or_500()
    if error_response:
        return error_response

    # What did the user actually ask for?
    want_cards = "fetch_all_cards" in request.form
    want_players = "fetch_top_players" in request.form
    want_clans = "fetch_top_clans" in request.form

    # If they didn't tick anything, bail early
    if not (want_cards or want_players or want_clans):
        return render_template(
            "Game_dp.html",
            all_cards=None,
            top_players=None,
            top_clans=None,
            placeholder="You didn't select any data to fetch.",
        )

    all_cards_data = None
    top_players_data = None
    top_clans_data = None

    all_cards_error = False
    top_players_error = False
    top_clans_error = False

    error_messages = []

    # 4 = all cards
    if want_cards:
        all_cards_data = asyncio.run(initialize(api_key, "", 4))
        if isinstance(all_cards_data, str):
            all_cards_error = True
            error_messages.append(all_cards_data)

    # 5 = top players
    if want_players:
        top_players_data = asyncio.run(initialize(api_key, "", 5))
        if isinstance(top_players_data, str):
            top_players_error = True
            error_messages.append(top_players_data)

    # 6 = top clans, with optional limit
    raw_clan_limit = request.form.get("fetch_clan_limit", "").strip()
    if raw_clan_limit.isdigit():
        clan_limit = int(raw_clan_limit)
    else:
        clan_limit = None

    if want_clans:
        if clan_limit is not None:
            top_clans_data = asyncio.run(
                initialize(api_key, "", 6, limit=clan_limit)
            )
        else:
            top_clans_data = asyncio.run(initialize(api_key, "", 6))

        if isinstance(top_clans_data, str):
            top_clans_error = True
            error_messages.append(top_clans_data)

    # Only pass successful data to the template
    all_cards = None if (not want_cards or all_cards_error) else all_cards_data
    top_players = None if (not want_players or top_players_error) else top_players_data
    top_clans = None if (not want_clans or top_clans_error) else top_clans_data

    placeholder = " | ".join(error_messages) if error_messages else ""

    # If there are no errors but everything came back empty, say so
    if not placeholder and not any((all_cards, top_players, top_clans)):
        placeholder = "No data was returned for your selection."

    return render_template(
        "Game_dp.html",
        all_cards=all_cards,
        top_players=top_players,
        top_clans=top_clans,
        placeholder=placeholder,
    )


# 15. This is just kept on for a while (it's not important), think
#     of it as confirming that the website is a 'test' area, the
#     debug=True is normally taken away in production
if __name__ == "__main__":
    app.run(debug=True)
