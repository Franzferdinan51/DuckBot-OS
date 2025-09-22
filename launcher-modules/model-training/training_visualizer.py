#!/usr/bin/env python3
"""
DuckBot Training Visualization System
Professional-grade real-time visualization dashboard for model training progress

Features:
- Real-time training metrics visualization
- Interactive charts and graphs
- System resource monitoring
- Training progress tracking
- Performance analysis
- Web-based dashboard
- Export capabilities
- Multi-metric comparison
"""

import asyncio
import json
import logging
import os
import time
import threading
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Try to import optional visualization dependencies
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from flask import Flask, render_template, jsonify, request, send_file
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

try:
    import dash
    from dash import dcc, html, Input, Output, State
    import dash_bootstrap_components as dbc
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False

# Import DuckBot modules
try:
    from launcher_modules.model_training.training_monitoring import TrainingMonitor, TrainingMetricsDatabase
    from launcher_modules.model_training.structured_logger import StructuredLogger
    DUCKBOT_AVAILABLE = True
except ImportError:
    DUCKBOT_AVAILABLE = False

class VisualizationType(Enum):
    """Types of visualizations"""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    VIOLIN_PLOT = "violin_plot"
    PIE_CHART = "pie_chart"
    AREA_CHART = "area_chart"
    RADAR_CHART = "radar_chart"

class MetricCategory(Enum):
    """Categories of metrics for visualization"""
    TRAINING_LOSS = "training_loss"
    VALIDATION_LOSS = "validation_loss"
    TRAINING_ACCURACY = "training_accuracy"
    VALIDATION_ACCURACY = "validation_accuracy"
    LEARNING_RATE = "learning_rate"
    GRADIENT_NORM = "gradient_norm"
    THROUGHPUT = "throughput"
    GPU_UTILIZATION = "gpu_utilization"
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_USAGE = "memory_usage"
    CUSTOM = "custom"

