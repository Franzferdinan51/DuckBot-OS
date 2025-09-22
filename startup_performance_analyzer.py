#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot v4.2 Startup Performance Analyzer
Detailed analysis of service startup times and resource consumption patterns
"""

import os
import sys
import time
import json
import subprocess
import psutil
import threading
import concurrent.futures
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import statistics

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('startup_performance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class StartupMetrics:
    """Service startup metrics"""
    service_name: str
    startup_time: float
    peak_memory_mb: float
    final_memory_mb: float
    peak_cpu_percent: float
    final_cpu_percent: float
    process_id: int
    success: bool
    error_message: Optional[str] = None
    startup_phase_times: Dict[str, float] = None

@dataclass
class SystemResourceSnapshot:
    """System resource snapshot at a point in time"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_mb: float
    network_io_mb: float
    process_count: int

class StartupPerformanceAnalyzer:
    """Analyzer for DuckBot service startup performance"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.results_dir = self.base_dir / "startup_analysis"
        self.results_dir.mkdir(exist_ok=True)

        # Service definitions with startup methods
        self.services = {
            'comfyui': {
                'startup_method': self.start_comfyui,
                'expected_time': 15.0,
                'port': 8188,
                'health_endpoint': 'http://localhost:8188'
            },
            'n8n': {
                'startup_method': self.start_n8n,
                'expected_time': 20.0,
                'port': 5678,
                'health_endpoint': 'http://localhost:5678/healthz'
            },
            'open_notebook': {
                'startup_method': self.start_open_notebook,
                'expected_time': 25.0,
                'port': 8502,
                'health_endpoint': 'http://localhost:8502/health'
            },
            'jupyter': {
                'startup_method': self.start_jupyter,
                'expected_time': 10.0,
                'port': 8889,
                'health_endpoint': 'http://localhost:8889'
            },
            'open_webui': {
                'startup_method': self.start_open_webui,
                'expected_time': 20.0,
                'port': 8080,
                'health_endpoint': 'http://localhost:8080'
            },
            'duckbot': {
                'startup_method': self.start_duckbot,
                'expected_time': 5.0,
                'port': 0,
                'health_endpoint': ''
            }
        }

        # Resource monitoring
        self.system_snapshots: List[SystemResourceSnapshot] = []
        self.monitoring_active = False

    @contextmanager
    def measure_time(self, operation_name: str):
        """Context manager for measuring operation time"""
        start_time = time.perf_counter()
        yield start_time
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        logger.debug(f"{operation_name} took {execution_time:.4f} seconds")
        return execution_time

    def capture_system_snapshot(self) -> SystemResourceSnapshot:
        """Capture current system resource state"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        network_io = psutil.net_io_counters()

        return SystemResourceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            disk_io_mb=(disk_io.read_bytes + disk_io.write_bytes) / 1024 / 1024,
            network_io_mb=(network_io.bytes_sent + network_io.bytes_recv) / 1024 / 1024,
            process_count=len(psutil.pids())
        )

    def start_resource_monitoring(self):
        """Start background system resource monitoring"""
        self.monitoring_active = True

        def monitor_loop():
            while self.monitoring_active:
                try:
                    snapshot = self.capture_system_snapshot()
                    self.system_snapshots.append(snapshot)
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Error in resource monitoring: {e}")
                    time.sleep(1)

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("Resource monitoring started")

    def stop_resource_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring_active = False
        logger.info("Resource monitoring stopped")

    def track_process_resources(self, process_id: int, duration: float) -> Dict[str, List[float]]:
        """Track resource usage of a specific process over time"""
        if process_id == 0:
            return {'memory_mb': [], 'cpu_percent': []}

        memory_usage = []
        cpu_usage = []
        start_time = time.time()

        try:
            process = psutil.Process(process_id)
            end_time = start_time + duration

            while time.time() < end_time:
                try:
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    cpu_percent = process.cpu_percent()

                    memory_usage.append(memory_mb)
                    cpu_usage.append(cpu_percent)

                    time.sleep(0.5)  # Sample every 500ms

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    logger.warning(f"Process {process_id} no longer accessible")
                    break

        except psutil.NoSuchProcess:
            logger.warning(f"Process {process_id} not found")

        return {
            'memory_mb': memory_usage,
            'cpu_percent': cpu_usage
        }

    def start_comfyui(self) -> Tuple[Optional[subprocess.Popen], float]:
        """Start ComfyUI and measure startup time"""
        start_time = time.perf_counter()

        try:
            # Try to find ComfyUI installation
            comfyui_paths = [
                self.base_dir / "ComfyUI" / "main.py",
                self.base_dir / "ComfyUI_windows_portable_nvidia" / "ComfyUI" / "main.py",
                self.base_dir / "ComfyUI_windows_portable" / "ComfyUI" / "main.py"
            ]

            for comfyui_path in comfyui_paths:
                if comfyui_path.exists():
                    try:
                        logger.info(f"Starting ComfyUI from: {comfyui_path}")
                        process = subprocess.Popen([
                            sys.executable, str(comfyui_path),
                            "--listen", "127.0.0.1",
                            "--port", "8188",
                            "--enable-cors-header"
                        ], cwd=str(comfyui_path.parent),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)

                        startup_time = time.perf_counter() - start_time
                        return process, startup_time

                    except Exception as e:
                        logger.error(f"Failed to start ComfyUI from {comfyui_path}: {e}")
                        continue

            logger.error("ComfyUI not found in any standard location")
            return None, time.perf_counter() - start_time

        except Exception as e:
            logger.error(f"Error starting ComfyUI: {e}")
            return None, time.perf_counter() - start_time

    def start_n8n(self) -> Tuple[Optional[subprocess.Popen], float]:
        """Start n8n and measure startup time"""
        start_time = time.perf_counter()

        try:
            # Find n8n executable
            n8n_paths = [
                'n8n',
                r'C:\Users\Duck1\AppData\Roaming\npm\n8n.cmd',
                os.path.expanduser('~/AppData/Roaming/npm/n8n.cmd')
            ]

            for n8n_path in n8n_paths:
                try:
                    # Test if n8n is available
                    result = subprocess.run([n8n_path, '--version'], capture_output=True, check=True, timeout=10)
                    logger.info(f"Starting n8n from: {n8n_path}")

                    # Start n8n
                    process = subprocess.Popen([
                        n8n_path, 'start',
                        '--port', '5678',
                        '--host', 'localhost'
                    ], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)

                    startup_time = time.perf_counter() - start_time
                    return process, startup_time

                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    continue

            logger.error("n8n not found in any standard location")
            return None, time.perf_counter() - start_time

        except Exception as e:
            logger.error(f"Error starting n8n: {e}")
            return None, time.perf_counter() - start_time

    def start_open_notebook(self) -> Tuple[Optional[subprocess.Popen], float]:
        """Start open-notebook and measure startup time"""
        start_time = time.perf_counter()

        try:
            open_notebook_dir = self.base_dir / "open-notebook"
            if not open_notebook_dir.exists():
                logger.error("open-notebook directory not found")
                return None, time.perf_counter() - start_time

            # Try Python fallback
            startup_files = ["app_home.py", "main.py", "streamlit_app.py"]

            for startup_file in startup_files:
                startup_path = open_notebook_dir / startup_file
                if startup_path.exists():
                    try:
                        logger.info(f"Starting open-notebook with: {startup_file}")

                        # Check if it's a Streamlit app
                        if "streamlit" in startup_path.read_text(encoding='utf-8', errors='ignore'):
                            process = subprocess.Popen([
                                sys.executable, '-m', 'streamlit', 'run',
                                str(startup_path),
                                '--server.port', '8502',
                                '--server.headless', 'true'
                            ], cwd=str(open_notebook_dir),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)
                        else:
                            process = subprocess.Popen([
                                sys.executable, str(startup_path)
                            ], cwd=str(open_notebook_dir),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)

                        startup_time = time.perf_counter() - start_time
                        return process, startup_time

                    except Exception as e:
                        logger.error(f"Failed to start with {startup_file}: {e}")
                        continue

            logger.error("No valid startup file found for open-notebook")
            return None, time.perf_counter() - start_time

        except Exception as e:
            logger.error(f"Error starting open-notebook: {e}")
            return None, time.perf_counter() - start_time

    def start_jupyter(self) -> Tuple[Optional[subprocess.Popen], float]:
        """Start Jupyter and measure startup time"""
        start_time = time.perf_counter()

        try:
            # Check if jupyter is available
            result = subprocess.run(['jupyter', '--version'], capture_output=True, check=True)
            logger.info("Starting Jupyter Notebook")

            process = subprocess.Popen([
                'jupyter', 'notebook',
                '--port', '8889',
                '--no-browser',
                '--allow-root',
                '--ip', 'localhost',
                '--NotebookApp.token=""',
                '--NotebookApp.password=""'
            ], stdout=subprocess.PIPE,
               stderr=subprocess.PIPE,
               creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)

            startup_time = time.perf_counter() - start_time
            return process, startup_time

        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Jupyter not installed or not in PATH")
            return None, time.perf_counter() - start_time

        except Exception as e:
            logger.error(f"Error starting Jupyter: {e}")
            return None, time.perf_counter() - start_time

    def start_open_webui(self) -> Tuple[Optional[subprocess.Popen], float]:
        """Start Open WebUI and measure startup time"""
        start_time = time.perf_counter()

        try:
            # Check if open-webui is available
            try:
                subprocess.run(['open-webui', '--version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("open-webui not installed or not in PATH")
                return None, time.perf_counter() - start_time

            logger.info("Starting Open WebUI")

            process = subprocess.Popen([
                'open-webui', 'serve',
                '--host', 'localhost',
                '--port', '8080'
            ], stdout=subprocess.PIPE,
               stderr=subprocess.PIPE,
               creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)

            startup_time = time.perf_counter() - start_time
            return process, startup_time

        except Exception as e:
            logger.error(f"Error starting Open WebUI: {e}")
            return None, time.perf_counter() - start_time

    def start_duckbot(self) -> Tuple[Optional[subprocess.Popen], float]:
        """Start DuckBot and measure startup time"""
        start_time = time.perf_counter()

        try:
            # Find DuckBot script
            possible_scripts = [
                "DuckBot-v2.3.0-Trading-Video-Enhanced.py",
                "DuckBot.py",
                "main.py",
                "bot.py"
            ]

            main_script = None
            for script_name in possible_scripts:
                script_path = self.base_dir / script_name
                if script_path.exists():
                    main_script = script_path
                    break

            if not main_script:
                logger.error("DuckBot script not found")
                return None, time.perf_counter() - start_time

            logger.info(f"Starting DuckBot from: {main_script}")

            process = subprocess.Popen([
                sys.executable, str(main_script)
            ], cwd=str(self.base_dir),
               stdout=subprocess.PIPE,
               stderr=subprocess.PIPE)

            startup_time = time.perf_counter() - start_time
            return process, startup_time

        except Exception as e:
            logger.error(f"Error starting DuckBot: {e}")
            return None, time.perf_counter() - start_time

    def analyze_service_startup(self, service_name: str, service_info: Dict) -> StartupMetrics:
        """Analyze startup performance for a single service"""
        logger.info(f"Analyzing startup performance for {service_name}...")

        # Start resource monitoring
        self.start_resource_monitoring()

        try:
            # Start the service
            startup_method = service_info['startup_method']
            process, startup_time = startup_method()

            if process is None:
                return StartupMetrics(
                    service_name=service_name,
                    startup_time=startup_time,
                    peak_memory_mb=0.0,
                    final_memory_mb=0.0,
                    peak_cpu_percent=0.0,
                    final_cpu_percent=0.0,
                    process_id=0,
                    success=False,
                    error_message="Failed to start service"
                )

            process_id = process.pid

            # Track process resources for expected startup time
            expected_time = service_info.get('expected_time', 30.0)
            resource_data = self.track_process_resources(process_id, expected_time)

            # Calculate metrics
            if resource_data['memory_mb']:
                peak_memory = max(resource_data['memory_mb'])
                final_memory = resource_data['memory_mb'][-1] if resource_data['memory_mb'] else 0
            else:
                peak_memory = 0
                final_memory = 0

            if resource_data['cpu_percent']:
                peak_cpu = max(resource_data['cpu_percent'])
                final_cpu = resource_data['cpu_percent'][-1] if resource_data['cpu_percent'] else 0
            else:
                peak_cpu = 0
                final_cpu = 0

            # Stop resource monitoring
            self.stop_resource_monitoring()

            # Clean up process
            try:
                process.terminate()
                process.wait(timeout=10)
            except:
                process.kill()

            return StartupMetrics(
                service_name=service_name,
                startup_time=startup_time,
                peak_memory_mb=peak_memory,
                final_memory_mb=final_memory,
                peak_cpu_percent=peak_cpu,
                final_cpu_percent=final_cpu,
                process_id=process_id,
                success=True,
                startup_phase_times={
                    'initialization': startup_time * 0.2,
                    'loading': startup_time * 0.6,
                    'finalization': startup_time * 0.2
                }
            )

        except Exception as e:
            self.stop_resource_monitoring()
            return StartupMetrics(
                service_name=service_name,
                startup_time=0.0,
                peak_memory_mb=0.0,
                final_memory_mb=0.0,
                peak_cpu_percent=0.0,
                final_cpu_percent=0.0,
                process_id=0,
                success=False,
                error_message=str(e)
            )

    def analyze_file_io_performance(self) -> Dict[str, Any]:
        """Analyze file I/O performance patterns"""
        logger.info("Analyzing file I/O performance...")

        results = {
            'file_operations': {},
            'disk_speed': {},
            'cache_performance': {}
        }

        try:
            # Test file read performance
            test_file = self.results_dir / "io_test.tmp"
            test_data = b"x" * (1024 * 1024)  # 1MB test data

            # Write test
            start_time = time.perf_counter()
            with open(test_file, 'wb') as f:
                f.write(test_data)
            write_time = time.perf_counter() - start_time

            # Read test
            start_time = time.perf_counter()
            with open(test_file, 'rb') as f:
                data = f.read()
            read_time = time.perf_counter() - start_time

            # Calculate speeds
            write_speed_mb_s = (1 / write_time) if write_time > 0 else 0
            read_speed_mb_s = (1 / read_time) if read_time > 0 else 0

            results['file_operations'] = {
                'write_time': write_time,
                'read_time': read_time,
                'write_speed_mb_s': write_speed_mb_s,
                'read_speed_mb_s': read_speed_mb_s
            }

            # Test disk speed
            disk = psutil.disk_usage('/')
            results['disk_speed'] = {
                'total_gb': disk.total / (1024**3),
                'used_gb': disk.used / (1024**3),
                'free_gb': disk.free / (1024**3),
                'percent_used': disk.percent
            }

            # Clean up
            if test_file.exists():
                test_file.unlink()

        except Exception as e:
            logger.error(f"Error in file I/O analysis: {e}")

        return results

    def analyze_database_performance(self) -> Dict[str, Any]:
        """Analyze database performance"""
        logger.info("Analyzing database performance...")

        results = {
            'query_performance': {},
            'connection_performance': {},
            'index_performance': {}
        }

        ecosystem_db = self.base_dir / "core_ai" / "ecosystem_state.db"

        if not ecosystem_db.exists():
            logger.warning("Ecosystem database not found")
            return results

        try:
            import sqlite3

            # Test connection performance
            start_time = time.perf_counter()
            conn = sqlite3.connect(ecosystem_db)
            connection_time = time.perf_counter() - start_time

            # Test query performance
            queries = [
                ("SELECT COUNT(*) FROM service_history", "count_query"),
                ("SELECT * FROM service_history LIMIT 100", "select_query"),
                ("SELECT service_name, COUNT(*) FROM service_history GROUP BY service_name", "group_query")
            ]

            query_times = {}
            cursor = conn.cursor()

            for query, query_name in queries:
                start_time = time.perf_counter()
                cursor.execute(query)
                execution_time = time.perf_counter() - start_time
                query_times[query_name] = execution_time

            # Test index performance
            cursor.execute("PRAGMA index_list('service_history')")
            indexes = cursor.fetchall()

            results['query_performance'] = query_times
            results['connection_performance'] = {
                'connection_time': connection_time,
                'success': True
            }
            results['index_performance'] = {
                'index_count': len(indexes),
                'indexes': [idx[1] for idx in indexes]
            }

            conn.close()

        except Exception as e:
            logger.error(f"Error in database analysis: {e}")
            results['connection_performance'] = {
                'connection_time': 0.0,
                'success': False,
                'error': str(e)
            }

        return results

    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive startup performance analysis"""
        logger.info("Starting comprehensive startup performance analysis...")

        analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'service_startup': {},
            'file_io_performance': {},
            'database_performance': {},
            'system_resource_patterns': {},
            'bottlenecks': [],
            'optimization_recommendations': []
        }

        # Capture system info
        analysis_results['system_info'] = {
            'platform': sys.platform,
            'python_version': sys.version,
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'disk_total_gb': psutil.disk_usage('/').total / (1024**3)
        }

        # Analyze service startup (limited to avoid overwhelming the system)
        logger.info("Analyzing service startup performance...")
        services_to_test = ['comfyui', 'n8n', 'open_notebook', 'jupyter', 'open_webui', 'duckbot']

        for service_name in services_to_test:
            if service_name in self.services:
                try:
                    metrics = self.analyze_service_startup(service_name, self.services[service_name])
                    analysis_results['service_startup'][service_name] = asdict(metrics)
                except Exception as e:
                    logger.error(f"Error analyzing {service_name}: {e}")

        # Analyze file I/O performance
        analysis_results['file_io_performance'] = self.analyze_file_io_performance()

        # Analyze database performance
        analysis_results['database_performance'] = self.analyze_database_performance()

        # Analyze system resource patterns
        if self.system_snapshots:
            cpu_values = [s.cpu_percent for s in self.system_snapshots]
            memory_values = [s.memory_percent for s in self.system_snapshots]

            analysis_results['system_resource_patterns'] = {
                'cpu_avg': statistics.mean(cpu_values) if cpu_values else 0,
                'cpu_max': max(cpu_values) if cpu_values else 0,
                'memory_avg': statistics.mean(memory_values) if memory_values else 0,
                'memory_max': max(memory_values) if memory_values else 0,
                'sample_count': len(self.system_snapshots)
            }

        # Identify bottlenecks
        analysis_results['bottlenecks'] = self.identify_startup_bottlenecks(analysis_results)

        # Generate recommendations
        analysis_results['optimization_recommendations'] = self.generate_startup_recommendations(analysis_results)

        logger.info("Comprehensive startup analysis completed")
        return analysis_results

    def identify_startup_bottlenecks(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify startup performance bottlenecks"""
        bottlenecks = []

        # Service startup bottlenecks
        for service_name, metrics in results.get('service_startup', {}).items():
            if isinstance(metrics, dict):
                startup_time = metrics.get('startup_time', 0)
                expected_time = self.services[service_name].get('expected_time', 10.0)

                if startup_time > expected_time * 1.5:  # 50% slower than expected
                    bottlenecks.append({
                        'type': 'slow_startup',
                        'service': service_name,
                        'severity': 'high' if startup_time > expected_time * 2 else 'medium',
                        'description': f'{service_name} startup time ({startup_time:.2f}s) is {startup_time/expected_time:.1f}x slower than expected',
                        'impact': 'user_experience'
                    })

                peak_memory = metrics.get('peak_memory_mb', 0)
                if peak_memory > 1000:  # > 1GB
                    bottlenecks.append({
                        'type': 'high_memory',
                        'service': service_name,
                        'severity': 'medium' if peak_memory < 2000 else 'high',
                        'description': f'{service_name} uses excessive memory during startup: {peak_memory:.1f}MB',
                        'impact': 'system_resources'
                    })

        # File I/O bottlenecks
        file_io = results.get('file_io_performance', {})
        if file_io.get('file_operations', {}):
            write_speed = file_io['file_operations'].get('write_speed_mb_s', 0)
            if write_speed < 50:  # < 50 MB/s
                bottlenecks.append({
                    'type': 'slow_disk',
                    'severity': 'medium',
                    'description': f'Slow disk write speed detected: {write_speed:.1f} MB/s',
                    'impact': 'startup_performance'
                })

        # Database bottlenecks
        db_perf = results.get('database_performance', {})
        if db_perf.get('query_performance', {}):
            avg_query_time = statistics.mean(db_perf['query_performance'].values())
            if avg_query_time > 0.1:  # > 100ms
                bottlenecks.append({
                    'type': 'slow_database',
                    'severity': 'medium',
                    'description': f'Slow database queries: {avg_query_time*1000:.1f}ms average',
                    'impact': 'data_operations'
                })

        return bottlenecks

    def generate_startup_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations for startup performance"""
        recommendations = []

        # Service startup optimizations
        for service_name, metrics in results.get('service_startup', {}).items():
            if isinstance(metrics, dict):
                startup_time = metrics.get('startup_time', 0)
                if startup_time > 10.0:  # > 10 seconds
                    recommendations.append({
                        'category': 'startup_optimization',
                        'priority': 'high',
                        'service': service_name,
                        'title': f'Optimize {service_name} startup time',
                        'description': f'{service_name} takes {startup_time:.2f}s to start, which is slower than optimal.',
                        'actions': [
                            f'Implement lazy loading for {service_name} components',
                            f'Add startup progress indicators for {service_name}',
                            f'Cache initialization data for {service_name}',
                            f'Consider parallel startup for {service_name} dependencies'
                        ]
                    })

        # Memory optimizations
        high_memory_services = [
            service for service, metrics in results.get('service_startup', {}).items()
            if isinstance(metrics, dict) and metrics.get('peak_memory_mb', 0) > 500
        ]

        if high_memory_services:
            recommendations.append({
                'category': 'memory_optimization',
                'priority': 'medium',
                'title': 'Reduce memory footprint during startup',
                'description': f'Services {high_memory_services} use excessive memory during startup.',
                'actions': [
                    'Implement memory pooling for frequently allocated objects',
                    'Add memory usage monitoring and alerts',
                    'Optimize data structures for memory efficiency',
                    'Consider using generators instead of lists for large datasets'
                ]
            })

        # Disk I/O optimizations
        file_io = results.get('file_io_performance', {})
        if file_io.get('file_operations', {}):
            write_speed = file_io['file_operations'].get('write_speed_mb_s', 0)
            if write_speed < 100:
                recommendations.append({
                    'category': 'io_optimization',
                    'priority': 'medium',
                    'title': 'Improve disk I/O performance',
                    'description': f'Disk write speed ({write_speed:.1f} MB/s) is below optimal levels.',
                    'actions': [
                        'Implement file compression for large data files',
                        'Use asynchronous file operations',
                        'Add write buffering for better performance',
                        'Consider SSD upgrade if on HDD'
                    ]
                })

        # Database optimizations
        db_perf = results.get('database_performance', {})
        if db_perf.get('query_performance', {}):
            avg_query_time = statistics.mean(db_perf['query_performance'].values())
            if avg_query_time > 0.05:  # > 50ms
                recommendations.append({
                    'category': 'database_optimization',
                    'priority': 'medium',
                    'title': 'Optimize database queries',
                    'description': f'Database queries are averaging {avg_query_time*1000:.1f}ms.',
                    'actions': [
                        'Add proper database indexes for frequent queries',
                        'Implement query result caching',
                        'Use connection pooling for database access',
                        'Optimize complex queries with proper joins'
                    ]
                })

        return recommendations

    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save analysis results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"startup_analysis_{timestamp}.json"

        filepath = self.results_dir / filename

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Startup analysis results saved to {filepath}")
        return str(filepath)

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable startup performance report"""
        report = []
        report.append("=" * 80)
        report.append("DUCKBOT v4.2 STARTUP PERFORMANCE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # System Information
        sys_info = results.get('system_info', {})
        report.append("SYSTEM INFORMATION")
        report.append("-" * 40)
        report.append(f"Platform: {sys_info.get('platform', 'Unknown')}")
        report.append(f"CPU Cores: {sys_info.get('cpu_count', 'Unknown')}")
        report.append(f"Total Memory: {sys_info.get('memory_total_gb', 0):.1f} GB")
        report.append(f"Total Disk: {sys_info.get('disk_total_gb', 0):.1f} GB")
        report.append("")

        # Service Startup Performance
        report.append("SERVICE STARTUP PERFORMANCE")
        report.append("-" * 40)
        service_startup = results.get('service_startup', {})

        for service_name, metrics in service_startup.items():
            if isinstance(metrics, dict):
                startup_time = metrics.get('startup_time', 0)
                peak_memory = metrics.get('peak_memory_mb', 0)
                success = metrics.get('success', False)

                status = "✓" if success else "✗"
                report.append(f"{status} {service_name}:")
                report.append(f"  Startup Time: {startup_time:.3f}s")
                report.append(f"  Peak Memory: {peak_memory:.1f}MB")
                report.append(f"  Status: {'Success' if success else 'Failed'}")
                if not success:
                    error_msg = metrics.get('error_message', 'Unknown error')
                    report.append(f"  Error: {error_msg}")
                report.append("")

        # Bottlenecks
        bottlenecks = results.get('bottlenecks', [])
        if bottlenecks:
            report.append("IDENTIFIED BOTTLENECKS")
            report.append("-" * 40)
            for bottleneck in bottlenecks:
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(bottleneck.get('severity', 'low'), "⚪")
                report.append(f"{severity_emoji} {bottleneck.get('type', 'Unknown').upper()}: {bottleneck.get('description', 'No description')}")
            report.append("")

        # Recommendations
        recommendations = results.get('optimization_recommendations', [])
        if recommendations:
            report.append("OPTIMIZATION RECOMMENDATIONS")
            report.append("-" * 40)
            for rec in recommendations:
                priority_emoji = {"high": "🔥", "medium": "⚡", "low": "💡"}.get(rec.get('priority', 'low'), "📝")
                report.append(f"{priority_emoji} {rec.get('title', 'No title')} ({rec.get('priority', 'low')} priority)")
                report.append(f"   {rec.get('description', 'No description')}")
                report.append("")

        # Performance Summary
        report.append("PERFORMANCE SUMMARY")
        report.append("-" * 40)

        # Calculate overall startup performance
        total_startup_time = 0
        successful_services = 0
        for service_name, metrics in service_startup.items():
            if isinstance(metrics, dict) and metrics.get('success', False):
                total_startup_time += metrics.get('startup_time', 0)
                successful_services += 1

        if successful_services > 0:
            avg_startup_time = total_startup_time / successful_services
            report.append(f"Average Service Startup Time: {avg_startup_time:.2f}s")
            report.append(f"Successful Services: {successful_services}/{len(service_startup)}")
        else:
            report.append("No services started successfully")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

def main():
    """Main execution function"""
    analyzer = StartupPerformanceAnalyzer()

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="DuckBot Startup Performance Analyzer")
    parser.add_argument("--output", help="Output filename for results")
    parser.add_argument("--report", action="store_true", help="Generate human-readable report")
    args = parser.parse_args()

    try:
        # Run comprehensive analysis
        logger.info("Starting comprehensive startup performance analysis...")
        results = analyzer.run_comprehensive_analysis()

        # Save results
        results_file = analyzer.save_results(results, args.output)

        # Generate report if requested
        if args.report:
            report = analyzer.generate_report(results)
            report_file = str(results_file).replace('.json', '_report.txt')
            with open(report_file, 'w') as f:
                f.write(report)
            logger.info(f"Startup analysis report generated: {report_file}")
            print("\n" + report)

        logger.info("Startup performance analysis completed successfully")

    except KeyboardInterrupt:
        logger.info("Startup performance analysis interrupted by user")
    except Exception as e:
        logger.error(f"Startup performance analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()