import asyncio
import os
import discord
from discord.ext import commands

from exceptions import CommandTimeoutException as TimeoutException, TournamentTypeException as TypeException, \
    TournamentNumberOfPlayersException as NumberOfPlayersException

intents = discord.Intents(messages=True, guilds=True, reactions=True)

# Remember to create herokuenv
TOKEN = os.environ['DISCORD_TOKEN']
CHANNEL_NAME = "torneio"
FIRST_QUESTION = "Qual tipo de torneio você deseja fazer?\n""Premium ou Principal?"
SECOND_QUESTION = "Qual o numero de participantes? (2,4,8,16,32)"
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
    print("TODO")


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
    print("creating tournament for " + str(creator_id) + " with type: " + tournament_type + ", number_of_players: " + str(number_of_players))
    # create a try/retry in case of errors


bot.run(TOKEN)
