#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot v4.2 Comprehensive Performance Report Generator
Combines all performance analysis results into a comprehensive report
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import statistics

class ComprehensivePerformanceReporter:
    """Generates comprehensive performance reports for DuckBot v4.2"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.results_dir = self.base_dir / "performance_results"
        self.startup_results_dir = self.base_dir / "startup_analysis"
        self.ai_websocket_results_dir = self.base_dir / "ai_websocket_analysis"

        # Ensure results directories exist
        self.results_dir.mkdir(exist_ok=True)
        self.startup_results_dir.mkdir(exist_ok=True)
        self.ai_websocket_results_dir.mkdir(exist_ok=True)

    def load_json_results(self, directory: Path, pattern: str = "*.json") -> List[Dict[str, Any]]:
        """Load JSON results from directory"""
        results = []
        if directory.exists():
            for file_path in directory.glob(pattern):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        data['_source_file'] = str(file_path)
                        results.append(data)
                except Exception as e:
                    print(f"Warning: Could not load {file_path}: {e}")
        return results

    def extract_system_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract and aggregate system metrics from all results"""
        system_metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': [],
            'network_latency': [],
            'service_uptime': [],
            'error_rates': []
        }

        for result in results:
            # Extract system metrics
            if 'system_metrics' in result:
                for metric in result['system_metrics']:
                    if isinstance(metric, dict):
                        system_metrics['cpu_usage'].append(metric.get('cpu_percent', 0))
                        system_metrics['memory_usage'].append(metric.get('memory_percent', 0))
                        system_metrics['disk_usage'].append(metric.get('disk_usage_percent', 0))

            # Extract service metrics
            if 'service_metrics' in result:
                for service_name, service_data in result['service_metrics'].items():
                    if isinstance(service_data, list) and service_data:
                        latest_metrics = service_data[-1]  # Get latest metrics
                        if isinstance(latest_metrics, dict):
                            system_metrics['error_rates'].append(latest_metrics.get('error_count', 0))

            # Extract network metrics
            if 'network_metrics' in result:
                net_metrics = result['network_metrics']
                if isinstance(net_metrics, dict):
                    system_metrics['network_latency'].append(net_metrics.get('latency_ms', 0))

        return system_metrics

    def extract_service_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract service performance metrics"""
        service_performance = {}

        for result in results:
            # Service startup metrics
            if 'service_startup' in result:
                startup_data = result['service_startup']
                for service_name, metrics in startup_data.items():
                    if service_name not in service_performance:
                        service_performance[service_name] = {
                            'startup_times': [],
                            'memory_usage': [],
                            'success_rate': 0,
                            'error_count': 0
                        }

                    if isinstance(metrics, dict):
                        if 'startup_times' not in service_performance[service_name]:
                            service_performance[service_name]['startup_times'] = []
                        service_performance[service_name]['startup_times'].append(metrics.get('startup_time', 0))
                        service_performance[service_name]['memory_usage'].append(metrics.get('peak_memory_mb', 0))
                        service_performance[service_name]['success_rate'] = 1 if metrics.get('success', False) else 0

            # Service runtime metrics
            if 'service_metrics' in result:
                runtime_data = result['service_metrics']
                for service_name, metrics_list in runtime_data.items():
                    if service_name not in service_performance:
                        service_performance[service_name] = {
                            'response_times': [],
                            'memory_usage': [],
                            'cpu_usage': [],
                            'error_count': 0
                        }

                    if isinstance(metrics_list, list):
                        for metrics in metrics_list:
                            if isinstance(metrics, dict):
                                service_performance[service_name]['response_times'].append(metrics.get('response_time', 0))
                                service_performance[service_name]['memory_usage'].append(metrics.get('memory_mb', 0))
                                service_performance[service_name]['cpu_usage'].append(metrics.get('cpu_percent', 0))
                                service_performance[service_name]['error_count'] += metrics.get('error_count', 0)

        return service_performance

    def extract_ai_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract AI model performance metrics"""
        ai_performance = {}

        for result in results:
            if 'ai_model_performance' in result:
                ai_data = result['ai_model_performance']
                for model_name, metrics in ai_data.items():
                    if model_name not in ai_performance:
                        ai_performance[model_name] = {
                            'load_times': [],
                            'inference_times': [],
                            'error_rates': [],
                            'throughput': [],
                            'memory_usage': []
                        }

                    if isinstance(metrics, dict):
                        ai_performance[model_name]['load_times'].append(metrics.get('load_time', 0))
                        ai_performance[model_name]['inference_times'].extend(metrics.get('inference_times', []))
                        ai_performance[model_name]['error_rates'].append(metrics.get('error_rate', 0))
                        ai_performance[model_name]['throughput'].append(metrics.get('throughput_requests_per_sec', 0))
                        ai_performance[model_name]['memory_usage'].append(metrics.get('memory_usage_mb', 0))

        return ai_performance

    def extract_database_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract database performance metrics"""
        db_performance = {
            'query_times': [],
            'connection_times': [],
            'table_scan_times': [],
            'cache_hit_ratios': []
        }

        for result in results:
            # Database metrics
            if 'database_metrics' in result:
                db_metrics = result['database_metrics']
                if isinstance(db_metrics, dict):
                    db_performance['query_times'].extend(db_metrics.get('query_times', []))
                    db_performance['connection_times'].append(db_metrics.get('connection_time', 0))
                    db_performance['cache_hit_ratios'].append(db_metrics.get('cache_hit_ratio', 0))

                    # Table scan times
                    table_scans = db_metrics.get('table_scan_times', {})
                    if isinstance(table_scans, dict):
                        db_performance['table_scan_times'].extend(table_scans.values())

        return db_performance

    def extract_network_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract network performance metrics"""
        network_performance = {
            'latencies': [],
            'bandwidth': [],
            'connection_times': [],
            'request_times': {}
        }

        for result in results:
            # Network metrics
            if 'network_metrics' in result:
                net_metrics = result['network_metrics']
                if isinstance(net_metrics, dict):
                    network_performance['latencies'].append(net_metrics.get('latency_ms', 0))
                    network_performance['bandwidth'].append(net_metrics.get('bandwidth_mbps', 0))

            # Request times
            if 'request_times' in net_metrics:
                request_times = net_metrics['request_times']
                if isinstance(request_times, dict):
                    for endpoint, times in request_times.items():
                        if endpoint not in network_performance['request_times']:
                            network_performance['request_times'][endpoint] = []
                        network_performance['request_times'][endpoint].extend(times)

        return network_performance

    def calculate_performance_scores(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Calculate performance scores (0-100, higher is better)"""
        scores = {}

        # System performance score
        cpu_usage = metrics.get('system', {}).get('cpu_usage', [])
        memory_usage = metrics.get('system', {}).get('memory_usage', [])
        network_latency = metrics.get('system', {}).get('network_latency', [])

        if cpu_usage:
            cpu_score = max(0, 100 - statistics.mean(cpu_usage))
        else:
            cpu_score = 50

        if memory_usage:
            memory_score = max(0, 100 - statistics.mean(memory_usage))
        else:
            memory_score = 50

        if network_latency:
            latency_score = max(0, 100 - statistics.mean(network_latency) / 2)  # Penalize high latency
        else:
            latency_score = 50

        scores['system'] = (cpu_score + memory_score + latency_score) / 3

        # Service performance score
        service_metrics = metrics.get('services', {})
        service_scores = []

        for service_name, service_data in service_metrics.items():
            startup_times = service_data.get('startup_times', [])
            success_rate = service_data.get('success_rate', 0)

            if startup_times:
                startup_score = max(0, 100 - statistics.mean(startup_times) * 10)  # Penalize slow startup
            else:
                startup_score = 50

            service_score = (startup_score + success_rate * 100) / 2
            service_scores.append(service_score)

        scores['services'] = statistics.mean(service_scores) if service_scores else 50

        # AI performance score
        ai_metrics = metrics.get('ai', {})
        ai_scores = []

        for model_name, model_data in ai_metrics.items():
            load_times = model_data.get('load_times', [])
            inference_times = model_data.get('inference_times', [])
            error_rates = model_data.get('error_rates', [])

            if load_times:
                load_score = max(0, 100 - statistics.mean(load_times) * 5)
            else:
                load_score = 50

            if inference_times:
                inference_score = max(0, 100 - statistics.mean(inference_times) * 10)
            else:
                inference_score = 50

            if error_rates:
                error_score = max(0, 100 - statistics.mean(error_rates))
            else:
                error_score = 50

            model_score = (load_score + inference_score + error_score) / 3
            ai_scores.append(model_score)

        scores['ai'] = statistics.mean(ai_scores) if ai_scores else 50

        # Database performance score
        db_metrics = metrics.get('database', {})
        query_times = db_metrics.get('query_times', [])

        if query_times:
            db_score = max(0, 100 - statistics.mean(query_times) * 1000)  # Penalize slow queries
        else:
            db_score = 50

        scores['database'] = db_score

        # Overall performance score
        scores['overall'] = (scores['system'] + scores['services'] + scores['ai'] + scores['database']) / 4

        return scores

    def generate_bottleneck_analysis(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate bottleneck analysis"""
        bottlenecks = []

        # System bottlenecks
        cpu_usage = metrics.get('system', {}).get('cpu_usage', [])
        memory_usage = metrics.get('system', {}).get('memory_usage', [])

        if cpu_usage and statistics.mean(cpu_usage) > 80:
            bottlenecks.append({
                'type': 'system',
                'component': 'cpu',
                'severity': 'high',
                'description': f'High CPU usage: {statistics.mean(cpu_usage):.1f}% average',
                'impact': 'system_responsiveness'
            })

        if memory_usage and statistics.mean(memory_usage) > 85:
            bottlenecks.append({
                'type': 'system',
                'component': 'memory',
                'severity': 'high',
                'description': f'High memory usage: {statistics.mean(memory_usage):.1f}% average',
                'impact': 'system_stability'
            })

        # Service bottlenecks
        service_metrics = metrics.get('services', {})
        for service_name, service_data in service_metrics.items():
            startup_times = service_data.get('startup_times', [])
            success_rate = service_data.get('success_rate', 0)

            if startup_times and statistics.mean(startup_times) > 5.0:
                bottlenecks.append({
                    'type': 'service',
                    'component': service_name,
                    'severity': 'medium',
                    'description': f'{service_name} has slow startup: {statistics.mean(startup_times):.2f}s average',
                    'impact': 'user_experience'
                })

            if success_rate < 0.8:
                bottlenecks.append({
                    'type': 'service',
                    'component': service_name,
                    'severity': 'high',
                    'description': f'{service_name} has low success rate: {success_rate*100:.1f}%',
                    'impact': 'service_reliability'
                })

        # AI bottlenecks
        ai_metrics = metrics.get('ai', {})
        for model_name, model_data in ai_metrics.items():
            load_times = model_data.get('load_times', [])
            inference_times = model_data.get('inference_times', [])
            error_rates = model_data.get('error_rates', [])

            if load_times and statistics.mean(load_times) > 10.0:
                bottlenecks.append({
                    'type': 'ai',
                    'component': model_name,
                    'severity': 'high',
                    'description': f'{model_name} has slow load time: {statistics.mean(load_times):.2f}s average',
                    'impact': 'startup_performance'
                })

            if inference_times and statistics.mean(inference_times) > 3.0:
                bottlenecks.append({
                    'type': 'ai',
                    'component': model_name,
                    'severity': 'medium',
                    'description': f'{model_name} has slow inference: {statistics.mean(inference_times):.2f}s average',
                    'impact': 'user_experience'
                })

            if error_rates and statistics.mean(error_rates) > 10.0:
                bottlenecks.append({
                    'type': 'ai',
                    'component': model_name,
                    'severity': 'high',
                    'description': f'{model_name} has high error rate: {statistics.mean(error_rates):.1f}%',
                    'impact': 'service_reliability'
                })

        # Database bottlenecks
        db_metrics = metrics.get('database', {})
        query_times = db_metrics.get('query_times', [])

        if query_times and statistics.mean(query_times) > 0.1:
            bottlenecks.append({
                'type': 'database',
                'component': 'queries',
                'severity': 'medium',
                'description': f'Slow database queries: {statistics.mean(query_times)*1000:.1f}ms average',
                'impact': 'data_operations'
            })

        return bottlenecks

    def generate_recommendations(self, bottlenecks: List[Dict[str, Any]], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        recommendations = []

        # System optimization recommendations
        system_bottlenecks = [b for b in bottlenecks if b['type'] == 'system']
        if system_bottlenecks:
            recommendations.append({
                'category': 'system_optimization',
                'priority': 'high',
                'title': 'Optimize System Resource Usage',
                'description': 'High system resource usage detected affecting overall performance.',
                'actions': [
                    'Implement resource monitoring and alerting',
                    'Optimize service resource allocation',
                    'Consider load balancing for high-traffic services',
                    'Implement auto-scaling based on resource usage'
                ],
                'expected_improvement': '20-40% performance increase'
            })

        # Service optimization recommendations
        service_bottlenecks = [b for b in bottlenecks if b['type'] == 'service']
        if service_bottlenecks:
            recommendations.append({
                'category': 'service_optimization',
                'priority': 'high',
                'title': 'Improve Service Performance and Reliability',
                'description': 'Service performance and reliability issues detected.',
                'actions': [
                    'Implement service health monitoring',
                    'Add automatic service recovery mechanisms',
                    'Optimize service startup processes',
                    'Implement proper error handling and logging'
                ],
                'expected_improvement': '30-50% service reliability improvement'
            })

        # AI optimization recommendations
        ai_bottlenecks = [b for b in bottlenecks if b['type'] == 'ai']
        if ai_bottlenecks:
            recommendations.append({
                'category': 'ai_optimization',
                'priority': 'medium',
                'title': 'Optimize AI Model Performance',
                'description': 'AI model performance issues detected affecting user experience.',
                'actions': [
                    'Implement model caching and pre-loading',
                    'Use model quantization and optimization',
                    'Add request batching and queuing',
                    'Consider using smaller, faster models for common queries'
                ],
                'expected_improvement': '40-60% AI response time improvement'
            })

        # Database optimization recommendations
        db_bottlenecks = [b for b in bottlenecks if b['type'] == 'database']
        if db_bottlenecks:
            recommendations.append({
                'category': 'database_optimization',
                'priority': 'medium',
                'title': 'Optimize Database Performance',
                'description': 'Database performance issues detected affecting data operations.',
                'actions': [
                    'Add proper database indexes',
                    'Implement query result caching',
                    'Use connection pooling',
                    'Optimize complex queries and joins'
                ],
                'expected_improvement': '50-70% database query performance improvement'
            })

        # General performance recommendations
        recommendations.append({
            'category': 'general_optimization',
            'priority': 'medium',
            'title': 'Implement Performance Monitoring',
            'description': 'Comprehensive performance monitoring is essential for maintaining optimal performance.',
            'actions': [
                'Set up continuous performance monitoring',
                'Implement automated performance testing',
                'Add performance metrics to dashboards',
                'Establish performance baselines and alerts'
            ],
            'expected_improvement': 'Proactive performance management'
        })

        return recommendations

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        print("Loading performance analysis results...")

        # Load all results
        general_results = self.load_json_results(self.results_dir)
        startup_results = self.load_json_results(self.startup_results_dir)
        ai_websocket_results = self.load_json_results(self.ai_websocket_results_dir)

        all_results = general_results + startup_results + ai_websocket_results

        if not all_results:
            print("No performance results found. Please run performance analysis first.")
            return {}

        print(f"Loaded {len(all_results)} result files")

        # Extract metrics
        print("Extracting performance metrics...")
        system_metrics = self.extract_system_metrics(all_results)
        service_performance = self.extract_service_performance(all_results)
        ai_performance = self.extract_ai_performance(all_results)
        database_performance = self.extract_database_performance(all_results)
        network_performance = self.extract_network_performance(all_results)

        # Combine all metrics
        combined_metrics = {
            'system': system_metrics,
            'services': service_performance,
            'ai': ai_performance,
            'database': database_performance,
            'network': network_performance
        }

        # Calculate performance scores
        print("Calculating performance scores...")
        performance_scores = self.calculate_performance_scores(combined_metrics)

        # Generate bottleneck analysis
        print("Analyzing performance bottlenecks...")
        bottlenecks = self.generate_bottleneck_analysis(combined_metrics)

        # Generate recommendations
        print("Generating optimization recommendations...")
        recommendations = self.generate_recommendations(bottlenecks, combined_metrics)

        # Create comprehensive report
        report = {
            'timestamp': datetime.now().isoformat(),
            'report_version': '1.0',
            'analysis_summary': {
                'total_result_files': len(all_results),
                'analysis_duration': '60 seconds per test',
                'services_analyzed': len(service_performance),
                'ai_models_analyzed': len(ai_performance),
                'bottlenecks_identified': len(bottlenecks),
                'recommendations_generated': len(recommendations)
            },
            'performance_metrics': combined_metrics,
            'performance_scores': performance_scores,
            'bottlenecks': bottlenecks,
            'optimization_recommendations': recommendations,
            'executive_summary': self.generate_executive_summary(performance_scores, bottlenecks, recommendations)
        }

        return report

    def generate_executive_summary(self, scores: Dict[str, float], bottlenecks: List[Dict[str, Any]], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate executive summary"""
        # Calculate overall health
        overall_score = scores.get('overall', 0)
        health_status = "Excellent" if overall_score >= 80 else "Good" if overall_score >= 60 else "Fair" if overall_score >= 40 else "Poor"

        # Count bottlenecks by severity
        high_severity = len([b for b in bottlenecks if b.get('severity') == 'high'])
        medium_severity = len([b for b in bottlenecks if b.get('severity') == 'medium'])
        low_severity = len([b for b in bottlenecks if b.get('severity') == 'low'])

        # Count recommendations by priority
        high_priority = len([r for r in recommendations if r.get('priority') == 'high'])
        medium_priority = len([r for r in recommendations if r.get('priority') == 'medium'])
        low_priority = len([r for r in recommendations if r.get('priority') == 'low'])

        return {
            'overall_health': health_status,
            'overall_score': overall_score,
            'key_findings': [
                f"Overall system health: {health_status} ({overall_score:.1f}/100)",
                f"Total bottlenecks identified: {len(bottlenecks)} ({high_severity} high, {medium_severity} medium, {low_severity} low)",
                f"Optimization recommendations: {len(recommendations)} ({high_priority} high priority, {medium_priority} medium priority)",
                f"System performance score: {scores.get('system', 0):.1f}/100",
                f"Service performance score: {scores.get('services', 0):.1f}/100",
                f"AI performance score: {scores.get('ai', 0):.1f}/100",
                f"Database performance score: {scores.get('database', 0):.1f}/100"
            ],
            'critical_issues': [b for b in bottlenecks if b.get('severity') == 'high'],
            'top_recommendations': [r for r in recommendations if r.get('priority') == 'high'][:3]
        }

    def generate_human_readable_report(self, report: Dict[str, Any]) -> str:
        """Generate human-readable report"""
        lines = []
        lines.append("=" * 80)
        lines.append("DUCKBOT v4.2 COMPREHENSIVE PERFORMANCE PROFILE REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Report Version: {report.get('report_version', '1.0')}")
        lines.append("")

        # Executive Summary
        exec_summary = report.get('executive_summary', {})
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Overall System Health: {exec_summary.get('overall_health', 'Unknown')}")
        lines.append(f"Overall Performance Score: {exec_summary.get('overall_score', 0):.1f}/100")
        lines.append("")

        lines.append("KEY FINDINGS")
        for finding in exec_summary.get('key_findings', []):
            lines.append(f"• {finding}")
        lines.append("")

        # Performance Scores
        lines.append("PERFORMANCE SCORES")
        lines.append("-" * 40)
        scores = report.get('performance_scores', {})
        for category, score in scores.items():
            if category != 'overall':
                lines.append(f"{category.replace('_', ' ').title()}: {score:.1f}/100")
        lines.append(f"Overall: {scores.get('overall', 0):.1f}/100")
        lines.append("")

        # Bottlenecks
        bottlenecks = report.get('bottlenecks', [])
        if bottlenecks:
            lines.append("IDENTIFIED BOTTLENECKS")
            lines.append("-" * 40)
            for bottleneck in bottlenecks:
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(bottleneck.get('severity', 'low'), "⚪")
                lines.append(f"{severity_emoji} {bottleneck.get('type', 'Unknown').upper()} - {bottleneck.get('component', 'Unknown')}")
                lines.append(f"   {bottleneck.get('description', 'No description')}")
                lines.append(f"   Impact: {bottleneck.get('impact', 'Unknown')}")
                lines.append("")
        else:
            lines.append("No significant bottlenecks identified.")
            lines.append("")

        # Recommendations
        recommendations = report.get('optimization_recommendations', [])
        if recommendations:
            lines.append("OPTIMIZATION RECOMMENDATIONS")
            lines.append("-" * 40)
            for rec in recommendations:
                priority_emoji = {"high": "🔥", "medium": "⚡", "low": "💡"}.get(rec.get('priority', 'low'), "📝")
                lines.append(f"{priority_emoji} {rec.get('title', 'No title')} ({rec.get('priority', 'low')} priority)")
                lines.append(f"   {rec.get('description', 'No description')}")
                lines.append(f"   Expected Improvement: {rec.get('expected_improvement', 'Unknown')}")
                lines.append("   Actions:")
                for action in rec.get('actions', []):
                    lines.append(f"   - {action}")
                lines.append("")
        else:
            lines.append("No optimization recommendations at this time.")
            lines.append("")

        # Detailed Metrics
        lines.append("DETAILED PERFORMANCE METRICS")
        lines.append("-" * 40)

        # System Metrics
        system_metrics = report.get('performance_metrics', {}).get('system', {})
        if system_metrics.get('cpu_usage'):
            lines.append(f"System CPU Usage: {statistics.mean(system_metrics['cpu_usage']):.1f}% average")
        if system_metrics.get('memory_usage'):
            lines.append(f"System Memory Usage: {statistics.mean(system_metrics['memory_usage']):.1f}% average")
        if system_metrics.get('network_latency'):
            lines.append(f"Network Latency: {statistics.mean(system_metrics['network_latency']):.1f}ms average")
        lines.append("")

        # Service Metrics
        service_metrics = report.get('performance_metrics', {}).get('services', {})
        if service_metrics:
            lines.append("Service Performance:")
            for service_name, service_data in service_metrics.items():
                startup_times = service_data.get('startup_times', [])
                if startup_times:
                    lines.append(f"  {service_name}:")
                    lines.append(f"    Average Startup Time: {statistics.mean(startup_times):.2f}s")
                    lines.append(f"    Success Rate: {service_data.get('success_rate', 0)*100:.1f}%")
            lines.append("")

        # AI Metrics
        ai_metrics = report.get('performance_metrics', {}).get('ai', {})
        if ai_metrics:
            lines.append("AI Model Performance:")
            for model_name, model_data in ai_metrics.items():
                load_times = model_data.get('load_times', [])
                inference_times = model_data.get('inference_times', [])
                if load_times:
                    lines.append(f"  {model_name}:")
                    lines.append(f"    Average Load Time: {statistics.mean(load_times):.2f}s")
                    if inference_times:
                        lines.append(f"    Average Inference Time: {statistics.mean(inference_times):.2f}s")
            lines.append("")

        # Database Metrics
        db_metrics = report.get('performance_metrics', {}).get('database', {})
        if db_metrics.get('query_times'):
            lines.append(f"Database Query Performance: {statistics.mean(db_metrics['query_times'])*1000:.1f}ms average")
        lines.append("")

        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)

    def save_report(self, report: Dict[str, Any], human_readable: bool = True) -> Dict[str, str]:
        """Save comprehensive report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON report
        json_file = self.results_dir / f"comprehensive_performance_report_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        saved_files = {'json': str(json_file)}

        # Save human-readable report
        if human_readable:
            txt_file = self.results_dir / f"comprehensive_performance_report_{timestamp}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(self.generate_human_readable_report(report))
            saved_files['txt'] = str(txt_file)

        return saved_files

def main():
    """Main execution function"""
    reporter = ComprehensivePerformanceReporter()

    try:
        print("Generating comprehensive performance report...")
        report = reporter.generate_comprehensive_report()

        if not report:
            print("No performance data available for report generation.")
            return

        # Save report
        saved_files = reporter.save_report(report)

        print(f"Comprehensive performance report generated successfully!")
        print(f"JSON Report: {saved_files['json']}")
        if 'txt' in saved_files:
            print(f"Human-readable Report: {saved_files['txt']}")

        # Print executive summary
        exec_summary = report.get('executive_summary', {})
        print(f"\nEXECUTIVE SUMMARY:")
        print(f"Overall Health: {exec_summary.get('overall_health', 'Unknown')}")
        print(f"Overall Score: {exec_summary.get('overall_score', 0):.1f}/100")
        print(f"Bottlenecks: {len(report.get('bottlenecks', []))} identified")
        print(f"Recommendations: {len(report.get('optimization_recommendations', []))} generated")

    except Exception as e:
        print(f"Error generating comprehensive performance report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()