import asyncio
import os
import modio
import discord
import requests
import re
import json
import time
import sqlite3
import requests
from datetime import datetime
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

def date_format(date: str):
    datetime_object = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    new_date = datetime_object.strftime("%B %d, %Y @ %H:%M:%S")
    return new_date

def ms_to_string(time_in_ms: int):
    outputString = ''

    milliseconds = time_in_ms[-3:]
    seconds = (int(time_in_ms) // 1000) % 60
    minutes = (int(time_in_ms) // (1000 * 60)) % 60
    hours = (int(time_in_ms) // (1000 * 60 * 60)) % 60
    if hours:
        outputString += f'{hours}h, '
    if minutes:
        outputString += f'{minutes}m, '
    if seconds:
        outputString += f'{seconds}s '
    if milliseconds:
        outputString += f'{milliseconds}ms'

    return outputString

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

def get_all_mods(game, qmfilter):
    offsetValue = 0
    allMods = []
    queryCount = 0
    tagString = ''

    print(f'get_all_mods function game: {game}')
    while True:
        queryCount += 1
        if queryCount > 100:
            print(f'Waiting 60 seconds to avoid rate-limiting.')
            # time.sleep(60)
            queryCount = 0

        modList = game.get_mods(filters=qmfilter)
        print(modList)
        offsetValue += len(modList.results)
        qmfilter.offset(offsetValue)

        allMods.extend(modList.results)

        if not len(modList.results):
            return allMods, queryCount

def get_latest_comment(mod, qmfilter):
    commentString = ''

    comments = mod.get_comments(filters=qmfilter)
    if len(comments[0]):

        latestComment = comments[0]

        for comment in latestComment:
            commentString = f'{comment.content}'

    return commentString

async def get_mod(game, mod_to_retrieve):
    print(game)
    try:
        mod = await game.async_get_mod(mod_to_retrieve)
    except modio.errors.modioException:
        return
    # mod = await bot.game.async_get_mod(mod_to_retrieve)
    return mod

def int_epoch_time():
    current_time = datetime.now()
    epoch_time = int(round(current_time.timestamp()))

    return epoch_time


async def write_user_to_db(game, user_id: int):

    qmfilter = modio.objects.Filter()
    qmfilter.limit(1)
    qmfilter.sort("id", reverse=False)
    qmfilter.equals(tags=f'User')
    qmfilter.equals(name=f'{user_id}')

    con = sqlite3.connect(f'data/dungeon_database.db'.encode('utf-8'))
    cur = con.cursor()

    modTuple = get_all_mods(game, qmfilter)
    # mod = await get_mod(bot, user_id)
    print(modTuple)
    modList = modTuple[0]
    print(len(modList))
    print(modList)

    for mod in modList:
        mod.submitter.username = mod.submitter.username.replace('"', '\"')
        mod.submitter.username = mod.submitter.username.replace('\'', '\'\'')
        print(mod.id, mod.name)
        cur.execute(f"INSERT OR REPLACE INTO users (mod_id, user_id, username) "
                    f"values ({mod.id}, {int(mod.name)}, \'{mod.submitter.username}\');")

    con.commit()
    con.close()
    # await ctx.reply(f'Updating the database!')

async def write_to_queue(channel, dungeon_id, dungeon_name, dungeon_creator):

    con = sqlite3.connect(f'data/dungeon_database.db'.encode('utf-8'))
    cur = con.cursor()

    query = (f'select position from ( '
             f'select row_number() over (order by added_at asc) as position, '
             f'channel_name, dungeon_id from dungeon_queue '
             f'where channel_name = \'{channel}\' ) '
             f'where dungeon_id = {dungeon_id} and channel_name = \'{channel}\'')
    cur.execute(f"{query}")
    result = cur.fetchone()
    if not result:
        query = (f'insert or replace into dungeon_queue (channel_name, added_at, dungeon_id, dungeon_name, dungeon_creator) '
                 f'values (\'{channel}\', {int_epoch_time()}, {dungeon_id}, \'{dungeon_name}\', \'{dungeon_creator}\')')
        print(f'{query}')
        cur.execute(f"{query}")
        con.commit()

        query = (f'select position from ( '
                 f'select row_number() over (order by added_at asc) as position, '
                 f'channel_name, dungeon_id from dungeon_queue '
                 f'where channel_name = \'{channel}\' ) '
                 f'where dungeon_id = {dungeon_id} and channel_name = \'{channel}\'')
        cur.execute(f"{query}")

        position = cur.fetchone()[0]
        con.close()

        return f"Added {dungeon_name} ({dungeon_id}) to the queue at position # {position}"
    else:
        con.close()
        return f"{dungeon_name} ({dungeon_id}) is already in the queue at position # {result[0]}"


async def write_dungeon_to_db(game, dungeon_id: int):

    tagString = ''
    comment = ''
    attempts = completions = failures = wrTime = wrName = completionTime = completionAvg = 0

    con = sqlite3.connect(f'data/dungeon_database.db'.encode('utf-8'))
    cur = con.cursor()

    qmfilter = modio.objects.Filter()
    qmfilter.limit(100)
    qmfilter.sort("id", reverse=False)
    qmfilter.equals(id=f'{dungeon_id}')
    qmfilter.equals(tags=f'Dungeon')

    commentfilter = modio.Filter()
    commentfilter.limit(1)
    commentfilter.sort("id", reverse=True)

    print(f'write function game: {game}')
    # task = asyncio.create_task(get_all_mods(game, qmfilter))
    # modList, queryCount = await task
    modList, queryCount = get_all_mods(game, qmfilter)
    print(modList)
    if len(modList) == 0:
        return False

    # print(len(modList.results), modList.results)

    for index, mod in enumerate(modList):
        print(f'Processing comment for mod # {index} of {len(modList)}...')
        if queryCount > 100:
            print(f'Waiting 60 seconds to avoid rate-limiting.')
            # time.sleep(60)
            queryCount = 0

        # if 'comments' in option:
        comment = get_latest_comment(mod, commentfilter)
        splitComment = comment.split(f'|')
        # account for comments before june 2024
        if len(splitComment) == 5:
            attempts, completions, failures, wrTime, wrName = splitComment
            completionTime = 0
            completionAvg = 0
        elif len(splitComment) == 7:
            attempts, completions, failures, wrTime, wrName, completionTime, completionAvg = splitComment
        queryCount += 1

        # print(mod.id, mod.name)
        # mod_detail = re.match(r'<Mod id=(.*?) name=(.*?) game_id=', str(mod_result))
        # mod = await game.async_get_mod(mod_detail.groups()[0])

        # modid = mod_detail.groups(0)
        # modname = str(mod_detail.groups(1))
        # print(mod.id, mod.name)
        # queryCount += 1
        # if queryCount > 60:
        #     print(f'Waiting 60 seconds to avoid rate-limiting.')
        #     time.sleep(60)
        #     queryCount = 0
        mod.name = mod.name.replace('"', '\"')
        mod.name = mod.name.replace('\'', '\'\'')
        mod.submitter.username = mod.submitter.username.replace('"', '\"')
        mod.submitter.username = mod.submitter.username.replace('\'', '\'\'')
        mod.summary = mod.summary.replace('"', '\"')
        mod.summary = mod.summary.replace('\'', '\'\'')
        for tag in mod.tags:
            tagString += f'{tag}, '
        # print(tagString)
        tagString.replace('"', '\"')
        tagString.replace('\'', '\'\'')
        # if 'comments' in option:
        query = (f"INSERT OR REPLACE INTO dungeons (id, name, creator_user_id, "
                    f"summary, link, tags, latest_comment, likes, attempts, completions, failures,"
                    f"worldrecordduration, worldrecordholder, completiontimecount, completiontimeaverage, uploaded, updated) "
                    f"values ({mod.id}, \'{mod.name}\', {mod.submitter.id}, "
                    f"\'{mod.summary}\', \'{mod.profile}\', \'{tagString[:-2]}\', \'{comment}\', "
                    f"{mod.stats.positive}, {attempts}, {completions}, {failures}, {wrTime}, "
                    f"{wrName}, {completionTime}, {completionAvg}, \'{mod.live}\', \'{mod.updated}\');")
        print(f"{query}")

        cur.execute(f"{query}")
        # else:
        #    cur.execute(f"UPDATE dungeons set likes = {mod.stats.positive} where id = {mod.id};")

        con.commit()
        tagString = ''

    con.close()

    return mod.submitter.id


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
