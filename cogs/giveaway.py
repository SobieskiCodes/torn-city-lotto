import discord
import asyncio
import datetime
import random
import time
from discord.ext import commands, tasks
import aiosqlite


def parse_duration(sec):
    try:
        d = datetime.datetime(1, 1, 1) + datetime.timedelta(seconds=sec)
    except OverflowError:
        return 'Ended'

    parsed = []
    if d.day - 1:
        s = f'{d.day - 1} day'
        if (d.day - 1) > 1:
            s += 's'
        parsed.append(s)

    if d.hour:
        s = f'{d.hour} hour'
        if d.hour > 1:
            s += 's'
        parsed.append(s)

    if d.minute:
        s = f'{d.minute} minute'
        if d.minute > 1:
            s += 's'
        parsed.append(s)

    if d.second:
        s = f'{d.second} second'
        if d.second > 1:
            s += 's'
        parsed.append(s)

    return ', '.join(parsed)


def plurals(a_string, amount):
    return f'{a_string}s' if amount >= 2 else a_string


def time_in_seconds(str_time):
    duration = 0
    if str_time[-1:].lower() == 'm':
        duration = (int(str_time[:-1]) * 60)
    if str_time[-1:].lower() == 'h':
        duration = (int(str_time[:-1]) * 3600)
    if str_time[-1:].lower() == 'd':
        duration = (int(str_time[:-1]) * 86400)
    return duration


class Giveaway:
    def __init__(self, ctx, prize, number_of_winners, duration, status, endtime, message_id):
        self.ctx = ctx  # ctx covers; guild, channel, author, message id
        self.prize = prize
        self.number_of_winners = number_of_winners
        self.duration = duration  # in seconds
        self.status = status  # 0 = started & in progress. 1 = concluded. 2 = announced.
        self.endtime = endtime
        self.message_id = message_id

    def __repr__(self):
        return f'{self.message_id}'


class RexGiveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cog_load()
        self.bot.fetch = self.Fetch(bot)
        self.bot.giveaways = []

    async def db_connect(self):
        self.bot.db = await aiosqlite.connect("giveaway.db")
        await self.bot.db.execute(
                            "CREATE TABLE IF NOT EXISTS giveaways (GuildID INTEGER, ChannelID INTEGER, "
                            "MessageID INTEGER, AuthorID INTEGER, NumberOfWinners INTEGER, Duration INTEGER, "
                            "Status INTEGER, EndTime INTEGER, Prize TEXT, Winners TEXT)"
                           )
        await self.bot.db.commit()

    def cog_load(self):
        self.bot.loop.create_task(self.db_connect())
        self.update.start()

    def cog_unload(self):
        self.update.cancel()


    class Fetch:  # allow for self.bot.fetch.one() and self.bot.fetch.all()
        def __init__(self, bot):
            self.bot = bot

        async def all(self, *arg):
            get = await self.bot.db.execute(*arg)
            results = await get.fetchall()
            return results

        async def one(self, *arg):
            get = await self.bot.db.execute(*arg)
            results = await get.fetchone()
            return results

    async def rebuild_context(self, message):
        return await self.bot.get_context(message)
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html?highlight=get_context#discord.ext.commands.Bot.get_context

    async def giveaway(self, ctx, prize, number_of_winners, duration, status, timestamp):
        emb = discord.Embed(title=prize,
                            description=f'React with :tada: to enter!\n'
                                        f'Time remaining: {parse_duration(duration)} seconds',
                            color=6527730)
        emb.set_footer(
            text=f"{number_of_winners} {plurals('Winner', number_of_winners)} | Ends {parse_duration(duration)}")
        the_message = await ctx.send(embed=emb)
        await the_message.add_reaction(discord.utils.get(self.bot.emojis, name='tada'))
        await self.bot.db.execute(
            f"INSERT INTO giveaways(GuildID, ChannelID, MessageID, AuthorID, NumberOfWinners, Duration, Status, EndTime, Prize) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (ctx.guild.id, ctx.channel.id, the_message.id, ctx.author.id, number_of_winners,
                                                 duration, status, (timestamp + duration), prize))
        await self.bot.db.commit()
        create_giveaway_object = Giveaway(
            ctx=ctx,
            prize=prize,
            number_of_winners=number_of_winners,
            duration=duration,
            status=0,
            endtime=timestamp + duration,
            message_id=the_message.id
        )

        self.bot.giveaways.append(create_giveaway_object)
        await asyncio.sleep(duration)
        await self.pick_winner(ctx, create_giveaway_object, the_message.id, number_of_winners, prize)

    async def pick_winner(self, ctx, create_giveaway_object, the_message, number_of_winners, prize):
        if create_giveaway_object in self.bot.giveaways:
            create_giveaway_object.status = 1
            await self.bot.db.execute(f"UPDATE giveaways SET Status=? WHERE MessageID=?", (1, the_message))
            await self.bot.db.commit()
            refresh_message = await ctx.channel.fetch_message(the_message)  # to get all reactions
            for reaction in refresh_message.reactions:
                users = await reaction.users().flatten()
            if len(users) <= 2 or len(users) < number_of_winners:
                await ctx.send('not enough people entered the giveaway!\n')
            while True:
                winner = random.sample(users, number_of_winners)
                if len(users) <= 2:
                    winner = None
                    break
                if self.bot.user not in winner and ctx.author not in winner:
                    for win in winner:
                        user_still_here = await self.bot.guild.get_member(win.id)
                        if not user_still_here:
                            return
                    break
            if len(users) >= 2 and len(users) > number_of_winners:
                win = "The winner is:" if number_of_winners > 1 else "The winners are:"
                win_phrase = ', '.join([f"{u.mention} **[insert id here]**" for u in winner])
                await ctx.send(f':tada: Congratulations {win} {win_phrase}! You won the {prize}')
            await self.bot.db.execute(f"UPDATE giveaways SET Status=?, Winners=? WHERE MessageID=?",
                                      (2, str([win.id for win in winner]) if winner else None, the_message))
            await self.bot.db.commit()
            self.bot.giveaways.remove(create_giveaway_object)

    async def preview(self, ctx, prize, number_of_winners, duration):
        emb = discord.Embed(title=f'**Giveaway Preview:**\n{prize}',
                            description=f'React with :tada: to enter!\nTime remaining: {parse_duration(duration)}',
                            color=6527730)
        emb.set_footer(text=f'{number_of_winners} {plurals("winner", number_of_winners)}')
        preview_msg = await ctx.send(content='**Please react to confirm.**', embed=emb)
        await preview_msg.add_reaction('👍')
        await preview_msg.add_reaction('👎')

        def is_correct(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['👍', '👎']

        try:
            res = await self.bot.wait_for('reaction_add', check=is_correct, timeout=30)
        except asyncio.TimeoutError:
            return False

        await preview_msg.delete()
        if str(res[0]) == '👍':
            return True
        else:
            return False

    @commands.command(hidden=True)
    @commands.has_permissions(manage_messages=True)
    async def gnew(self, ctx, length: str = None, winners: str = None, *, prize: str = None):
        if not length or not winners or not prize or not winners[:-1].isdigit() or not length[:-1].isdigit() \
                or length[-1:].lower() not in ['m', 'd', 'h'] or winners[-1:].lower() != 'w':
            # should probably try and find a better solution here ^

            return await ctx.send(f"{ctx.author.mention} - Those options don't don't quite work.\n"
                                  f"<time> [winners]w [prize]\n"
                                  f"For example, `gstart 30s 2w Donator Pack` would start a 30-second Giveaway "
                                  f"for a Donator Pack with 2 winners! To use minutes / hours / days, instead of "
                                  f"seconds, simply include an `m`, `h`, or `d` in the time.")
        else:
            duration = time_in_seconds(length)
            number_of_winners = int(winners[:-1])
            confirm = await self.preview(ctx, prize, number_of_winners, duration)
            if not confirm:
                return await ctx.send("Giveaway cancelled!", delete_after=5)
            else:
                await ctx.send(f"The giveaway for `{prize}` is starting in {ctx.channel.mention}", delete_after=2)
                await asyncio.sleep(1)
                await ctx.message.delete()
                self.bot.loop.create_task(self.giveaway(ctx, prize, number_of_winners, duration, 0, int(time.time())))

    @commands.command(hidden=True)
    @commands.has_permissions(manage_messages=True)
    async def gend(self, ctx, message_id: str = None):
        if not message_id or not message_id.isdigit():
            return await ctx.send("please provide a message id")
        if self.bot.giveaways:
            for m in self.bot.giveaways:
                if m.message_id == int(message_id):
                    await self.pick_winner(ctx, m, m.message_id, m.number_of_winners, m.prize)
                    return
        await ctx.send("No giveaways found.")

    @commands.command(hidden=True)
    @commands.has_permissions(manage_messages=True)
    async def gredraw(self, ctx, message_id: str = None):
        if not message_id or not message_id.isdigit():
            return await ctx.send("please provide a message id")
        get_db_context = await self.bot.fetch.one("SELECT * FROM giveaways WHERE MessageID=?", (int(message_id),))
        if get_db_context:
            guild = self.bot.get_guild(get_db_context[0])
            channel = guild.get_channel(get_db_context[1])
            message = await channel.fetch_message(get_db_context[2])
            new_ctx = await self.rebuild_context(message)
            prize = get_db_context[8]
            number_of_winners = get_db_context[4]
            create_giveaway_object = Giveaway(
                ctx=new_ctx,
                prize=prize,
                number_of_winners=number_of_winners,
                duration=get_db_context[5],
                status=2,
                endtime=int(time.time()),
                message_id=int(message_id)
            )

            self.bot.giveaways.append(create_giveaway_object)
            await self.pick_winner(ctx, create_giveaway_object, message.id, number_of_winners, prize)
        else:
            await ctx.send("Didn't find any messages by that ID, please verify its correct.")

    @commands.command(hidden=True)
    @commands.has_permissions(manage_messages=True)
    async def glist(self, ctx):
        string_building = f':tada: Active Giveaways on **{ctx.guild.name}:**\n\n'
        found = False
        for item in self.bot.giveaways:
            if item.ctx.guild.id == ctx.guild.id:
                found = True
                string_building += f"Starter: {item.ctx.author}\n" \
                                   f"Prize: {item.prize}\n" \
                                   f"Winners: {item.number_of_winners}\n" \
                                   f"Time Left: {parse_duration(item.endtime - time.time())}\n" \
                                   f"Channel: {item.ctx.channel.mention}\n" \
                                   f"Message ID: {item.message_id}\n\n"
        if found:
            await ctx.send(string_building)
        else:
            await ctx.send("No giveaways found for this server.")

    @commands.command(hidden=True)
    @commands.has_permissions(manage_messages=True)
    async def gdelete(self, ctx, message_id: str = None):
        if not message_id or not message_id.isdigit():
            return await ctx.send("please provide a message id")
        else:
            for m in self.bot.giveaways:
                if m.message_id == int(message_id):
                    really_delete = await ctx.send(content='**Please react to confirm.**')
                    await really_delete.add_reaction('👍')
                    await really_delete.add_reaction('👎')

                    def sure_to_delete(reaction, user):
                        return user == ctx.author and str(reaction.emoji) in ['👍', '👎']

                    try:
                        res = await self.bot.wait_for('reaction_add', check=sure_to_delete, timeout=30)
                    except asyncio.TimeoutError:
                        return

                    await really_delete.delete()
                    if str(res[0]) == '👍':
                        self.bot.giveaways.remove(m)
                        await self.bot.db.execute(f"DELETE FROM giveaways WHERE MessageID=?", (int(message_id),))
                        await self.bot.db.commit()
                        return await ctx.send(f"{message_id} has been removed from the giveaways")

            await ctx.send(f"Couldn't find {message_id}, are you sure that's correct?")

    @commands.command(hidden=True)
    @commands.has_permissions(manage_messages=True)
    async def ghelp(self, ctx):
        await ctx.send(
            f"__Commands__:\n\n"
            f"**!gcreate** - creates a Giveaway (interactive setup)\n"
            f"**!gnew** <time> <winners>w <prize> (quick setup)\n"
            f"**!gend** <message id> - ends (picks a winner for) the specified Giveaway\n"
            f"**!gredraw** <message id> - re-draws the winners for the specified Giveaway\n"
            f"**!glist** - lists all Giveaways on the server\n"
            f"**!gdelete** - Clears a specified Giveaway and stops tracking it\n\n"
            f"Do not include <> - <> means required.")

    @tasks.loop(seconds=10, reconnect=True)
    async def update(self):
        if not self.bot.giveaways:
            return
        for item in self.bot.giveaways:
            time_left = item.endtime - time.time()
            if int(time_left) <= 60:
                m = await item.ctx.channel.fetch_message(item.message_id)
                emb = discord.Embed(title=item.prize,
                                    description=f'React with :tada: to enter!\n'
                                                f'Time remaining: {parse_duration(time_left)} seconds',
                                    color=6527730)
                emb.set_footer(
                    text=f"{item.number_of_winners} {plurals('Winner', item.number_of_winners)} | Ends {parse_duration(time_left)}")
                await m.edit(embed=emb)

    @update.before_loop
    async def before_update(self):
        # will add db boot here too with all status that's not 2.
        print('waiting... for bot to fully boot')
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(RexGiveaway(bot))
