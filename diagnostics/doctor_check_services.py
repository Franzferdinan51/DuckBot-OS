#!/usr/bin/env python3
"""
DuckBot Doctor - Service Checker
Quick service availability testing for batch file
"""

import requests

def check_services():
    """Check service availability"""
    services = [
        ('WebUI', 'http://localhost:8787'), 
        ('n8n', 'http://localhost:5678'),
        ('Jupyter', 'http://localhost:8889'),
        ('LM Studio', 'http://localhost:1234/v1/models'),
        ('Open-WebUI', 'http://localhost:8080')
    ]
    
    running_count = 0
    
    for name, url in services:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print(f'  [RUNNING] {name}')
                running_count += 1
            else:
                print(f'  [STATUS {r.status_code}] {name}')
        except:
            print(f'  [NOT ACCESSIBLE] {name}')
    
    print(f'SUMMARY: Services running: {running_count}/{len(services)}')
    return 0

if __name__ == "__main__":
    exit(check_services())