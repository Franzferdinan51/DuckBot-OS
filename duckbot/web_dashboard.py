#!/usr/bin/env python3
"""
DuckBot Cost Dashboard WebUI
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime, timedelta
from .cost_tracker import CostTracker
from .cost_visualizer import CostVisualizer
import base64
from io import BytesIO

app = Flask(__name__)
cost_tracker = CostTracker()
cost_visualizer = CostVisualizer(cost_tracker)

@app.route('/')
def dashboard():
    """Redirect to cost dashboard"""
    return render_template('cost_dashboard.html')

@app.route('/cost')
def cost_dashboard():
    """Cost dashboard page"""
    return render_template('cost_dashboard.html')

@app.route('/api/cost_summary')
def api_cost_summary():
    """Get cost summary data"""
    days = request.args.get('days', 30, type=int)
    
    try:
        summary = cost_tracker.get_usage_summary(days)
        predictions = cost_tracker.get_cost_predictions()
        
        return jsonify({
            'success': True,
            'data': {
                'total_cost': summary.total_cost,
                'total_tokens': summary.total_tokens,
                'total_requests': summary.total_requests,
                'by_model': dict(summary.by_model),
                'by_provider': dict(summary.by_provider),
                'predictions': predictions,
                'period_days': days
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cost_chart')
def api_cost_chart():
    """Generate cost chart as base64 image"""
    days = request.args.get('days', 30, type=int)
    
    try:
        # Generate dashboard image
        dashboard_path = cost_visualizer.create_cost_dashboard(days)
        
        # Convert to base64
        with open(dashboard_path, 'rb') as f:
            img_data = f.read()
        
        img_b64 = base64.b64encode(img_data).decode('utf-8')
        
        # Cleanup
        if os.path.exists(dashboard_path):
            os.remove(dashboard_path)
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_b64}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/budget_status')
def api_budget_status():
    """Get budget status"""
    try:
        status = cost_tracker.check_budget_status()
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/set_budget', methods=['POST'])
def api_set_budget():
    """Set budget alert"""
    try:
        data = request.get_json()
        budget = data.get('budget')
        threshold = data.get('threshold', 80) / 100
        
        if not budget or budget <= 0:
            return jsonify({'success': False, 'error': 'Invalid budget amount'})
        
        cost_tracker.set_budget_alert(budget, threshold)
        return jsonify({'success': True, 'message': 'Budget set successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/model_comparison')
def api_model_comparison():
    """Generate model comparison chart"""
    try:
        comparison_path = cost_visualizer.create_model_comparison_chart()
        
        if not comparison_path:
            return jsonify({'success': False, 'error': 'No comparison data available'})
        
        # Convert to base64
        with open(comparison_path, 'rb') as f:
            img_data = f.read()
        
        img_b64 = base64.b64encode(img_data).decode('utf-8')
        
        # Cleanup
        if os.path.exists(comparison_path):
            os.remove(comparison_path)
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_b64}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/usage_patterns')
def api_usage_patterns():
    """Generate usage patterns heatmap"""
    days = request.args.get('days', 30, type=int)
    
    try:
        heatmap_path = cost_visualizer.create_usage_heatmap(days)
        
        if not heatmap_path:
            return jsonify({'success': False, 'error': 'No usage pattern data available'})
        
        # Convert to base64
        with open(heatmap_path, 'rb') as f:
            img_data = f.read()
        
        img_b64 = base64.b64encode(img_data).decode('utf-8')
        
        # Cleanup
        if os.path.exists(heatmap_path):
            os.remove(heatmap_path)
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_b64}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def run_dashboard(host='127.0.0.1', port=8080, debug=False):
    """Run the dashboard server"""
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_dashboard(debug=True)