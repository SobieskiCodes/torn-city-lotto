from discord.ext import commands
import discord
from datetime import datetime


class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.boottime = datetime.now()
        self.version = 'v1.0.0'

    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def load_cog(self, ctx, *, cog: str):
        """Command which Loads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.load_extension(f'cogs.{cog}')
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def unload_cog(self, ctx, *, cog: str):
        """Command which Unloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            await self.bot.change_presence(status=discord.Status.idle,
                                           activity=discord.Activity(type=3, name=f"Reloading.."))
            self.bot.unload_extension(f'cogs.{cog}')
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def reload_cog(self, ctx, *, cog: str):
        """Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.reload_extension(f'cogs.{cog}')
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(name='vme', hidden=True)
    @commands.is_owner()
    async def vme(self, ctx):
        time = datetime.now() - self.boottime
        days = time.days
        hours, remainder = divmod(time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        onlinefor = f'{days}:d {hours}:h {minutes}:m'
        embed = discord.Embed(colour=discord.Colour(0x50bdfe), description=f'Here is some information about me... \n '
                                                                           f'```'
                                                                           f'Version: {self.version}\n'
                                                                           f'Library: d.py rewrite \n'
                                                                           f'Uptime: {onlinefor} \n'
                                                                           f'Server Count: {len(self.bot.guilds)}\n'
                                                                           f'Member Count: {len(self.bot.users)}'
                                                                           f'```')
        embed.set_footer(text='justin@sobieski.codes | ProbsJustin#0001')
        await ctx.send(embed=embed)

    @commands.command(name='sts', hidden=True)
    @commands.is_owner()
    async def status(self, ctx, *, status: str = None):
        await self.bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=3, name=f"{status}"))

    @commands.command(name='invite', hidden=True)
    async def invite(self, ctx):
        embed = discord.Embed(colour=discord.Colour(0x608f30),
                              description=f'Invite me [here](https://discordapp.com/oauth2/authorize?client_id'
                                          f'={self.bot.user.id}&scope=bot&permissions=0)')
        embed.set_footer(text='')
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(OwnerCog(bot))
