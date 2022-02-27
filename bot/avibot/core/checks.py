from discord.ext import commands


async def check_is_owner(ctx):
    return await ctx.bot.is_owner(ctx.author)


async def check_is_guildowner(ctx):
    if ctx.author.id == ctx.guild.owner.id:
        return True
    return False


async def check_is_admin(ctx):
    if await check_is_guildowner(ctx):
        return True
    if ctx.author.guild_permissions.manage_guild:
        return True
    return False


async def check_is_mod(ctx):
    if await check_is_admin(ctx):
        return True
    if ctx.author.permissions_in(ctx.channel).manage_messages:
        return True
    return False


def is_owner():
    return commands.check(check_is_owner)


def is_guildowner():
    return commands.check(check_is_guildowner)


def is_admin():
    return commands.check(check_is_admin)


def is_mod():
    return commands.check(check_is_mod)
