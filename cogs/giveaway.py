from discord.ext import commands
import discord
import asyncio
from cogs.util.checks import is_mod, is_guild_owner
from cogs.util.errorhandling import NotAdded
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
            if get_giveaway_chan:
                if get_giveaway_chan[0]:
                    self.bot.gaveawaydict[guild.id] = get_giveaway_chan[0]

    async def cog_check(self, ctx):
        if not self.bot.cogcheck.get(str(ctx.guild.id)).get('giveaway').data:
            return False

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

        if user.id not in self.bot.addedids and user.id != self.bot.user.id:
            test = await reaction.message.channel.send(f"{user.mention}, please add your torn ID using $addid <id>!")
            await reaction.message.remove_reaction(reaction.emoji, user)
            await asyncio.sleep(3)
            await test.delete()
            return

        get_the_emoji = self.bot.get_emoji(679861713293934635)
        if reaction.emoji != get_the_emoji:
            await reaction.message.remove_reaction(reaction.emoji, user)

    async def get_user_profile_link(self, user):
        get_user = await self.bot.fetch.one(f'SELECT TornID FROM Users WHERE DiscordID=?', (user.id,))
        profile = await self.bot.torn.url.get_profiles(get_user[0])
        return profile


    async def giveaway(self, ctx, length, winners, prize):
        e = discord.Embed(
            title=f"<:party:679861713293934635>{ctx.message.author.name} just started a giveaway!<:party:679861713293934635>",
            description=f"The prize: {prize} \nGiveaway ends in {length // 60}m\nNumber of winners: {winners}\n"
                        f"React with <:party:679861713293934635> to enter!",
            timestamp=datetime.utcnow(),
            colour=discord.Colour(0x278d89)
        )
        e.set_thumbnail(url=f"{ctx.message.author.avatar_url}")
        e.set_footer(text="Started")
        the_giveaway = await ctx.send(embed=e)
        get_the_emoji = self.bot.get_emoji(679861713293934635)
        await the_giveaway.add_reaction(get_the_emoji)
        self.bot.giveawayslist.append(the_giveaway.id)
        await asyncio.sleep(length)
        self.bot.giveawayslist.remove(the_giveaway.id)
        users = []
        refresh_message = await ctx.channel.fetch_message(the_giveaway.id)
        for reaction in refresh_message.reactions:
            users = await reaction.users().flatten()
        while True:
            winner = random.sample(users, winners)
            if len(users) <= 2:
                break
            if self.bot.user not in winner and ctx.author not in winner:
                break

        if len(users) > 2:
            profile_links = []
            for person in winner:
                link = await timedGiveaway.get_user_profile_link(self, person)
                profile_links.append(f"[{person.display_name}]({link})")
            new_e = discord.Embed(
                title=f"<:party:679861713293934635>{ctx.message.author.name}'s giveaway has ended!<:party:679861713293934635>",
                description=f"The prize: {prize} \nWinner: {', '.join(win.mention for win in winner)}\nNumber of entries: {len(users)}\n",
                timestamp=datetime.utcnow(),
                colour=discord.Colour(0x278d89)
            )
            e.set_footer(text="Ended")
            await the_giveaway.edit(embed=new_e)
            another_e = discord.Embed(
                description=f"<:party:679861713293934635>{ctx.message.author.name}'s giveaway has ended! \n"
                                            f"Winner: {', '.join(win.mention for win in winner)}\n"
                                            f"The prize: {prize} \n"
                                            f"[link]({the_giveaway.jump_url}) | {' | '.join(profile_links)}",
                timestamp=datetime.utcnow(),
                colour=discord.Colour(0x278d89)
            )
            await the_giveaway.channel.send(embed=another_e)

        if len(users) <= 2:
            new_e = discord.Embed(
                title=f"<:party:679861713293934635>{ctx.message.author.name}'s giveaway has ended!<:party:679861713293934635>",
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
            remove = await ctx.send(embed=e)
            await ctx.message.delete()
            await asyncio.sleep(3)
            await remove.delete()
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
                remove = await ctx.send(embed=e)
                await ctx.message.delete()
                await asyncio.sleep(3)
                await remove.delete()

            else:
                e = discord.Embed(colour=discord.Colour(0xbf2003),
                                  description=f"<:no:609076414469373971> {ctx.author.name}, please provide only a single channel to set!")
                remove = await ctx.send(embed=e)
                await ctx.message.delete()
                await asyncio.sleep(3)
                await remove.delete()


def setup(bot):
    bot.add_cog(timedGiveaway(bot))
