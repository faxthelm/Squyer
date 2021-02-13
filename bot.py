import asyncio
import os
import discord
from discord import Embed
from discord.ext import commands

from exceptions import CommandTimeoutException as TimeoutException, TournamentTypeException as TypeException, \
    TournamentNumberOfPlayersException as NumberOfPlayersException

intents = discord.Intents(messages=True, guilds=True, reactions=True)

# Remember to create herokuenv
BOT_ID = 801287710316298261
TOKEN = os.environ['DISCORD_TOKEN']
CHANNEL_NAME = "torneio"
REACTIONS = {"YES": '🇾', "NO": '🇳'}
FIRST_QUESTION = "Qual tipo de torneio você deseja fazer?\n""Premium ou Principal?"
SECOND_QUESTION = "Qual o numero de participantes? (2,4,8,16,32)"
CHAR_QUESTION = "Digite o nome da classe que você irá utilizar para confirmar sua inscrição, "
EMPTY_DESCRIPTION = "```\n```"
NUMBER_OF_PLAYERS = {2, 4, 8, 16, 32}

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.command(name="torneio", help="Cria um torneio, o usuário que usar esse comando vira o dono do torneio")
async def create_tournament_listener(ctx, *args):
    try:
        tournament_details = await create_tournament(ctx, args)
        create_tournament_document(ctx.message.author.id, tournament_details[0], tournament_details[1])
    except TimeoutException.CommandTimeoutException as cte:
        await ctx.send(cte.args[0], delete_after=10.0)
        raise
    except TypeException.TournamentTypeException as tte:
        await ctx.send(tte.args[0], delete_after=10.0)
        raise
    except NumberOfPlayersException.TournamentNumberOfPlayersException as tnpe:
        await ctx.send(tnpe.args[0], delete_after=10.0)
        raise
    finally:
        await ctx.message.delete()

    embed = discord.Embed(colour=discord.Colour(0xf32c))
    embed.add_field(name="Tipo", value=tournament_details[0], inline=True)
    embed.add_field(name="Vagas Restantes", value=str(tournament_details[1]))
    embed.add_field(name="Organizador", value=ctx.message.author.display_name, inline=True)
    message = await ctx.send(embed=embed)
    await message.add_reaction("\U0001F1FE")
    await message.add_reaction("\U0001F1F3")


@bot.event
async def on_raw_reaction_add(payload):
    channel_id = payload.channel_id
    member = payload.member
    channels = member.guild.channels
    channel = None
    # Get the channel object from the channels list, without having to request it.
    for ch in channels:
        if ch.id == channel_id:
            channel = ch
            break
    # If this reaction wasn't on the tournament channel, don't list to it.
    if channel.name != CHANNEL_NAME:
        return
    message = await channel.fetch_message(payload.message_id)
    try:
        internal_response = await on_reaction_add_logic(payload, message, channel)
        # TODO: save our change to the MongoDB
    except TimeoutException.CommandTimeoutException as cte:
        await channel.send(cte.args[0], delete_after=10.0)
        raise
    finally:
        # Only remove reactions by users other than bots
        if not payload.member.bot:
            await message.remove_reaction(payload.emoji, payload.member)


@bot.event
async def on_raw_reaction_remove(payload):
    channel_id = payload.channel_id
    member = payload.member


@bot.command(name="cancelar", help="Cancela o torneio (somente o criador do torneio)")
async def cancel_tournament(ctx, *args):
    if ctx.message.channel != CHANNEL_NAME:
        return
    # await ctx.send(response)


@bot.command(name="iniciar", help="Inicia o torneio (somente o criador do torneio)")
async def start_tournament(ctx, *args):
    if ctx.message.channel != CHANNEL_NAME:
        return

    if len(args) == 0:
        print()
    # await ctx.send(response)


async def create_tournament(ctx, args):
    print("Uso do comando !torneio")
    if ctx.message.channel.name != CHANNEL_NAME:
        print("Uso do comando !torneio fora do chat #torneio")
        return
    # If the user already sent the required arguments, create the tournament
    if len(args) == 2:
        try:
            if int(args[1]) not in NUMBER_OF_PLAYERS:
                raise NumberOfPlayersException.TournamentNumberOfPlayersException()
        except ValueError:
            raise NumberOfPlayersException.TournamentNumberOfPlayersException()
        tournament_type = check_tournament_type(args[0])
        if tournament_type is None:
            raise TypeException.TournamentTypeException()
        return args[0].upper(), args[1]
    else:
        first_response = await ask_question(ctx.channel, ctx.author.id, FIRST_QUESTION)
        check_tournament_type(first_response)
        second_response = await ask_question(ctx.channel, ctx.author.id, SECOND_QUESTION)
        try:
            if int(second_response) not in NUMBER_OF_PLAYERS:
                raise NumberOfPlayersException.TournamentNumberOfPlayersException()
        except ValueError:
            raise NumberOfPlayersException.TournamentNumberOfPlayersException()
        return first_response.upper(), second_response


