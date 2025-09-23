@echo off 
echo Testing direct transformers import... 
echo. 
python -c "from transformers import Qwen2AudioForConditionalGeneration, Qwen2AudioProcessor; print('✓ Qwen2Audio classes imported successfully')" 
echo. 
python -c "from transformers import Qwen2AudioForConditionalGeneration, Qwen2AudioProcessor; model = Qwen2AudioForConditionalGeneration.from_pretrained('./models/Qwen3-Omni-30B-A3B-Instruct'); print('✓ Model loaded successfully'); processor = Qwen2AudioProcessor.from_pretrained('./models/Qwen3-Omni-30B-A3B-Instruct'); print('✓ Processor loaded successfully')" 
echo. 
echo Test completed successfully! 
pause 
