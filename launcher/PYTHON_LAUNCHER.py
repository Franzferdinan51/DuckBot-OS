import subprocess
import sys
import os

def check_python():
    """Check if Python is installed and meets version requirements"""
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.strip()
            print(f"Python version: {version_line}")
            return True
        else:
            print("Python not found!")
            return False
    except Exception as e:
        print(f"Error checking Python: {e}")
        return False

def start_ecosystem():
    """Start the DuckBot ecosystem"""
    try:
        print("Starting DuckBot ecosystem...")
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Change to the script directory
        os.chdir(script_dir)
        
        # Run the ecosystem script
        result = subprocess.run([sys.executable, "start_ecosystem.py"], 
                              cwd=script_dir, 
                              capture_output=False,  # Don't capture output so user can see it
                              text=True)
        
        if result.returncode == 0:
            print("DuckBot ecosystem started successfully.")
        else:
            print(f"DuckBot ecosystem exited with code {result.returncode}")
            
    except Exception as e:
        print(f"Error starting ecosystem: {e}")

def main():
    print("=" * 80)
    print("DUCKBOT v3.1.0+ PYTHON LAUNCHER")
    print("=" * 80)
    print()
    
    # Check Python installation
    if not check_python():
        print("Please install Python 3.8 or later.")
        input("Press Enter to exit...")
        return
    
    # Start the ecosystem
    start_ecosystem()
    
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()