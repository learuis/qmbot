from discord.ext import commands

class HelloWorld(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='hello', aliases=['hi', 'yo'])
    @commands.has_any_role('admin')
    async def hello(self, ctx):
        """

        Parameters
        ----------
        ctx

        Returns
        -------

        """
        await ctx.reply(f'Hello World!')

@commands.Cog.listener()
async def setup(bot):
    await bot.add_cog(HelloWorld(bot))
