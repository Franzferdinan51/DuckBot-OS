#!/usr/bin/env python3
"""
DuckBot Doctor - Import Tester
Comprehensive import testing for batch file
"""

def test_all_imports():
    """Test all imports and show success rate"""
    test_modules = [
        'discord', 'aiohttp', 'requests', 'seaborn', 'matplotlib', 
        'pandas', 'numpy', 'jupyter', 'fastapi', 'torch', 'psutil',
        'cv2', 'PIL', 'websockets', 'yaml', 'neo4j'
    ]
    
    success = 0
    total = len(test_modules)
    
    for module in test_modules:
        try:
            __import__(module)
            success += 1
            print(f'  [OK] {module}')
        except ImportError:
            print(f'  [MISSING] {module}')
    
    print(f'SUMMARY: Import Success Rate: {success}/{total} ({(success/total*100):.1f}%)')
    if success == total:
        print('SUCCESS: All modules imported successfully!')
    else:
        print('WARNING: Some modules missing - ecosystem may have limited functionality')
    
    return 0

if __name__ == "__main__":
    exit(test_all_imports())