async def ask_question(channel, member_id, question_text):
    response = None
    question = await channel.send(question_text)
    try:
        response = await bot.wait_for('message', check=lambda message: message.author.id == member_id, timeout=10.0)
    except asyncio.TimeoutError:
        await question.delete()
        raise TimeoutException.CommandTimeoutException()
    await question.delete()
    if response is not None:
        await response.delete()
    return response.content


def check_tournament_type(tournament_type_check):
    tournament_type = None
    if tournament_type_check.upper() == "PREMIUM":
        tournament_type = "PREMIUM"
    if tournament_type_check.upper() == "PRINCIPAL":
        tournament_type = "PRINCIPAL"
    if tournament_type is None:
        raise TypeException.TournamentTypeException()
    return tournament_type


def create_tournament_document(creator_id, tournament_type, number_of_players):
    print(
        "creating tournament for " + str(creator_id) + " with type: " + tournament_type + ", number_of_players: " + str(
            number_of_players))
    # create a try/retry in case of errors


async def on_reaction_add_logic(payload, message, channel):
    print("Reação adicionada")
    member = payload.member
    # Only act upon these reactions
    if payload.emoji.name != REACTIONS.get("YES") and payload.emoji.name != REACTIONS.get("NO"):
        return
    # We won't act to bots reactions
    if member.bot:
        return
    # We will only act on reactions from messages sent by our bot that contain embed
    if message.author.id != BOT_ID and len(message.embeds) == 0:
        return
    embed_dict = message.embeds[0].to_dict()
    if "description" not in embed_dict:
        embed_dict["description"] = EMPTY_DESCRIPTION
    if payload.emoji.name == REACTIONS.get("YES"):
        # We don't want anyone entering the tournament if there are no slots
        if int(embed_dict["fields"][1]["value"]) <= 0:
            return
        char = await ask_question(message.channel, payload.user_id, CHAR_QUESTION + member.display_name)
        embed_dict = update_participants("add", payload.member, char, embed_dict)
    elif payload.emoji.name == REACTIONS.get("NO"):
        embed_dict = update_participants("remove", payload.member, None, embed_dict)
    else:
        return

    # Retrive the message once more to check if we can actually fit this member into the list
    message_recheck = await channel.fetch_message(payload.message_id)
    if int(message_recheck.embeds[0].to_dict()["fields"][1]["value"]) > 0 or payload.emoji.name == REACTIONS.get("NO"):
        new_embed = Embed.from_dict(embed_dict)
        await message.edit(embed=new_embed)


def update_participants(action, member, char, embed_dict):
    description = embed_dict["description"]
    if action == "add":
        if member.display_name not in description:
            list_members = description_to_list(description)
            list_members.append({"char": char, "name": member.display_name})
            embed_dict["fields"][1]["value"] = str(int(embed_dict["fields"][1]["value"]) - 1)
            embed_dict["description"] = format_description(list_members)
    elif action == "remove":
        if member.display_name in description:
            list_members = description_to_list(description)
            # If someone presses the N while there are no members in the list
            if len(list_members) == 0:
                return description
            for item in list_members:
                if item["name"] == member.display_name:
                    list_members.remove(item)
                    break
            embed_dict["description"] = format_description(list_members)
            embed_dict["fields"][1]["value"] = str(int(embed_dict["fields"][1]["value"]) + 1)
    return embed_dict


def description_to_list(description):
    list = []
    if description == EMPTY_DESCRIPTION:
        return list
    list_members = description.split("\n")
    # Removing the Quotes that create the code box in discord
    list_members.pop(0)
    list_members.pop()
    for member in list_members:
        list.append({"char": member[0:13].strip(), "name": member[15:].strip()})

    return sorted(list, key=lambda k: k["name"])


def format_description(list):
    response = ""
    if len(list) == 0:
        return response
    sorted_list = sorted(list, key=lambda k: k["name"])
    for member in sorted_list:
        response += "{} | {}\n".format(member["char"][0:13].center(13, " "), member["name"][0:41])
    if response != "":
        response = "```\n" + response + "```"
    return response


bot.run(TOKEN)
