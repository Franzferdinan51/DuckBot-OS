#!/usr/bin/env python3
"""Simple service detection test for startup script"""

try:
    from duckbot.service_detector import ServiceDetector
    detector = ServiceDetector()
    recommendations = detector.get_startup_recommendations()
    print('[SCAN] Service detection results:')
    for service_name, rec in recommendations.items():
        if not rec['can_start']:
            print(f'  OK {service_name}: {rec["reason"]}')
        else:
            print(f'  Available {service_name}: Available to start')
    print('[SUCCESS] Service detection completed')
except Exception as e:
    print(f'[WARN] Service detection failed: {e}')
    print('[INFO] Continuing with basic startup...')