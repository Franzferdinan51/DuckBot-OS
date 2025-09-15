#!/usr/bin/env python3
"""WebUI service detection test for startup script"""

try:
    from duckbot.service_detector import ServiceDetector
    detector = ServiceDetector()
    
    # Check if WebUI is already running
    webui_status = detector.detect_service_status('webui')
    if webui_status['status'] in ['running_healthy', 'running_unhealthy']:
        print(f'[DETECTED] WebUI already running on port 8787')
        print(f'[ACTION] Will attempt to connect to existing instance')
        print(f'[URL] http://localhost:8787')
    else:
        print('[CLEAR] Port 8787 available for WebUI')
    
    # Check other services for reference
    lm_status = detector.detect_service_status('lm_studio')
    if lm_status['status'] == 'running_healthy':
        print('[INFO] LM Studio detected - WebUI can connect to it')
except Exception as e:
    print(f'[WARN] Service detection unavailable: {e}')
    print('[INFO] Continuing with WebUI startup...')