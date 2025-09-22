"""
DuckBot Entertainment Commands
Complete entertainment system with fun commands, games, social features, and utilities
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import random
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import aiohttp
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..core.cost_management import CostTracker
from ..integrations.vibevoice_client import vibevoice_integration

logger = logging.getLogger(__name__)

class EntertainmentCommands(commands.Cog):
    """Entertainment commands for Discord with VibeVoice integration."""

    def __init__(self, bot: commands.Bot, cost_tracker: Optional[CostTracker] = None):
        self.bot = bot
        self.cost_tracker = cost_tracker
        self.vibevoice = vibevoice_integration

        # Rate limiting
        self.rate_limits = {
            "fun_commands": {"calls": 10, "period": 60},  # 10 calls per minute
            "games": {"calls": 5, "period": 60},  # 5 calls per minute
            "voice_entertainment": {"calls": 3, "period": 300}  # 3 calls per 5 minutes
        }
        self.user_calls = defaultdict(lambda: defaultdict(list))

        # Game states
        self.hangman_games = {}  # guild_id: game_state
        self.quiz_games = {}  # channel_id: game_state

        # Load data files
        self.data_dir = Path(__file__).parent.parent / "data"
        self.jokes = self._load_json_data("jokes.json")
        self.quotes = self._load_json_data("quotes.json")
        self.facts = self._load_json_data("facts.json")
        self.trivia = self._load_json_data("trivia.json")

        # 8-ball responses
        self.eightball_responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes - definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.",
            "Outlook not so good.", "Very doubtful."
        ]

        # RPS choices
        self.rps_choices = ["rock", "paper", "scissors"]
        self.rps_emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

        logger.info(f"Entertainment commands loaded with {len(self.jokes)} jokes, {len(self.quotes)} quotes, {len(self.facts)} facts, {len(self.trivia.get('questions', []))} trivia questions")

    def _load_json_data(self, filename: str) -> List[Dict]:
        """Load JSON data from file."""
        try:
            with open(self.data_dir / filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            return []

    def check_rate_limit(self, user_id: int, command_type: str) -> bool:
        """Check if user is rate limited."""
        if command_type not in self.rate_limits:
            return True

        limit = self.rate_limits[command_type]
        now = datetime.now()
        cutoff = now - timedelta(seconds=limit["period"])

        # Remove old calls
        self.user_calls[user_id][command_type] = [
            call_time for call_time in self.user_calls[user_id][command_type]
            if call_time > cutoff
        ]

        # Check if user has exceeded limit
        if len(self.user_calls[user_id][command_type]) >= limit["calls"]:
            return False

        # Add current call
        self.user_calls[user_id][command_type].append(now)
        return True

    async def get_random_meme(self) -> Optional[Dict]:
        """Get a random meme from Reddit API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://meme-api.herokuapp.com/gimme") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "title": data.get("title"),
                            "url": data.get("url"),
                            "author": data.get("author"),
                            "subreddit": data.get("subreddit")
                        }
        except Exception as e:
            logger.error(f"Failed to fetch meme: {e}")
        return None

    # === FUN COMMANDS ===

    @app_commands.command(name="joke", description="Get a random joke")
    @app_commands.describe(category="Filter jokes by category (optional)")
    async def joke_command(self, interaction: discord.Interaction, category: Optional[str] = None):
        """Get a random joke."""
        if not self.check_rate_limit(interaction.user.id, "fun_commands"):
            embed = discord.Embed(
                title="⚠️ Rate Limit",
                description="You're using this command too quickly! Please wait a minute.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            if category:
                jokes = [j for j in self.jokes if j.get("category", "").lower() == category.lower()]
            else:
                jokes = self.jokes

            if not jokes:
                embed = discord.Embed(
                    title="❌ No Jokes Found",
                    description=f"No jokes found in category: {category}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return

            joke = random.choice(jokes)

            embed = discord.Embed(
                title="😄 Random Joke",
                description=f"**{joke['setup']}**\n\n{joke['punchline']}",
                color=discord.Color.yellow()
            )
            embed.add_field(name="Category", value=joke.get("category", "General"), inline=True)
            embed.set_footer(text=f"Joke #{joke['id']}")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Joke command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching a joke.",
                ephemeral=True
            )

    @app_commands.command(name="meme", description="Get a random meme")
    async def meme_command(self, interaction: discord.Interaction):
        """Get a random meme from Reddit."""
        if not self.check_rate_limit(interaction.user.id, "fun_commands"):
            embed = discord.Embed(
                title="⚠️ Rate Limit",
                description="You're using this command too quickly! Please wait a minute.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            meme_data = await self.get_random_meme()

            if meme_data:
                embed = discord.Embed(
                    title="🎭 Random Meme",
                    description=meme_data.get("title", "Unknown Title"),
                    color=discord.Color.purple()
                )
                embed.set_image(url=meme_data.get("url"))
                embed.add_field(name="Author", value=meme_data.get("author", "Unknown"), inline=True)
                embed.add_field(name="Subreddit", value=f"r/{meme_data.get('subreddit', 'Unknown')}", inline=True)
                embed.set_footer(text="Meme fetched from Reddit")

                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Failed to Fetch Meme",
                    description="Could not fetch a meme at this time. Please try again later.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Meme command error: {e}")
            await interaction.followup.send(
                "❌ An error occurred while fetching a meme.",
                ephemeral=True
            )

    @app_commands.command(name="quote", description="Get an inspirational quote")
    @app_commands.describe(category="Filter quotes by category (optional)")
    async def quote_command(self, interaction: discord.Interaction, category: Optional[str] = None):
        """Get an inspirational quote."""
        if not self.check_rate_limit(interaction.user.id, "fun_commands"):
            embed = discord.Embed(
                title="⚠️ Rate Limit",
                description="You're using this command too quickly! Please wait a minute.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            if category:
                quotes = [q for q in self.quotes if q.get("category", "").lower() == category.lower()]
            else:
                quotes = self.quotes

            if not quotes:
                embed = discord.Embed(
                    title="❌ No Quotes Found",
                    description=f"No quotes found in category: {category}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return

            quote = random.choice(quotes)

            embed = discord.Embed(
                title="💭 Inspirational Quote",
                description=f'"{quote["quote"]}"',
                color=discord.Color.blue()
            )
            embed.add_field(name="Author", value=quote["author"], inline=True)
            embed.add_field(name="Category", value=quote.get("category", "General"), inline=True)
            embed.set_footer(text=f"Quote #{quote['id']}")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Quote command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching a quote.",
                ephemeral=True
            )

    @app_commands.command(name="fact", description="Get a random interesting fact")
    @app_commands.describe(category="Filter facts by category (optional)")
    async def fact_command(self, interaction: discord.Interaction, category: Optional[str] = None):
        """Get a random interesting fact."""
        if not self.check_rate_limit(interaction.user.id, "fun_commands"):
            embed = discord.Embed(
                title="⚠️ Rate Limit",
                description="You're using this command too quickly! Please wait a minute.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            if category:
                facts = [f for f in self.facts if f.get("category", "").lower() == category.lower()]
            else:
                facts = self.facts

            if not facts:
                embed = discord.Embed(
                    title="❌ No Facts Found",
                    description=f"No facts found in category: {category}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return

            fact = random.choice(facts)

            embed = discord.Embed(
                title="🧠 Did You Know?",
                description=fact["fact"],
                color=discord.Color.green()
            )
            embed.add_field(name="Category", value=fact.get("category", "General"), inline=True)
            embed.set_footer(text=f"Fact #{fact['id']}")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Fact command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching a fact.",
                ephemeral=True
            )

    @app_commands.command(name="trivia", description="Start a trivia quiz")
    @app_commands.describe(
        category="Filter questions by category (optional)",
        difficulty="Question difficulty: Easy, Medium, Hard (optional)"
    )
    async def trivia_command(self,
                           interaction: discord.Interaction,
                           category: Optional[str] = None,
                           difficulty: Optional[str] = None):
        """Start a trivia quiz."""
        if not self.check_rate_limit(interaction.user.id, "games"):
            embed = discord.Embed(
                title="⚠️ Rate Limit",
                description="You're using game commands too quickly! Please wait a minute.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            questions = self.trivia.get("questions", [])

            if category:
                questions = [q for q in questions if q.get("category", "").lower() == category.lower()]

            if difficulty:
                questions = [q for q in questions if q.get("difficulty", "").lower() == difficulty.lower()]

            if not questions:
                embed = discord.Embed(
                    title="❌ No Questions Found",
                    description="No trivia questions match your criteria.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return

            question = random.choice(questions)

            # Store quiz state
            self.quiz_games[interaction.channel_id] = {
                "question": question,
                "asked_by": interaction.user.id,
                "timestamp": datetime.now(),
                "answered": False
            }

            embed = discord.Embed(
                title="🎯 Trivia Question",
                description=question["question"],
                color=discord.Color.gold()
            )

            # Add options as numbered buttons
            options_text = ""
            for i, option in enumerate(question["options"], 1):
                options_text += f"**{i}.** {option}\n"

            embed.add_field(name="Options", value=options_text, inline=False)
            embed.add_field(name="Category", value=question.get("category", "General"), inline=True)
            embed.add_field(name="Difficulty", value=question.get("difficulty", "Unknown"), inline=True)

            # Create buttons for answers
            view = discord.ui.View()
            for i in range(len(question["options"])):
                button = discord.ui.Button(
                    label=str(i + 1),
                    style=discord.ButtonStyle.primary,
                    custom_id=f"trivia_answer_{i}"
                )
                button.callback = lambda i=i, interaction=interaction: self.trivia_button_callback(i, interaction)
                view.add_item(button)

            await interaction.response.send_message(embed=embed, view=view)

            # Set timeout for question
            asyncio.create_task(self.trivia_timeout(interaction.channel_id))

        except Exception as e:
            logger.error(f"Trivia command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while starting trivia.",
                ephemeral=True
            )

    async def trivia_button_callback(self, answer_index: int, interaction: discord.Interaction):
        """Handle trivia answer button clicks."""
        try:
            game_state = self.quiz_games.get(interaction.channel_id)
            if not game_state or game_state["answered"]:
                return

            question = game_state["question"]
            correct_answer = question["correct_answer"]
            is_correct = (answer_index == correct_answer)

            game_state["answered"] = True

            embed = discord.Embed(
                title="✅ Answer Submitted",
                description=f"Your answer: **{question['options'][answer_index]}**",
                color=discord.Color.green() if is_correct else discord.Color.red()
            )

            if is_correct:
                embed.description += "\n\n🎉 **Correct!** Well done!"
            else:
                embed.description += f"\n\n❌ **Incorrect!** The correct answer was: **{question['options'][correct_answer]}**"

            embed.add_field(name="Category", value=question.get("category", "General"), inline=True)
            embed.add_field(name="Difficulty", value=question.get("difficulty", "Unknown"), inline=True)

            # Disable all buttons
            for child in interaction.message.components:
                for item in child.children:
                    item.disabled = True

            await interaction.response.edit_message(embed=embed, view=interaction.message.view)

            # Clean up
            if interaction.channel_id in self.quiz_games:
                del self.quiz_games[interaction.channel_id]

        except Exception as e:
            logger.error(f"Trivia button callback error: {e}")

    async def trivia_timeout(self, channel_id: int, timeout: int = 30):
        """Handle trivia question timeout."""
        await asyncio.sleep(timeout)

        if channel_id in self.quiz_games:
            game_state = self.quiz_games[channel_id]
            if not game_state["answered"]:
                question = game_state["question"]
                correct_answer = question["correct_answer"]

                embed = discord.Embed(
                    title="⏰ Time's Up!",
                    description=f"The correct answer was: **{question['options'][correct_answer]}**",
                    color=discord.Color.orange()
                )

                # Try to edit the original message
                try:
                    channel = self.bot.get_channel(channel_id)
                    if channel and channel.last_message:
                        for child in channel.last_message.components:
                            for item in child.children:
                                item.disabled = True
                        await channel.last_message.edit(embed=embed, view=channel.last_message.view)
                except:
                    pass

                del self.quiz_games[channel_id]

    # === GAME COMMANDS ===

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="Your question for the 8-ball")
    async def eightball_command(self, interaction: discord.Interaction, question: str):
        """Ask the magic 8-ball a question."""
        if not self.check_rate_limit(interaction.user.id, "games"):
            embed = discord.Embed(
                title="⚠️ Rate Limit",
                description="You're using game commands too quickly! Please wait a minute.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            response = random.choice(self.eightball_responses)

            embed = discord.Embed(
                title="🎱 Magic 8-Ball",
                description=f"**Question:** {question}\n\n**Answer:** {response}",
                color=discord.Color.purple()
            )
            embed.set_thumbnail(url="https://i.imgur.com/3Z6j6zD.png")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"8-ball command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while consulting the 8-ball.",
                ephemeral=True
            )

    @app_commands.command(name="rps", description="Play Rock Paper Scissors")
    @app_commands.describe(choice="Your choice: rock, paper, or scissors")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Rock", value="rock"),
        app_commands.Choice(name="Paper", value="paper"),
        app_commands.Choice(name="Scissors", value="scissors")
    ])
    async def rps_command(self, interaction: discord.Interaction, choice: str):
        """Play Rock Paper Scissors against the bot."""
        if not self.check_rate_limit(interaction.user.id, "games"):
            embed = discord.Embed(
                title="⚠️ Rate Limit",
                description="You're using game commands too quickly! Please wait a minute.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            bot_choice = random.choice(self.rps_choices)

            # Determine winner
            if choice == bot_choice:
                result = "It's a tie!"
                color = discord.Color.yellow()
            elif (
                (choice == "rock" and bot_choice == "scissors") or
                (choice == "paper" and bot_choice == "rock") or
                (choice == "scissors" and bot_choice == "paper")
            ):
                result = "You win!"
                color = discord.Color.green()
            else:
                result = "Bot wins!"
                color = discord.Color.red()

            embed = discord.Embed(
                title="🎮 Rock Paper Scissors",
                description=f"**You chose:** {self.rps_emojis[choice]} {choice.title()}\n"
                           f"**Bot chose:** {self.rps_emojis[bot_choice]} {bot_choice.title()}\n\n"
                           f"**Result:** {result}",
                color=color
            )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"RPS command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while playing Rock Paper Scissors.",
                ephemeral=True
            )

    @app_commands.command(name="hangman", description="Start a hangman game")
    @app_commands.describe(word="The word to guess (optional, random if not provided)")
    async def hangman_command(self, interaction: discord.Interaction, word: Optional[str] = None):
        """Start a hangman game."""
        if not self.check_rate_limit(interaction.user.id, "games"):
            embed = discord.Embed(
                title="⚠️ Rate Limit",
                description="You're using game commands too quickly! Please wait a minute.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            # Use random word if none provided
            if not word:
                words = ["python", "discord", "programming", "computer", "algorithm", "database", "interface", "network", "security", "development"]
                word = random.choice(words)

            word = word.upper()
            guessed_letters = set()
            wrong_guesses = 0
            max_wrong = 6

            game_state = {
                "word": word,
                "guessed_letters": guessed_letters,
                "wrong_guesses": wrong_guesses,
                "max_wrong": max_wrong,
                "started_by": interaction.user.id,
                "channel_id": interaction.channel_id
            }

            self.hangman_games[interaction.guild.id] = game_state

            embed = self._create_hangman_embed(game_state)

            # Create letter buttons
            view = discord.ui.View()
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                button = discord.ui.Button(
                    label=letter,
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"hangman_letter_{letter}"
                )
                button.callback = lambda l=letter, interaction=interaction: self.hangman_letter_callback(l, interaction)
                view.add_item(button)

            await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Hangman command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while starting hangman.",
                ephemeral=True
            )

    def _create_hangman_embed(self, game_state: dict) -> discord.Embed:
        """Create hangman game embed."""
        word = game_state["word"]
        guessed_letters = game_state["guessed_letters"]
        wrong_guesses = game_state["wrong_guesses"]

        # Create word display
        display_word = ""
        for letter in word:
            if letter in guessed_letters:
                display_word += letter + " "
            else:
                display_word += "_ "

        # Hangman stages
        stages = [
            "```\n  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========```"
        ]

        embed = discord.Embed(
            title="🎯 Hangman Game",
            description=f"**Word:** {display_word.strip()}",
            color=discord.Color.blue()
        )

        embed.add_field(name="Hangman", value=stages[wrong_guesses], inline=False)
        embed.add_field(name="Wrong Guesses", value=f"{wrong_guesses}/{game_state['max_wrong']}", inline=True)
        embed.add_field(name="Guessed Letters", value=" ".join(sorted(guessed_letters)) if guessed_letters else "None", inline=True)

        return embed

    async def hangman_letter_callback(self, letter: str, interaction: discord.Interaction):
        """Handle hangman letter button clicks."""
        try:
            guild_id = interaction.guild.id
            if guild_id not in self.hangman_games:
                return

            game_state = self.hangman_games[guild_id]
            letter = letter.upper()

            if letter in game_state["guessed_letters"]:
                await interaction.response.send_message(
                    "You already guessed that letter!",
                    ephemeral=True
                )
                return

            game_state["guessed_letters"].add(letter)

            if letter in game_state["word"]:
                # Correct guess
                # Check if word is complete
                word_complete = all(l in game_state["guessed_letters"] for l in game_state["word"])

                if word_complete:
                    embed = discord.Embed(
                        title="🎉 You Won!",
                        description=f"Congratulations! You guessed the word: **{game_state['word']}**",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Wrong Guesses", value=str(game_state["wrong_guesses"]), inline=True)

                    # Disable all buttons
                    for child in interaction.message.components:
                        for item in child.children:
                            item.disabled = True

                    await interaction.response.edit_message(embed=embed, view=interaction.message.view)
                    del self.hangman_games[guild_id]
                else:
                    embed = self._create_hangman_embed(game_state)
                    await interaction.response.edit_message(embed=embed)
            else:
                # Wrong guess
                game_state["wrong_guesses"] += 1

                if game_state["wrong_guesses"] >= game_state["max_wrong"]:
                    embed = discord.Embed(
                        title="💀 Game Over",
                        description=f"You lost! The word was: **{game_state['word']}**",
                        color=discord.Color.red()
                    )

                    # Disable all buttons
                    for child in interaction.message.components:
                        for item in child.children:
                            item.disabled = True

                    await interaction.response.edit_message(embed=embed, view=interaction.message.view)
                    del self.hangman_games[guild_id]
                else:
                    embed = self._create_hangman_embed(game_state)
                    await interaction.response.edit_message(embed=embed)

            # Disable the clicked button
            for child in interaction.message.components:
                for item in child.children:
                    if item.custom_id == f"hangman_letter_{letter}":
                        item.disabled = True
                        break

        except Exception as e:
            logger.error(f"Hangman button callback error: {e}")

    # === SOCIAL COMMANDS ===

    @app_commands.command(name="userinfo", description="Get information about a user")
    @app_commands.describe(user="The user to get info about (optional, defaults to you)")
    async def userinfo_command(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        """Get information about a user."""
        try:
            target_user = user or interaction.user
            member = interaction.guild.get_member(target_user.id) if interaction.guild else None

            embed = discord.Embed(
                title=f"👤 User Information",
                description=f"Information about {target_user.mention}",
                color=target_user.color or discord.Color.blue()
            )

            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.add_field(name="Username", value=target_user.name, inline=True)
            embed.add_field(name="Display Name", value=target_user.display_name, inline=True)
            embed.add_field(name="ID", value=target_user.id, inline=True)
            embed.add_field(name="Bot", value="Yes" if target_user.bot else "No", inline=True)
            embed.add_field(name="Created", value=target_user.created_at.strftime("%Y-%m-%d"), inline=True)

            if member:
                embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
                if member.nick:
                    embed.add_field(name="Nickname", value=member.nick, inline=True)

                roles = [role.mention for role in member.roles[1:]]  # Exclude @everyone
                if roles:
                    embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles[:10]), inline=False)
                    if len(roles) > 10:
                        embed.set_footer(text=f"+ {len(roles) - 10} more roles")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Userinfo command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching user information.",
                ephemeral=True
            )

    @app_commands.command(name="serverinfo", description="Get information about the server")
    async def serverinfo_command(self, interaction: discord.Interaction):
        """Get information about the server."""
        try:
            guild = interaction.guild

            embed = discord.Embed(
                title=f"🏢 Server Information",
                description=f"Information about {guild.name}",
                color=discord.Color.blue()
            )

            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)

            embed.add_field(name="Name", value=guild.name, inline=True)
            embed.add_field(name="ID", value=guild.id, inline=True)
            embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
            embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
            embed.add_field(name="Members", value=guild.member_count, inline=True)
            embed.add_field(name="Channels", value=len(guild.channels), inline=True)
            embed.add_field(name="Roles", value=len(guild.roles), inline=True)
            embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)

            if guild.premium_subscription_count:
                embed.add_field(name="Boost Level", value=str(guild.premium_tier), inline=True)
                embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Serverinfo command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching server information.",
                ephemeral=True
            )

    @app_commands.command(name="avatar", description="Get a user's avatar")
    @app_commands.describe(user="The user to get avatar from (optional, defaults to you)")
    async def avatar_command(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        """Get a user's avatar."""
        try:
            target_user = user or interaction.user

            embed = discord.Embed(
                title=f"🖼️ {target_user.name}'s Avatar",
                color=target_user.color or discord.Color.blue()
            )

            embed.set_image(url=target_user.display_avatar.url)
            embed.add_field(name="Download", value=f"[Click here]({target_user.display_avatar.url})", inline=False)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Avatar command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching the avatar.",
                ephemeral=True
            )

    @app_commands.command(name="emoji", description="Get information about an emoji")
    @app_commands.describe(emoji="The emoji to get info about")
    async def emoji_command(self, interaction: discord.Interaction, emoji: str):
        """Get information about an emoji."""
        try:
            # Parse emoji
            if emoji.startswith("<") and emoji.endswith(">"):
                # Custom emoji
                emoji_id = int(emoji.split(":")[2][:-1])
                emoji_name = emoji.split(":")[1]

                embed = discord.Embed(
                    title=f"😀 Emoji Information",
                    description=f"**Name:** {emoji_name}\n**ID:** {emoji_id}",
                    color=discord.Color.blue()
                )

                embed.set_thumbnail(url=f"https://cdn.discordapp.com/emojis/{emoji_id}.png?v=1")
                embed.add_field(name="Animated", value="Yes" if emoji.startswith("<a:") else "No", inline=True)
                embed.add_field(name="Usage", value=emoji, inline=False)

            else:
                # Unicode emoji
                embed = discord.Embed(
                    title="😀 Unicode Emoji",
                    description=f"**Emoji:** {emoji}\n**Unicode:** {' '.join(f'U+{ord(c):04X}' for c in emoji)}",
                    color=discord.Color.blue()
                )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Emoji command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching emoji information.",
                ephemeral=True
            )

    # === UTILITY COMMANDS ===

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping_command(self, interaction: discord.Interaction):
        """Check bot latency."""
        try:
            latency = round(self.bot.latency * 1000)  # Convert to milliseconds

            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Bot latency: **{latency}ms**",
                color=discord.Color.green() if latency < 100 else discord.Color.orange() if latency < 200 else discord.Color.red()
            )

            embed.add_field(name="Status", value="Excellent" if latency < 50 else "Good" if latency < 100 else "Fair" if latency < 200 else "Poor", inline=True)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Ping command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while checking latency.",
                ephemeral=True
            )

    @app_commands.command(name="uptime", description="Check bot uptime")
    async def uptime_command(self, interaction: discord.Interaction):
        """Check bot uptime."""
        try:
            # Get bot start time (you'll need to store this in the bot class)
            if hasattr(self.bot, 'start_time'):
                uptime = datetime.now() - self.bot.start_time
                days = uptime.days
                hours, remainder = divmod(uptime.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                embed = discord.Embed(
                    title="⏱️ Bot Uptime",
                    description=f"Bot has been online for:",
                    color=discord.Color.green()
                )

                embed.add_field(name="Days", value=str(days), inline=True)
                embed.add_field(name="Hours", value=str(hours), inline=True)
                embed.add_field(name="Minutes", value=str(minutes), inline=True)
                embed.add_field(name="Seconds", value=str(seconds), inline=True)

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    "❌ Start time not available.",
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Uptime command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while checking uptime.",
                ephemeral=True
            )

    @app_commands.command(name="invite", description="Get bot invite link")
    async def invite_command(self, interaction: discord.Interaction):
        """Get bot invite link."""
        try:
            # Create invite URL with permissions
            permissions = discord.Permissions(
                read_messages=True,
                send_messages=True,
                embed_links=True,
                attach_files=True,
                read_message_history=True,
                connect=True,
                speak=True,
                use_application_commands=True
            )

            invite_url = discord.utils.oauth_url(
                self.bot.user.id,
                permissions=permissions,
                scopes=("bot", "applications.commands")
            )

            embed = discord.Embed(
                title="🔗 Invite DuckBot",
                description=f"[Click here to invite DuckBot to your server]({invite_url})",
                color=discord.Color.blue()
            )

            embed.add_field(name="Required Permissions", value=(
                "• Read Messages\n"
                "• Send Messages\n"
                "• Embed Links\n"
                "• Attach Files\n"
                "• Read Message History\n"
                "• Connect to Voice\n"
                "• Speak in Voice\n"
                "• Use Slash Commands"
            ), inline=False)

            embed.set_footer(text="Thank you for inviting DuckBot! 🦆")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Invite command error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while generating invite link.",
                ephemeral=True
            )

    # === VIBEVOICE INTEGRATION ===

    @app_commands.command(name="tell_joke", description="Have VibeVoice tell you a joke")
    async def tell_joke_command(self, interaction: discord.Interaction):
        """Have VibeVoice tell you a joke."""
        if not self.check_rate_limit(interaction.user.id, "voice_entertainment"):
            embed = discord.Embed(
                title="⚠️ Rate Limit",
                description="You're using voice commands too quickly! Please wait 5 minutes.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not self.vibevoice.available:
            embed = discord.Embed(
                title="❌ VibeVoice Unavailable",
                description="VibeVoice TTS service is not available.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        await interaction.response.defer()

        try:
            # Get a random joke
            joke = random.choice(self.jokes)
            joke_text = f"{joke['setup']} {joke['punchline']}"

            # Generate voice
            result = await self.vibevoice.generate_speech(
                text=joke_text,
                speakers=["en-alice"],
                style="humorous"
            )

            if result.get("success") and result.get("audio_path"):
                audio_path = result["audio_path"]
                file_size = os.path.getsize(audio_path) / (1024 * 1024)  # MB

                if file_size < 8:  # Discord file limit
                    embed = discord.Embed(
                        title="🎙️ Joke by VibeVoice",
                        description=f"**{joke['setup']}**\n\n{joke['punchline']}",
                        color=discord.Color.green()
                    )

                    file = discord.File(audio_path, filename=f"joke_{interaction.id}.wav")
                    await interaction.followup.send(embed=embed, file=file)

                    # Clean up
                    asyncio.create_task(self._cleanup_file(audio_path))
                else:
                    embed = discord.Embed(
                        title="❌ File Too Large",
                        description="The generated audio file is too large to upload.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Generation Failed",
                    description="Failed to generate voice for the joke.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Tell joke command error: {e}")
            await interaction.followup.send(
                "❌ An error occurred while generating the joke.",
                ephemeral=True
            )

    async def _cleanup_file(self, file_path: str, delay: int = 300):
        """Clean up generated audio file after delay."""
        try:
            await asyncio.sleep(delay)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}")

# Setup function
async def setup_entertainment_commands(bot: commands.Bot, cost_tracker: Optional[CostTracker] = None):
    """Add entertainment commands to the bot."""
    try:
        cog = EntertainmentCommands(bot, cost_tracker)
        await bot.add_cog(cog)
        logger.info("Entertainment commands loaded successfully")
        return cog
    except Exception as e:
        logger.error(f"Failed to load entertainment commands: {e}")
        return None

# Fix missing import
import sys