from discord.ext import commands
import discord
import asyncio
from cogs.util.checks import has_id_added, is_mod, is_guild_owner
from datetime import datetime
import random


class timedGiveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.giveawayslist = []
        self.bot.gaveawaydict = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            get_giveaway_chan = await self.bot.fetch.one('SELECT GiveAwayChan FROM Guild WHERE GuildID=?', (guild.id, ))
            if get_giveaway_chan[0]:
                self.bot.gaveawaydict[guild.id] = get_giveaway_chan[0]

    async def cog_check(self, ctx):
        if self.bot.gaveawaydict:
            for guild in self.bot.gaveawaydict:
                if ctx.guild.id == guild:
                    if ctx.message.channel.id == self.bot.gaveawaydict.get(ctx.guild.id):
                        return True
                    if ctx.message.channel.id != self.bot.gaveawaydict.get(ctx.guild.id):
                        return False
            return True
        return True

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.id not in self.bot.giveawayslist:
            return
        get_the_emoji = self.bot.get_emoji(577578847080546304)
        if reaction.emoji != get_the_emoji:
            await reaction.message.remove_reaction(reaction.emoji, user)

    async def giveaway(self, ctx, length, winners, prize):
        e = discord.Embed(
            title=f"<:party:577578847080546304>{ctx.message.author.name} just started a giveaway!<:party:577578847080546304>",
            description=f"The prize: {prize} \nGiveaway ends in {length // 60}m\nNumber of winners: {winners}\n"
                        f"React with <:party:577578847080546304> to enter!",
            timestamp=datetime.utcnow(),
            colour=discord.Colour(0x278d89)
        )
        e.set_thumbnail(url=f"{ctx.message.author.avatar_url}")
        e.set_footer(text="Started")
        the_giveaway = await ctx.send(embed=e)
        get_the_emoji = self.bot.get_emoji(577578847080546304)
        await the_giveaway.add_reaction(get_the_emoji)
        self.bot.giveawayslist.append(the_giveaway.id)
        await asyncio.sleep(length)
        self.bot.giveawayslist.remove(the_giveaway.id)
        users = []
        refresh_message = await ctx.channel.fetch_message(the_giveaway.id)
        for reaction in refresh_message.reactions:
            users = await reaction.users().flatten()
        while True:
            winner = random.choice(users)
            if winner != self.bot.user and winner != ctx.author:
                break
            if len(users) <= 2:
                break
        if len(users) > 2:
            new_e = discord.Embed(
                title=f"<:party:577578847080546304>{ctx.message.author.name}'s giveaway has ended!<:party:577578847080546304>",
                description=f"The prize: {prize} \nWinner: {winner.mention}\nNumber of entries: {len(users)}\n",
                timestamp=datetime.utcnow(),
                colour=discord.Colour(0x278d89)
            )
            e.set_footer(text="Ended")
            await the_giveaway.edit(embed=new_e)
        if len(users) <= 2:
            new_e = discord.Embed(
                title=f"<:party:577578847080546304>{ctx.message.author.name}'s giveaway has ended!<:party:577578847080546304>",
                description=f"The prize: {prize} \nWinner: no one won because not enough people joined :(\n"
                            f"Number of entries: {len(users)}\n",
                timestamp=datetime.utcnow(),
                colour=discord.Colour(0x278d89)
            )
            e.set_footer(text="Ended")
            await the_giveaway.edit(embed=new_e)

    @is_mod()
    @commands.command()
    async def gstart(self, ctx, time: str = None, winners: str = None, *, prize: str = None):
        if not time or not winners or not prize:
            e = discord.Embed(colour=discord.Colour(0xbf2003),
                                description=f"<:no:609076414469373971> {ctx.author.name}, "
                                            f"format is $gstart time winners prize")
            await ctx.send(embed=e)
            return

        if str(time[-1:]) != 'm':
            e = discord.Embed(colour=discord.Colour(0xbf2003),
                                description=f"<:no:609076414469373971> {ctx.author.name}, "
                                            f"Time needs to be in minutes eg: 10m")
            await ctx.send(embed=e)
            return

        if str(winners[-1:]) != 'w':
            e = discord.Embed(colour=discord.Colour(0xbf2003),
                                description=f"<:no:609076414469373971> {ctx.author.name}, "
                                            f"please specify winners eg: 5w")
            await ctx.send(embed=e)
            return

        if not prize:
            e = discord.Embed(colour=discord.Colour(0xbf2003),
                              description=f"<:no:609076414469373971> {ctx.author.name}, "
                                          f"please add a prize!")
            await ctx.send(embed=e)
            return

        if str(time[-1:]) == 'm':
            if not str(time[:-1]).isdigit():
                e = discord.Embed(colour=discord.Colour(0xbf2003),
                                  description=f"<:no:609076414469373971> {ctx.author.name}, "
                                              f"looks like time is not a valid digit!")
                await ctx.send(embed=e)
                return
            if not str(winners[:-1]).isdigit():
                e = discord.Embed(colour=discord.Colour(0xbf2003),
                                  description=f"<:no:609076414469373971> {ctx.author.name}, "
                                              f"looks like winners is not a valid digit!")
                await ctx.send(embed=e)
                return
            if str(time[:-1]).isdigit() and str(winners[:-1]).isdigit():
                giveaway_length = (int(time[:-1]) * 60)
                number_of_winners = int(winners[:-1])
                self.bot.loop.create_task(timedGiveaway.giveaway(self, ctx, giveaway_length, number_of_winners, prize))

    @is_guild_owner()
    async def giveawaychan(self,  ctx, chan: str = None):
        """The channel you would like to use for the giveaway, $giveaway <#channel>"""
        if not chan or not ctx.message.channel_mentions:
            e = discord.Embed(colour=discord.Colour(0xbf2003),
                              description=f"<:no:609076414469373971> {ctx.author.name}, please provide a channel to set!")
            await ctx.send(embed=e)
            return
        if ctx.message.channel_mentions:
            if len(ctx.message.channel_mentions) == 1:
                the_chan = ctx.message.channel_mentions[0]
                await self.bot.db.execute(
                    f"UPDATE Guild SET GiveAwayChan=? WHERE GuildID=?", (the_chan.id, ctx.message.guild.id))
                await self.bot.db.commit()
                self.bot.gaveawaydict[ctx.guild.id] = the_chan.id
                e = discord.Embed(colour=discord.Colour(0x03bd33),
                                  description=f"<:tickYes:611582439126728716> Giveaway channel has been updated to {the_chan.name}")
                await ctx.send(embed=e)

            else:
                e = discord.Embed(colour=discord.Colour(0xbf2003),
                                  description=f"<:no:609076414469373971> {ctx.author.name}, please provide only a single channel to set!")
                await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(timedGiveaway(bot))
