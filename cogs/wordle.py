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

class GameInstance:
    def __init__(self, answer):
        self.answer = answer.lower()
        self.attempts = []
        self.num_attempts = 0
        self.MAX_ATTEMPTS = 6
        self.is_over = False

class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.words = []
        self.valid = []
        self.CHANNEL_NAME = "wordle"
        self.games = {}
        self.emotes = {1: ":one:", 2: ":two:", 3: ":three:", 4: ":four:", 5: ":five:", 6: ":six:"}

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

    @app_commands.command(name="wordle", description="Starts a game of Wordle!")
    async def wordle(self, interaction):
        if interaction.channel.name != self.CHANNEL_NAME:
            channel = discord.utils.get(interaction.guild.text_channels, name=self.CHANNEL_NAME)
            if channel:
                embed = discord.Embed(title="Wordle!", description=f"Please use the {channel.mention} channel to start a game!", color=discord.Color.red())
            else:
                embed = discord.Embed(title="Wordle!", description=f"#{self.CHANNEL_NAME} not found! Please ensure you have a #{self.CHANNEL_NAME} text channel setup to play!", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        current_channel = interaction.channel.id

        if current_channel in self.games and not self.games[current_channel].is_over:
            embed = discord.Embed(title="Wordle!", description="A game is already running!", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        answer = random.choice(self.words)
        self.games[current_channel] = GameInstance(answer)

        embed = discord.Embed(title="Wordle!", description="A game of Wordle has been initiated! You have 6 tries to guess the word, type your guess in chat! (Must be a 5 letter word)", colour=discord.Colour.green())

        await interaction.response.send_message(embed=embed)
        print(f"{answer} is the word (This is for debugging)")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.channel.name != self.CHANNEL_NAME:
            return

        current_channel = message.channel.id

        if current_channel not in self.games or self.games[current_channel].is_over:
            return

        content = message.content.strip().lower()

        if not re.fullmatch(r"[a-z]{5}", content):
            return

        if content not in self.valid:
            embed = discord.Embed(title="Wordle!", description=f"{content.upper()} is not a valid word!", color=discord.Color.red())
            await message.channel.send(embed=embed)
            return

        game = self.games[current_channel]

        if any(past_guess == content for _, past_guess, _ in game.attempts):
            embed = discord.Embed(title="Wordle!", description=f"{content.upper()} has already been guessed!", color=discord.Color.red())
            await message.channel.send(embed=embed)
            return

        game.num_attempts += 1

        history = ""
        response = ""

        for guesser, _, past_response in game.attempts:
            history += f"{past_response} - Guessed by {guesser}\n"

        response += f"{self.emotes[game.num_attempts]} "

        available_letters = defaultdict(int)
        for letter in game.answer:
            available_letters[letter] += 1

        for i, letter in enumerate(content):
            if content[i] == game.answer[i]:
                response += ":green_square: "
                available_letters[letter] -= 1
            elif content[i] in game.answer and available_letters[letter] > 0:
                response += ":yellow_square: "
                available_letters[letter] -= 1
            else:
                response += ":black_large_square: "

        response += f"{content.upper()}"

        game.attempts.append((message.author.mention, content, response))

        response = history + response + f" - Guessed by {message.author.mention}"

        embed = discord.Embed(title="Wordle!", description=response, color=discord.Color.green())

        await message.channel.send(embed=embed)

        if content == game.answer:
            game.is_over = True
            embed = discord.Embed(title="Wordle!", description=f'{message.author.mention} guessed the correct word "{game.answer}" in {game.num_attempts} tries! Well done!', color=discord.Color.green())
            await message.channel.send(embed=embed)
            del self.games[current_channel]
            return

        if game.num_attempts >= game.MAX_ATTEMPTS:
            game.is_over = True
            embed = discord.Embed(title="Wordle!", description=f'Out of guesses! The correct word was "{game.answer}"! Better Luck Next Time!', color=discord.Color.red())
            await message.channel.send(embed=embed)
            del self.games[current_channel]
            return

async def setup(bot):
    await bot.add_cog(Wordle(bot))