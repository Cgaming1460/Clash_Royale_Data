import asyncio
import os

from flask import Flask, render_template, request
from Data_Searcher import initialize  # or data_searcher, depending on filename

app = Flask(__name__)


@app.route('/')
@app.route('/home')
def main_page():
    return render_template('main_page.html')


@app.route('/submit', methods=["POST"])
def submit():
    api_key = os.getenv("CR_API_KEY")
    if not api_key:
        # Fail fast if the server isn't configured properly
        return "Server configuration error: CR_API_KEY is not set.", 500

    user_tag = request.form["tag"].strip()  # maybe .upper() if tags are uppercase
    player = asyncio.run(initialize(api_key, user_tag, 1))

    # initialize() returns a string if something went wrong
    if isinstance(player, str):
        # Send the error into the template instead of crashing
        return render_template(
            'data_page.html',
            tag=user_tag,
            trophies=None,
            exp_level=None,
            cards=None,
            placeholder=player,  # show the error message
        )

    # Data I'm retrieving
    trophies = player.trophies if 'fetch_trophies' in request.form else None
    exp_level = player.exp_level if 'fetch_exp_level' in request.form else None
    cards = player.cards if 'fetch_cards' in request.form else None
	arena_name = player.arena.name if 'fetch_arena_name' in request.form else None
	arena_id = player.arena.id if 'fetch_arena_id' in request.form else None
	current_deck = player.current_deck if 'fetch_current_deck' in request.form else None
	clan = player.clan if 'fetch_clan' in request.form else None
	clan_name = player.clan.name if 'fetch_clan_name' in request.form else None
	badges = player.badges if 'fetch_badges' in request.form else None
	league_stats = player.league_statistics if 'fetch_league_stats' in request.form else None
	
	
	
    
    
    
    
    
    if trophies is None and exp_level is None and cards is None:
        placeholder = "You didn't select any data to fetch."
    else:
        placeholder = ""

    return render_template(
        'data_page.html',
        tag=user_tag,
        trophies=trophies,
        exp_level=exp_level,
        cards=cards,
        placeholder=placeholder,
    )


if __name__ == '__main__':
    app.run(debug=True)


