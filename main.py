import os
from discord.ext import commands
from pathlib import Path
import aiosqlite
import aiohttp
import jthon
from cogs.util.errorhandling import NotAuthorized, SlyBastard, NotAdded, TempBan, TornAPIUnavailable, TornAPIError


async def get_prefix(bot, message):
    if message.guild:
        if message.guild.id in list(bot.prefixdict.keys()):
            prefix = bot.prefixdict.get(message.guild.id)
        else:
            prefix = '$'
    else:
        prefix = '$'
    return commands.when_mentioned_or(*prefix)(bot, message)


bot = commands.AutoShardedBot(command_prefix=get_prefix, pm_help=True)
bot.prefixdict = {}
bot.bot_commands = ['j', 'join', 'close', 'end', 'lastcall', 'c', 'lc', 'release', 'sl', 'startlotto', 'll', 'lootlevel', 'loot']
@bot.event
async def on_guild_join(guild):
    get_guild = await bot.db.execute(f'SELECT GuildID FROM Guild WHERE GuildID=?', (guild.id, ))
    results = await get_guild.fetchone()
    if not results:
        await bot.db.execute(f"INSERT INTO Guild(GuildID, Prefix, LottosRun, ItemValues, CashValues) VALUES (?, ?, ?, ?, ?)", (guild.id, '$', 0, 0, 0))
        await bot.db.commit()
    bot.cogcheck[str(guild.id)] = {"lotto": True, "giveaway": True}
    bot.cogstuff.save()


@bot.event
async def on_ready():
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}')
    bot.prefixdict = {}
    for guild in bot.guilds:
        fetch = await bot.db.execute(f'SELECT Prefix FROM Guild WHERE GuildID=?', (guild.id,))
        result = await fetch.fetchone()
        bot.prefixdict[guild.id] = result[0] if result else '$'
        if str(guild.id) not in bot.cogcheck:
            bot.cogcheck[str(guild.id)] = {"lotto": True, "giveaway": True}
            bot.cogstuff.save()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure) or isinstance(error, commands.errors.CommandNotFound):
        return
    if isinstance(error, commands.errors.BadArgument):
        return
    if isinstance(error, NotAuthorized):
        #pretty-fi this
        await ctx.send('You are not authorized for this command.')
        return
    if isinstance(error, SlyBastard):
        await ctx.message.author.send('Good try though. Not added.')
        await ctx.send(f"{ctx.message.author} tried to join their own lotto, here is the shame.")
        return
    if isinstance(error, NotAdded):
        await ctx.send(f"{ctx.message.author.mention}, please add your torn ID before trying to join lottos with $addid <tornID>")
        return
    if isinstance(error, TempBan):
        await ctx.author.send(f"You are currently banned from the lottery in {ctx.message.channel.mention}, please talk to staff to resolve this.")
        await ctx.message.delete()
        return
    if isinstance(error, TornAPIUnavailable):
        await ctx.send(f"Looks like torns api is unavailable at the moment, try again later.")
        return
    if isinstance(error, TornAPIError):
        await ctx.send(f"{error}")
        return
    else:
        print(f'Error in {ctx.guild.id} with message {ctx.message.content}')
        raise error


def load_extensions():
    bot.startup_extensions = []
    path = Path('./cogs')
    for dirpath, dirnames, filenames in os.walk(path):
        if dirpath.strip('./') == str(path):
            for cog in filenames:
                if cog.endswith('.py'):
                    extension = 'cogs.'+cog[:-3]
                    bot.startup_extensions.append(extension)

    if __name__ == "__main__":
        for extension in bot.startup_extensions:
            try:
                bot.load_extension(extension)
                print(f'Loaded {extension}')
            except Exception as e:
                exc = f'{type(e).__name__}: {e}'
                print(f'Failed to load extension {extension}\n{exc}')


async def create_dbconnect():
    bot.db = await aiosqlite.connect("tornlootlevel.db")


class Request_Base:
    def __init__(self, loop):
        self.loop = loop

    async def request(self, url):
        async with aiohttp.ClientSession(loop=self.loop) as session:
            r = await session.get(url)
            if r.status == 200:
                get_json = await r.json()
                if 'error' not in get_json.keys():
                    return get_json
                else:
                    raise TornAPIError(f"Torn says Error code:{get_json['error']['code']}, {get_json['error']['error']}.")
            else:
                raise TornAPIUnavailable


class API(Request_Base):

    def __init__(self, loop, key=None):
        super().__init__(loop)
        self.key = key
        self.base = "https://api.torn.com/"

    async def get_profile(self, userID):
        url = f"{self.base}user/{userID}?selections=profile&key={self.key}"
        return await self.request(url)

    async def get_basic(self, userID):
        url = f"{self.base}user/{userID}?selections=basic&key={self.key}"
        return await self.request(url)

    async def get_item(self, item):
        url = f"{self.base}torn/{item}?selections=items&key={self.key}"
        return await self.request(url)


class URL(Request_Base):
    def __init__(self, loop):
        super().__init__(loop)
        self.base = "https://www.torn.com/"

    async def get_profiles(self, userID):
        url = f"{self.base}profiles.php?XID={userID}"
        return url

    async def get_attack(self, userID):
        url = f"{self.base}loader.php?sid=attack&user2ID={userID}"
        return url

    async def get_faction(self, factionID):
        url = f"{self.base}factions.php?step=profile&ID={factionID}"
        return url


class Torn:
    def __init__(self, loop, key=None):
        self.url = URL(loop=loop)
        self.api = API(loop=loop, key=key)


class Fetch:
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



bot.fetch = Fetch(bot)
bot.loop.create_task(create_dbconnect())
bot.config = jthon.load('data')
bot.cogstuff = jthon.load('cogcheck')
bot.cogcheck = bot.cogstuff.get('guilds')
token = bot.config.get('config').get('token').data
bot.torn_key = bot.config.get('config').get('torn_token').data
bot.torn = Torn(bot.loop, key=bot.torn_key)
load_extensions()
bot.run(token)
