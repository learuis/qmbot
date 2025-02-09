import discord
import asyncio

class Buttons(discord.ui.View):
    def __init__(self, ctx, label1, label2=None, label3=None, label4=None, label5=None):
        self.labelList = label1, label2, label3, label4, label5
        super().__init__(timeout=15)
        self.ctx = ctx

    async def init(self):
        button1, button2, button3, button4, button5 = await Buttons.add_buttons(self, self.ctx, *self.labelList)

        if button1:
            self.add_item(button1)
        if button2:
            self.add_item(button2)
        if button3:
            self.add_item(button3)
        if button4:
            self.add_item(button4)
        if button5:
            self.add_item(button5)

    async def add_buttons(self, ctx, label1, label2, label3, label4, label5):
        button1, button2, button3, button4, button5 = False, False, False, False, False
        if label1:
            button1 = discord.ui.Button(label=label1)
        if label2:
            button2 = discord.ui.Button(label=label2)
        if label3:
            button3 = discord.ui.Button(label=label3)
        if label4:
            button4 = discord.ui.Button(label=label4)
        if label5:
            button5 = discord.ui.Button(label=label5)

        async def mod_button1(interaction: discord.Interaction):
            await interaction.response.send_message(f'Fetching details for {label1}.')
            await ctx.invoke(ctx.bot.get_command('idlookup'), modid=f'{label1}')

        async def mod_button2(interaction: discord.Interaction):
            await interaction.response.send_message(f'Fetching details for {label2}.')
            await ctx.invoke(ctx.bot.get_command('idlookup'), modid=f'{label2}')

        async def mod_button3(interaction: discord.Interaction):
            await interaction.response.send_message(f'Fetching details for {label3}.')
            await ctx.invoke(ctx.bot.get_command('idlookup'), modid=f'{label3}')

        async def mod_button4(interaction: discord.Interaction):
            await interaction.response.send_message(f'Fetching details for {label4}.')
            await ctx.invoke(ctx.bot.get_command('idlookup'), modid=f'{label4}')

        async def mod_button5(interaction: discord.Interaction):
            await interaction.response.send_message(f'Fetching details for {label5}.')
            await ctx.invoke(ctx.bot.get_command('idlookup'), modid=f'{label5}')

        if label1:
            button1.callback = mod_button1
        if label2:
            button2.callback = mod_button2
        if label3:
            button3.callback = mod_button3
        if label4:
            button4.callback = mod_button4
        if label5:
            button5.callback = mod_button5

        return button1, button2, button3, button4, button5
