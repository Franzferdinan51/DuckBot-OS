@echo off 
cd /d "C:\Users\Ryan\Desktop\DuckBot-Consolidated-v4.2\" 
echo Starting Qwen3-Omni AI Brain... 
python -c "import asyncio; import sys; import os; sys.path.append(os.getcwd()); from duckbot.core.qwen3_omni_integration import qwen3_omni_integration; from duckbot.integrations.qwen3_voice_assistant import qwen3_voice_assistant; asyncio.run(qwen3_omni_integration.load_model())" 
pause 
