#!/usr/bin/env python3
"""
Test script for DuckBot Entertainment Commands
This script tests the entertainment command functionality
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from duckbot.discord_commands.entertainment import EntertainmentCommands
from duckbot.core.cost_management import CostTracker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class MockBot:
    """Mock bot for testing."""
    def __init__(self):
        self.user = None
        self.start_time = None

class MockInteraction:
    """Mock interaction for testing."""
    def __init__(self):
        self.user = MockUser()
        self.channel = MockChannel()
        self.guild = MockGuild()

class MockUser:
    """Mock user for testing."""
    def __init__(self):
        self.id = 12345
        self.name = "TestUser"
        self.display_name = "Test User"
        self.mention = "@TestUser"

class MockChannel:
    """Mock channel for testing."""
    def __init__(self):
        self.id = 67890

class MockGuild:
    """Mock guild for testing."""
    def __init__(self):
        self.id = 11111

async def test_data_loading():
    """Test data loading functionality."""
    logger.info("Testing data loading...")

    bot = MockBot()
    cost_tracker = None

    try:
        entertainment = EntertainmentCommands(bot, cost_tracker)

        # Check if data loaded correctly
        logger.info(f"Jokes loaded: {len(entertainment.jokes)}")
        logger.info(f"Quotes loaded: {len(entertainment.quotes)}")
        logger.info(f"Facts loaded: {len(entertainment.facts)}")
        logger.info(f"Trivia questions loaded: {len(entertainment.trivia.get('questions', []))}")

        # Test 8-ball responses
        logger.info(f"8-ball responses: {len(entertainment.eightball_responses)}")

        # Test RPS choices
        logger.info(f"RPS choices: {entertainment.rps_choices}")

        logger.info("✅ Data loading test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Data loading test failed: {e}")
        return False

async def test_rate_limiting():
    """Test rate limiting functionality."""
    logger.info("Testing rate limiting...")

    bot = MockBot()
    cost_tracker = None

    try:
        entertainment = EntertainmentCommands(bot, cost_tracker)
        user_id = 12345

        # Test rate limiting
        for i in range(15):  # Should hit the limit of 10
            allowed = entertainment.check_rate_limit(user_id, "fun_commands")
            if not allowed:
                logger.info(f"Rate limit kicked in after {i+1} requests")
                break

        logger.info("✅ Rate limiting test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Rate limiting test failed: {e}")
        return False

async def test_meme_fetching():
    """Test meme fetching functionality."""
    logger.info("Testing meme fetching...")

    bot = MockBot()
    cost_tracker = None

    try:
        entertainment = EntertainmentCommands(bot, cost_tracker)

        # Test meme fetching
        meme_data = await entertainment.get_random_meme()
        if meme_data:
            logger.info(f"Meme fetched: {meme_data.get('title', 'Unknown')}")
            logger.info("✅ Meme fetching test completed successfully!")
        else:
            logger.warning("⚠️ Meme fetching returned no data (this might be expected)")

        return True

    except Exception as e:
        logger.error(f"❌ Meme fetching test failed: {e}")
        return False

async def test_hangman_game():
    """Test hangman game functionality."""
    logger.info("Testing hangman game...")

    bot = MockBot()
    cost_tracker = None

    try:
        entertainment = EntertainmentCommands(bot, cost_tracker)

        # Test hangman embed creation
        game_state = {
            "word": "PYTHON",
            "guessed_letters": set(),
            "wrong_guesses": 0,
            "max_wrong": 6,
            "started_by": 12345,
            "channel_id": 67890
        }

        embed = entertainment._create_hangman_embed(game_state)
        logger.info(f"Hangman embed created for word: {game_state['word']}")

        # Test with some guessed letters
        game_state["guessed_letters"] = {"P", "Y", "T"}
        game_state["wrong_guesses"] = 2

        embed = entertainment._create_hangman_embed(game_state)
        logger.info("Hangman embed updated with guesses")

        logger.info("✅ Hangman game test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Hangman game test failed: {e}")
        return False

async def main():
    """Main test function."""
    logger.info("Starting DuckBot Entertainment Commands Test...")

    tests = [
        test_data_loading,
        test_rate_limiting,
        test_meme_fetching,
        test_hangman_game
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if await test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Test {test.__name__} crashed: {e}")
            failed += 1

    logger.info(f"\n=== Test Results ===")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")

    if failed == 0:
        logger.info("🎉 All tests passed!")
        return True
    else:
        logger.error("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)