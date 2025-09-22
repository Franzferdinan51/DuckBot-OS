# DuckBot Entertainment Commands

A comprehensive entertainment system for Discord with fun commands, games, social features, and utilities, fully integrated with VibeVoice TTS capabilities.

## Features

### 🎮 Fun Commands
- **/joke** - Get a random joke (with category filtering)
- **/meme** - Fetch a random meme from Reddit
- **/quote** - Get an inspirational quote (with category filtering)
- **/fact** - Learn interesting facts (with category filtering)
- **/trivia** - Start an interactive trivia quiz

### 🎯 Games
- **/8ball** - Ask the magic 8-ball a question
- **/rps** - Play Rock Paper Scissors against the bot
- **/hangman** - Classic hangman game with visual display
- **/quiz** - Interactive trivia with multiple choice

### 👥 Social Commands
- **/userinfo** - Get detailed information about a user
- **/serverinfo** - Get server information and statistics
- **/avatar** - Display user avatars
- **/emoji** - Get information about custom and unicode emojis

### 🛠️ Utility Commands
- **/ping** - Check bot latency
- **/uptime** - Check bot uptime
- **/invite** - Get bot invite link

### 🎙️ VibeVoice Integration
- **/tell_joke** - Have VibeVoice tell you a joke with natural speech

## Setup

### Requirements
- Discord.py 2.0+
- aiohttp for API requests
- Optional: VibeVoice TTS for voice features

### Installation

1. Ensure the entertainment commands are in your bot's cog directory:
   ```
   duckbot/discord_commands/entertainment.py
   duckbot/discord_commands/__init__.py
   ```

2. Add data files to your bot's data directory:
   ```
   duckbot/data/jokes.json
   duckbot/data/quotes.json
   duckbot/data/facts.json
   duckbot/data/trivia.json
   ```

3. Import and add the cog to your bot:
   ```python
   from duckbot.discord_commands.entertainment import setup_entertainment_commands

   # In your setup_hook
   await setup_entertainment_commands(bot, cost_tracker)
   ```

## Usage Examples

### Fun Commands
```
/joke category:Programming
/meme
/quote category:Inspiration
/fact category:Science
/trivia category:Geography difficulty:Easy
```

### Games
```
/8ball question:"Will it rain today?"
/rps choice:rock
/hangman word:python
```

### Social Commands
```
/userinfo @user
/serverinfo
/avatar @user
/emoji 😎
```

### Utilities
```
/ping
/uptime
/invite
```

### VibeVoice
```
/tell_joke
```

## Configuration

### Rate Limiting
The entertainment commands include built-in rate limiting:
- **Fun commands**: 10 requests per minute
- **Games**: 5 requests per minute
- **Voice entertainment**: 3 requests per 5 minutes

### Categories
Content is organized by categories:
- **Jokes**: Programming, General, Technology, Animals, Math, Food
- **Quotes**: Inspiration, Wisdom, Programming, Life, Leadership
- **Facts**: Science, Animals, History, Geography, Technology, Language
- **Trivia**: Geography, Science, Art, History, Programming

### Game Features
- **Hangman**: Visual hangman display with 6 wrong guesses allowed
- **Trivia**: Multiple choice questions with timeout
- **RPS**: Animated rock-paper-scissors with emojis
- **8-ball**: 20 different responses for variety

## Data Files

### Jokes (jokes.json)
```json
{
  "id": 1,
  "category": "Programming",
  "setup": "Why do programmers prefer dark mode?",
  "punchline": "Because light attracts bugs!",
  "rating": "G"
}
```

### Quotes (quotes.json)
```json
{
  "id": 1,
  "quote": "The only way to do great work is to love what you do.",
  "author": "Steve Jobs",
  "category": "Inspiration"
}
```

### Facts (facts.json)
```json
{
  "id": 1,
  "fact": "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat.",
  "category": "Science"
}
```

### Trivia (trivia.json)
```json
{
  "questions": [
    {
      "id": 1,
      "question": "What is the capital of France?",
      "options": ["London", "Berlin", "Paris", "Madrid"],
      "correct_answer": 2,
      "category": "Geography",
      "difficulty": "Easy"
    }
  ]
}
```

## Integration Features

### VibeVoice TTS
The entertainment system integrates with VibeVoice for:
- **/tell_joke** - Converts jokes to natural speech
- Automatic cleanup of generated audio files
- Rate limiting for voice commands

### Cost Tracking
Optional cost tracking integration for:
- API call monitoring
- Usage statistics
- Cost analysis

### Error Handling
Comprehensive error handling for:
- Failed API requests
- Invalid user input
- Missing permissions
- Rate limit exceeded

## Permissions

The bot requires these Discord permissions:
- `view_channel`
- `send_messages`
- `embed_links`
- `attach_files`
- `read_message_history`
- `connect` (for voice features)
- `speak` (for voice features)
- `use_application_commands`

## Testing

Run the included test suite:
```bash
python test_entertainment_commands.py
```

The test suite covers:
- Data loading verification
- Rate limiting functionality
- API request handling
- Game logic testing

## Customization

### Adding New Content
1. Add entries to the appropriate JSON files
2. Follow the existing format
3. Restart the bot to load new content

### Customizing Categories
- Modify category filters in individual commands
- Add new categories to data files
- Update help text as needed

### Rate Limiting
Adjust rate limits in the `EntertainmentCommands` class:
```python
self.rate_limits = {
    "fun_commands": {"calls": 10, "period": 60},
    "games": {"calls": 5, "period": 60},
    "voice_entertainment": {"calls": 3, "period": 300}
}
```

## Contributing

When adding new entertainment features:
1. Follow the existing command structure
2. Add proper error handling
3. Include rate limiting if appropriate
4. Update help documentation
5. Add tests for new functionality

## Troubleshooting

### Common Issues
- **Import errors**: Ensure all dependencies are installed
- **Permission errors**: Check bot permissions in server
- **Rate limiting**: Wait for the cooldown period
- **Missing data**: Verify JSON files are in correct location

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

*Entertainment Commands for DuckBot v4.2*
*Part of the DuckBot Enhanced Ecosystem*