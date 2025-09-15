import subprocess
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Path to the fixed batch file
batch_file = os.path.join(script_dir, "QWENMAX-START_ENHANCED_DUCKBOT_FIXED.bat")

# Run the batch file
try:
    result = subprocess.run([batch_file], cwd=script_dir, capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
except Exception as e:
    print(f"Error running batch file: {e}")