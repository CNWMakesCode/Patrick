import re
import typing
from random import choice

import discord
from discord import app_commands
from discord.ext import commands


class RelayMember(discord.Member):
    __slots__ = tuple()
    """A subclass of discord.Member to signify that the member is a relay member.
    The class holds no functionality, but is used to signify that the member is a relay member for permission checks.
    """


def return_or_truncate(text, max_length):
    """Takes a string and truncates it to a maximum length, adding ellipsis if truncated.
    If the string is shorter than the maximum length, it returns the original string.

    Args:
        text (str): The string to be truncated.
        max_length (int): The maximum length of the string before truncation.

    Returns:
        str: The original string if it's shorter than max_length, otherwise the truncated string with ellipsis.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def reformat_relay_chat(bot, message) -> discord.Message:
    """Takes a discord message and checks if it's a server relay message.
    If it is, it reformats the message to be processed as a command by the bot.
    It also changes the author of the message to a RelayMember object.
    This is done to prevent the bot from trying to process commands as itself.
    The message is then returned or None if it is not a relay message to signify that it's a regular chat message.

    Args:
        bot (commands.Bot): The bot instance.
        message (discord.Message): The message to be reformatted.

    Returns:
        discord.Message: The reformatted message if it is a relay message, otherwise None.
    """
    match = bot.relay_regex.match(message.content)
    if match:
        author_name, content = match.groups()
        message.author.__class__ = RelayMember
        message.author.nick = author_name
        message.content = content
        return message
    return None


async def process_custom_command(bot, message) -> bool:
    """Take a message and check if it is a custom command. If it is, send a random response from the list of responses.
    If the command is not found, return False.

    Args:
        bot (commands.Bot): The bot instance.
        message (discord.Message): The message to check for a custom command.

    Returns:
        bool: True if the command was found and processed, False otherwise.
    """
    commands = bot.database.commands_cache
    for prefix in bot.command_prefix:
        if message.content.removeprefix(prefix) in commands:
            bot.logger.info(
                f"User '{message.author.display_name}' ran custom command '{message.content[1:]}'"
            )
            await message.channel.send(
                f"{message.author.display_name}: {choice(commands[message.content.removeprefix(prefix)])}"
            )
            await bot.database.add_command_history(
                message.author.display_name, message.content.removeprefix(prefix)
            )
            return True
    return False


def load_automod_regexes(bot):
    """A setup function that loads the automod regexes from the config file.
    This runs a re.compile on each regex to create a compiled regex object for performance.

    Args:
        bot (commands.Bot): The bot instance.
    """
    bot.automod_regexes = [re.compile(regex) for regex in bot.config["automod_regexes"]]


def find_automod_matches(bot, message: discord.Message) -> bool:
    """Checks a message against the automod regexes to see if it matches any of them.

    Args:
        bot (commands.Bot): The bot instance.
        message (discord.Message): A discord message to check.

    Returns:
        bool: True if the message matches any of the automod regexes, False otherwise.
    """
    for regex in bot.automod_regexes:
        if regex.search(message.content) is not None:
            return True
    return False


def is_staff():
    """A decorator that adds a commands.Check to a command to check if the user is a staff member.
    It checks if the user has the staff role in the config file. If they do, it returns True.
    If the user is a RelayMember, it returns False as well.
    If they don't, it raises a MissingPermissions error.
    """

    def predicate(ctx):
        if (
            not isinstance(ctx.author, RelayMember)
            and discord.utils.get(ctx.author.roles, id=ctx.bot.config["roles"]["staff"])
            is not None
        ):
            return True
        else:
            raise commands.MissingPermissions("You are not staff.")

    return commands.check(predicate)


def app_is_staff():
    """A decorator that adds a app_commands.Check to a command to check if the user is a staff member.
    It checks if the user has the staff role in the config file. If they do, it returns True.
    If they don't, it sends a message to the user saying they are not staff and returns False.
    """

    async def predicate(interaction: discord.Interaction):
        if (
            discord.utils.get(
                interaction.user.roles, id=interaction.client.config["roles"]["staff"]
            )
            is not None
        ):
            return True
        else:
            await interaction.response.send_message(
                "You are not staff.", ephemeral=True
            )
            return False

    return app_commands.check(predicate)


def is_admin():
    """A decorator that adds a commands.Check to a command to check if the user is an admin.
    It checks if the user has the admin role in the config file. If they do, it returns True.
    If the user is a RelayMember, it returns False as well.
    If they don't, it raises a MissingPermissions error.
    """

    def predicate(ctx):
        if (
            not isinstance(ctx.author, RelayMember)
            and discord.utils.get(ctx.author.roles, id=ctx.bot.config["roles"]["admin"])
            is not None
        ):
            return True
        else:
            raise commands.MissingPermissions("You are not an admin.")

    return commands.check(predicate)


def app_is_admin():
    """A decorator that adds a app_commands.Check to a command to check if the user is an admin.
    It checks if the user has the admin role in the config file. If they do, it returns True.
    If they don't, it sends a message to the user saying they are not staff and returns False.
    """

    async def predicate(interaction: discord.Interaction):
        if (
            discord.utils.get(
                interaction.user.roles, id=interaction.client.config["roles"]["admin"]
            )
            is not None
        ):
            return True
        else:
            await interaction.response.send_message(
                "You are not an admin.", ephemeral=True
            )
            return False

    return app_commands.check(predicate)
