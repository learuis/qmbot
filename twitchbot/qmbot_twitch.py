import sqlite3

from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import asyncio
import os
import modio

from dotenv import load_dotenv

from functions.common import db_query, write_dungeon_to_db, write_user_to_db, write_to_queue

# from functions.common import get_game, get_mod_w_game

load_dotenv('../data/server.env')
TWITCH_APP_ID = os.getenv('TWITCH_APP_ID')
TWITCH_SECRET = os.getenv('TWITCH_SECRET')
TARGET_CHANNEL = os.getenv('TWITCH_CHANNEL')
OAUTH_TOKEN = os.getenv('OAUTH_TOKEN')
OAUTH_REFRESH_TOKEN = os.getenv('OAUTH_REFRESH_TOKEN')
GAMEID = os.getenv('MODIO_GAME_ID')
API_KEY = str(os.getenv('API_KEY'))
ACCESS_TOKEN = str(os.getenv('ACCESS_TOKEN'))

USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]

def get_mod(game, mod_to_retrieve):
    try:
        mod = game.get_mod(mod_to_retrieve)
    except modio.errors.modioException:
        return
    # mod = await bot.game.async_get_mod(mod_to_retrieve)
    return mod

async def get_game():
    client = modio.Client(
        api_key=API_KEY,
        access_token=ACCESS_TOKEN
    )

    await client.start()

    game = client.get_game(int(GAMEID))
    return game

# this will be called when the event READY is triggered, which will be on bot start
async def on_ready(ready_event: EventData):
    print('Bot is ready for work, joining channels')
    # join our target channel, if you want to join multiple, either call join for each individually
    # or even better pass a list of channels as the argument
    await ready_event.chat.join_room(TARGET_CHANNEL)
    # you can do other bot initialization things in here

# this will be called whenever a message in a channel was send by either the bot OR another user
async def on_message(msg: ChatMessage):
    print(f'in {msg.room.name}, {msg.user.name} said: {msg.text}')


# this will be called whenever someone subscribes to a channel
async def on_sub(sub: ChatSub):
    print(f'New subscription in {sub.room.name}:\\n'
          f'  Type: {sub.sub_plan}\\n'
          f'  Message: {sub.sub_message}')


# this will be called whenever the !reply command is issued
async def test_command(cmd: ChatCommand):
    if len(cmd.parameter) == 0:
        await cmd.reply('you did not tell me what to reply with')
    else:
        await cmd.send(f'{cmd.user.name}: {cmd.parameter}')

async def qm_info(cmd: ChatCommand):
    try:
        int(cmd.parameter)
    except ValueError:
        await cmd.reply(f'{cmd.parameter} is not a valid ID!')
        return

    game = await get_game()
    print(f'command function game: {game}')

    response = f'No dungeons or blueprints with ID {cmd.parameter} found!'

    user_id = await write_dungeon_to_db(game, int(cmd.parameter))
    if user_id is False:
        await cmd.reply(response)
        return

    print(f"user id {user_id}")

    await write_user_to_db(game, int(user_id))

    queryString = (f"select dungeons.*, users.username from dungeons "
                   f"left join users on dungeons.creator_user_id = users.user_id where "
                   f"dungeons.id = {cmd.parameter} limit 1")
    results = db_query(queryString)
    if not results:
        await cmd.reply(f'{response}')
        return

    resultList = sum(results, ())
    print(resultList)
    (mod_id, mod_name, mod_creator_id, mod_summary,
     mod_link, mod_tagString, mod_comment, mod_likes, attempts, completions, failures, wrTime,
     wrName, completionTime, completionAvg, uploaded, updated, mod_creator_name) = resultList

    await cmd.reply(f'ID: {mod_id}\nName: {mod_name}\nLikes: {mod_likes}\n')
    return

async def qm_add(cmd: ChatCommand):
    try:
        int(cmd.parameter)
    except ValueError:
        await cmd.reply(f'{cmd.parameter} is not a valid ID!')
        return
    if int(cmd.parameter) < 0 or int(cmd.parameter) > 10000000000:
        await cmd.reply(f'{cmd.parameter} is not a valid ID!')
        return

    game = await get_game()
    print(f'command function game: {game}')

    response = f'No dungeons or blueprints with ID {cmd.parameter} found!'

    user_id = await write_dungeon_to_db(game, int(cmd.parameter))
    if user_id is False:
        await cmd.reply(response)
        return

    print(f"user id {user_id}")

    await write_user_to_db(game, int(user_id))

    queryString = (f"select dungeons.*, users.username from dungeons "
                   f"left join users on dungeons.creator_user_id = users.user_id where "
                   f"dungeons.id = {cmd.parameter} limit 1")
    results = db_query(queryString)
    if not results:
        await cmd.reply(f'{response}')
        return

    resultList = sum(results, ())
    print(resultList)
    (mod_id, mod_name, mod_creator_id, mod_summary,
     mod_link, mod_tagString, mod_comment, mod_likes, attempts, completions, failures, wrTime,
     wrName, completionTime, completionAvg, uploaded, updated, mod_creator_name) = resultList

    response = await write_to_queue(TARGET_CHANNEL, mod_id, mod_name, mod_creator_name)
    await cmd.reply(f'{response}')
    return

