import modio
import os
import re
import discord
import math
import requests
from discord.ext import commands

from dotenv import load_dotenv

load_dotenv('data/server.env')
GAMEID = int(os.getenv('MODIO_GAME_ID'))
API_KEY = str(os.getenv('API_KEY'))
ACCESS_TOKEN = str(os.getenv('ACCESS_TOKEN'))

def get_game():
    client = modio.Client(
        api_key=API_KEY,
        access_token=ACCESS_TOKEN
    )

    game = client.get_game(GAMEID)
    return game

def get_mods(bot, qmfilter):
    outputString = ''
    splitOutput = ''
    once = True

    modlist = bot.game.get_mods(filters=qmfilter)

    result_count = len(modlist.results)

    return modlist, result_count

def prepare_embed(mod, titlePrefix: str, tagString: str):
    memberPrefix = 'https://mod.io/members'

    embed = discord.Embed(title=f'{titlePrefix}{mod.name}')
    embed.add_field(name=f'Mod ID', value=f'[{mod.id}]({mod.profile})')
    embed.add_field(name=f'Maker', value=f'[{mod.submitter.username}]'
                                     f'({memberPrefix}/{mod.submitter.name_id})')
    embed.add_field(name=f'Likes', value=f'{mod.stats.positive} <a:qmheart:1336494334366978139> ')
    embed.add_field(name=f'Description', value=f'{mod.summary}', inline=False)
    embed.add_field(name=f'Tags', value=f'{tagString}', inline=False)
    embed.set_image(url=f'{mod.logo.original}')

    return embed

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
    async def hello(self, ctx):
        """

        Parameters
        ----------
        ctx

        Returns
        -------

        """
        await ctx.reply(f'Hello World!')

    @commands.command(name='idlookup', aliases=['id', 'dungeonid', 'i'])
    @commands.has_any_role('admin', 'Moderator')
    async def idLookup(self, ctx, modid: int):
        """

        Parameters
        ----------
        ctx
        modid

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

        embed = discord.Embed(title=f'No dungeons or blueprints with ID {modid} found!')

        try:
            mod = self.bot.game.get_mod(modid)
        except modio.errors.modioException:
            await ctx.send(embed=e)
            return

        if not mod:
            await ctx.send(embed=e)
            return

        if 'Blueprint' in mod.tags:
            titlePrefix = '<:Blueprint:1334602701308432454> '
            mod.tags.pop('Blueprint')
            isBlueprint = True
        else:
            mod.tags.pop('Dungeon')
            titlePrefix = '<:Map:1337663369959837760> '

        for tag, value in mod.tags.items():
            tagString += f'{tag} | '

        tagString = tagString[:-3]

        embed = prepare_embed(mod, titlePrefix, tagString)

        if not isBlueprint:

            commentFilter = modio.Filter()
            commentFilter.limit(1)
            comments = mod.get_comments(filters=commentFilter)
            print(len(comments[0]))
            latestComment = comments[0]

            for comment in latestComment:
                commentString = f'{comment.content}'

            latestCommentDetails = commentString.split(f'|')
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

            # Attempts | Completions | Failures | WorldRecordDurationInMilliseconds | WorldRecordUserId |
            # CompletionTimeCount | CompletionTimeAverageInMilliseconds

            embed.add_field(name=f'World Record', value=f'{wrHolder} in {recordString}', inline=True)
            embed.add_field(name=f'Clear Rate', value=f'{completions}/{attempts} - '
                                                      f'({completionRate}%)', inline=True)

        await ctx.reply(embed=embed)

    @commands.command(name='makerprofile', aliases=['maker', 'profile', 'm'])
    @commands.has_any_role('admin', 'Moderator')
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
            outputString += f'**{mod.id}** - {mod.name} by {mod.submitter.username} <{mod.profile}>\n'

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
            await message.edit(content=f'No dungeon found containing `{dungeonName}`')

    @commands.command(name='dungeonsearch', aliases=['ds', 'dungeon', 'd'])
    @commands.has_any_role('admin', 'Moderator')
    async def dungeonsearch(self, ctx, dungeonName: str):
        """

        Parameters
        ----------
        ctx
        dungeonName

        Returns
        -------

        """

        result_list = []
        outputString = ''
        splitOutput = ''
        once = True

        qmfilter = modio.objects.Filter()
        qmfilter.like(name=f'*{dungeonName}*')

        # game_list = client.get_games(filters=qmfilter)
        # print(f'{game_list}')

        # game = client.get_game(GAMEID)

        # print(game.name)
        # prints the name of the game

        # mod = game.get_mod(1234)

        message = await ctx.reply(f'Searching... please wait:\n')

        modlist = self.bot.game.get_mods(filters=qmfilter)
        # print(f'{self.bot.game}')

        # print(mod.name)
        # print(modlist)
        # print(modlist.results)

        result_count = len(modlist.results)

        for mod_result in modlist.results:
            mod_detail = re.match(r'<Mod id=(.*?) name=(.*?) game_id=', str(mod_result))
            mod = self.bot.game.get_mod(mod_detail.groups()[0])
            outputString += f'**{mod.id}** - {mod.name} by {mod.submitter.username} <{mod.profile}>\n'

        # print(f'{result_list}')
        if result_count >= 1:
            await message.edit(content=f'Found {result_count} result(s) matching {dungeonName}, please wait:\n')
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
                    await message.edit(content=f'{outputString}')
                    return
        else:
            await message.edit(content=f'No dungeon found containing `{dungeonName}`')
        # gets the mod for that game with id 231
@commands.Cog.listener()
async def setup(bot):
    await bot.add_cog(DungeonSearch(bot))
