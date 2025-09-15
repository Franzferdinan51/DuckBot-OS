#!/usr/bin/env python3
"""
Integrate VibeVoice commands into existing DuckBot Discord bot
Adds the VibeVoice cog to the bot without modifying core files
"""
import os
import sys
from pathlib import Path

def integrate_vibevoice_into_bot():
    """Add VibeVoice integration code to the main Discord bot file."""
    
    bot_file = Path("DuckBot-v2.3.0-Trading-Video-Enhanced.py")
    if not bot_file.exists():
        print("[FAIL] Bot file not found: DuckBot-v2.3.0-Trading-Video-Enhanced.py")
        return False
    
    print("[EMOJI] Reading existing bot file...")
    
    with open(bot_file, 'r', encoding='utf-8') as f:
        bot_content = f.read()
    
    # Check if VibeVoice is already integrated
    if "vibevoice_commands" in bot_content.lower():
        print("[OK] VibeVoice already integrated into bot")
        return True
    
    # Find insertion points
    import_section_end = bot_content.find("# --- 2. CONFIGURATION ---")
    if import_section_end == -1:
        import_section_end = bot_content.find("# Load environment variables")
        
    bot_ready_section = bot_content.find("@bot.event\nasync def on_ready():")
    
    if import_section_end == -1 or bot_ready_section == -1:
        print("[FAIL] Could not find insertion points in bot file")
        return False
    
    print("[LIST] Adding VibeVoice imports...")
    
    # Add imports
    vibevoice_imports = '''
# VibeVoice TTS integration
try:
    from duckbot.vibevoice_commands import setup_vibevoice_commands
    VIBEVOICE_AVAILABLE = True
except ImportError:
    print("[WARN] VibeVoice not available - install with: python setup_vibevoice.py")
    VIBEVOICE_AVAILABLE = False
'''
    
    # Insert imports
    bot_content = (bot_content[:import_section_end] + 
                  vibevoice_imports + 
                  bot_content[import_section_end:])
    
    print("[LIST] Adding VibeVoice initialization...")
    
    # Find the on_ready function and add VibeVoice setup
    on_ready_start = bot_content.find("@bot.event\nasync def on_ready():")
    on_ready_end = bot_content.find("\n@", on_ready_start + 1)
    if on_ready_end == -1:
        on_ready_end = bot_content.find("\n# ", on_ready_start + 1)
    
    if on_ready_end != -1:
        # Find the end of the on_ready function
        lines = bot_content[on_ready_start:on_ready_end].split('\n')
        
        # Add VibeVoice setup before the last print statement
        vibevoice_setup = '''
    # Initialize VibeVoice TTS
    if VIBEVOICE_AVAILABLE:
        try:
            await setup_vibevoice_commands(bot, cost_tracker)
            print("[EMOJI] VibeVoice TTS commands loaded")
        except Exception as e:
            print(f"[WARN] VibeVoice initialization failed: {e}")'''
        
        # Insert VibeVoice setup
        insert_pos = on_ready_end - 50  # Before final print statements
        bot_content = (bot_content[:insert_pos] + 
                      vibevoice_setup + 
                      bot_content[insert_pos:])
    
    print("[SAVE] Writing updated bot file...")
    
    # Create backup
    backup_file = bot_file.with_suffix('.py.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(open(bot_file, 'r', encoding='utf-8').read())
    
    print(f"[DIR] Backup created: {backup_file}")
    
    # Write updated content
    with open(bot_file, 'w', encoding='utf-8') as f:
        f.write(bot_content)
    
    print("[OK] VibeVoice integration added to bot successfully!")
    return True

def create_integration_patch():
    """Create a patch file for manual integration."""
    
    patch_content = '''# VibeVoice Integration Patch for DuckBot
# Add these lines to your DuckBot-v2.3.0-Trading-Video-Enhanced.py

# 1. Add to imports section (after other duckbot imports):
try:
    from duckbot.vibevoice_commands import setup_vibevoice_commands
    VIBEVOICE_AVAILABLE = True
except ImportError:
    print("[WARN] VibeVoice not available - install with: python setup_vibevoice.py")
    VIBEVOICE_AVAILABLE = False

# 2. Add to on_ready() function (before final print statements):
    # Initialize VibeVoice TTS
    if VIBEVOICE_AVAILABLE:
        try:
            await setup_vibevoice_commands(bot, cost_tracker)
            print("[EMOJI] VibeVoice TTS commands loaded")
        except Exception as e:
            print(f"[WARN] VibeVoice initialization failed: {e}")

# That's it! The VibeVoice commands will be available in Discord:
# /vibevoice - Generate multi-speaker voice content
# /voice_presets - Show available voices
# /voice_status - Check server status  
# /voice_help - Usage guide
'''
    
    patch_file = Path("vibevoice_integration_patch.txt")
    with open(patch_file, 'w') as f:
        f.write(patch_content)
    
    print(f"[DOC] Integration patch created: {patch_file}")
    return True

def main():
    """Main integration function."""
    print("[EMOJI] VibeVoice Integration for DuckBot")
    print("="*50)
    
    try:
        # Try automatic integration first
        if integrate_vibevoice_into_bot():
            print("\n[OK] Automatic integration successful!")
            print("\n[LIST] Next steps:")
            print("1. Run: python setup_vibevoice.py")
            print("2. Start VibeVoice server: START_VIBEVOICE_SERVER.bat")
            print("3. Start your DuckBot")
            print("4. Use /vibevoice commands in Discord")
        else:
            print("\n[WARN] Automatic integration failed, creating manual patch...")
            create_integration_patch()
            print("\n[LIST] Manual integration required:")
            print("1. Check vibevoice_integration_patch.txt")
            print("2. Manually add the code to your bot file")
    
    except Exception as e:
        print(f"\n[FAIL] Integration failed: {e}")
        print("Creating manual patch as fallback...")
        create_integration_patch()

if __name__ == "__main__":
    main()