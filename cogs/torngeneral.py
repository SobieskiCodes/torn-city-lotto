from discord.ext import commands
import discord
import random


class general(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def profile(self, ctx, userID: str = None):
        """Display your or someone elses profile, $profile <@name>
        :param userID:
        """
        if userID and ctx.message.mentions:
            if len(ctx.message.mentions) == 1:
                get_user = await self.bot.fetch.one(f'SELECT TornID FROM Users WHERE DiscordID=?', (ctx.message.mentions[0].id, ))
                if get_user:
                    get_json = await self.bot.torn.api.get_profile(get_user[0])
                    get_faction = await self.bot.torn.url.get_faction(get_json['faction']['faction_id'])
                    faction = f"[{get_json['faction']['faction_name']}]({get_faction})" if get_json['faction']['faction_name'] != "None" else "N/A"
                    profile = await self.bot.torn.url.get_profiles(get_json['player_id'])
                    e = discord.Embed(
                        title=f"{get_json['name']} [{get_json['player_id']}]",
                        description=f"Rank: {get_json['rank']}\n"
                                    f"Level: {get_json['level']}\n"
                                    f"Status: {get_json['status'][0]}\n"
                                    f"Faction: {faction}\n"
                                    f"Last Action: {get_json['last_action']['relative']}\n\n"
                                    f"[profile]({profile})",
                        colour=discord.Colour(0x278d89)
                        )
                    e.set_thumbnail(url=f"https://sobieski.codes/torn/profile/{random.choice([1,2,4])}.png")
                    await ctx.send(embed=e)
                else:
                    e = discord.Embed(colour=discord.Colour(0xbf2003),
                        description=f"<:no:609076414469373971> {ctx.author.name} sorry couldnt find that user.")
                    await ctx.send(embed=e)
                    return
            else:
                e = discord.Embed(colour=discord.Colour(0xbf2003),
                        description=f"<:no:609076414469373971> {ctx.author.name} please provide only a single user!")
                await ctx.send(embed=e)
                return
        else:
            get_user = await self.bot.fetch.one(f'SELECT TornID FROM Users WHERE DiscordID=?', (ctx.author.id, ))
            if get_user:
                get_json = await self.bot.torn.api.get_profile(get_user[0])
                get_faction = await self.bot.torn.url.get_faction(get_json['faction']['faction_id'])
                faction = f"[{get_json['faction']['faction_name']}]({get_faction})" if get_json['faction'][
                                                                                           'faction_name'] != "None" else "N/A"
                profile = await self.bot.torn.url.get_profiles(get_json['player_id'])
                e = discord.Embed(
                    title=f"{get_json['name']} [{get_json['player_id']}]",
                    description=f"Rank: {get_json['rank']}\n"
                                f"Level: {get_json['level']}\n"
                                f"Status: {get_json['status'][0]}\n"
                                f"Faction: {faction}\n"
                                f"Last Action: {get_json['last_action']['relative']}\n\n"
                                f"[profile]({profile})",
                    colour=discord.Colour(0x278d89)
                )
                e.set_thumbnail(url=f"https://sobieski.codes/torn/profile/{random.choice([1, 2, 4])}.png")
                await ctx.send(embed=e)
            else:
                e = discord.Embed(colour=discord.Colour(0xbf2003),
                            description=f"<:no:609076414469373971> {ctx.author.name} seems i dont have an id for you!")
                await ctx.send(embed=e)


    @commands.command()
    async def addid(self, ctx, torn_id):
        """Add your torn id, $addid 1517715
        :param torn_id: Your in game torn ID
        """
        if not torn_id.isdigit():
            e = discord.Embed(colour=discord.Colour(0xbf2003),
                            description=f"<:no:609076414469373971> {ctx.author.name} that doesnt look like a torn id!")
            await ctx.send(embed=e)
        else:
            get_json = await self.bot.torn.api.get_profile(torn_id)
            if get_json:
                get_user = await self.bot.fetch.one(f'SELECT TornID FROM Users WHERE DiscordID=?', (ctx.author.id, ))
                if not get_user:
                    id_check = await self.bot.fetch.one(f'SELECT DiscordID FROM Users WHERE TornID=?', (torn_id, ))
                    if not id_check:
                        await self.bot.db.execute(f"INSERT INTO Users(TornID, DiscordID) "
                                                                  f"VALUES (?, ?)", (torn_id, ctx.author.id))
                        await self.bot.db.commit()
                        self.bot.addedids.append(ctx.author.id)
                        await ctx.message.add_reaction(discord.utils.get(self.bot.emojis, name='check'))
                        e = discord.Embed(colour=discord.Colour(0x03bd33),
                                          description=f"{ctx.author.name} has been added with ID: {torn_id}")
                        await ctx.send(embed=e)
                        return
                    else:
                        member = await ctx.guild.fetch_member(id_check[0])
                        e = discord.Embed(colour=discord.Colour(0xbf2003),
                            description=f"<:no:609076414469373971> {ctx.author.name}, "
                                        f"looks like your torn ID is added to {member.name}, "
                                        f"is this incorrect? If so please contact staff.")
                        await ctx.send(embed=e)
                        return

                if get_user:
                    e = discord.Embed(colour=discord.Colour(0xbf2003),
                                      description=f"<:no:609076414469373971> {ctx.author.name}, "
                                                  f"Looks like you already have an id stored as: "
                                                  f"{get_user[0]}, please contact staff if this is incorrect.")
                    await ctx.send(embed=e)

    @commands.command()
    async def pick(self, ctx, limit: str = None, *, some_choices: str = None):
        if not limit:
            e = discord.Embed(colour=discord.Colour(0x03bd33),
                              description=f"<:no:609076414469373971> {ctx.author.name}, \n"
                                          f"Usage is pick <optional limit> <list of items seperated by a comma>.'")
            await ctx.send(embed=e)
            return

        if not limit.isdigit() and some_choices:
            if len(some_choices.split(' ')):
                some_choices = f"{limit} {some_choices}"
            if ', ' in some_choices:
                the_string = f"{limit} {some_choices}"
                new_list = the_string.split(', ')
                e = discord.Embed(colour=discord.Colour(0x03bd33),
                                  description=f"<:tickYes:611582439126728716> {ctx.author.name}, "
                                              f"You asked me to pick an item from your list, I pick '{random.choice(new_list)}'")
                await ctx.send(embed=e)

            if ', ' not in some_choices:
                e = discord.Embed(colour=discord.Colour(0xbf2003),
                                  description=f"<:no:609076414469373971> {ctx.author.name}, "
                                              f"Please provide commas between the items you would like me to pick from.")
                await ctx.send(embed=e)

        if not limit.isdigit() and not some_choices:
            e = discord.Embed(colour=discord.Colour(0x03bd33),
                              description=f"<:no:609076414469373971> {ctx.author.name}, \n"
                                          f"Usage is pick <optional limit> <list of items seperated by a comma>.'")
            await ctx.send(embed=e)
            return

        if limit.isdigit():
            if ', ' in some_choices:
                new_list = []
                limit = int(limit)
                if limit < len(some_choices.split(', ')):
                    for i in range(limit):
                        while True:
                            pick_one = random.choice(some_choices.split(', '))
                            if pick_one not in new_list:
                                new_list.append(pick_one)
                                break
                    e = discord.Embed(colour=discord.Colour(0x03bd33),
                                      description=f"<:tickYes:611582439126728716> {ctx.author.name}, "
                                                  f"You asked me to pick {limit} item(s) from your list, I pick '{', '.join(new_list)}'")
                    await ctx.send(embed=e)
                if limit >= len(some_choices.split(', ')):
                    e = discord.Embed(colour=discord.Colour(0xbf2003),
                                      description=f"<:no:609076414469373971> {ctx.author.name}, "
                                                  f"the limit seems to be higher than my options..?")
                    await ctx.send(embed=e)
            if ', ' not in some_choices:
                e = discord.Embed(colour=discord.Colour(0xbf2003),
                                    description=f"<:no:609076414469373971> {ctx.author.name}, "
                                                f"Please provide commas between the items you would like me to pick from.")
                await ctx.send(embed=e)

    @commands.command(aliases=['rn'])
    async def randomnumber(self, ctx, max_or_range: str = None):
        if not max_or_range:
            await ctx.send('please provide a max or range')
            return
        if max_or_range.isdigit():
            e = discord.Embed(colour=discord.Colour(0x03bd33),
                              description=f"<:tickYes:611582439126728716> {ctx.author.name}, "
                                          f"You asked me to pick a number between 1 and {max_or_range}, I pick '{random.randint(1, int(max_or_range))}'")
            await ctx.send(embed=e)

        if '-' in max_or_range:
            split_it = max_or_range.split('-')
            if len(split_it) == 2:
                if split_it[0].isdigit and split_it[1].isdigit():
                    e = discord.Embed(colour=discord.Colour(0x03bd33),
                                      description=f"<:tickYes:611582439126728716> {ctx.author.name}, "
                                                  f"You asked me to pick a number between {split_it[0]} "
                                                  f"and {split_it[1]}, I pick "
                                                  f"'{random.randint(int(split_it[0]), int(split_it[1]))}'")
                    await ctx.send(embed=e)
            if len(split_it) != 2:
                e = discord.Embed(colour=discord.Colour(0xbf2003),
                                  description=f"<:no:609076414469373971> {ctx.author.name}, "
                                              f"Doesnt look like a valid format. $randomnumber <max> or <range> eg; 1-10")
                await ctx.send(embed=e)
        if '-' not in max_or_range and not max_or_range.isdigit():
            e = discord.Embed(colour=discord.Colour(0xbf2003),
                              description=f"<:no:609076414469373971> {ctx.author.name}, "
                                          f"Doesnt look like a valid format. $randomnumber <max> or <range> eg; 1-10")
            await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(general(bot))
