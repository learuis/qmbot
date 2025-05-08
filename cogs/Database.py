import modio
import asyncio
import sqlite3
import time
import os
from discord.ext import commands

from functions.common import get_all_mods, get_latest_comment, get_mod, write_dungeon_to_db, write_user_to_db

# from dotenv import load_dotenv
#
# load_dotenv('data/server.env')
BOT_ACCESS_ROLE = int(os.getenv('BOT_ACCESS_ROLE'))
#
# async def get_all_mods(gameid, qmfilter):
#     offsetValue = 0
#     allMods = []
#     queryCount = 0
#     tagString = ''
#
#     while True:
#         queryCount += 1
#         if queryCount > 100:
#             print(f'Waiting 60 seconds to avoid rate-limiting.')
#             time.sleep(60)
#             queryCount = 0
#
#         modList = await gameid.async_get_mods(filters=qmfilter)
#         print(modList)
#         offsetValue += len(modList.results)
#         qmfilter.offset(offsetValue)
#
#         allMods.extend(modList.results)
#
#         if not len(modList.results):
#             return allMods


# async def main():
#     game = await get_game()
#     await get_all_mods(game)
#
# if __name__ == "__main__":
#     loop = asyncio.run(main())


class Database(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='db_dungeons')
    @commands.has_any_role(BOT_ACCESS_ROLE)
    async def db_dungeons(self, ctx, dungeon_id: int):

        await write_dungeon_to_db(self.bot.game, ctx, dungeon_id)

        await ctx.reply(f'Updated the database!')

    @commands.command(name='db_users')
    @commands.has_any_role(BOT_ACCESS_ROLE)
    async def db_users(self, ctx, user_id: int):

        await write_user_to_db(self.bot.game, ctx, user_id)

        await ctx.reply(f'Updated the database!')

@commands.Cog.listener()
async def setup(bot):
    await bot.add_cog(Database(bot))
