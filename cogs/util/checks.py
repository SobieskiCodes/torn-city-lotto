from discord.ext import commands
from cogs.util.errorhandling import NotAdded, TempBan, NotAuthorized


def has_id_added():
    async def pred(ctx):
        if ctx.author.id not in ctx.bot.addedids:
            raise NotAdded
        if ctx.author.id in ctx.bot.addedids:
            return True
    return commands.check(pred)


def temp_ban():
    async def pred(ctx):
        for entry in ctx.bot.guildconfigs:
            if entry.guildid == ctx.guild.id:
                for role in ctx.author.roles:
                    if entry.bannedrole == role.id:
                        raise TempBan
                if entry.bannedrole not in ctx.author.roles:
                    return True
    return commands.check(pred)


def is_guild_owner():
    async def pred(ctx):
        if ctx.author == ctx.guild.owner:
            return True
        else:
            raise NotAuthorized
    return commands.check(pred)

