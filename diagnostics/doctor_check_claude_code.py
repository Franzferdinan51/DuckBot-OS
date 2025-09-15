#!/usr/bin/env python3
"""
DuckBot Doctor - Claude Code Integration Checker
Check Claude Code Router and native Claude Code availability
"""

import subprocess
import requests
import socket
from typing import Dict, Any

def check_claude_code_router() -> Dict[str, Any]:
    """Check Claude Code Router installation and availability"""
    status = {
        'installed': False,
        'version': None,
        'npm_installed': False,
        'server_running': False,
        'server_port': 8765
    }
    
    # Check if ccr command is available
    try:
        result = subprocess.run(['ccr', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            status['installed'] = True
            status['version'] = result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    
    # Check if installed via npm
    try:
        result = subprocess.run(['npm', 'list', '-g', '@musistudio/claude-code-router'], 
                              capture_output=True, text=True, timeout=5)
        if '@musistudio/claude-code-router' in result.stdout:
            status['npm_installed'] = True
    except:
        pass
    
    # Check if server is running
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', status['server_port']))
        status['server_running'] = (result == 0)
        sock.close()
    except:
        pass
    
    return status

def check_native_claude_code() -> Dict[str, Any]:
    """Check native Claude Code availability"""
    status = {
        'installed': False,
        'version': None,
        'accessible': False
    }
    
    try:
        result = subprocess.run(['claude-code', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            status['installed'] = True
            status['version'] = result.stdout.strip()
            status['accessible'] = True
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    
    return status

def check_openrouter_server() -> Dict[str, Any]:
    """Check if OpenRouter proxy server is running"""
    status = {
        'running': False,
        'port': 11434,
        'api_accessible': False
    }
    
    # Check port
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', status['port']))
        status['running'] = (result == 0)
        sock.close()
    except:
        pass
    
    # Check API endpoint
    if status['running']:
        try:
            response = requests.get(f"http://localhost:{status['port']}/v1/models", timeout=3)
            status['api_accessible'] = (response.status_code == 200)
        except:
            pass
    
    return status

def check_integration_health() -> Dict[str, Any]:
    """Check overall Claude Code integration health"""
    router_status = check_claude_code_router()
    native_status = check_native_claude_code()
    server_status = check_openrouter_server()
    
    # Determine overall status
    available = (
        router_status['installed'] or 
        native_status['installed']
    )
    
    functional = (
        (router_status['server_running'] and server_status['api_accessible']) or
        native_status['accessible']
    )
    
    return {
        'available': available,
        'functional': functional,
        'router': router_status,
        'native': native_status,
        'openrouter_server': server_status,
        'recommendations': get_recommendations(router_status, native_status, server_status)
    }

def get_recommendations(router_status, native_status, server_status) -> list:
    """Get recommendations for improving Claude Code integration"""
    recommendations = []
    
    if not router_status['installed'] and not native_status['installed']:
        recommendations.append("Install Claude Code Router: npm install -g @musistudio/claude-code-router")
        recommendations.append("Alternative: Install native Claude Code from Anthropic")
    
    if router_status['installed'] and not router_status['server_running']:
        recommendations.append("Start Claude Code Router server: ccr server --port 8765")
    
    if router_status['installed'] and not server_status['running']:
        recommendations.append("Start OpenRouter proxy: ccr server --provider openrouter --port 11434")
    
    if not server_status['api_accessible'] and server_status['running']:
        recommendations.append("Check OpenRouter API key configuration")
        recommendations.append("Verify network connectivity to OpenRouter services")
    
    return recommendations

def main():
    """Main diagnostic function"""
    print("Claude Code Integration Status:")
    print("=" * 40)
    
    health = check_integration_health()
    
    # Overall status
    if health['functional']:
        print("  [FUNCTIONAL] Claude Code integration is working")
    elif health['available']:
        print("  [AVAILABLE] Claude Code installed but not fully functional")
    else:
        print("  [NOT AVAILABLE] Claude Code integration not found")
    
    print()
    
    # Router details
    router = health['router']
    print("Claude Code Router:")
    if router['installed']:
        print(f"  [INSTALLED] Version: {router.get('version', 'Unknown')}")
        if router['server_running']:
            print(f"  [RUNNING] Server active on port {router['server_port']}")
        else:
            print(f"  [STOPPED] Server not running on port {router['server_port']}")
    else:
        print("  [NOT INSTALLED] Router not found")
    
    print()
    
    # Native details
    native = health['native']
    print("Native Claude Code:")
    if native['installed']:
        print(f"  [INSTALLED] Version: {native.get('version', 'Unknown')}")
        if native['accessible']:
            print("  [ACCESSIBLE] Command line interface working")
        else:
            print("  [ERROR] Command line interface not working")
    else:
        print("  [NOT INSTALLED] Native Claude Code not found")
    
    print()
    
    # OpenRouter server
    server = health['openrouter_server']
    print("OpenRouter Proxy Server:")
    if server['running']:
        print(f"  [RUNNING] Active on port {server['port']}")
        if server['api_accessible']:
            print("  [API OK] REST API responding")
        else:
            print("  [API ERROR] REST API not responding")
    else:
        print(f"  [STOPPED] Not running on port {server['port']}")
    
    print()
    
    # Recommendations
    if health['recommendations']:
        print("Recommendations:")
        for rec in health['recommendations']:
            print(f"  • {rec}")
    else:
        print("No recommendations - integration looks good!")
    
    # Return appropriate exit code
    return 0 if health['functional'] else 1

if __name__ == "__main__":
    exit(main())