#!/usr/bin/env python3
"""
DuckBot Doctor - Port Checker
Quick port usage testing for batch file
"""

import socket

def check_ports():
    """Check port usage"""
    ports = [8787, 8188, 5678, 8889, 1234, 8080, 8502]
    port_names = ['WebUI', 'ComfyUI', 'n8n', 'Jupyter', 'LM Studio', 'Open-WebUI', 'Open Notebook']
    
    for port, name in zip(ports, port_names):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f'  [IN USE] Port {port} ({name})')
        else:
            print(f'  [AVAILABLE] Port {port} ({name})')
    
    return 0

if __name__ == "__main__":
    exit(check_ports())