class DashboardTheme(Enum):
    """Dashboard themes"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

@dataclass
class VisualizationConfig:
    """Configuration for visualization dashboard"""
    enable_real_time_updates = True
    update_interval = 2.0  # seconds
    max_data_points = 1000
    enable_interactive_charts = True
    enable_export = True
    enable_alerts = True
    theme = DashboardTheme.AUTO
    port = 8081
    host = "localhost"
    auto_open_browser = True
    enable_api = True
    max_concurrent_connections = 100

@dataclass
class ChartData:
    """Data structure for chart visualization"""
    title: str
    x_data: List[Any]
    y_data: List[float]
    x_label: str
    y_label: str
    chart_type: VisualizationType
    metadata: Dict[str, Any] = None

class TrainingVisualizer:
    """Main training visualization system"""

    def __init__(self, config: VisualizationConfig = None):
        self.config = config or VisualizationConfig()
        self.is_running = False
        self.subscribers = []  # WebSocket subscribers for real-time updates
        self.update_thread = None
        self.database_path = "training_monitoring.db"

        # Initialize web components if available
        if FLASK_AVAILABLE:
            self._setup_flask_app()
        if DASH_AVAILABLE:
            self._setup_dash_app()

        # Data cache
        self.data_cache = {}
        self.last_update = {}

    def _setup_flask_app(self):
        """Setup Flask web application"""
        self.flask_app = Flask(__name__)
        self.flask_app.config['SECRET_KEY'] = 'training-visualization-secret-key'
        self.socketio = SocketIO(self.flask_app, cors_allowed_origins="*")

        # Setup routes
        self._setup_flask_routes()

        # Setup WebSocket events
        self._setup_socketio_events()

    def _setup_flask_routes(self):
        """Setup Flask routes"""

        @self.flask_app.route('/')
        def dashboard():
            """Main dashboard page"""
            return self._render_dashboard()

        @self.flask_app.route('/api/metrics/<run_id>')
        def get_metrics(run_id):
            """Get metrics for a specific run"""
            try:
                metrics = self._get_run_metrics(run_id)
                return jsonify(metrics)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.flask_app.route('/api/summary/<run_id>')
        def get_summary(run_id):
            """Get run summary"""
            try:
                summary = self._get_run_summary(run_id)
                return jsonify(summary)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.flask_app.route('/api/chart/<run_id>/<metric_name>')
        def get_chart_data(run_id, metric_name):
            """Get chart data for a specific metric"""
            try:
                chart_data = self._get_chart_data(run_id, metric_name)
                return jsonify(chart_data)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.flask_app.route('/api/export/<run_id>/<format>')
        def export_data(run_id, format):
            """Export training data"""
            try:
                return self._export_run_data(run_id, format)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.flask_app.route('/api/system_metrics/<run_id>')
        def get_system_metrics(run_id):
            """Get system metrics for a run"""
            try:
                metrics = self._get_system_metrics(run_id)
                return jsonify(metrics)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def _setup_socketio_events(self):
        """Setup SocketIO events for real-time updates"""

        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            self.subscribers.append(request.sid)
            self.socketio.emit('connected', {'message': 'Connected to training dashboard'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            if request.sid in self.subscribers:
                self.subscribers.remove(request.sid)

        @self.socketio.on('subscribe_run')
        def handle_subscribe_run(data):
            """Handle subscription to a specific run"""
            run_id = data.get('run_id')
            if run_id:
                # Send initial data
                metrics = self._get_run_metrics(run_id)
                self.socketio.emit('initial_metrics', metrics, room=request.sid)

    def _setup_dash_app(self):
        """Setup Dash application"""
        self.dash_app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.dash_app.title = "DuckBot Training Dashboard"

        # Define layout
        self.dash_app.layout = self._create_dash_layout()

        # Setup callbacks
        self._setup_dash_callbacks()

    def _create_dash_layout(self):
        """Create Dash application layout"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("DuckBot Training Dashboard", className="text-center mb-4"),
                    html.Hr()
                ])
            ]),

            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='run-selector',
                        placeholder="Select training run",
                        className="mb-3"
                    )
                ], width=6),
                dbc.Col([
                    dcc.Dropdown(
                        id='metric-selector',
                        placeholder="Select metrics to display",
                        multi=True,
                        className="mb-3"
                    )
                ], width=6)
            ]),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='main-chart')
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='loss-chart')
                ], width=6),
                dbc.Col([
                    dcc.Graph(id='accuracy-chart')
                ], width=6)
            ]),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='system-metrics-chart')
                ], width=12)
            ]),

            dcc.Interval(
                id='update-interval',
                interval=2000,  # 2 seconds
                n_intervals=0
            )
        ], fluid=True)

    def _setup_dash_callbacks(self):
        """Setup Dash application callbacks"""

        @self.dash_app.callback(
            [Output('run-selector', 'options'),
             Output('run-selector', 'value')],
            [Input('update-interval', 'n_intervals')]
        )
        def update_run_selector(n):
            """Update run selector dropdown"""
            runs = self._get_available_runs()
            options = [{'label': run, 'value': run} for run in runs]
            return options, options[0]['value'] if options else None

        @self.dash_app.callback(
            [Output('metric-selector', 'options')],
            [Input('run-selector', 'value')]
        )
        def update_metric_selector(selected_run):
            """Update metric selector based on selected run"""
            if not selected_run:
                return []

            metrics = self._get_available_metrics(selected_run)
            return [{'label': metric, 'value': metric} for metric in metrics]

        @self.dash_app.callback(
            [Output('main-chart', 'figure'),
             Output('loss-chart', 'figure'),
             Output('accuracy-chart', 'figure'),
             Output('system-metrics-chart', 'figure')],
            [Input('run-selector', 'value'),
             Input('metric-selector', 'value'),
             Input('update-interval', 'n_intervals')]
        )
        def update_charts(selected_run, selected_metrics, n):
            """Update all charts"""
            if not selected_run:
                return {}, {}, {}, {}

            try:
                # Main chart
                main_fig = self._create_main_chart(selected_run, selected_metrics)

                # Loss chart
                loss_fig = self._create_loss_chart(selected_run)

                # Accuracy chart
                accuracy_fig = self._create_accuracy_chart(selected_run)

                # System metrics chart
                system_fig = self._create_system_metrics_chart(selected_run)

                return main_fig, loss_fig, accuracy_fig, system_fig

            except Exception as e:
                print(f"Error updating charts: {e}")
                return {}, {}, {}, {}

    def start_dashboard(self):
        """Start the visualization dashboard"""
        if self.is_running:
            return

        self.is_running = True

        if self.config.enable_real_time_updates:
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()

        # Start web server
        if FLASK_AVAILABLE:
            def run_flask():
                self.flask_app.run(
                    host=self.config.host,
                    port=self.config.port,
                    debug=False,
                    threaded=True
                )

            flask_thread = threading.Thread(target=run_flask, daemon=True)
            flask_thread.start()

            dashboard_url = f"http://{self.config.host}:{self.config.port}"
            print(f"Training dashboard started at: {dashboard_url}")

            if self.config.auto_open_browser:
                webbrowser.open(dashboard_url)

        elif DASH_AVAILABLE:
            def run_dash():
                self.dash_app.run_server(
                    host=self.config.host,
                    port=self.config.port,
                    debug=False
                )

            dash_thread = threading.Thread(target=run_dash, daemon=True)
            dash_thread.start()

            dashboard_url = f"http://{self.config.host}:{self.config.port}"
            print(f"Training dashboard started at: {dashboard_url}")

            if self.config.auto_open_browser:
                webbrowser.open(dashboard_url)

        else:
            print("No web framework available. Please install Flask or Dash.")

    def stop_dashboard(self):
        """Stop the visualization dashboard"""
        self.is_running = False

        if self.update_thread:
            self.update_thread.join(timeout=5)

    def _update_loop(self):
        """Main update loop for real-time data"""
        while self.is_running:
            try:
                # Update data cache
                self._update_data_cache()

                # Notify subscribers
                if self.subscribers:
                    self._notify_subscribers()

                time.sleep(self.config.update_interval)

            except Exception as e:
                logging.error(f"Error in update loop: {e}")
                time.sleep(self.config.update_interval)

    def _update_data_cache(self):
        """Update cached data"""
        try:
            # Get available runs
            runs = self._get_available_runs()

            # Update cache for each run
            for run_id in runs:
                if run_id not in self.data_cache:
                    self.data_cache[run_id] = {}

                # Get metrics
                metrics = self._get_run_metrics(run_id)
                self.data_cache[run_id]['metrics'] = metrics

                # Get system metrics
                system_metrics = self._get_system_metrics(run_id)
                self.data_cache[run_id]['system_metrics'] = system_metrics

                # Get summary
                summary = self._get_run_summary(run_id)
                self.data_cache[run_id]['summary'] = summary

                self.last_update[run_id] = datetime.now()

        except Exception as e:
            logging.error(f"Error updating data cache: {e}")

    def _notify_subscribers(self):
        """Notify all subscribers of updates"""
        if not self.subscribers or not FLASK_AVAILABLE:
            return

        # Send update to all subscribers
        for subscriber_id in self.subscribers:
            try:
                self.socketio.emit('data_update', {
                    'timestamp': datetime.now().isoformat(),
                    'cache': self.data_cache
                }, room=subscriber_id)
            except Exception as e:
                logging.error(f"Error notifying subscriber {subscriber_id}: {e}")

    def _get_available_runs(self) -> List[str]:
        """Get list of available training runs"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute('SELECT DISTINCT run_id FROM training_runs ORDER BY start_time DESC')
                return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []

    def _get_available_metrics(self, run_id: str) -> List[str]:
        """Get available metrics for a run"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute('''
                    SELECT DISTINCT metric_name
                    FROM training_metrics
                    WHERE run_id = ?
                    ORDER BY metric_name
                ''', (run_id,))
                return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []

    def _get_run_metrics(self, run_id: str, limit: int = 1000) -> Dict[str, Any]:
        """Get metrics for a specific run"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute('''
                    SELECT metric_name, value, step, epoch, timestamp, category
                    FROM training_metrics
                    WHERE run_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (run_id, limit))

                metrics_data = {}
                for row in cursor.fetchall():
                    metric_name, value, step, epoch, timestamp, category = row

                    if metric_name not in metrics_data:
                        metrics_data[metric_name] = {
                            'values': [],
                            'steps': [],
                            'epochs': [],
                            'timestamps': [],
                            'category': category
                        }

                    metrics_data[metric_name]['values'].append(value)
                    metrics_data[metric_name]['steps'].append(step)
                    metrics_data[metric_name]['epochs'].append(epoch)
                    metrics_data[metric_name]['timestamps'].append(timestamp)

                # Reverse to get chronological order
                for metric_data in metrics_data.values():
                    metric_data['values'].reverse()
                    metric_data['steps'].reverse()
                    metric_data['epochs'].reverse()
                    metric_data['timestamps'].reverse()

                return metrics_data

        except Exception as e:
            logging.error(f"Error getting run metrics: {e}")
            return {}

    def _get_system_metrics(self, run_id: str, limit: int = 1000) -> Dict[str, Any]:
        """Get system metrics for a specific run"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute('''
                    SELECT timestamp, cpu_percent, memory_percent, gpu_utilization_percent,
                           memory_used_gb, gpu_memory_used_gb
                    FROM system_metrics
                    WHERE run_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (run_id, limit))

                timestamps = []
                cpu_data = []
                memory_data = []
                gpu_data = []
                memory_used_data = []
                gpu_memory_used_data = []

                for row in cursor.fetchall():
                    timestamp, cpu, memory, gpu, mem_used, gpu_mem_used = row
                    timestamps.append(timestamp)
                    cpu_data.append(cpu)
                    memory_data.append(memory)
                    gpu_data.append(gpu)
                    memory_used_data.append(mem_used)
                    gpu_memory_used_data.append(gpu_mem_used)

                # Reverse for chronological order
                timestamps.reverse()
                cpu_data.reverse()
                memory_data.reverse()
                gpu_data.reverse()
                memory_used_data.reverse()
                gpu_memory_used_data.reverse()

                return {
                    'timestamps': timestamps,
                    'cpu_percent': cpu_data,
                    'memory_percent': memory_data,
                    'gpu_utilization_percent': gpu_data,
                    'memory_used_gb': memory_used_data,
                    'gpu_memory_used_gb': gpu_memory_used_data
                }

        except Exception as e:
            logging.error(f"Error getting system metrics: {e}")
            return {}

    def _get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """Get summary for a specific run"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute('''
                    SELECT start_time, end_time, status, total_steps, total_epochs,
                           current_step, current_epoch, best_loss, best_accuracy
                    FROM training_runs
                    WHERE id = ?
                ''', (run_id,))

                row = cursor.fetchone()
                if row:
                    return {
                        'start_time': row[0],
                        'end_time': row[1],
                        'status': row[2],
                        'total_steps': row[3],
                        'total_epochs': row[4],
                        'current_step': row[5],
                        'current_epoch': row[6],
                        'best_loss': row[7],
                        'best_accuracy': row[8]
                    }
                return {}

        except Exception as e:
            logging.error(f"Error getting run summary: {e}")
            return {}

    def _get_chart_data(self, run_id: str, metric_name: str) -> Dict[str, Any]:
        """Get chart data for a specific metric"""
        metrics = self._get_run_metrics(run_id)
        if metric_name not in metrics:
            return {}

        metric_data = metrics[metric_name]
        return {
            'title': f'{metric_name} over Training Steps',
            'x_data': metric_data['steps'],
            'y_data': metric_data['values'],
            'x_label': 'Training Steps',
            'y_label': metric_name,
            'timestamps': metric_data['timestamps'],
            'category': metric_data['category']
        }

    def _export_run_data(self, run_id: str, format: str):
        """Export training data in various formats"""
        try:
            # Get all data
            metrics = self._get_run_metrics(run_id)
            system_metrics = self._get_system_metrics(run_id)
            summary = self._get_run_summary(run_id)

            # Prepare export data
            export_data = {
                'run_id': run_id,
                'summary': summary,
                'metrics': metrics,
                'system_metrics': system_metrics,
                'export_timestamp': datetime.now().isoformat()
            }

            # Create export directory
            export_dir = Path('exports')
            export_dir.mkdir(exist_ok=True)

            if format.lower() == 'json':
                filename = f'{run_id}_training_data.json'
                filepath = export_dir / filename

                with open(filepath, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)

                return send_file(filepath, as_attachment=True, download_name=filename)

            elif format.lower() == 'csv':
                # Convert metrics to DataFrame
                all_metrics = []
                for metric_name, data in metrics.items():
                    for i, value in enumerate(data['values']):
                        all_metrics.append({
                            'metric_name': metric_name,
                            'value': value,
                            'step': data['steps'][i],
                            'epoch': data['epochs'][i],
                            'timestamp': data['timestamps'][i]
                        })

                df = pd.DataFrame(all_metrics)
                filename = f'{run_id}_training_data.csv'
                filepath = export_dir / filename
                df.to_csv(filepath, index=False)

                return send_file(filepath, as_attachment=True, download_name=filename)

            else:
                return jsonify({"error": f"Unsupported format: {format}"}), 400

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def _render_dashboard(self) -> str:
        """Render HTML dashboard"""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>DuckBot Training Dashboard</title>
            <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .chart-container { margin: 20px 0; height: 400px; }
                .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .metric-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
                .status { padding: 10px; margin: 10px 0; border-radius: 3px; }
                .status.running { background-color: #d4edda; color: #155724; }
                .status.stopped { background-color: #f8d7da; color: #721c24; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>DuckBot Training Dashboard</h1>

                <div id="connection-status" class="status stopped">
                    Connecting to training monitoring system...
                </div>

                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>Active Runs</h3>
                        <div id="active-runs">Loading...</div>
                    </div>
                    <div class="metric-card">
                        <h3>Current Loss</h3>
                        <div id="current-loss">-</div>
                    </div>
                    <div class="metric-card">
                        <h3>Current Accuracy</h3>
                        <div id="current-accuracy">-</div>
                    </div>
                    <div class="metric-card">
                        <h3>GPU Utilization</h3>
                        <div id="gpu-util">-</div>
                    </div>
                </div>

                <div id="run-selector">
                    <h3>Select Training Run</h3>
                    <select id="run-dropdown" style="width: 100%; padding: 8px;">
                        <option value="">Loading runs...</option>
                    </select>
                </div>

                <div id="charts-container">
                    <div class="chart-container">
                        <div id="loss-chart"></div>
                    </div>
                    <div class="chart-container">
                        <div id="accuracy-chart"></div>
                    </div>
                    <div class="chart-container">
                        <div id="system-chart"></div>
                    </div>
                </div>
            </div>

            <script>
                // Socket.IO connection
                const socket = io();

                socket.on('connect', () => {
                    document.getElementById('connection-status').textContent = 'Connected to training monitoring system';
                    document.getElementById('connection-status').className = 'status running';
                });

                socket.on('disconnect', () => {
                    document.getElementById('connection-status').textContent = 'Disconnected from training monitoring system';
                    document.getElementById('connection-status').className = 'status stopped';
                });

                socket.on('initial_metrics', (data) => {
                    updateDashboard(data);
                });

                socket.on('data_update', (data) => {
                    updateDashboard(data.cache);
                });

                function updateDashboard(cache) {
                    // Update run selector
                    const runDropdown = document.getElementById('run-dropdown');
                    runDropdown.innerHTML = '<option value="">Select a run...</option>';

                    Object.keys(cache).forEach(runId => {
                        const option = document.createElement('option');
                        option.value = runId;
                        option.textContent = runId;
                        runDropdown.appendChild(option);
                    });

                    // Update metrics if run is selected
                    const selectedRun = runDropdown.value;
                    if (selectedRun && cache[selectedRun]) {
                        updateMetrics(cache[selectedRun]);
                    }
                }

                function updateMetrics(runData) {
                    // Update current metrics
                    const metrics = runData.metrics;
                    const systemMetrics = runData.system_metrics;

                    // Update loss
                    if (metrics.loss && metrics.loss.values.length > 0) {
                        document.getElementById('current-loss').textContent =
                            metrics.loss.values[metrics.loss.values.length - 1].toFixed(4);
                    }

                    // Update accuracy
                    if (metrics.accuracy && metrics.accuracy.values.length > 0) {
                        document.getElementById('current-accuracy').textContent =
                            (metrics.accuracy.values[metrics.accuracy.values.length - 1] * 100).toFixed(2) + '%';
                    }

                    // Update GPU utilization
                    if (systemMetrics.gpu_utilization_percent && systemMetrics.gpu_utilization_percent.length > 0) {
                        document.getElementById('gpu-util').textContent =
                            systemMetrics.gpu_utilization_percent[systemMetrics.gpu_utilization_percent.length - 1].toFixed(1) + '%';
                    }

                    // Update charts
                    updateCharts(runData);
                }

                function updateCharts(runData) {
                    const metrics = runData.metrics;
                    const systemMetrics = runData.system_metrics;

                    // Loss chart
                    if (metrics.loss) {
                        Plotly.newPlot('loss-chart', [{
                            x: metrics.loss.steps,
                            y: metrics.loss.values,
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: 'Training Loss'
                        }], {
                            title: 'Training Loss',
                            xaxis: { title: 'Step' },
                            yaxis: { title: 'Loss' }
                        });
                    }

                    // Accuracy chart
                    if (metrics.accuracy) {
                        Plotly.newPlot('accuracy-chart', [{
                            x: metrics.accuracy.steps,
                            y: metrics.accuracy.values,
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: 'Training Accuracy'
                        }], {
                            title: 'Training Accuracy',
                            xaxis: { title: 'Step' },
                            yaxis: { title: 'Accuracy', range: [0, 1] }
                        });
                    }

                    // System metrics chart
                    if (systemMetrics.timestamps && systemMetrics.timestamps.length > 0) {
                        Plotly.newPlot('system-chart', [
                            {
                                x: systemMetrics.timestamps,
                                y: systemMetrics.cpu_percent,
                                type: 'scatter',
                                mode: 'lines',
                                name: 'CPU %'
                            },
                            {
                                x: systemMetrics.timestamps,
                                y: systemMetrics.memory_percent,
                                type: 'scatter',
                                mode: 'lines',
                                name: 'Memory %'
                            },
                            {
                                x: systemMetrics.timestamps,
                                y: systemMetrics.gpu_utilization_percent,
                                type: 'scatter',
                                mode: 'lines',
                                name: 'GPU %'
                            }
                        ], {
                            title: 'System Resource Usage',
                            xaxis: { title: 'Time' },
                            yaxis: { title: 'Percentage' }
                        });
                    }
                }

                // Run selector change handler
                document.getElementById('run-dropdown').addEventListener('change', function(e) {
                    const selectedRun = e.target.value;
                    if (selectedRun && window.dashboardCache && window.dashboardCache[selectedRun]) {
                        updateMetrics(window.dashboardCache[selectedRun]);
                    }
                });

                // Store cache globally
                socket.on('data_update', (data) => {
                    window.dashboardCache = data.cache;
                });
            </script>
        </body>
        </html>
        '''

    def _create_main_chart(self, run_id: str, selected_metrics: List[str]) -> Dict:
        """Create main chart with selected metrics"""
        if not selected_metrics or not PLOTLY_AVAILABLE:
            return {}

        metrics = self._get_run_metrics(run_id)

        traces = []
        for metric_name in selected_metrics:
            if metric_name in metrics:
                metric_data = metrics[metric_name]
                traces.append({
                    'x': metric_data['steps'],
                    'y': metric_data['values'],
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'name': metric_name
                })

        return {
            'data': traces,
            'layout': {
                'title': f'Training Metrics - {run_id}',
                'xaxis': {'title': 'Training Step'},
                'yaxis': {'title': 'Value'},
                'height': 400
            }
        }

    def _create_loss_chart(self, run_id: str) -> Dict:
        """Create loss chart"""
        if not PLOTLY_AVAILABLE:
            return {}

        metrics = self._get_run_metrics(run_id)

        traces = []
        if 'loss' in metrics:
            loss_data = metrics['loss']
            traces.append({
                'x': loss_data['steps'],
                'y': loss_data['values'],
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Training Loss'
            })

        if 'val_loss' in metrics:
            val_loss_data = metrics['val_loss']
            traces.append({
                'x': val_loss_data['steps'],
                'y': val_loss_data['values'],
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Validation Loss'
            })

        return {
            'data': traces,
            'layout': {
                'title': 'Loss Metrics',
                'xaxis': {'title': 'Training Step'},
                'yaxis': {'title': 'Loss'},
                'height': 300
            }
        }

    def _create_accuracy_chart(self, run_id: str) -> Dict:
        """Create accuracy chart"""
        if not PLOTLY_AVAILABLE:
            return {}

        metrics = self._get_run_metrics(run_id)

        traces = []
        if 'accuracy' in metrics:
            acc_data = metrics['accuracy']
            traces.append({
                'x': acc_data['steps'],
                'y': acc_data['values'],
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Training Accuracy'
            })

        if 'val_accuracy' in metrics:
            val_acc_data = metrics['val_accuracy']
            traces.append({
                'x': val_acc_data['steps'],
                'y': val_acc_data['values'],
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': 'Validation Accuracy'
            })

        return {
            'data': traces,
            'layout': {
                'title': 'Accuracy Metrics',
                'xaxis': {'title': 'Training Step'},
                'yaxis': {'title': 'Accuracy', 'range': [0, 1]},
                'height': 300
            }
        }

    def _create_system_metrics_chart(self, run_id: str) -> Dict:
        """Create system metrics chart"""
        if not PLOTLY_AVAILABLE:
            return {}

        system_metrics = self._get_system_metrics(run_id)

        traces = []
        if system_metrics.get('timestamps'):
            timestamps = system_metrics['timestamps']

            if system_metrics.get('cpu_percent'):
                traces.append({
                    'x': timestamps,
                    'y': system_metrics['cpu_percent'],
                    'type': 'scatter',
                    'mode': 'lines',
                    'name': 'CPU %'
                })

            if system_metrics.get('memory_percent'):
                traces.append({
                    'x': timestamps,
                    'y': system_metrics['memory_percent'],
                    'type': 'scatter',
                    'mode': 'lines',
                    'name': 'Memory %'
                })

            if system_metrics.get('gpu_utilization_percent'):
                traces.append({
                    'x': timestamps,
                    'y': system_metrics['gpu_utilization_percent'],
                    'type': 'scatter',
                    'mode': 'lines',
                    'name': 'GPU %'
                })

        return {
            'data': traces,
            'layout': {
                'title': 'System Resource Usage',
                'xaxis': {'title': 'Time'},
                'yaxis': {'title': 'Percentage'},
                'height': 300
            }
        }

    def create_static_chart(self, chart_data: ChartData, output_path: str = None) -> str:
        """Create a static chart image"""
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Matplotlib is required for static charts")

        fig, ax = plt.subplots(figsize=(10, 6))

        if chart_data.chart_type == VisualizationType.LINE_CHART:
            ax.plot(chart_data.x_data, chart_data.y_data, marker='o')
        elif chart_data.chart_type == VisualizationType.SCATTER_PLOT:
            ax.scatter(chart_data.x_data, chart_data.y_data)
        elif chart_data.chart_type == VisualizationType.BAR_CHART:
            ax.bar(chart_data.x_data, chart_data.y_data)
        else:
            ax.plot(chart_data.x_data, chart_data.y_data, marker='o')

        ax.set_xlabel(chart_data.x_label)
        ax.set_ylabel(chart_data.y_label)
        ax.set_title(chart_data.title)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            return output_path
        else:
            return fig

    def generate_training_report(self, run_id: str, output_path: str = None) -> str:
        """Generate a comprehensive training report"""
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Matplotlib is required for training reports")

        # Get data
        metrics = self._get_run_metrics(run_id)
        system_metrics = self._get_system_metrics(run_id)
        summary = self._get_run_summary(run_id)

        # Create report figure
        fig = plt.figure(figsize=(16, 12))

        # Loss chart
        if 'loss' in metrics:
            ax1 = plt.subplot(2, 3, 1)
            loss_data = metrics['loss']
            ax1.plot(loss_data['steps'], loss_data['values'], 'b-', label='Training Loss')
            if 'val_loss' in metrics:
                val_loss_data = metrics['val_loss']
                ax1.plot(val_loss_data['steps'], val_loss_data['values'], 'r--', label='Validation Loss')
            ax1.set_xlabel('Step')
            ax1.set_ylabel('Loss')
            ax1.set_title('Training Loss')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

        # Accuracy chart
        if 'accuracy' in metrics:
            ax2 = plt.subplot(2, 3, 2)
            acc_data = metrics['accuracy']
            ax2.plot(acc_data['steps'], acc_data['values'], 'g-', label='Training Accuracy')
            if 'val_accuracy' in metrics:
                val_acc_data = metrics['val_accuracy']
                ax2.plot(val_acc_data['steps'], val_acc_data['values'], 'r--', label='Validation Accuracy')
            ax2.set_xlabel('Step')
            ax2.set_ylabel('Accuracy')
            ax2.set_title('Training Accuracy')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

        # Learning rate chart
        if 'learning_rate' in metrics:
            ax3 = plt.subplot(2, 3, 3)
            lr_data = metrics['learning_rate']
            ax3.plot(lr_data['steps'], lr_data['values'], 'purple')
            ax3.set_xlabel('Step')
            ax3.set_ylabel('Learning Rate')
            ax3.set_title('Learning Rate Schedule')
            ax3.set_yscale('log')
            ax3.grid(True, alpha=0.3)

        # System metrics
        if system_metrics.get('timestamps'):
            ax4 = plt.subplot(2, 3, 4)
            timestamps = system_metrics['timestamps']
            if system_metrics.get('cpu_percent'):
                ax4.plot(timestamps, system_metrics['cpu_percent'], 'r-', label='CPU')
            if system_metrics.get('memory_percent'):
                ax4.plot(timestamps, system_metrics['memory_percent'], 'b-', label='Memory')
            if system_metrics.get('gpu_utilization_percent'):
                ax4.plot(timestamps, system_metrics['gpu_utilization_percent'], 'g-', label='GPU')
            ax4.set_xlabel('Time')
            ax4.set_ylabel('Usage (%)')
            ax4.set_title('System Resource Usage')
            ax4.legend()
            ax4.grid(True, alpha=0.3)

        # Gradient norms
        if 'gradient_norm' in metrics:
            ax5 = plt.subplot(2, 3, 5)
            grad_data = metrics['gradient_norm']
            ax5.plot(grad_data['steps'], grad_data['values'], 'orange')
            ax5.set_xlabel('Step')
            ax5.set_ylabel('Gradient Norm')
            ax5.set_title('Gradient Norms')
            ax5.grid(True, alpha=0.3)

        # Training summary
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')
        summary_text = f"Training Summary\n{'='*30}\n"
        if summary:
            summary_text += f"Run ID: {run_id}\n"
            summary_text += f"Status: {summary.get('status', 'Unknown')}\n"
            summary_text += f"Total Steps: {summary.get('current_step', 0)}\n"
            summary_text += f"Total Epochs: {summary.get('current_epoch', 0)}\n"
            summary_text += f"Best Loss: {summary.get('best_loss', 'N/A'):.4f}\n"
            summary_text += f"Best Accuracy: {summary.get('best_accuracy', 'N/A'):.4f}\n"

            if summary.get('start_time'):
                start_time = datetime.fromisoformat(summary['start_time'])
                summary_text += f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"

            if summary.get('end_time'):
                end_time = datetime.fromisoformat(summary['end_time'])
                summary_text += f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                duration = end_time - start_time
                summary_text += f"Duration: {duration}"

        ax6.text(0.1, 0.9, summary_text, transform=ax6.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        plt.suptitle(f'Training Report - {run_id}', fontsize=16, fontweight='bold')
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            return output_path
        else:
            return fig

# Convenience functions
def create_visualizer(config: VisualizationConfig = None) -> TrainingVisualizer:
    """Create a training visualizer with default configuration"""
    return TrainingVisualizer(config)

def get_default_config() -> VisualizationConfig:
    """Get default visualization configuration"""
    return VisualizationConfig()

if __name__ == "__main__":
    # Test the training visualizer
    print("Testing DuckBot Training Visualizer")

    # Create visualizer
    visualizer = TrainingVisualizer()

    # Start dashboard
    print("Starting training dashboard...")
    visualizer.start_dashboard()

    print("Dashboard started. Press Ctrl+C to stop.")

    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping dashboard...")
        visualizer.stop_dashboard()
        print("Dashboard stopped.")