import modio
import os
import re
import discord
import math
import requests
import json
from discord.ext import commands

from functions.common import get_mods, custom_cooldown, find_steam_mod_by_tag, get_mod, db_query, get_og_image
from functions.Buttons import Buttons

# from dotenv import load_dotenv
#
# load_dotenv('data/server.env')
GAMEID = os.getenv('MODIO_GAME_ID')
API_KEY = str(os.getenv('API_KEY'))
ACCESS_TOKEN = str(os.getenv('ACCESS_TOKEN'))
STEAM_API_KEY = str(os.getenv('STEAM_API_KEY'))
BOT_ACCESS_ROLE = int(os.getenv('BOT_ACCESS_ROLE'))

validTags = ['dungeon', 'overworld', 'user', 'blueprint', 'emberstone quarry', 'dewdrop roots',
             'sandswept ruins', 'gustwind palace', 'deepcoral cove', 'coldfang grotto', 'moonlight brambles',
             'singleplayer', 'two-player', 'three-player', 'swordless', 'one-hit', 'friendly fire',
             'pitch black', 'permadeath', 'ringless', 'mapless', 'puzzle-solving', 'gauntlet',
             'boss battle', 'speedrun', 'traditional', 'troll', 'minigame', 'non-linear', 'parkour',
             'recreation', 'showcase', 'art', 'music', 'exploration', 'escort', 'featured', 'demo',
             'early access', 'halloween', 'winter', 'lead developer', 'developer', 'content creator',
             'untrendable', 'modded']

class DungeonSearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    class GameDetails:
        def __init__(self):
            self.modid = 0
            self.name = ''
            self.gameid = 0

    @commands.command(name='hello', aliases=['hi', 'yo'])
    @commands.has_any_role(BOT_ACCESS_ROLE)
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

    @commands.command(name='taglist', aliases=['listtags', 'tags'])
    @commands.dynamic_cooldown(custom_cooldown, type=commands.BucketType.user)
    async def taglist(self, ctx):
        """
        Lists all of the tags for use in qm/dungeonsearch tags

        Parameters
        ----------
        ctx

        Returns
        -------

        """
        outputString = ''

        for tag in validTags:
            outputString += f'`{tag}`, '

        await ctx.reply(f'List of valid tags: {outputString[:-2]}')

    # @commands.command(name='steamlookup')
    # @commands.has_any_role(BOT_ACCESS_ROLE)
    # @commands.dynamic_cooldown(custom_cooldown, type=commands.BucketType.user)
    # async def steamlookup(self, ctx, searchString: str):
    #     """
    #
    #     Parameters
    #     ----------
    #     ctx
    #     term
    #         Nmae of mod to search for
    #
    #     Returns
    #     -------
    #
    #     """
    #     api_url = (f"https://api.steampowered.com/IPublishedFileService/QueryFiles/v1/"
    #                f"?key={STEAM_API_KEY}&page=1&cursor=*&numperpage=100"
    #                f"&appid=2094070&return_tags=true")
    #
    #     steam_mod_id = find_steam_mod_by_tag(f'{searchString}')
    #     await ctx.reply(f'https://steamcommunity.com/sharedfiles/filedetails/?id={steam_mod_id}')

    # @commands.command(name='stats')
    # @commands.has_any_role(BOT_ACCESS_ROLE)
    # async def stats(self, ctx, modid: int):
    #     """
    #
    #     Parameters
    #     ----------
    #     ctx
    #     modid
    #
    #     Returns
    #     -------
    #
    #     """
    #
    #     embed = discord.Embed(title=f'No dungeons or blueprints with ID {modid} found!')
    #
    #     try:
    #         mod = self.bot.game.get_mod(modid)
    #     except modio.errors.modioException:
    #         await ctx.send(embed=embed)
    #         return
    #
    #     statsDict = mod.metadata
    #     print(statsDict)

    @commands.command(name='query')
    @commands.has_any_role(BOT_ACCESS_ROLE)
    @commands.dynamic_cooldown(custom_cooldown, type=commands.BucketType.user)
    async def query(self, ctx, query: str):
        """

        Parameters
        ----------
        ctx
        query

        Returns
        -------

        """
        results = db_query(query)
        resultList = sum(results, ())
        await ctx.reply(resultList)

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
            Exact ID to look up.

        Returns
        -------

        """

        outputString = ''
        tagString = ''
        commentString = ''
        recordString = ' in '
        isBlueprint = False
        searchPrefix = 'https://mod.io/search/users'
        urlPrefix = 'https://mod.io/u/'
        memberPrefix = 'https://mod.io/members'
        modString = ''
        steamModPrefix = 'https://steamcommunity.com/sharedfiles/filedetails/?id='
        attempts = completions = failures = wrTime = wrName = completionTime = completionAvg = 0

        embed = discord.Embed(title=f'No dungeons or blueprints with ID {modid} found!')

        # try:
        #     mod = get_mod(self.bot, modid)
        #     # mod = self.bot.game.get_mod(modid)
        # except modio.errors.modioException:
        #     await ctx.send(embed=embed)
        #     return

        mod = await get_mod(self.bot, modid)
        if not mod:
            await ctx.send(embed=embed)
            return

        print(mod.tags)
        if 'Blueprint' in mod.tags:
            titlePrefix = '<:Blueprint:1334602701308432454> '
            modType = 'Blueprint'
            mod.tags.pop('Blueprint')
            isBlueprint = True
        elif 'Dungeon' in mod.tags:
            mod.tags.pop('Dungeon')
            titlePrefix = '<:Map:1337877181237301279> '
            modType = 'Dungeon'
        else:
            await ctx.send(embed=embed)
            return

        for tag, value in mod.tags.items():
            tagString += f'{tag} | '

        tagString = tagString[:-3]

        embed = discord.Embed(title=f'{titlePrefix}{mod.name}')
        embed.add_field(name=f'{modType} ID', value=f'[{mod.id}]({mod.profile})')
        embed.add_field(name=f'Maker', value=f'[{mod.submitter.username}]'
                                             f'({memberPrefix}/{mod.submitter.name_id})')
        embed.add_field(name=f'Likes', value=f'<a:qmheart:1336494334366978139> {mod.stats.positive}')
        embed.add_field(name=f'Description', value=f'{mod.summary}', inline=False)
        embed.add_field(name=f'Tags', value=f'{tagString}', inline=False)
        embed.set_image(url=f'{mod.logo.original}')

        if 'Modded' in mod.tags:
            metadata = json.loads(mod.metadata)
            if metadata:
                if 'Mods' in metadata.keys():
                    modList = metadata['Mods']
                    print(f'{len(modList)} mods included')
                    for dungeonMod in modList:
                        modLink = find_steam_mod_by_tag(f'{dungeonMod["Id"]}')
                        if modLink:
                            modString += f'[{dungeonMod["Name"]}]({steamModPrefix}{modLink}) | '
                        else:
                            modString += f'{dungeonMod["Name"]} | '
                    embed.add_field(name=f'Bundled Mods', value=f'{modString[:-3]}', inline=False)

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
                if len(latestCommentDetails) == 5:
                    attempts, completions, failures, wrTime, wrName = latestCommentDetails
                    completionTime = 0
                    completionAvg = 0
                elif len(latestCommentDetails) == 7:
                    attempts, completions, failures, wrTime, wrName, completionTime, completionAvg \
                        = latestCommentDetails
                # attempts, completions, failures, wrTime, wrName, completionTime, completionAvg = latestCommentDetails
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

            embed.add_field(name=f'World Record', value=f'{wrHolder}{recordString}', inline=True)
            embed.add_field(name=f'Clear Rate', value=f'{completions}/{attempts} - '
                                                      f'({completionRate}%)', inline=True)

        await ctx.reply(embed=embed)

    @commands.command(name='idlookup2')
    @commands.has_any_role(BOT_ACCESS_ROLE)
    @commands.dynamic_cooldown(custom_cooldown, type=commands.BucketType.user)
    async def idLookup2(self, ctx, modid: int):
        """
        Locate a dungeon by ID and show information about it.
        Example: qm/idlookup 1234567

        Parameters
        ----------
        ctx
        modid
            Exact ID to look up.

        Returns
        -------

        """

        outputString = ''
        tagString = ''
        commentString = ''
        recordString = ' in '
        isBlueprint = False
        searchPrefix = 'https://mod.io/search/users'
        urlPrefix = 'https://mod.io/u/'
        memberPrefix = 'https://mod.io/members'
        modString = ''
        steamModPrefix = 'https://steamcommunity.com/sharedfiles/filedetails/?id='

        embed = discord.Embed(title=f'No dungeons or blueprints with ID {modid} found!')

        queryString = (f"select dungeons.*, users.username from dungeons "
                       f"left join users on dungeons.creator_user_id = users.user_id where "
                       f"dungeons.id = {modid} limit 1")
        results = db_query(queryString)
        if not results:
            await ctx.send(embed=embed)
            return

        resultList = sum(results, ())
        (mod_id, mod_name, mod_creator_id, mod_summary,
         mod_link, mod_tagString, mod_comment, mod_likes, attempts, completions, failures, wrTime,
         wrName, completionTime, completionAvg, mod_creator_name) = resultList
        titlePrefix = '<:Map:1337877181237301279> '
        mod_type = 'Dungeon'

        mod_tagString = mod_tagString.replace(', ', ' | ')
        mod_tagString = mod_tagString.replace('Dungeon | ', '')

        embed = discord.Embed(title=f'{titlePrefix}{mod_name}')
        embed.add_field(name=f'{mod_type} ID', value=f'[{mod_id}]({mod_link})')
        embed.add_field(name=f'Maker', value=f'[{mod_creator_name}]'
                                             f'({memberPrefix}/{mod_creator_id})')
        embed.add_field(name=f'Likes', value=f'<a:qmheart:1336494334366978139> {mod_likes}')
        embed.add_field(name=f'Description', value=f'{mod_summary}', inline=False)
        embed.add_field(name=f'Tags', value=f'{mod_tagString}', inline=False)

        og_image_url = get_og_image(str(mod_link))
        if og_image_url:
            embed.set_image(url=f'{og_image_url}')

        # add case for wrName = 0, meaning no clears yet
        print(mod_comment)
        if mod_comment:
            # latest_comment = mod_comment.split(f'|')
            # attempts, completions, failures, wrTime, wrName, completionTime, completionAvg = latest_comment
            completionRate = math.floor((int(completions)/int(attempts)) * 100)

            r = requests.head(f'{searchPrefix}/{wrName}', allow_redirects=True)

            wrHolder = r.url.replace(f'{urlPrefix}', f'')

            milliseconds = str(wrTime)[-3:]
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

        embed.add_field(name=f'World Record', value=f'{wrHolder}{recordString}', inline=True)
        embed.add_field(name=f'Clear Rate', value=f'{completions}/{attempts} - '
                                                  f'({completionRate}%)', inline=True)

        await ctx.reply(embed=embed)

    @commands.command(name='makerprofile', aliases=['maker', 'profile', 'm'])
    @commands.has_any_role(BOT_ACCESS_ROLE)
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

        modlist, result_count = await get_mods(self.bot, qmfilter)

        # modlist = self.bot.game.get_mods(filters=qmfilter)

        # result_count = len(modlist.results)

        for mod_result in modlist.results:
            mod_detail = re.match(r'<Mod id=(.*?) name=(.*?) game_id=', str(mod_result))
            # mod = await self.bot.game.async_get_mod(mod_detail.groups()[0])
            mod = await get_mod(self.bot, mod_detail.groups()[0])
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
    @commands.dynamic_cooldown(custom_cooldown, type=commands.BucketType.user)
    async def dungeonsearch(self, ctx, searchField: str, searchString: str):
        """
        Searches for dungeons by name or tags. Limit of 5 results.

        Parameters
        ----------
        ctx
        searchField
            name or tags
        searchString
            The string to search. Use double quotes for searches with spaces. Use qm/taglist for list of all valid tags.

        Returns
        -------

        """

        result_list = []
        outputString = ''
        splitOutput = ''
        once = True
        memberPrefix = 'https://mod.io/members'
        modLabels = []

        searchField = searchField.lower()
        searchString = searchString.lower()

        if 'tags' in searchField and searchString not in validTags:
            embed = discord.Embed(title=f'Invalid tag {searchString}', description=f'You must specify a valid tag and '
                                                                                   f'enclose any tags with spaces in '
                                                                                   f'double quotes. '
                                                                                   f'Run qm/tags for more information.')
            message = await ctx.reply(embed=embed)
            return

        qmfilter = modio.objects.Filter()
        qmfilter.limit(5)
        if 'name' in searchField:
            qmfilter.like(name=f'*{searchString}*')
        if 'tags' in searchField:
            qmfilter.equals(tags=f'{searchString}')

        # game_list = client.get_games(filters=qmfilter)
        # print(f'{game_list}')

        # game = client.get_game(GAMEID)

        # print(game.name)
        # prints the name of the game

        # mod = game.get_mod(1234)

        embed = discord.Embed(title=f'Searching for {searchString}...', description=f'Please wait! (~15 seconds)')

        message = await ctx.reply(embed=embed)

        modList, result_count = await get_mods(self.bot, qmfilter)
        if not modList:
            embed = discord.Embed(title=f'Search Results (Max 5)',
                                  description=f'Nothing found matching {searchString}!')
            await message.edit(embed=embed)
            return

        # modlist = self.bot.game.get_mods(filters=qmfilter)
        # print(f'{self.bot.game}')

        # print(mod.name)
        # print(modlist)
        # print(modlist.results)

        # result_count = len(modList.results)

        for mod_result in modList.results:
            mod_detail = re.match(r'<Mod id=(.*?) name=(.*?) game_id=', str(mod_result))
            mod = await get_mod(self.bot, mod_detail.groups()[0])
            # mod = self.bot.game.get_mod(mod_detail.groups()[0])
            outputString += (f'[{mod.id}](<{mod.profile}>) - '
                             f'{mod.name} by [{mod.submitter.username}](<{memberPrefix}/{mod.submitter.name_id}>)\n')
            # outputString += (f'[{mod.id}](<{mod.profile}>) - '
            #                  f'{mod.name} by [{mod.submitter.username}](<{memberPrefix}/{mod.submitter.name_id}>) '
            #                  f'```qm/i {mod.id}```\n')

            modLabels.append(mod.id)

        if result_count >= 1:
            embed = discord.Embed(title=f'Search Results (Max 5)', description=f'{outputString}')
            if 'tags' in searchField:
                embed.add_field(name=f"Didn\'t find what you wanted? Narrow your search or visit:",
                                value=f"<https://mod.io/g/questmaster?tags-in={searchString.replace(' ','+')}>")
            elif 'name' in searchField:
                embed.add_field(name=f"Didn\'t find what you wanted? Narrow your search or visit:",
                                value=f"<https://mod.io/g/questmaster?_q={searchString}>")
            view = Buttons(ctx, *modLabels)
            await view.init()

            embed.add_field(name=f"Note: Buttons only function for 15 seconds after using the command.",
                            value=f"")

            await message.edit(embed=embed, view=view)
            return
        else:
            embed = discord.Embed(title=f'Search Results (Max 5)', description=f'Nothing found matching {searchString}!')
            await message.edit(embed=embed)

    @commands.command(name='button')
    @commands.has_any_role(BOT_ACCESS_ROLE)
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
