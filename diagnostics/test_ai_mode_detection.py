#!/usr/bin/env python3
"""AI mode service detection test for startup script"""

try:
    from duckbot.service_detector import ServiceDetector
    detector = ServiceDetector()
    recommendations = detector.get_startup_recommendations()
    
    print('[AI-SCAN] Service detection for AI mode:')
    for service in ['lm_studio', 'comfyui', 'jupyter', 'n8n']:
        rec = recommendations.get(service, {})
        if not rec.get('can_start', True):
            print(f'  OK {service}: {rec.get("reason", "Running")}')
        else:
            print(f'  Available {service}: Will be started by AI manager')
except Exception as e:
    print(f'[WARN] Service detection failed: {e}')
    print('[INFO] AI manager will attempt basic startup...')