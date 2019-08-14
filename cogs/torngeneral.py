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
                get_user = await self.bot.fetch.one(f'SELECT TornID FROM Users WHERE DiscordID={ctx.message.mentions[0].id}')
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
                    await ctx.send("Sorry couldnt find that user")
            else:
                await ctx.send("Please provide only a single user to check")
        else:
            get_user = await self.bot.fetch.one(f'SELECT TornID FROM Users WHERE DiscordID={ctx.author.id}')
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
                await ctx.send('it seems i dont have an id added for you.')


    @commands.command()
    async def addid(self, ctx, torn_id):
        """Add your torn id, $addid 1517715
        :param torn_id: Your in game torn ID
        """
        if not torn_id.isdigit():
            await ctx.send('that doesnt look like a torn id...')
        else:
            get_json = await self.bot.torn.api.get_profile(torn_id)
            if get_json:
                get_user = await self.bot.fetch.one(f'SELECT TornID FROM Users WHERE DiscordID={ctx.author.id}')
                if not get_user:
                    id_check = await self.bot.fetch.one(f'SELECT DiscordID FROM Users WHERE TornID={torn_id}')
                    if not id_check:
                        await self.bot.db.execute(f"INSERT INTO Users(TornID, DiscordID) "
                                                                  f"VALUES (?, ?)", (torn_id, ctx.author.id))
                        await self.bot.db.commit()
                        self.bot.addedids.append(ctx.author.id)
                        await ctx.message.add_reaction(discord.utils.get(self.bot.emojis, name='check'))
                        await ctx.author.send(f"{ctx.author.name} has been added with ID: {torn_id}")
                        return
                    else:
                        member = await ctx.guild.fetch_member(id_check[0])
                        await ctx.send(f'{ctx.author.name}, looks like your torn ID is added to {member.name}, is this incorrect?')
                        return

                if get_user:
                    await ctx.send(f'Looks like you already have an id stored as: {get_user[0]}, please contact staff if this is incorrect.')


def setup(bot):
    bot.add_cog(general(bot))
