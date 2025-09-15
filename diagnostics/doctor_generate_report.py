#!/usr/bin/env python3
"""
DuckBot Doctor - Health Report Generator
Generate comprehensive system health report
"""

import os
import sys
import platform
import psutil
import requests
from datetime import datetime

def generate_health_report(report_file):
    """Generate comprehensive health report"""
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write(f'DuckBot v3.1.0 System Health Report\n')
            f.write(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write('=' * 50 + '\n\n')
            
            # System Information
            f.write('System Information:\n')
            f.write(f'OS: {platform.system()} {platform.release()}\n')
            f.write(f'Python: {platform.python_version()}\n')
            f.write(f'CPU: {psutil.cpu_count()} cores ({psutil.cpu_percent():.1f}% usage)\n')
            f.write(f'RAM: {psutil.virtual_memory().percent:.1f}% used\n')
            f.write(f'Disk: {psutil.disk_usage(".").percent:.1f}% used\n')
            f.write(f'Working Directory: {os.getcwd()}\n\n')
            
            # Service Status
            f.write('Service Status:\n')
            services = [
                ('WebUI', 'http://localhost:8787'), 
                ('n8n', 'http://localhost:5678'), 
                ('Jupyter', 'http://localhost:8889'), 
                ('LM Studio', 'http://localhost:1234/v1/models'),
                ('Open-WebUI', 'http://localhost:8080')
            ]
            
            for name, url in services:
                try:
                    r = requests.get(url, timeout=2)
                    status = 'Running' if r.status_code == 200 else f'Status {r.status_code}'
                except:
                    status = 'Not accessible'
                f.write(f'{name}: {status}\n')
            f.write('\n')
            
            # Import Status
            f.write('Critical Dependencies:\n')
            modules = ['discord', 'aiohttp', 'requests', 'seaborn', 'matplotlib', 'pandas', 'numpy', 'jupyter', 'fastapi', 'torch', 'psutil']
            for module in modules:
                try:
                    __import__(module)
                    f.write(f'{module}: [OK] Available\n')
                except ImportError:
                    f.write(f'{module}: [MISSING] Not Available\n')
            
            f.write('\n--- End of Report ---\n')
        
        print(f'SUCCESS: Health report generated: {report_file}')
        return True
        
    except Exception as e:
        print(f'ERROR: Failed to generate report: {e}')
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        report_file = sys.argv[1]
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        report_file = f'DuckBot_Health_Report_{timestamp}.txt'
    
    success = generate_health_report(report_file)
    exit(0 if success else 1)