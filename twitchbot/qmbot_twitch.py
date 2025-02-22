from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import asyncio
import os
import modio

from dotenv import load_dotenv

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

def get_mod(game, mod_to_retrive):
    try:
        mod = game.get_mod(mod_to_retrive)
    except modio.errors.modioException:
        return
    # mod = await bot.game.async_get_mod(mod_to_retrive)
    return mod.profile

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

async def qm_command(cmd: ChatCommand):
    game = await get_game()
    link = get_mod(game, cmd.parameter)
    await cmd.reply(f'{link}')

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
    chat.register_command('reply', test_command)
    chat.register_command('qm', qm_command)


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

