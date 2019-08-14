from discord.ext import commands
import discord
import asyncio

loot_dict = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5}
npc = {
    'npcs': {
        'duke': {
            'id': 4,
            'image': 'https://profileimages.torn.com/50c3ed98-ae8f-311d-4.png',
        },
        'leslie': {
            'id': 15,
            'image': 'https://profileimages.torn.com/4d661456-746e-b140-15.png',
        }
    }
}


class lootLevel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status = []

    async def main(self, time: int = 60):
        while True:
            for person in npc['npcs']:
                get_json = await self.bot.torn.api.get_profile(npc['npcs'].get(person).get('id'))
                loot_level = get_json['status'][1]
                if loot_level.startswith('Loot'):
                    get_lvl = get_json['status'][1].split(' ')[2]

                    if get_lvl in loot_dict.keys():
                        self.status.append(f"{get_json['name']} {get_lvl}")
            if self.status:
                await self.bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=3, name=f"{' | '.join(self.status)}"))
            else:
                await self.bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=3, name=f"$ll <name> | $ll"))
            self.status = []
            await asyncio.sleep(time)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(lootLevel.main(self))

    @commands.command(aliases=['ll', 'loot'])
    async def lootlevel(self, ctx, npc_name: str = None):
        """$lootlevel <npc name> or $lootlevel
        Aliases: $ll, $loot
        If a name is provided will display just that NPC's status
        Otherwise default is all lootable NPC's.
        example: $ll duke |or| $ll
        The two NPC's available are Duke and Leslie.
        """
        if npc_name:
            npc_name = npc_name.lower()
            if npc_name in npc['npcs'].keys():
                get_json = await self.bot.torn.api.get_profile(npc['npcs'].get(npc_name).get('id'))
                loot_level = get_json['status'][1]
                if loot_level.startswith('Loot'):
                    profile = await self.bot.torn.url.get_profiles(get_json['player_id'])
                    e = discord.Embed(
                            title=f"{get_json['name']} [{get_json['player_id']}]",
                            description=f"{loot_level}\n\n[profile]({profile})",
                            colour=discord.Colour(0x278d89)
                        )
                    e.set_thumbnail(url=f"{npc['npcs'].get(npc_name).get('image')}")
                    await ctx.send(embed=e)
                else:
                    profile = await self.bot.torn.url.get_profiles(get_json['player_id'])
                    e = discord.Embed(
                            title=f"{get_json['name']} [{get_json['player_id']}]",
                            description=f"Loot level unknown\n{get_json['status'][0]}\n\n"
                                            f"[profile]({profile})",
                            colour=discord.Colour(0x278d89)
                        )
                    e.set_thumbnail(url=f"{npc['npcs'].get(npc_name).get('image')}")
                    await ctx.send(embed=e)
        else:
            npc_loot_level = ''
            npc_name_list = ''
            lvls_list = []
            for person in npc['npcs']:
                get_json = await self.bot.torn.api.get_profile(npc['npcs'].get(person).get('id'))
                npc_id = get_json['player_id']
                npc_name = get_json['name']
                loot_level = get_json['status'][1]
                attack = await self.bot.torn.url.get_attack(get_json['player_id'])
                npc_name_list += f"[{npc_name} [{npc_id}]]({attack})\n"
                if loot_level.startswith('Loot'):
                    npc_loot_level += f'{loot_level}\n'
                    lvl = loot_dict.get(get_json['status'][1].split(' ')[2])
                    lvls_list.append(lvl)
                else:
                    npc_loot_level += f'Loot level unknown, {get_json["status"][0]}\n'
            embed = discord.Embed(colour=discord.Colour(0x278d89))
            if lvls_list:
                embed.set_thumbnail(url=f"https://sobieski.codes/torn/loot_{max(lvls_list)}.png")
            if not lvls_list:
                embed.set_thumbnail(url=f"https://sobieski.codes/torn/hospital.png")
            embed.add_field(name='NPC', value=npc_name_list)
            embed.add_field(name='Loot Level', value=npc_loot_level)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(lootLevel(bot))
