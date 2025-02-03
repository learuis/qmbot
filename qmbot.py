import discord
import time
import os
from time import localtime, strftime
from discord.ext import commands
from discord.ext.commands import Bot
from dotenv import load_dotenv

from functions.common import is_docker

load_dotenv('data/server.env')
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = int(os.getenv('DISCORD_GUILD'))
BOT_CHANNEL = int(os.getenv('BOT_CHANNEL'))


intents = discord.Intents.all()
intents.message_content = True

if is_docker():
    bot: Bot = commands.Bot(command_prefix=['qm/', 'QM/'], intents=intents)
else:
    bot: Bot = commands.Bot(command_prefix=['qmt/', 'QMt/'], intents=intents)

bot.quest_running = False

# @bot.event
# async def on_ready():

@bot.event
async def on_ready():
    for f in os.listdir('./cogs'):
        if f.endswith('.py'):
            await bot.load_extension(f'cogs.{f[:-3]}')
    loadtime = strftime('%m/%d/%y at %H:%M:%S', localtime(time.time()))
    channel = bot.get_channel(BOT_CHANNEL)

    if is_docker():
        await channel.send(f'QM_Bot PROD (use qm/) started on {loadtime}.')
    else:
        await channel.send(f'QM_Bot TEST (use qmt/) started on {loadtime}.')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing parameter! See qm/help for details.')
        return
    if isinstance(error, commands.errors.CheckFailure):
        print(f'Command from {ctx.message.author} failed checks. '
              f'{ctx.message.channel.id}.')
        channel = bot.get_channel(BOT_CHANNEL)
        await ctx.send(f'You do not have permission to use this command, or you cannot use that command in this '
                       f'channel. Try {channel.mention}!')
        return
    if isinstance(error, commands.errors.CommandOnCooldown):
        await ctx.send(error)
        return
    if isinstance(error, commands.errors.BadArgument):
        await ctx.send(error)
        return
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send(f'Invalid command `{ctx.message.content}`! Use `qm/help`')
        return
    if isinstance(error, discord.errors.DiscordServerError):
        channel = bot.get_channel(BOT_CHANNEL)
        await channel.send(f'A discord server error has occurred. QM_Bot may need to be restarted to recover.')
        return

    else:
        await ctx.send(error)
        raise error

bot.run(TOKEN)
