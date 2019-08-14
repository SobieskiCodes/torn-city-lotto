from discord.ext import commands
import discord
import random
import asyncio
from cogs.util.errorhandling import SlyBastard
import re
from datetime import datetime
from cogs.util.checks import has_id_added, temp_ban, is_guild_owner


class Lotto:
    def __init__(self, author, prize, descrip, messageid, chanid, guildid):
        self.author = author
        self.prize = prize
        self.descrip = descrip
        self.messageid = messageid
        self.chanid = chanid
        self.guildid = guildid
        self.entrants = []
        self.starttime = datetime.now()

    def __repr__(self):
        return f'{self.guildid}'


class GuildConfig:
    def __init__(self, guildid, lbembed, bannedrole, logchannel, lcrole, sentline, lastcall, sentlineauthor):
        self.guildid = guildid
        self.lbembed = lbembed
        self.bannedrole = bannedrole
        self.logchannel = logchannel
        self.lcrole = lcrole
        self.sentline = sentline
        self.lastcall = lastcall
        self.sentline = sentline
        self.sentlineauthor = sentlineauthor

    def __repr__(self):
        return f'{self.guildid}'


class Lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.running_lottos = []
        self.bot.guildconfigs = []
        self.bot.itemdict = {}
        self.bot.fullitems = {}
        self.bot.addedids = []

    @commands.Cog.listener()
    async def on_ready(self):
        print("Starting up...this could take up to 30 seconds...")
        addedids = await self.bot.fetch.all(f'SELECT DiscordID FROM Users')
        self.bot.addedids = [uid[0] for uid in addedids]
        for guild in self.bot.guilds:
            guildid = guild.id
            get_banned_role = await self.bot.fetch.one(f'SELECT BannedID FROM Guild WHERE GuildID={guild.id}')
            bannedrole = get_banned_role[0] if get_banned_role else None
            lbembed = None
            sentline = True
            lastcall = False
            sentlineauthor = ''
            get_logchannel = await self.bot.fetch.one(f'SELECT LogChannel FROM Guild WHERE GuildID={guild.id}')
            get_lcrole = await self.bot.fetch.one(f'SELECT LastCallRole FROM Guild WHERE GuildID={guild.id}')
            lcrole = get_lcrole[0] if get_lcrole else None
            logchannel = get_logchannel[0] if get_logchannel else None
            self.bot.loop.create_task(Lottery.update(self, guild))
            test = GuildConfig(guildid, lbembed, bannedrole, logchannel, lcrole, sentline, lastcall, sentlineauthor)
            self.bot.guildconfigs.append(test)
            self.bot.loop.create_task(Lottery.load_item_dict(self))
        print('Done loading startup and updating leaderboards... ids should be added.')

    async def load_item_dict(self):
        while True:
            url = f"https://api.torn.com/torn/?selections=items&key={self.bot.torn_key}"
            get_json = await self.bot.torn.api.request(url)
            self.bot.fullitems = get_json
            for item in get_json['items']:
                self.bot.itemdict[get_json['items'].get(item).get('name')] = item
            await asyncio.sleep(86400)

    async def update(self, guild):
        while True:
            get_users = await self.bot.fetch.all(f'SELECT * FROM Totals WHERE GuildID={guild.id}')
            server_items = await self.bot.fetch.one(f'SELECT ItemValues FROM Guild WHERE GuildID={guild.id}')
            server_cash = await self.bot.fetch.one(f'SELECT CashValues FROM Guild WHERE GuildID={guild.id}')
            user_dict = {}
            total = 0
            if get_users:
                if server_cash:
                    total = server_items[0] + server_cash[0]
                if get_users:
                    for GuildID, DiscordID, TornID, LottosRun, ItemValues, CashValues in get_users:
                        total_value = ItemValues + CashValues
                        user_dict[DiscordID] = {"lottos": LottosRun, "value": total_value}
                leaderboard = sorted(user_dict, key=lambda x: user_dict[x]['value'], reverse=True)
                leaderboard = list(enumerate(leaderboard))
                embed = discord.Embed(timestamp=datetime.utcnow(), colour=discord.Colour(0x278d89))
                users_list = ''
                value_list = ''
                lotto_list = ''
                for place, entry in leaderboard[:5]:
                    lotto_num = user_dict[entry]['lottos']
                    value_num = user_dict[entry]['value']
                    pretty_num = f"{value_num:,.2f}"
                    player = guild.get_member(entry)
                    users_list += f'**#{place + 1}** {player.mention}\n'
                    value_list += f'${pretty_num[:-3]}\n'
                    lotto_list += f'{lotto_num}\n'

                embed.add_field(name='User', value=users_list, inline=True)
                embed.add_field(name='Total Value', value=value_list, inline=True)
                embed.add_field(name='Lottos', value=lotto_list, inline=True)
                total_pretty = f"{total:,.2f}"
                embed.set_footer(text=f"Server total donated ${total_pretty[:-3]} - Last updated")
                for get_guild in self.bot.guildconfigs:
                    if get_guild.guildid == guild.id:
                        guildconfigobject = list(self.bot.guildconfigs).index(get_guild)
                        self.bot.guildconfigs[guildconfigobject].lbembed = embed
            await asyncio.sleep(300)

    async def get_guild_object(self, id):
        for guild in self.bot.guildconfigs:
            if guild.guildid == id:
                guildconfigobject = list(self.bot.guildconfigs).index(guild)
                return self.bot.guildconfigs[guildconfigobject]
        return

    async def get_running_lottos(self, id):
        for lotto in self.bot.running_lottos:
            if lotto.guildid == id:
                lottoobject = list(self.bot.running_lottos).index(lotto)
                return self.bot.running_lottos[lottoobject]
        return

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            return
        bot_commands = ['$j', '$c', '$lc']
        get_lotto_object = await Lottery.get_running_lottos(self, message.guild.id)
        if get_lotto_object and message.content not in bot_commands:
            if message.channel.id == get_lotto_object.chanid and message.author.id != self.bot.user.id:
                get_message_id = get_lotto_object.messageid
                get_the_message = await message.channel.fetch_message(get_message_id)
                sticky_bottom = await message.channel.send(embed=get_the_message.embeds[0])
                get_lotto_object.messageid = sticky_bottom.id
                await get_the_message.delete()

    @temp_ban()
    @has_id_added()
    @commands.command(aliases=['startlotto'])
    async def sl(self, ctx, *, item: str = None):
        """Start the lottery $sl <item>
        :param item: the item you wish to add to the lottery
        """
        if not item:
            await ctx.send("please tell us what you want to add to the lottery!")
            return

        get_guild_object = await Lottery.get_guild_object(self, ctx.message.guild.id)
        if get_guild_object:
            get_lotto_object = await Lottery.get_running_lottos(self, ctx.message.guild.id)

            if not get_guild_object.sentline:
                await ctx.send(f'still waiting on a sent line from {get_guild_object.sentlineauthor}')
                return

            if get_lotto_object in list(self.bot.running_lottos):
                await ctx.send('already a lotto running...') #need to fix how this is handled - shows up in same message lol
                return

            if get_lotto_object not in list(self.bot.running_lottos) and get_guild_object.sentline:
                price = None
                if item in list(self.bot.itemdict.keys()):
                    get_item = self.bot.itemdict.get(item)
                    item_info = self.bot.fullitems.get('items').get(get_item)
                    item_value = item_info.get('market_value')
                    price = f"${item_value:,.2f}"

                string_formatting = f"\nMarket value: {price[:-3]}" if price else ''
                string_discript = f"The prize is: {item} {string_formatting}\n"
                e = discord.Embed(
                    title=f"{ctx.message.author.name} just started a lotto!",
                    description=f"{string_discript}",
                    colour=discord.Colour(0x278d89)
                )
                e.set_thumbnail(url=f"{ctx.message.author.avatar_url}")
                e.set_footer(text="Type $j to join!")
                lottery_message = await ctx.send(embed=e)
                test = Lotto(ctx.author, item, string_discript, lottery_message.id, ctx.channel.id, ctx.guild.id)
                self.bot.running_lottos.append(test)

    @temp_ban()
    @has_id_added()
    @commands.command(aliases=['join'])
    async def j(self, ctx):
        """Join an on going lottery if one is going.
        """
        if self.bot.running_lottos:
            get_lotto_object = await Lottery.get_running_lottos(self, ctx.message.guild.id)
            if get_lotto_object:
                if ctx.author.id == get_lotto_object.author.id:
                    raise SlyBastard
                if ctx.author.id in list(get_lotto_object.entrants):
                    e = discord.Embed(description=f"<:no:609076414469373971> {ctx.author.name} has already entered")
                    remove = await ctx.send(embed=e)
                    await ctx.message.delete()
                    await asyncio.sleep(3)
                    await remove.delete()
                    return
                if ctx.author.id not in list(get_lotto_object.entrants):
                    get_lotto_object.entrants.append(ctx.author.id)
                    get_message_id = get_lotto_object.messageid
                    get_the_message = await ctx.message.channel.fetch_message(get_message_id)
                    e = discord.Embed(
                        title=f"{get_lotto_object.author.name} is running a lotto!",
                        description=f"{get_lotto_object.descrip}\nEntries: "
                                    f"{len(get_lotto_object.entrants)}",
                        colour=discord.Colour(0x278d89)
                    )
                    e.set_thumbnail(url=f"{get_the_message.embeds[0].thumbnail.url}")
                    e.set_footer(text="Type $j to join!")
                    await get_the_message.edit(embed=e)
                await ctx.message.delete()
            else:
                await ctx.send("Currently no lotto running!")
                return
        else:
            await ctx.send("Currently no lotto running!")

    async def end_lotto(self, ctx):
        await asyncio.sleep(15)
        get_lotto_object = await Lottery.get_running_lottos(self, ctx.message.guild.id)
        get_message_id = get_lotto_object.messageid
        entrants = len(get_lotto_object.entrants)
        get_the_message = await ctx.message.channel.fetch_message(get_message_id)
        winner = ctx.guild.get_member(random.choice(get_lotto_object.entrants))
        winner_torn_id = await self.bot.fetch.one(f'SELECT TornID FROM Users WHERE DiscordID={winner.id}')
        e = discord.Embed(
            title=f"{ctx.message.author.name}'s lotto has ended!",
            description=f"{winner.mention} won {get_lotto_object.prize}! <:party:577578847080546304>\n"
                        f"Number of entries: {len(get_lotto_object.entrants)}\n\n\n"
                        f"[{winner.name}'s profile](https://www.torn.com/profiles.php?XID={winner_torn_id[0]})",
            colour=discord.Colour(0x278d89)
        )
        e.set_thumbnail(url=f"{get_the_message.embeds[0].thumbnail.url}")
        e.set_footer(text=f"Waiting for sent line from {ctx.message.author.name}")
        await get_the_message.edit(embed=e)
        get_guild_object = await Lottery.get_guild_object(self, ctx.message.guild.id)
        get_guild_object.sentline = False
        time = datetime.now() - get_lotto_object.starttime
        self.bot.running_lottos.remove(get_lotto_object)
        get_guild_object.sentlineauthor = ctx.author
        regex = r"^(?:you sent) (?:[a-z]+)?([0-9]+[a-z]{1}|\$[0-9,]+)?\ ?([0-9a-z\-,+: ]+?)? (?:to)(?:.*)"

        def sent_check(m):
            matches = re.search(regex, m.content, re.IGNORECASE)
            return m.author is ctx.author and matches

        sent_line = await self.bot.wait_for('message', check=sent_check)

        get_matches = re.search(regex, sent_line.content, re.IGNORECASE)
        if get_matches.group(1) and not get_matches.group(2): #if just 1
            print('some cash', get_matches.group(1))
            prize = get_matches.group(1)
        if get_matches.group(2) and not get_matches.group(1): #if just 2
            print('just an item', get_matches.group(2))
            prize = get_matches.group(2)
        if get_matches.group(1) and get_matches.group(2): #if 1 AND 2
            print('amount sent', get_matches.group(1)[:-1], get_matches.group(2))
            prize = (get_matches.group(1)[:-1], get_matches.group(2))

        prize_name = prize if len(prize) != 2 else prize[1]
        price = None
        if prize_name in list(self.bot.itemdict.keys()):
            get_item = self.bot.itemdict.get(prize_name)
            item_info = self.bot.fullitems.get('items').get(get_item)
            price = f"{item_info.get('market_value')}"

        if price:
            value = price if len(prize) != 2 else (int(price) * int(prize[0]))
            type = 1
        if not price:
            if prize_name.startswith('$'):
                value = int(''.join(filter(str.isdigit, prize_name)))
                type = 0
            else:
                value = 0

        if sent_line:
            await sent_line.add_reaction(discord.utils.get(self.bot.emojis, name='check'))
            torn_id = await self.bot.fetch.one(f'SELECT TornID FROM Users WHERE DiscordID={ctx.author.id}')
            get_current_lottos = await self.bot.fetch.one(f'SELECT LottosRun FROM Guild WHERE GuildID={ctx.message.guild.id}')
            get_current_itemvalues = await self.bot.fetch.one(f'SELECT ItemValues FROM Guild WHERE GuildID={ctx.message.guild.id}')
            get_current_cashvalues = await self.bot.fetch.one(f'SELECT CashValues FROM Guild WHERE GuildID={ctx.message.guild.id}')
            get_user = await self.bot.fetch.one(f'SELECT DiscordID FROM Totals WHERE DiscordID={ctx.author.id} AND GuildID={ctx.guild.id}')
            if get_user:
                user_lottos = await self.bot.fetch.one(f'SELECT LottosRun FROM Totals WHERE DiscordID={ctx.author.id} AND GuildID={ctx.guild.id}')
                user_cash = await self.bot.fetch.one(f'SELECT CashValues FROM Totals WHERE DiscordID={ctx.author.id} AND GuildID={ctx.guild.id}')
                user_items = await self.bot.fetch.one(f'SELECT ItemValues FROM Totals WHERE DiscordID={ctx.author.id} AND GuildID={ctx.guild.id}')
                await self.bot.db.execute(f"UPDATE Totals SET LottosRun={user_lottos[0] + 1} WHERE GuildID={ctx.message.guild.id} AND DiscordID={ctx.author.id}")
                if type == 0:
                    await self.bot.db.execute(
                        f"UPDATE Totals SET CashValues={user_cash[0] + int(value)} WHERE GuildID={ctx.message.guild.id} AND DiscordID={ctx.author.id}")
                if type == 1:
                    await self.bot.db.execute(
                        f"UPDATE Totals SET ItemValues={user_cash[0] + int(value)} WHERE GuildID={ctx.message.guild.id} AND DiscordID={ctx.author.id}")

            if not get_user:
                await self.bot.db.execute(f"INSERT INTO Totals(GuildID, DiscordID, TornID, LottosRun, ItemValues, CashValues) VALUES"
                                          f" (?, ?, ?, ?, ?, ?)", (ctx.guild.id, ctx.author.id, torn_id[0], 1, 0, 0))
                if type == 0:
                    await self.bot.db.execute(
                        f"UPDATE Totals SET CashValues={int(value)} WHERE GuildID={ctx.message.guild.id} AND DiscordID={ctx.author.id}")
                if type == 1:
                    await self.bot.db.execute(
                        f"UPDATE Totals SET ItemValues={int(value)} WHERE GuildID={ctx.message.guild.id} AND DiscordID={ctx.author.id}")

            await self.bot.db.execute(f"UPDATE Guild SET LottosRun={get_current_lottos[0] + 1} WHERE GuildID={ctx.message.guild.id}")
            if type == 0:
                await self.bot.db.execute(f"UPDATE Guild SET CashValues={get_current_cashvalues[0] + int(value)} WHERE GuildID={ctx.message.guild.id}")
            if type == 1:
                await self.bot.db.execute(f"UPDATE Guild SET ItemValues={get_current_itemvalues[0] + int(value)} WHERE GuildID={ctx.message.guild.id}")
            await self.bot.db.commit()
            get_guild_object.sentline = True
            get_guild_object.lastcall = True
            days = time.days
            hours, remainder = divmod(time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if days != 0:
                ran_for = f'{days}d {hours}h {minutes}m {seconds}s'
            if days == 0:
                if hours != 0:
                    ran_for = f'{hours}h {minutes}m {seconds}s'
                if hours == 0:
                    if minutes == 0:
                        ran_for = f'{seconds}s'
                    if minutes != 0:
                        ran_for = f'{minutes}m {seconds}s'

            pretty_value = f"{int(value):,.2f}"
            e = discord.Embed(
                title=f"{ctx.message.author.name} lotto has ended!",
                description=#f"<:blank:609080105444311046>\n"
                            f":sheep: {winner.name} won {prize_name}! :sheep:\n\n"
                            f"Number of entries: {entrants}\n"
                            f"Lotto ran for: {ran_for}\n"
                ,
                colour=discord.Colour(0x278d89)

            )
            e.set_footer(text=f"Total value of prize: ${pretty_value[:-3]}")
            e.set_thumbnail(url=f"{ctx.guild.icon_url}")
            await get_the_message.edit(embed=e)
            if get_guild_object.logchannel:
                channel = self.bot.get_channel(get_guild_object.logchannel)
                e = discord.Embed(
                    title=f"[ModLog]",
                    timestamp=f"{datetime.utcnow()}",
                    description=
                    f"Lotto author: {ctx.message.author.name} [{torn_id[0]}]\n"
                    f"Prize: {prize_name}!\n\n"
                    f"SentLine: {get_matches[0]}\n"
                    f"Winner: {winner.name} [{winner_torn_id[0]}]\n"
                    ,
                    colour=discord.Colour(0xe1760b)

                )
                e.set_footer(text=f"Last updated")
                e.set_thumbnail(url=f"{ctx.author.avatar_url}")
                await channel.send(embed=e)

    @commands.command(aliases=['close', 'end'])
    async def c(self, ctx):
        """Close the drawing for the lottery if you are the author of a running lottery.
        """
        if not self.bot.running_lottos:
            await ctx.send('no running lottos')
            return

        # if self.running_lottos and len(self.running_lottos[0].entrants) == 1:
        #     await ctx.send('how you gonna close the lotto with one user?')
        #     return
        get_lotto_object = await Lottery.get_running_lottos(self, ctx.message.guild.id)
        if get_lotto_object:
            if get_lotto_object and len(get_lotto_object.entrants) >= 1:
                if ctx.author.id == get_lotto_object.author.id:
                    await ctx.message.delete()
                    get_message_id = get_lotto_object.messageid
                    get_the_message = await ctx.message.channel.fetch_message(get_message_id)
                    e = discord.Embed(
                        title=f"{get_the_message.embeds[0].title}",
                        description=f"{get_the_message.embeds[0].description}\n"
                                    f"Last chance! Closing in 15 seconds",
                        colour=discord.Colour(0x278d89)
                    )
                    e.set_thumbnail(url=f"{get_the_message.embeds[0].thumbnail.url}")
                    await get_the_message.edit(embed=e)
                    await Lottery.end_lotto(self, ctx)

                else:
                    await ctx.send("you arent the owner of the lotto guy.")
        else:
            await ctx.send('no running lottooooos')

    @commands.command()
    async def price(self, ctx, *, item: str = None):
        """Get the price of an item in torn - case sensitive $price <item>
        :param item: A torn item
        """

        if not item:
            await ctx.send('please provide an item')
        if item:
            if item in list(self.bot.itemdict.keys()):
                item_info = self.bot.fullitems.get('items').get(self.bot.itemdict.get(item))
                price = f"${item_info.get('market_value'):,.2f}"
                e = discord.Embed(
                    title=f"{item}",
                    description=f"{item_info.get('description')}\n\n",
                    colour=discord.Colour(0x278d89)
                    )
                circ = f"{item_info.get('circulation'):,.2f}"
                buy = f"${item_info.get('buy_price'):,.2f}"
                sell = f"${item_info.get('sell_price'):,.2f}"
                e.add_field(name="Market Value", value=f"{price[:-3]}", inline=True)
                e.add_field(name="Circulation", value=f"{circ[:-3]}", inline=True)
                e.add_field(name="Torn Buy Price", value=f"{buy[:-3]}", inline=True)
                e.add_field(name="Torn Sell Price", value=f"{sell[:-3]}", inline=True)
                await ctx.send(embed=e)
            else:
                await ctx.send(f'Seems we cant find and item named {item}')

    @commands.command(aliases=['lastcall'])
    async def lc(self, ctx):
        """Last call for the lottery, lets everyone know the lottery is ending.
        """
        get_lotto_object = await Lottery.get_running_lottos(self, ctx.message.guild.id)
        if get_lotto_object:
            if ctx.author.id != get_lotto_object.author.id:
                not_starter = await ctx.send(f"<:no:609076414469373971> {ctx.author.name}, you arent the lotto starter")
                await asyncio.sleep(2)
                await not_starter.delete()
                return
            get_guild_object = await Lottery.get_guild_object(self, ctx.message.guild.id)
            if not get_guild_object.lastcall:
                get_guild_object = await Lottery.get_guild_object(self, ctx.message.guild.id)
                if get_guild_object.lcrole:
                    e = discord.Embed(
                        description=f"<@&{get_guild_object.lcrole}>, this is the last chance to enter the lotto! <:party:577578847080546304>")
                    test = await ctx.send(f"<@&{get_guild_object.lcrole}>")
                    await test.delete()
                    get_guild_object.lastcall = True
                    await ctx.message.delete()
                    await ctx.send(embed=e)
                    return
                if not get_guild_object.lcrole:
                    not_configured = await ctx.send(f"<:no:609076414469373971> {ctx.author.name}, lc isnt configured on this server.")
                    await asyncio.sleep(2)
                    await not_configured.delete()

            if get_guild_object.lastcall:
                e = discord.Embed(description=f"<:no:609076414469373971> {ctx.author.name}, you only get one LC per lotto.")
                last_call = await ctx.send(embed=e)
                await ctx.message.delete()
                await asyncio.sleep(3)
                await last_call.delete()
                return

        else:
            await ctx.send('no running lottos')

    @commands.command()
    async def top(self, ctx):
        """Display the lotto leader board for the server"""
        get_guild_object = await Lottery.get_guild_object(self, ctx.message.guild.id)
        if get_guild_object.lbembed:
            await ctx.send(embed=get_guild_object.lbembed)
        else:
            await ctx.send("No users found :(")

    @commands.command()
    async def total(self, ctx, user: str = None):
        """Display the lotto total for the server or user
        :param user: user you would like to check $total <@user>
        """
        if not user:
            get_current_lottos = await self.bot.fetch.one(
                f'SELECT LottosRun FROM Guild WHERE GuildID={ctx.message.guild.id}')
            get_current_itemvalues = await self.bot.fetch.one(
                f'SELECT ItemValues FROM Guild WHERE GuildID={ctx.message.guild.id}')
            get_current_cashvalues = await self.bot.fetch.one(
                f'SELECT CashValues FROM Guild WHERE GuildID={ctx.message.guild.id}')
            if get_current_lottos:
                server_total = get_current_itemvalues[0] + get_current_cashvalues[0]
                server_total_pretty = f"{server_total:,.2f}"
                cash_pretty = f"{get_current_cashvalues[0]:,.2f}"
                item_pretty = f"{get_current_itemvalues[0]:,.2f}"
                e = discord.Embed(
                    title=f"{ctx.guild.name} total: ${server_total_pretty[:-3]}",
                    colour=discord.Colour(0x278d89)
                    )
                e.add_field(name="Total Lottos", value=f"{get_current_lottos[0]}", inline=True)
                e.add_field(name="Total Cash Value", value=f"${cash_pretty[:-3]}", inline=True)
                e.add_field(name="Total Item Value", value=f"${item_pretty[:-3]}", inline=True)
                await ctx.send(embed=e)
                return

        if user and len(ctx.message.mentions) == 1:
            get_author = await self.bot.fetch.one(
                f'SELECT * FROM Totals WHERE GuildID={ctx.message.guild.id} AND DiscordID={ctx.message.mentions[0].id}')
            if get_author:
                user_total = get_author[4] + get_author[5]
                user_total_pretty = f"{user_total:,.2f}"
                cash_pretty = f"{get_author[5]:,.2f}"
                item_pretty = f"{get_author[4]:,.2f}"
                e = discord.Embed(
                    title=f"{ctx.author.name} total value given: ${user_total_pretty[:-3]}",
                    colour=discord.Colour(0x278d89)
                        )
                e.add_field(name="Total lottos run", value=f"{get_author[3]}", inline=True)
                e.add_field(name="Total Cash Value", value=f"${cash_pretty[:-3]}", inline=True)
                e.add_field(name="Total Item Value", value=f"${item_pretty[:-3]}", inline=True)
                await ctx.send(embed=e)
                return

            if not get_author:
                e = discord.Embed(
                    title=f"{ctx.message.mentions[0].name} total: $0",
                    colour=discord.Colour(0x278d89)
                )
                e.add_field(name="Total Lottos", value=f"0", inline=True)
                e.add_field(name="Total Cash Value", value=f"$0", inline=True)
                e.add_field(name="Total Item Value", value=f"$0", inline=True)
                await ctx.send(embed=e)
                return

            else:
                await ctx.send("please provide only a single mention")

    @commands.group()
    @is_guild_owner()
    async def config(self, ctx):
        """Guild owner only, configuration setup"""
        if ctx.invoked_subcommand is None:
            await ctx.send("not a valid command.")

    @is_guild_owner()
    @config.command()
    async def bannedrole(self, ctx, role: str = None):
        """The role you would like to add to the banned from lottos list, $config bannedrole <@role>"""
        if not role or not ctx.message.role_mentions:
            await ctx.send("Please provide a role to set")
            return
        if ctx.message.role_mentions:
            if len(ctx.message.role_mentions) == 1:
                the_role = ctx.message.role_mentions[0]
                await self.bot.db.execute(
                    f"UPDATE Guild SET BannedID={the_role.id} WHERE GuildID={ctx.message.guild.id}")
                await self.bot.db.commit()
                get_guild_object = await Lottery.get_guild_object(self, ctx.message.guild.id)
                get_guild_object.bannedid = the_role.id
                await ctx.send(f"Banned role has been updated to {the_role.name}")

            else:
                await ctx.send('Please provide only a single role.')

    @is_guild_owner()
    @config.command()
    async def logchan(self, ctx, chan: str = None):
        """The channel you would like to use for logging, $config logchan <#channel>"""
        if not chan or not ctx.message.channel_mentions:
            await ctx.send("Please provide a channel to set")
            return
        if ctx.message.channel_mentions:
            if len(ctx.message.channel_mentions) == 1:
                the_chan = ctx.message.channel_mentions[0]
                await self.bot.db.execute(
                    f"UPDATE Guild SET LogChannel={the_chan.id} WHERE GuildID={ctx.message.guild.id}")
                await self.bot.db.commit()
                get_guild_object = await Lottery.get_guild_object(self, ctx.message.guild.id)
                get_guild_object.logchannel = the_chan.id
                await ctx.send(f"Log Channel has been updated to {the_chan.name}")

            else:
                await ctx.send('Please provide only a single channel')

    @is_guild_owner()
    @config.command()
    async def lcrole(self, ctx, lcrole: str = None):
        """The role you would like to add to the last call for the lottery, $config lcrole <@role>"""
        if not lcrole or not ctx.message.role_mentions:
            await ctx.send("Please provide a role to set")
            return
        if ctx.message.role_mentions:
            if len(ctx.message.role_mentions) == 1:
                the_role = ctx.message.role_mentions[0]
                await self.bot.db.execute(
                    f"UPDATE Guild SET LastCallRole={the_role.id} WHERE GuildID={ctx.message.guild.id}")
                await self.bot.db.commit()
                get_guild_object = await Lottery.get_guild_object(self, ctx.message.guild.id)
                get_guild_object.lcrole = the_role.id
                await ctx.send(f"Last Call role has been updated to {the_role.name}")

            else:
                await ctx.send('Please provide only a single role.')

    @commands.command()
    async def test(self, ctx):
        print(self.bot.addedids)
        print(type(self.bot.addedids))


def setup(bot):
    bot.add_cog(Lottery(bot))

