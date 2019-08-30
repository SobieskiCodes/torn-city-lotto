from discord.ext import commands
import discord
from datetime import datetime
from cogs.util.checks import is_mod


class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.boottime = datetime.now()
        self.version = 'v1.0.0'

    @is_mod()
    @commands.command()
    async def fixid(self, ctx, member: discord.User = None, torn_id: str = None):
        if not torn_id:
            e = discord.Embed(colour=discord.Colour(0xbf2003),
                              description=f"<:no:609076414469373971> {ctx.author.name} please provide a torn id!")
            await ctx.send(embed=e)
            return

        if not torn_id.isdigit():
            e = discord.Embed(colour=discord.Colour(0xbf2003),
                            description=f"<:no:609076414469373971> {ctx.author.name} that doesnt look like a torn id!")
            await ctx.send(embed=e)
            return

        if torn_id and torn_id.isdigit():
            get_user = await self.bot.fetch.one(f'SELECT * FROM Users WHERE DiscordID=?', (member.id, ))
            if get_user:
                get_json = await self.bot.torn.api.get_profile(torn_id)
                if get_json:
                    await self.bot.db.execute(f"UPDATE Users SET TornID=? WHERE DiscordID=?",
                                              (torn_id, member.id))
                    await self.bot.db.commit()
                    e = discord.Embed(colour=discord.Colour(0x03bd33),
                                      description=f"<:tickYes:611582439126728716> {ctx.author.name}, {member.name}'s id has been updated to {torn_id}")
                    await ctx.send(embed=e)
                    return

            if not get_user:
                e = discord.Embed(colour=discord.Colour(0xbf2003),
                                  description=f"<:no:609076414469373971> {ctx.author.name}, couldnt find an id for {member.name}")
                await ctx.send(embed=e)
                return

    @fixid.error
    async def member_not_found_error(self, ctx, exception):
        pass

    @commands.command()
    @is_mod()
    async def enable(self, ctx, cog_name: str = None):
        if not cog_name:
            await ctx.send("Please provide the Category you would like to enable; giveaway, lotto")
        choices = ['lotto', 'giveaway']
        if cog_name in choices:
            self.bot.cogcheck[str(ctx.guild.id)][cog_name] = True
            self.bot.cogstuff.save()
            await ctx.send(f"{cog_name} has been enabled.")
        if not cog_name:
            await ctx.send("Please provide the Category you would like to ensable; giveaway, lotto")

    @commands.command()
    @is_mod()
    async def disable(self, ctx, cog_name: str = None):
        if not cog_name:
            await ctx.send("Please provide the Category you would like to disable; giveaway, lotto")
        choices = ['lotto', 'giveaway']
        if cog_name in choices:
            self.bot.cogcheck[str(ctx.guild.id)][cog_name] = False
            self.bot.cogstuff.save()
            await ctx.send(f"{cog_name} has been enabled.")
        if not cog_name:
            await ctx.send("Please provide the Category you would like to disable; giveaway, lotto")

    @commands.command()
    @is_mod()
    async def checkcogs(self, ctx):
        the_string = ''
        for item in self.bot.cogcheck[str(ctx.guild.id)]:
            the_string += f"{item}: {self.bot.cogcheck[str(ctx.guild.id)].get(item)}\n"
        await ctx.send(the_string)



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
