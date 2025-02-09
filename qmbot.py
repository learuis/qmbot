import discord
import os
from discord.ext import commands
from discord.ext.commands import Bot
from dotenv import load_dotenv

from functions.common import is_docker, get_game

load_dotenv('data/server.env')
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
BOT_CHANNEL = os.getenv('BOT_CHANNEL')
GAMEID = os.getenv('MODIO_GAME_ID')

intents = discord.Intents.all()
intents.message_content = True

if is_docker():
    bot: Bot = commands.Bot(command_prefix=['qm/', 'q/', 'aa/', 'QM/', 'Qm/', 'qM/', 'Aa/', 'aA/', 'AA/'],
                            intents=intents)
else:
    bot: Bot = commands.Bot(command_prefix=['qmt/'], intents=intents)

game = get_game()
bot.game = game

@bot.event
async def on_ready():
    for f in os.listdir('./cogs'):
        if f.endswith('.py'):
            await bot.load_extension(f'cogs.{f[:-3]}')

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
