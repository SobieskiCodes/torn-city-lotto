from discord.ext import commands


class NotAuthorized(commands.CommandError):
    message = """Exception raised when the message author is not an owner/admin/has bot rights of the bot."""
    pass


class SlyBastard(commands.CommandError):
    message = """Exception raised when the message author tries to join their own lotto"""
    pass


class NotAdded(commands.CommandError):
    message = """Exception raised when the message author tries to join a lotto without adding their ID"""
    pass


class TempBan(commands.CommandError):
    message = """Exception raised when the message author is banned from the lottery"""
    pass


class TornAPIUnavailable(commands.CommandError):
    message = """Exception raised when the Torn API is unavailable"""
    pass


class TornAPIError(commands.CommandError):
    pass