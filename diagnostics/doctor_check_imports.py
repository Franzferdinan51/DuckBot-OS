#!/usr/bin/env python3
"""
DuckBot Doctor - Import Checker
Quick and reliable import testing for batch file
"""

def check_critical_imports():
    """Test critical Python imports and report status"""
    critical_imports = [
        ('discord.py', 'discord'),
        ('aiohttp', 'aiohttp'), 
        ('requests', 'requests'),
        ('seaborn', 'seaborn'),
        ('matplotlib', 'matplotlib'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('jupyter', 'jupyter'),
        ('fastapi', 'fastapi'),
        ('torch', 'torch'),
        ('psutil', 'psutil')
    ]
    
    failed = []
    
    for name, module in critical_imports:
        try:
            __import__(module)
            print(f'  [OK] {name}')
        except ImportError:
            print(f'  [MISSING] {name}')
            failed.append(name)
    
    if failed:
        print(f'WARNING: {len(failed)} critical dependencies missing!')
        print('TIP: Run Doctor > Fix Dependencies to install')
        return 1
    else:
        print('SUCCESS: All critical imports successful')
        return 0

if __name__ == "__main__":
    exit(check_critical_imports())