async def qm_remove(cmd: ChatCommand):
    try:
        int(cmd.parameter)
    except ValueError:
        await cmd.reply(f'{cmd.parameter} is not a valid ID!')
        return
    if int(cmd.parameter) < 0 or int(cmd.parameter) > 10000000000:
        await cmd.reply(f'{cmd.parameter} is not a valid ID!')
        return

    con = sqlite3.connect(f'data/dungeon_database.db'.encode('utf-8'))
    cur = con.cursor()

    query = f'select rowid from dungeon_queue where dungeon_id = {int(cmd.parameter)} and channel_name = \'{TARGET_CHANNEL}\''
    cur.execute(f"{query}")
    position = cur.fetchone()[0]
    if position:
        query = f'delete from dungeon_queue where dungeon_id = {int(cmd.parameter)} and channel_name = \'{TARGET_CHANNEL}\''
        cur.execute(f"{query}")
        con.commit()
        con.close()
        await cmd.reply(f'Removed {cmd.parameter} from the queue!')
        return
    else:
        await cmd.reply(f'{cmd.parameter} was not in the queue.')
        return

async def qm_queue(cmd: ChatCommand):
    next_text = f''
    is_are = f'is'
    s = f''

    con = sqlite3.connect(f'data/dungeon_database.db'.encode('utf-8'))
    cur = con.cursor()

    query = f'select dungeon_id, dungeon_name from dungeon_queue where channel_name = \'{TARGET_CHANNEL}\' order by added_at asc'
    cur.execute(f"{query}")
    result = cur.fetchall()
    if not result:
        await cmd.reply(f'The queue is empty! Add some with !qmadd 1234567')
        return
    else:
        current_dungeon = result[0]
        if len(result) > 1:
            next_dungeon = result[1]
            next_text = f' Next: {next_dungeon[0]}'
            is_are = f'are'
            s = f's'
        await cmd.reply(f'There {is_are} {len(result)} dungeon{s} in the queue. Current: {current_dungeon[0]}{next_text}')
        return

async def qm_next(cmd: ChatCommand):
    next_text = f''

    con = sqlite3.connect(f'data/dungeon_database.db'.encode('utf-8'))
    cur = con.cursor()

    query = f'select dungeon_id, dungeon_name from dungeon_queue where channel_name = \'{TARGET_CHANNEL}\' order by added_at asc'
    cur.execute(f"{query}")
    result = cur.fetchall()
    if not result:
        await cmd.reply(f'The queue is empty! Add some with !qmadd 1234567')
        return
    else:
        current_dungeon = result[0]
        if len(result) > 1:
            next_dungeon = result[1]
            next_text = f' Next: {next_dungeon[0]}'
            query = (f'delete from dungeon_queue '
                     f'where channel_name = \'{TARGET_CHANNEL}\' '
                     f'and added_at in ( select added_at from dungeon_queue where channel_name = \'{TARGET_CHANNEL}\' '
                     f'order by added_at asc limit 1 )')
            cur.execute(f"{query}")
            con.commit()
            con.close()
            await cmd.reply(f'Removed {current_dungeon[0]} from the queue.{next_text}')
            return
        else:
            query = (f'delete from dungeon_queue '
                     f'where channel_name = \'{TARGET_CHANNEL}\' '
                     f'and added_at in ( select added_at from dungeon_queue where channel_name = \'{TARGET_CHANNEL}\' '
                     f'order by added_at asc limit 1 )')
            cur.execute(f"{query}")
            con.commit()
            con.close()
            await cmd.reply(f'Removed {current_dungeon[0]} from the queue. There are no more dungeons in the queue! '
                            f'Add some with !qmadd 1234567')
            return

async def qm_clear(cmd: ChatCommand):
    con = sqlite3.connect(f'data/dungeon_database.db'.encode('utf-8'))
    cur = con.cursor()

    query = f'delete from dungeon_queue where channel_name = \'{TARGET_CHANNEL}\''
    cur.execute(f"{query}")
    con.commit()
    con.close()
    await cmd.reply(f'Cleared the dungeon queue. Add some more with !qmadd 1234567')
    return

async def qm_help(cmd: ChatCommand):
    await cmd.reply(f'Available commands: qminfo | qmqueue | qmadd | qmremove | qmclear | qmnext')
    return

# this is where we set up the bot
async def run():

    # set up twitchbot api instance and add user authentication with some scopes
    twitch = await Twitch(TWITCH_APP_ID, TWITCH_SECRET)
    auth = UserAuthenticator(twitch, USER_SCOPE)
    # token, refresh_token = await auth.authenticate()
    # print(token, refresh_token)
    await twitch.set_user_authentication(OAUTH_TOKEN, USER_SCOPE, OAUTH_REFRESH_TOKEN)

    # create chat instance
    chat = await Chat(twitch)

    # register the handlers for the events you want

    # listen to when the bot is done starting up and ready to join channels
    chat.register_event(ChatEvent.READY, on_ready)
    # listen to chat messages
    chat.register_event(ChatEvent.MESSAGE, on_message)
    # listen to channel subscriptions
    chat.register_event(ChatEvent.SUB, on_sub)
    # there are more events, you can view them all in this documentation

    # you can directly register commands and their handlers, this will register the !reply command
    chat.register_command('qminfo', qm_info)
    chat.register_command('qmi', qm_info)
    chat.register_command('qmadd', qm_add)
    chat.register_command('qma', qm_add)
    chat.register_command('qmremove', qm_remove)
    chat.register_command('qmr', qm_remove)
    chat.register_command('qmqueue', qm_queue)
    chat.register_command('qmq', qm_queue)
    chat.register_command('qmnext', qm_next)
    chat.register_command('qmn', qm_next)
    chat.register_command('qmclear', qm_clear)
    chat.register_command('qmc', qm_clear)
    chat.register_command('qmhelp', qm_help)


    # we are done with our setup, lets start this bot up!
    chat.start()

    # lets run till we press enter in the console
    # try:
    #     input('press ENTER to stop\n')
    # finally:
    #     # now we can close the chat bot and the twitchbot api client
    #     chat.stop()
    #     await twitchbot.close()

# lets run our setup
asyncio.run(run())

