import os
import modio
import discord
import requests
import re
import json
import time
import sqlite3
import requests
# from bs4 import BeautifulSoup

from dotenv import load_dotenv

load_dotenv('data/server.env')
GAMEID = os.getenv('MODIO_GAME_ID')
API_KEY = str(os.getenv('API_KEY'))
ACCESS_TOKEN = str(os.getenv('ACCESS_TOKEN'))
STEAM_API_KEY = str(os.getenv('STEAM_API_KEY'))
STEAM_GAME_ID = str(os.getenv('STEAM_GAME_ID'))

async def db_insert(query: str):
    con = sqlite3.connect(f'data/dungeon_database.db'.encode('utf-8'))
    cur = con.cursor()

    cur.execute(f"{str}")

    con.commit()
    con.close()

    return True

def is_docker():
    path = '/proc/self/cgroup'
    return (
        os.path.exists('/.dockerenv') or
        os.path.isfile(path) and any('docker' in line for line in open(path))
    )
async def get_game():
    client = modio.Client(
        api_key=API_KEY,
        access_token=ACCESS_TOKEN,
        ratelimit_max_sleep=60
    )

    await client.start()

    game = client.get_game(int(GAMEID))
    return game

async def get_mods(bot, qmfilter):

    try:
        modlist = await bot.game.async_get_mods(filters=qmfilter)
    except modio.errors.modioException:
        return False, False

    if modlist:
        print(modlist)
        result_count = len(modlist.results)
        print(result_count)

        return modlist, result_count
    else:
        return False, False

async def get_all_mods(gameid, qmfilter):
    offsetValue = 0
    allMods = []
    queryCount = 0
    tagString = ''

    while True:
        queryCount += 1
        if queryCount > 100:
            print(f'Waiting 60 seconds to avoid rate-limiting.')
            # time.sleep(60)
            queryCount = 0

        modList = await gameid.async_get_mods(filters=qmfilter)
        # print(modList)
        offsetValue += len(modList.results)
        qmfilter.offset(offsetValue)

        allMods.extend(modList.results)

        if not len(modList.results):
            return allMods, queryCount

async def get_latest_comment(mod, qmfilter):
    commentString = ''

    comments = await mod.async_get_comments(filters=qmfilter)
    if len(comments[0]):

        latestComment = comments[0]

        for comment in latestComment:
            commentString = f'{comment.content}'

    return commentString

async def get_mod(bot, mod_to_retrive):
    print(bot.game)
    try:
        mod = await bot.game.async_get_mod(mod_to_retrive)
    except modio.errors.modioException:
        return
    # mod = await bot.game.async_get_mod(mod_to_retrive)
    return mod


def custom_cooldown(ctx):

    roles = {role.name for role in ctx.author.roles}
    if 'Moderator' in roles:
        return None
    else:
        return discord.app_commands.Cooldown(2, 30)

def find_steam_mod_by_tag(tagString):
    api_url = (f"https://api.steampowered.com/IPublishedFileService/QueryFiles/v1/"
               f"?key={STEAM_API_KEY}&page=1&cursor=*&numperpage=100"
               f"&appid={STEAM_GAME_ID}&return_tags=true")

    response = requests.get(api_url)

    responseJson = json.loads(response.content)
    modList = responseJson['response']['publishedfiledetails']
    # print(len(modList))

    for mod in modList:
        tagList = mod['tags']
        if len(tagList) == 1:
            continue
        if tagString in tagList[1]['tag']:
            # print(mod['publishedfileid'])
            return mod['publishedfileid']
        else:
            continue
            # print('not found')

    return

def db_query(query: str):
    con = sqlite3.connect(f'data/dungeon_database.db'.encode('utf-8'))
    cur = con.cursor()

    cur.execute(f"{query}")
    results = cur.fetchall()
    con.close()

    if results:
        return results
    else:
        return False

def get_og_image(link):
    response = requests.get(link)
    content = re.search(r'<meta property="og:image" content="([^"]+)"', str(response.text))
    print(content.group(1))
    return content.group(1)


# def get_og_image(link):
#     try:
#         response = requests.get(link)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.content, 'html.parser')
#         og_image_tag = soup.find('meta', property='og:image')
#         if og_image_tag:
#             return og_image_tag['content']
#         else:
#             return None
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching URL: {e}")
#         return None
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return None
