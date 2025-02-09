import modio
import os
import re
import discord
import math
import requests
from discord.ext import commands
from functions.common import get_mods, custom_cooldown
from functions.Buttons import Buttons

from dotenv import load_dotenv

load_dotenv('data/server.env')
GAMEID = os.getenv('MODIO_GAME_ID')
API_KEY = str(os.getenv('API_KEY'))
ACCESS_TOKEN = str(os.getenv('ACCESS_TOKEN'))

class DungeonSearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    class GameDetails:
        def __init__(self):
            self.modid = 0
            self.name = ''
            self.gameid = 0

    @commands.command(name='hello', aliases=['hi', 'yo'])
    @commands.has_any_role('admin', 'Moderator')
    @commands.dynamic_cooldown(custom_cooldown, type=commands.BucketType.user)
    async def hello(self, ctx):
        """

        Parameters
        ----------
        ctx

        Returns
        -------

        """
        await ctx.reply(f'Hello World!')

    @commands.command(name='stats')
    @commands.has_any_role('Admin', 'Moderator')
    async def stats(self, ctx, modid: int):
        """

        Parameters
        ----------
        ctx
        modid

        Returns
        -------

        """

        embed = discord.Embed(title=f'No dungeons or blueprints with ID {modid} found!')

        try:
            mod = self.bot.game.get_mod(modid)
        except modio.errors.modioException:
            await ctx.send(embed=embed)
            return

        statsDict = mod.metadata
        print(statsDict)

    @commands.command(name='idlookup', aliases=['id', 'dungeonid', 'i'])
    @commands.dynamic_cooldown(custom_cooldown, type=commands.BucketType.user)
    async def idLookup(self, ctx, modid: int):
        """
        Locate a dungeon by ID and show information about it.
        Example: qm/idlookup 1234567

        Parameters
        ----------
        ctx
        modid
            The ID of the dungeon of blueprint to look up. Must be exact!

        Returns
        -------

        """

        outputString = ''
        tagString = ''
        commentString = ''
        recordString = ''
        isBlueprint = False
        searchPrefix = 'https://mod.io/search/users'
        urlPrefix = 'https://mod.io/u/'
        memberPrefix = 'https://mod.io/members'

        embed = discord.Embed(title=f'No dungeons or blueprints with ID {modid} found!')

        try:
            mod = self.bot.game.get_mod(modid)
        except modio.errors.modioException:
            await ctx.send(embed=embed)
            return

        if not mod:
            await ctx.send(embed=embed)
            return

        if 'Blueprint' in mod.tags:
            titlePrefix = '<:Blueprint:1334602701308432454> '
            mod.tags.pop('Blueprint')
            isBlueprint = True
        else:
            mod.tags.pop('Dungeon')
            titlePrefix = '<:Map:1337877181237301279> '

        for tag, value in mod.tags.items():
            tagString += f'{tag} | '

        tagString = tagString[:-3]

        embed = discord.Embed(title=f'{titlePrefix}{mod.name}')
        embed.add_field(name=f'Mod ID', value=f'[{mod.id}]({mod.profile})')
        embed.add_field(name=f'Maker', value=f'[{mod.submitter.username}]'
                                             f'({memberPrefix}/{mod.submitter.name_id})')
        embed.add_field(name=f'Likes', value=f'<a:qmheart:1336494334366978139> {mod.stats.positive}')
        embed.add_field(name=f'Description', value=f'{mod.summary}', inline=False)
        embed.add_field(name=f'Tags', value=f'{tagString}', inline=False)
        embed.set_image(url=f'{mod.logo.original}')

        if not isBlueprint:

            commentFilter = modio.Filter()
            commentFilter.limit(1)
            comments = mod.get_comments(filters=commentFilter)

            if len(comments[0]):

                latestComment = comments[0]

                for comment in latestComment:
                    commentString = f'{comment.content}'

                latestCommentDetails = commentString.split(f'|')
                # add case for wrName = 0, meaning no clears yet
                attempts, completions, failures, wrTime, wrName, completionTime, completionAvg = latestCommentDetails
                completionRate = math.floor((int(completions)/int(attempts)) * 100)

                r = requests.head(f'{searchPrefix}/{wrName}', allow_redirects=True)

                wrHolder = r.url.replace(f'{urlPrefix}', f'')

                milliseconds = wrTime[-3:]
                seconds = (int(wrTime) // 1000) % 60
                minutes = (int(wrTime) // (1000 * 60)) % 60
                hours = (int(wrTime) // (1000 * 60 * 60)) % 60
                if hours:
                    recordString += f'{hours}h, '
                if minutes:
                    recordString += f'{minutes}m, '
                if seconds:
                    recordString += f'{seconds}s '
                if milliseconds:
                    recordString += f'{milliseconds}ms'
            else:
                wrHolder = f'Uncleared'
                recordString = f''
                completions = 0
                attempts = 0
                completionRate = 0
                # Attempts | Completions | Failures | WorldRecordDurationInMilliseconds | WorldRecordUserId |
                # CompletionTimeCount | CompletionTimeAverageInMilliseconds

            embed.add_field(name=f'World Record', value=f'{wrHolder} in {recordString}', inline=True)
            embed.add_field(name=f'Clear Rate', value=f'{completions}/{attempts} - '
                                                      f'({completionRate}%)', inline=True)

        await ctx.reply(embed=embed)

    @commands.command(name='makerprofile', aliases=['maker', 'profile', 'm'])
    @commands.has_any_role('Admin', 'Moderator')
    @commands.dynamic_cooldown(custom_cooldown, type=commands.BucketType.user)
    async def makerprofile(self, ctx, makerid: int):
        """

        Parameters
        ----------
        ctx
        makerid

        Returns
        -------

        """

        result_list = []
        outputString = ''
        splitOutput = ''
        once = True
        memberPrefix = 'https://mod.io/members'

        qmfilter = modio.objects.Filter()
        qmfilter.equals(submitter=int(makerid))

        print('alive1')

        message = await ctx.reply(f'Searching... please wait:\n')

        print('alive2')

        modlist, result_count = get_mods(self.bot, qmfilter)

        # modlist = self.bot.game.get_mods(filters=qmfilter)

        # result_count = len(modlist.results)

        for mod_result in modlist.results:
            mod_detail = re.match(r'<Mod id=(.*?) name=(.*?) game_id=', str(mod_result))
            mod = self.bot.game.get_mod(mod_detail.groups()[0])
            outputString += (f'[{mod.id}]({mod.profile}) - '
                             f'{mod.name} by [{mod.submitter.username}]({memberPrefix}/{mod.submitter.name_id}')

        # print(f'{result_list}')
        if result_count >= 1:
            await message.edit(content=f'Found {result_count} result(s) for creator {makerid}, please wait:\n')
            if outputString:
                if len(outputString) > 1800:
                    workList = outputString.splitlines()
                    for items in workList:
                        splitOutput += f'{str(items)}\n'
                        print(f'splitOutput size: {len(str(splitOutput))}')
                        if len(str(splitOutput)) > 1800:
                            if once:
                                once = False
                                await message.edit(content=str(splitOutput))
                                splitOutput = '(continued)\n'
                            else:
                                await ctx.send(str(splitOutput))
                                splitOutput = '(continued)\n'
                        else:
                            continue
                    await ctx.send(str(splitOutput))
                else:
                    await message.edit(content=f'Found {result_count} dungeon(s) created by '
                                               f'{mod.submitter.username}:\n{outputString}')
                    return
        else:
            await message.edit(content=f'No dungeon found containing`')

    @commands.command(name='dungeonsearch', aliases=['ds', 'dungeon', 'd', 'search'])
    @commands.has_any_role('Admin', 'Moderator')
    @commands.dynamic_cooldown(custom_cooldown, type=commands.BucketType.user)
    async def dungeonsearch(self, ctx, searchField: str, dungeonName: str):
        """
        Searches for dungeons by partial name. Limit of 5 results.

        Parameters
        ----------
        ctx
        dungeonName
        searchField

        Returns
        -------

        """

        result_list = []
        outputString = ''
        splitOutput = ''
        once = True
        memberPrefix = 'https://mod.io/members'
        modLabels = []

        qmfilter = modio.objects.Filter()
        qmfilter.like(name=f'*{dungeonName}*')
        qmfilter.limit(5)

        # game_list = client.get_games(filters=qmfilter)
        # print(f'{game_list}')

        # game = client.get_game(GAMEID)

        # print(game.name)
        # prints the name of the game

        # mod = game.get_mod(1234)

        embed = discord.Embed(title=f'Searching for {dungeonName}...', description=f'Please wait! (~15 seconds)')

        message = await ctx.reply(embed=embed)

        modlist = self.bot.game.get_mods(filters=qmfilter)
        # print(f'{self.bot.game}')

        # print(mod.name)
        # print(modlist)
        # print(modlist.results)

        result_count = len(modlist.results)

        for mod_result in modlist.results:
            mod_detail = re.match(r'<Mod id=(.*?) name=(.*?) game_id=', str(mod_result))
            mod = self.bot.game.get_mod(mod_detail.groups()[0])
            outputString += (f'[{mod.id}](<{mod.profile}>) - '
                             f'{mod.name} by [{mod.submitter.username}](<{memberPrefix}/{mod.submitter.name_id}>)\n')
            # outputString += (f'[{mod.id}](<{mod.profile}>) - '
            #                  f'{mod.name} by [{mod.submitter.username}](<{memberPrefix}/{mod.submitter.name_id}>) '
            #                  f'```qm/i {mod.id}```\n')

            modLabels.append(mod.id)

        if result_count >= 1:
            embed = discord.Embed(title=f'Search Results (Max 5)', description=f'{outputString}')
            view = Buttons(ctx, *modLabels)
            await view.init()

            await message.edit(content=f'test', embed=embed, view=view)
            return
        else:
            embed = discord.Embed(title=f'Search Results (Max 5)', description=f'Nothing found matching {dungeonName}!')
            await message.edit(embed=embed)

    @commands.command(name='button')
    @commands.has_any_role('Admin', 'Moderator')
    @commands.dynamic_cooldown(custom_cooldown, type=commands.BucketType.user)
    async def buttonpress(self, ctx):
        """
        I press the button.

        Parameters
        ----------
        ctx

        Returns
        -------

        """

        await ctx.send("This message has buttons!", view=Buttons(f'Test'))

@commands.Cog.listener()
async def setup(bot):
    await bot.add_cog(DungeonSearch(bot))
