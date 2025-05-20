# Author: Alec Creasy
# File Name: wordle.py
# Description: Creates the Wordle cog to handle the Wordle game! (Derived from the
# NYT game of the same name)

import discord
from discord import app_commands, channel
from discord.ext import commands
import re
import random
import os
from collections import defaultdict
import asyncio
from time import time
from configparser import ConfigParser

# An instance of a wordle game. The instance will contain the answer of this round, the attempts which consists
# of the guesser, the guess itself, and the bot's chat response, the start time, the number of attempts, and a timeout
# task placeholder variable for the handle_timeout coroutine.
class GameInstance:
    def __init__(self, answer):
        self.answer = answer.lower()
        self.attempts = []
        self.start_time = time()
        self.num_attempts = 0
        self.points_available = defaultdict(int)
        self.timeout_task = None

# The Wordle Cog itself which handles the main logic for the Wordle game and it's commands. Initialized with the bot,
# the list of answers and valid words, the channel name of where wordle will run, the embedded message title, the
# time limit duration of the game, and a dictionary which will house all running games by current channel ID.
# There will also be a ConfigParser that will be responsible for parsing data from the config.ini file.
class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigParser()
        self.config.read("./config.ini")
        self.words = []
        self.valid = []
        self.games = {}
        self.leaderboard = defaultdict(int)
        self.CHANNEL_NAME = self.config.get("Wordle", "CHANNEL_NAME", fallback="wordle")
        self.EMBED_NAME = self.config.get("Wordle", "EMBED_NAME", fallback="Wordle! (Beta)")
        self.DURATION = int(self.config.get("Wordle", "DURATION", fallback=300))
        self.ANSWER_FILE = self.config.get("Wordle", "ANSWER_FILE", fallback=None)
        self.VALID_FILE = self.config.get("Wordle", "VALID_FILE", fallback=None)

        # Check to see if there is an answers and a valid file for the word list. If so, populate the lists with their
        # content. Otherwise, use a simple list of sample words.
        if os.path.exists(self.ANSWER_FILE) and os.path.exists(self.VALID_FILE):
            with open(self.ANSWER_FILE) as file:
                for word in file:
                    self.words.append(word.strip())
                    self.valid.append(word.strip())

                with open(self.VALID_FILE) as file:
                    for word in file:
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
        # in the games dictionary with the key being the current channel ID as well as create a new asynchronous task
        # to handle timeouts (the maximum time duration allowed for the game is up) and store it in the game instance.
        answer = random.choice(self.words)
        print(answer) #Debuggin'
        game = self.games[current_channel] = GameInstance(answer)
        game.timeout_task = asyncio.create_task(self.handle_timeout(current_channel))

        for letter in game.answer:
            game.points_available[letter] += 2

        # Send the message to the user that the game has begun!
        # embed = discord.Embed(title=self.EMBED_NAME, description="A game of Wordle has been initiated! You have 6 tries to guess the word, type your guess in chat! (Must be a 5 letter word)", colour=discord.Colour.green())
        embed = discord.Embed(title=self.EMBED_NAME, description=f"A game of Wordle has been initiated! You have {self.DURATION // 60} minutes to guess the word, type your guess in chat! (Must be a 5 letter word)", colour=discord.Colour.green())
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

        # Create a dictionary for every available letter in the answer, and increment each one's count by 1. This is
        # how we will determine how many times a letter has been used in the current guess. The key is the letter and
        # the value is the amount of letters in the answer.
        available_letters = defaultdict(int)
        for letter in game.answer:
            available_letters[letter] += 1

        # This boolean list will be used for the first pass through the answer. A 0 at a position indicates an incorrect
        # placement of a letter, and 1 indicates a correct placement.
        correct_pos = [0] * 5

        score = 0

        # For every letter in content, compare it to that of the answer and if the letter is in the appropriate place,
        # update the value of correct_pos to reflect that the current letter is in the correct position, and decrement
        # the count of this letter by 1.
        for i, letter in enumerate(content):
            if content[i] == game.answer[i]:
                correct_pos[i] = 1
                available_letters[letter] -= 1

        # For every letter in content, first compare it to the correct_pos list element at the same position and if it
        # is 1 (that is, the letter is in the appropriate place), to that of the answer and if the letter is in the
        # appropriate place, add a green square emoji to the responser. Otherwise, if the letter is not in the right
        # place but is found elsewhere in the answer, add a yellow square emoji indicating the letter is in the answer,
        # just not here. Finally, if the letter is not in the answer at all, add a black square emoji to the response.
        for i, letter in enumerate(content):
            if correct_pos[i] == 1:
                response += ":green_square: "

                if game.points_available[letter] >= 2:
                    score += 2
                    game.points_available[letter] -= 2
                elif game.points_available[letter] >= 1:
                    score += 1
                    game.points_available[letter] -= 1

            elif content[i] in game.answer and available_letters[letter] > 0:
                response += ":yellow_square: "

                if game.points_available[letter] >= 1:
                    score += 1
                    game.points_available[letter] -= 1
                available_letters[letter] -= 1

            else:
                response += ":black_large_square: "

        # Add the guess to the response, and make the guess all capitalized.
        response += f"{content.upper()}"

        # Add the guesser, the guess, and the response to the game's attempts list.
        game.attempts.append((message.author.mention, content, response))

        # Get the amount of time elapsed to calculate the amount of time remaining, and always round the time up to the
        # nearest minute. (For example, if there is 1 minute and 30 seconds remaining, round up to 2 whole minutes).
        time_elapsed = time() - game.start_time
        time_remaining = max(0, self.DURATION - time_elapsed)
        time_remaining = int((time_remaining + 59) // 60)

        self.leaderboard[message.author.mention] += score

        # Set the response to the history string (all past responses) and concatenate the new response to the end of
        # the history string, and then concatenate the guesser to the end of the message.
        response = history + response + f" - Guessed by {message.author.mention} (+{score})\n\n{time_remaining} minute{'s' if time_remaining != 1 else ''} remaining!"

        # Create the embedded message with the response and send it.
        embed = discord.Embed(title=self.EMBED_NAME, description=response, color=discord.Color.green())
        await message.channel.send(embed=embed)

        # If the guess is the answer, report that the guesser got the word and the number of attempts used, and delete
        # the game instance for the games dictionary, ending the game, and return.
        if content == game.answer:
            self.leaderboard[message.author.mention] += 4
            embed = discord.Embed(title=self.EMBED_NAME, description=f'{message.author.mention} guessed the correct word {game.answer.upper()} in {game.num_attempts} tries and has been awarded 4 points! Well done!', color=discord.Color.green())
            await message.channel.send(embed=embed)
            game.timeout_task.cancel()
            del self.games[current_channel]
            return

    # Handles displaying the leaderboard stats
    @app_commands.command(name="leaderboard", description="Displays the current leaderboard for Wordle!")
    async def leaderboard(self, interaction):
        if interaction.channel.name != self.CHANNEL_NAME:
            channel = discord.utils.get(interaction.guild.text_channels, name=self.CHANNEL_NAME)
            if channel:
                embed = discord.Embed(title=self.EMBED_NAME, description=f"Please use the {channel.mention} channel to display the leaderboard!", color=discord.Color.red())
            else:
                embed = discord.Embed(title=self.EMBED_NAME, description=f"#{self.CHANNEL_NAME} not found! Please ensure you have a #{self.CHANNEL_NAME} text channel setup to play and use the leaderboard!", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        response = ""
        sorted_leaderboard = sorted(self.leaderboard.items(), key=lambda item: item[1], reverse=True)

        for i, (user, score) in enumerate(sorted_leaderboard):
            response += f"{i+1}. {user}: {score}\n"

        response += "\nThe leaderboard resets every Sunday at 12PM Central Time!"

        embed = discord.Embed(title=self.EMBED_NAME, description=response, color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    # Handles ending the game if the time has run out.
    async def handle_timeout(self, channel_id):
        try:
            # Sleep for the duration of the game.
            await asyncio.sleep(self.DURATION)

            # If the coroutine is woken back up, time is up for the game. If the game is still running and the channel
            # still exists (it should), then send an embedded message that the time is up with the correct answer and
            # delete the game from the games dictionary.
            game = self.games.get(channel_id)
            if game:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(title=self.EMBED_NAME, description=f"Time's Up! The correct word was {game.answer.upper()}!", color=discord.Color.red())
                    await channel.send(embed=embed)
                    del self.games[channel_id]
        # Catch the exception if the game ended due to the correct word being guessed within the time limit and ignore
        # it.
        except asyncio.CancelledError:
            pass

# Setups the Cog to be used by the bot.
async def setup(bot):
    await bot.add_cog(Wordle(bot))