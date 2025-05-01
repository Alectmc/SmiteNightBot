# Author: Alec Creasy
# File Name: wordle.py
# Description: Creates the Wordle cog to handle the Wordle game! (Derived from the
# NYT game of the same name)
from sys import builtin_module_names

import discord
from discord import app_commands
from discord.ext import commands
import re
import random
import os
from collections import defaultdict

# An instance of a wordle game. The instance will contain the answer of this round, the attempts which consists
# of the guesser, the guess itself, and the bot's chat response, the number of attempts, and the maximum amount of
# attempts.
class GameInstance:
    def __init__(self, answer):
        self.answer = answer.lower()
        self.attempts = []
        self.num_attempts = 0
        self.MAX_ATTEMPTS = 6

# The Wordle Cog itself which handles the main logic for the Wordle game and it's commands. Initialized with the bot,
# the list of answers and valid words, the channel name of where wordle will run, the embeded message title, a
# dictionary which will house all running games by current channel ID, and a dictionary for the emotes for
# which attempt the game is on.
class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.words = []
        self.valid = []
        self.CHANNEL_NAME = "wordle"
        self.EMBED_NAME = "Wordle! (Beta)"
        self.games = {}
        self.emotes = {1: ":one:", 2: ":two:", 3: ":three:", 4: ":four:", 5: ":five:", 6: ":six:"}

        # Check to see if there is an answers and a valid file for the word list. If so, populate the lists with their
        # content. Otherwise, use a simple list of sample words.
        if os.path.exists('./data/answers.txt') and os.path.exists('./data/valid.txt'):
            with open("./data/answers.txt") as f:
                for word in f:
                    self.words.append(word.strip())
                    self.valid.append(word.strip())

                with open("./data/valid.txt") as f:
                    for word in f:
                        self.valid.append(word.strip())
        else:
            self.words = self.valid = ["chair", "table", "plant", "apple", "grape", "brick", "story", "shelf", "piano", "train"]

    # Creates the command for /wordle, which will begin a new game of Wordle if the user is in the #wordle text channel.
    @app_commands.command(name="wordle", description="Starts a game of Wordle!")
    async def wordle(self, interaction):
        # Check to see if the current channel is the #wordle channel. If not, see if the channel exists and if it does,
        # report to the user that they must use the #wordle channel and return. If the channel does not exist, notify the user that
        # a #wordle channel was not found and that one needs to be setup to play and return.
        if interaction.channel.name != self.CHANNEL_NAME:
            channel = discord.utils.get(interaction.guild.text_channels, name=self.CHANNEL_NAME)
            if channel:
                embed = discord.Embed(title=self.EMBED_NAME, description=f"Please use the {channel.mention} channel to start a game!", color=discord.Color.red())
            else:
                embed = discord.Embed(title=self.EMBED_NAME, description=f"#{self.CHANNEL_NAME} not found! Please ensure you have a #{self.CHANNEL_NAME} text channel setup to play!", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # If the #wordle channel exists and the command was run in the /wordle channel, get the channel ID.
        current_channel = interaction.channel.id

        # Check if a game is already running. If so, report this to the user and return.
        if current_channel in self.games:
            embed = discord.Embed(title=self.EMBED_NAME, description="A game is already running!", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # If a game is not running, select a random word and create a new instance of the Wordle game, and store it
        # in the games dictionary with the key being the current channel ID.
        answer = random.choice(self.words)
        self.games[current_channel] = GameInstance(answer)

        # Send the message to the user that the game has begun!
        embed = discord.Embed(title=self.EMBED_NAME, description="A game of Wordle has been initiated! You have 6 tries to guess the word, type your guess in chat! (Must be a 5 letter word)", colour=discord.Colour.green())
        await interaction.response.send_message(embed=embed)

    # Event listener for messages. Will trigger for every message that is sent, but the only logic that will apply is
    # if the message was sent in the #wordle channel and ONLY contains a 5 letter word with a game currently running.
    @commands.Cog.listener()
    async def on_message(self, message):
        # If the message was sent by the bot, ignore it and return.
        if message.author == self.bot.user:
            return

        # If the message was not sent in #wordle, ignore it and return.
        if message.channel.name != self.CHANNEL_NAME:
            return

        # Get the channel ID of the current channel (should be #wordle).
        current_channel = message.channel.id

        # If the current_channel is not found in the games dictionary (that is, a game is not running), ignore the
        # message and return. If we pass this if statement, then we now know that a game is indeed running.
        if current_channel not in self.games:
            return

        # Get the message content, strip it of any whitespace and set all characters to lowercase.
        content = message.content.strip().lower()

        # Use a regular expression to check if the message contains only lowercase letters of the alphabet and that
        # the message is only 5 characters long. If it is not, ignore the message and return. If we pass this if
        # statement, we know a game is running and that the sent message was a guess that matches the approriate
        # pattern.
        if not re.fullmatch(r"[a-z]{5}", content):
            return

        # If the sent message is a word not in the valid list (that is, it is not a valid word), report this to the
        # user and return.
        if content not in self.valid:
            embed = discord.Embed(title=self.EMBED_NAME, description=f"{content.upper()} is not a valid word!", color=discord.Color.red())
            await message.channel.send(embed=embed)
            return

        # Get the current game instance for this channel.
        game = self.games[current_channel]

        # Check to see if the guessed word was used at all in this game. We do this by checking the attempts list to see
        # if the current guess has appeared elsewhere in the game. If it has, report this to the user and return.
        if any(past_guess == content for _, past_guess, _ in game.attempts):
            embed = discord.Embed(title=self.EMBED_NAME, description=f"{content.upper()} has already been guessed!", color=discord.Color.red())
            await message.channel.send(embed=embed)
            return

        # At this point, we now know that the user has made a valid guess, so we increment the number of attempts by 1
        # and we can now address the logic of if the guess was right or wrong, and the correct characters picked in
        # this guess.
        game.num_attempts += 1

        # Create 2 empty string variables for the history of past responses by the bot and the new reponse line
        # to be added when the bot reports the past guesses and the newest guess that we just received.
        history = ""
        response = ""

        # This simply gets every guesser and their past responses and adds them to the history string, which will be
        # sent out as part of the bots response to the guess. If this is the first guess, then this will be skipped
        # automatically.
        for guesser, _, past_response in game.attempts:
            history += f"{past_response} - Guessed by {guesser}\n"

        # Add the current emoji corresponding to the attempt number to the front of the new response.
        response += f"{self.emotes[game.num_attempts]} "

        # Create a dictionary for every available letter in the answer, and increment each one's count by 1. This is
        # how we will determine how many times a letter has been used in the current guess. The key is the letter and
        # the value is the amount of letters in the answer.
        available_letters = defaultdict(int)
        for letter in game.answer:
            available_letters[letter] += 1

        # For every letter in content, compare it to that of the answer and if the letter is in the approriate place,
        # add a green square emoji to the response and decrement the count of that letter. Otherwise, if the letter
        # is not in the right place but is found elsewhere in the answer, add a yellow square emoji indicating the
        # letter is in the answer, just not here. Finally, if the letter is not in the answer at all, add a black
        # square emoji to the response.
        # NOTE: This current implementation has a bug that will need to be ironed out. The issue is best seen with
        # an example: If the answer is "gates" and the user guesses "grass", the second to last "s" will be marked as
        # a yellow emoji, and then the last "s" will be marked with a green emoji. This makes it seem as if there are
        # 2 "s"'s in the answer, when there is only 1. This will be fixed in a future update very soon.
        for i, letter in enumerate(content):
            if content[i] == game.answer[i]:
                response += ":green_square: "
                available_letters[letter] -= 1
            elif content[i] in game.answer and available_letters[letter] > 0:
                response += ":yellow_square: "
                available_letters[letter] -= 1
            else:
                response += ":black_large_square: "

        # Add the guess to the response, and make the guess all capitalized.
        response += f"{content.upper()}"

        # Add the guesser, the guess, and the response to the game's attempts list.
        game.attempts.append((message.author.mention, content, response))

        # Set the response to the history string (all past responses) and concatenate the new response to the end of
        # the history string, and then concatenate the guesser to the end of the message.
        response = history + response + f" - Guessed by {message.author.mention}"

        # Create the embedded message with the response and send it.
        embed = discord.Embed(title=self.EMBED_NAME, description=response, color=discord.Color.green())
        await message.channel.send(embed=embed)

        # If the guess is the answer, report that the guesser got the word and the number of attempts used, and delete
        # the game instance for the games dictionary, ending the game, and return.
        if content == game.answer:
            embed = discord.Embed(title=self.EMBED_NAME, description=f'{message.author.mention} guessed the correct word "{game.answer}" in {game.num_attempts} tries! Well done!', color=discord.Color.green())
            await message.channel.send(embed=embed)
            del self.games[current_channel]
            return

        # If the number of attempts meets or exceeds the maximum number of attempts, report that everyone is out of
        # guesses and what the word was, delete the game instance from the games dictionary, ending the game, and
        # return.
        if game.num_attempts >= game.MAX_ATTEMPTS:
            embed = discord.Embed(title=self.EMBED_NAME, description=f'Out of guesses! The correct word was "{game.answer}"! Better Luck Next Time!', color=discord.Color.red())
            await message.channel.send(embed=embed)
            del self.games[current_channel]
            return

# Setups the Cog to be used by the bot.
async def setup(bot):
    await bot.add_cog(Wordle(bot))