import os
import modio
import discord

from dotenv import load_dotenv

load_dotenv('data/server.env')
GAMEID = os.getenv('MODIO_GAME_ID')
API_KEY = str(os.getenv('API_KEY'))
ACCESS_TOKEN = str(os.getenv('ACCESS_TOKEN'))

def is_docker():
    path = '/proc/self/cgroup'
    return (
        os.path.exists('/.dockerenv') or
        os.path.isfile(path) and any('docker' in line for line in open(path))
    )
def get_game():
    client = modio.Client(
        api_key=API_KEY,
        access_token=ACCESS_TOKEN
    )

    game = client.get_game(int(GAMEID))
    return game

def get_mods(bot, qmfilter):
    outputString = ''
    splitOutput = ''
    once = True

    modlist = bot.game.get_mods(filters=qmfilter)

    result_count = len(modlist.results)

    return modlist, result_count

def custom_cooldown(ctx):

    roles = {role.name for role in ctx.author.roles}
    print(roles)
    if 'Moderator' in roles:
        return None
    else:
        return discord.app_commands.Cooldown(2, 30)
