#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot AI Knowledge Base
Comprehensive knowledge base for AI system management, monitoring, and maintenance
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import sqlite3
import os
from pathlib import Path
import yaml
import hashlib

# Local imports
from duckbot.core.ai_system_controller import get_ai_controller
from duckbot.core.monitoring_system import get_monitoring
from duckbot.core.health_predictive_maintenance import PredictiveMaintenanceSystem

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    PROCEDURE = "procedure"
    BEST_PRACTICE = "best_practice"
    TROUBLESHOOTING = "troubleshooting"
    OPTIMIZATION = "optimization"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    MAINTENANCE = "maintenance"
    PERFORMANCE = "performance"
    ERROR_HANDLING = "error_handling"
    RECOVERY = "recovery"

class KnowledgeLevel(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class KnowledgeStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    REVIEW_NEEDED = "review_needed"

@dataclass
class KnowledgeEntry:
    """Individual knowledge base entry"""
    id: str
    title: str
    content: str
    type: KnowledgeType
    level: KnowledgeLevel
    status: KnowledgeStatus
    tags: List[str]
    category: str
    subcategory: str
    prerequisites: List[str]
    related_entries: List[str]
    created_at: datetime
    updated_at: datetime
    author: str
    effectiveness_score: float
    usage_count: int
    last_used: datetime
    metadata: Dict[str, Any]

@dataclass
class KnowledgeQuery:
    """Query for knowledge base search"""
    query_text: str
    knowledge_types: List[KnowledgeType] = None
    categories: List[str] = None
    tags: List[str] = None
    level_filter: KnowledgeLevel = None
    status_filter: KnowledgeStatus = None
    limit: int = 10
    include_metadata: bool = False

@dataclass
class KnowledgeSearchResult:
    """Result of knowledge base search"""
    entries: List[KnowledgeEntry]
    total_results: int
    query_time_ms: float
    relevance_scores: Dict[str, float]
    suggestions: List[str]

class AIKnowledgeBase:
    """Comprehensive AI knowledge base for system management"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.getcwd(), "ai_knowledge_base.db")

        self.db_path = db_path
        self.embedding_cache = {}
        self.usage_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "avg_query_time": 0.0,
            "most_accessed_entries": [],
            "knowledge_gaps": []
        }

        self._init_database()
        self._load_knowledge_graph()
        self._populate_initial_knowledge()

        logger.info("AI Knowledge Base initialized")

    def _init_database(self):
        """Initialize knowledge base database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Knowledge entries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_entries (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    type TEXT NOT NULL,
                    level TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tags TEXT,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    prerequisites TEXT,
                    related_entries TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    author TEXT NOT NULL,
                    effectiveness_score REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    last_used DATETIME,
                    metadata TEXT
                )
            ''')

            # Knowledge usage table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id TEXT NOT NULL,
                    query_text TEXT,
                    success BOOLEAN NOT NULL,
                    execution_time_ms REAL,
                    user_satisfaction INTEGER,
                    timestamp DATETIME NOT NULL,
                    context TEXT,
                    FOREIGN KEY (entry_id) REFERENCES knowledge_entries (id)
                )
            ''')

            # Knowledge relationships table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_entry_id TEXT NOT NULL,
                    target_entry_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    strength REAL NOT NULL,
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY (source_entry_id) REFERENCES knowledge_entries (id),
                    FOREIGN KEY (target_entry_id) REFERENCES knowledge_entries (id)
                )
            ''')

            # Knowledge gaps table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_gaps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT NOT NULL,
                    gap_description TEXT NOT NULL,
                    category TEXT,
                    priority TEXT NOT NULL,
                    suggested_knowledge TEXT,
                    created_at DATETIME NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at DATETIME
                )
            ''')

            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_entries_type ON knowledge_entries(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_entries_category ON knowledge_entries(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_entries_tags ON knowledge_entries(tags)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_usage_entry_id ON knowledge_usage(entry_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_usage_timestamp ON knowledge_usage(timestamp)')

            conn.commit()

    def _load_knowledge_graph(self):
        """Load knowledge graph for relationships"""
        self.knowledge_graph = {}
        self.category_index = {}
        self.tag_index = {}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM knowledge_entries WHERE status = ?', ('active',))

            for row in cursor.fetchall():
                entry = self._row_to_knowledge_entry(row)
                self.knowledge_graph[entry.id] = entry

                # Update category index
                if entry.category not in self.category_index:
                    self.category_index[entry.category] = []
                self.category_index[entry.category].append(entry.id)

                # Update tag index
                for tag in entry.tags:
                    if tag not in self.tag_index:
                        self.tag_index[tag] = []
                    self.tag_index[tag].append(entry.id)

    def _row_to_knowledge_entry(self, row) -> KnowledgeEntry:
        """Convert database row to KnowledgeEntry"""
        return KnowledgeEntry(
            id=row[0],
            title=row[1],
            content=row[2],
            type=KnowledgeType(row[3]),
            level=KnowledgeLevel(row[4]),
            status=KnowledgeStatus(row[5]),
            tags=json.loads(row[6]) if row[6] else [],
            category=row[7],
            subcategory=row[8],
            prerequisites=json.loads(row[9]) if row[9] else [],
            related_entries=json.loads(row[10]) if row[10] else [],
            created_at=datetime.fromisoformat(row[11]),
            updated_at=datetime.fromisoformat(row[12]),
            author=row[13],
            effectiveness_score=row[14],
            usage_count=row[15],
            last_used=datetime.fromisoformat(row[16]) if row[16] else None,
            metadata=json.loads(row[17]) if row[17] else {}
        )

    def _populate_initial_knowledge(self):
        """Populate knowledge base with initial system management knowledge"""
        if len(self.knowledge_graph) > 0:
            return  # Knowledge base already populated

        logger.info("Populating initial knowledge base...")

        initial_knowledge = self._get_initial_knowledge_entries()

        for entry_data in initial_knowledge:
            self.add_knowledge_entry(entry_data)

        logger.info(f"Added {len(initial_knowledge)} initial knowledge entries")

    def _get_initial_knowledge_entries(self) -> List[Dict[str, Any]]:
        """Get initial knowledge entries for system management"""
        return [
            {
                "title": "System Health Monitoring Procedures",
                "content": self._get_system_health_monitoring_content(),
                "type": KnowledgeType.PROCEDURE,
                "level": KnowledgeLevel.INTERMEDIATE,
                "category": "monitoring",
                "subcategory": "health",
                "tags": ["monitoring", "health", "system", "procedures"],
                "prerequisites": [],
                "related_entries": []
            },
            {
                "title": "Performance Optimization Best Practices",
                "content": self._get_performance_optimization_content(),
                "type": KnowledgeType.BEST_PRACTICE,
                "level": KnowledgeLevel.ADVANCED,
                "category": "optimization",
                "subcategory": "performance",
                "tags": ["optimization", "performance", "best_practices", "system"],
                "prerequisites": ["system_health_monitoring"],
                "related_entries": []
            },
            {
                "title": "Error Recovery Protocols",
                "content": self._get_error_recovery_content(),
                "type": KnowledgeType.RECOVERY,
                "level": KnowledgeLevel.INTERMEDIATE,
                "category": "error_handling",
                "subcategory": "recovery",
                "tags": ["error", "recovery", "protocols", "troubleshooting"],
                "prerequisites": ["system_health_monitoring"],
                "related_entries": []
            },
            {
                "title": "Service Management Guidelines",
                "content": self._get_service_management_content(),
                "type": KnowledgeType.PROCEDURE,
                "level": KnowledgeLevel.BASIC,
                "category": "services",
                "subcategory": "management",
                "tags": ["services", "management", "guidelines", "procedures"],
                "prerequisites": [],
                "related_entries": []
            },
            {
                "title": "Resource Management Strategies",
                "content": self._get_resource_management_content(),
                "type": KnowledgeType.OPTIMIZATION,
                "level": KnowledgeLevel.ADVANCED,
                "category": "optimization",
                "subcategory": "resources",
                "tags": ["resources", "management", "optimization", "strategies"],
                "prerequisites": ["service_management"],
                "related_entries": []
            },
            {
                "title": "Predictive Maintenance Procedures",
                "content": self._get_predictive_maintenance_content(),
                "type": KnowledgeType.MAINTENANCE,
                "level": KnowledgeLevel.EXPERT,
                "category": "maintenance",
                "subcategory": "predictive",
                "tags": ["maintenance", "predictive", "procedures", "automation"],
                "prerequisites": ["system_health_monitoring", "performance_optimization"],
                "related_entries": []
            },
            {
                "title": "Security Hardening Guidelines",
                "content": self._get_security_hardening_content(),
                "type": KnowledgeType.SECURITY,
                "level": KnowledgeLevel.ADVANCED,
                "category": "security",
                "subcategory": "hardening",
                "tags": ["security", "hardening", "guidelines", "protection"],
                "prerequisites": [],
                "related_entries": []
            },
            {
                "title": "Troubleshooting Common Issues",
                "content": self._get_troubleshooting_content(),
                "type": KnowledgeType.TROUBLESHOOTING,
                "level": KnowledgeLevel.INTERMEDIATE,
                "category": "troubleshooting",
                "subcategory": "common_issues",
                "tags": ["troubleshooting", "issues", "common", "solutions"],
                "prerequisites": ["system_health_monitoring", "error_recovery"],
                "related_entries": []
            }
        ]

    def _get_system_health_monitoring_content(self) -> str:
        """Get content for system health monitoring procedures"""
        return """
# System Health Monitoring Procedures

## Overview
Continuous system health monitoring is essential for maintaining optimal DuckBot performance and preventing issues before they impact users.

## Key Metrics to Monitor
- **CPU Usage**: Maintain below 80% for normal operations
- **Memory Usage**: Keep below 85% to ensure responsive performance
- **Disk Usage**: Monitor for available space and I/O performance
- **Network Health**: Check latency, bandwidth, and packet loss
- **Service Status**: All critical services should be running and responsive
- **Error Rates**: Monitor application and system error rates
- **Response Times**: Track API and service response times

## Monitoring Procedures
1. **Continuous Monitoring**: Use the monitoring system to collect metrics every 5-30 seconds
2. **Alert Thresholds**: Set appropriate thresholds for different metrics
3. **Health Checks**: Perform regular health checks on all services
4. **Performance Analysis**: Analyze trends and identify patterns
5. **Resource Optimization**: Monitor resource usage and optimize as needed

## Alert Response
- **Critical Alerts**: Immediate response required (within 5 minutes)
- **Warning Alerts**: Respond within 30 minutes
- **Info Alerts**: Review and address during regular maintenance

## Best Practices
- Implement automated alerting for critical issues
- Regular review and adjustment of monitoring thresholds
- Keep monitoring data for historical analysis
- Use predictive analytics to identify potential issues
"""

    def _get_performance_optimization_content(self) -> str:
        """Get content for performance optimization best practices"""
        return """
# Performance Optimization Best Practices

## System Performance Optimization
Optimize overall system performance through systematic analysis and improvement.

## CPU Optimization
1. **Identify CPU-Intensive Processes**: Monitor CPU usage by process
2. **Optimize Code**: Review and optimize CPU-intensive code paths
3. **Load Balancing**: Distribute workload across available resources
4. **Caching**: Implement caching for frequently accessed data
5. **Background Processing**: Move non-critical processing to background jobs

## Memory Optimization
1. **Memory Leaks**: Identify and fix memory leaks in applications
2. **Garbage Collection**: Optimize garbage collection settings
3. **Memory Pooling**: Use memory pooling for frequently allocated objects
4. **Cache Management**: Implement intelligent cache eviction policies
5. **Database Optimization**: Optimize database queries and memory usage

## I/O Optimization
1. **Disk I/O**: Optimize disk access patterns and use SSD storage
2. **Network I/O**: Minimize network calls and use connection pooling
3. **Buffer Management**: Use appropriate buffer sizes for I/O operations
4. **Async Processing**: Use asynchronous I/O for better performance
5. **Compression**: Compress data to reduce I/O overhead

## Database Optimization
1. **Query Optimization**: Analyze and optimize slow queries
2. **Index Management**: Create and maintain appropriate indexes
3. **Connection Pooling**: Use database connection pooling
4. **Caching**: Implement query result caching
5. **Database Maintenance**: Regular maintenance and optimization

## AI Model Optimization
1. **Model Selection**: Choose appropriate models for specific tasks
2. **Quantization**: Use quantized models for better performance
3. **Batch Processing**: Process multiple requests in batches
4. **Model Caching**: Cache frequently used models in memory
5. **Resource Allocation**: Allocate appropriate resources for AI models

## Monitoring and Analysis
1. **Performance Metrics**: Continuously monitor key performance indicators
2. **Bottleneck Analysis**: Identify and address performance bottlenecks
3. **Trend Analysis**: Analyze performance trends over time
4. **Capacity Planning**: Plan for future capacity requirements
5. **Benchmarking**: Regular performance benchmarking and comparison

## Continuous Improvement
1. **Regular Reviews**: Regular performance reviews and optimization
2. **A/B Testing**: Test optimization strategies before deployment
3. **Rollback Plans**: Have rollback plans for performance changes
4. **Documentation**: Document all optimization procedures
5. **Training**: Train team on performance optimization techniques
"""

    def _get_error_recovery_content(self) -> str:
        """Get content for error recovery protocols"""
        return """
# Error Recovery Protocols

## Error Management Strategy
Implement systematic error recovery to minimize downtime and maintain service availability.

## Error Classification
1. **Critical Errors**: System down, data loss, security breaches
2. **Major Errors**: Service degradation, partial functionality loss
3. **Minor Errors**: Non-critical issues, temporary glitches
4. **Warnings**: Potential issues that need attention

## Recovery Procedures

### Critical Error Recovery
1. **Immediate Assessment**: Determine scope and impact
2. **Stabilization**: Prevent further damage
3. **Recovery Plan**: Execute recovery procedures
4. **Verification**: Confirm system stability
5. **Post-Mortem**: Analyze root cause and implement prevention

### Service Recovery
1. **Health Check**: Verify service status
2. **Restart Service**: If unresponsive, restart the service
3. **Configuration Check**: Verify service configuration
4. **Log Analysis**: Analyze logs for error patterns
5. **Monitor**: Monitor service after recovery

### Data Recovery
1. **Backup Assessment**: Check available backups
2. **Data Restoration**: Restore from appropriate backup
3. **Data Validation**: Verify data integrity
4. **Service Restart**: Restart affected services
5. **Monitoring**: Monitor for data consistency issues

## Error Prevention
1. **Redundancy**: Implement redundancy for critical components
2. **Monitoring**: Comprehensive monitoring and alerting
3. **Testing**: Regular testing of recovery procedures
4. **Documentation**: Maintain up-to-date recovery documentation
5. **Training**: Regular training for recovery procedures

## Automation
1. **Auto-Restart**: Configure automatic service restart
2. **Auto-Failover**: Implement automatic failover mechanisms
3. **Auto-Scaling**: Implement automatic scaling for load handling
4. **Auto-Healing**: Implement self-healing capabilities
5. **Auto-Alerting**: Configure automatic alerting for issues

## Communication
1. **Stakeholder Notification**: Notify stakeholders of critical issues
2. **Status Updates**: Provide regular status updates during recovery
3. **Incident Reports**: Document all incidents and recovery actions
4. **Lessons Learned**: Share lessons learned from incidents
5. **Process Improvement**: Continuously improve recovery processes

## Tools and Resources
1. **Monitoring Tools**: Use comprehensive monitoring tools
2. **Log Management**: Centralized log management and analysis
3. **Backup Systems**: Reliable backup and recovery systems
4. **Automation Tools**: Use automation tools for recovery procedures
5. **Documentation**: Maintain detailed recovery documentation
"""

    def _get_service_management_content(self) -> str:
        """Get content for service management guidelines"""
        return """
# Service Management Guidelines

## Service Lifecycle Management
Manage DuckBot services throughout their lifecycle for optimal performance and reliability.

## Service Categories
1. **Core Services**: Essential system services (monitoring, AI, database)
2. **Application Services**: User-facing applications and APIs
3. **Support Services**: Supporting services (caching, messaging, storage)
4. **External Services**: Third-party integrations and dependencies

## Service Deployment
1. **Planning**: Plan deployment strategy and timeline
2. **Testing**: Test in staging environment before production
3. **Deployment**: Deploy using automated deployment tools
4. **Verification**: Verify service health after deployment
5. **Monitoring**: Monitor service performance and health

## Service Monitoring
1. **Health Checks**: Implement comprehensive health checks
2. **Metrics Collection**: Collect key performance metrics
3. **Alerting**: Configure appropriate alerting thresholds
4. **Logging**: Maintain comprehensive service logs
5. **Dashboards**: Create monitoring dashboards

## Service Scaling
1. **Vertical Scaling**: Increase resources for existing instances
2. **Horizontal Scaling**: Add more instances for load distribution
3. **Auto-Scaling**: Configure automatic scaling based on demand
4. **Load Balancing**: Implement load balancing for service instances
5. **Capacity Planning**: Plan for future capacity requirements

## Service Maintenance
1. **Regular Updates**: Schedule regular service updates and patches
2. **Maintenance Windows**: Plan maintenance during low-traffic periods
3. **Rolling Updates**: Implement rolling updates to minimize downtime
4. **Backout Plans**: Have rollback plans for failed updates
5. **Communication**: Communicate maintenance schedules to stakeholders

## Service Troubleshooting
1. **Symptom Analysis**: Analyze service issues and symptoms
2. **Log Analysis**: Review service logs for error patterns
3. **Resource Analysis**: Check resource usage and availability
4. **Dependency Analysis**: Check service dependencies
5. **Resolution**: Implement and test resolution

## Service Documentation
1. **Service Catalog**: Maintain comprehensive service catalog
2. **Runbooks**: Create detailed runbooks for service operations
3. **API Documentation**: Maintain up-to-date API documentation
4. **Configuration**: Document service configurations
5. **Dependencies**: Document service dependencies

## Service Security
1. **Access Control**: Implement proper access controls
2. **Authentication**: Configure proper authentication mechanisms
3. **Authorization**: Implement authorization policies
4. **Encryption**: Use encryption for sensitive data
5. **Security Audits**: Regular security audits and assessments
"""

    def _get_resource_management_content(self) -> str:
        """Get content for resource management strategies"""
        return """
# Resource Management Strategies

## Resource Optimization Overview
Optimize system resource usage to ensure efficient operation and cost-effectiveness.

## CPU Resource Management
1. **Process Prioritization**: Prioritize critical processes
2. **CPU Affinity**: Set CPU affinity for performance-critical processes
3. **Load Balancing**: Distribute CPU load across available cores
4. **Throttling**: Implement CPU throttling for non-critical processes
5. **Scheduling**: Use intelligent scheduling for CPU-intensive tasks

## Memory Resource Management
1. **Memory Allocation**: Optimize memory allocation strategies
2. **Garbage Collection**: Configure appropriate garbage collection
3. **Memory Pooling**: Use memory pools for frequently allocated objects
4. **Cache Management**: Implement intelligent cache management
5. **Swap Management**: Optimize swap usage and configuration

## Storage Resource Management
1. **Storage Allocation**: Plan storage allocation for different data types
2. **I/O Optimization**: Optimize I/O operations and storage access
3. **Data Tiering**: Implement data tiering based on access patterns
4. **Backup Management**: Optimize backup storage and retention
5. **Storage Monitoring**: Monitor storage performance and capacity

## Network Resource Management
1. **Bandwidth Allocation**: Allocate bandwidth based on priority
2. **Connection Management**: Optimize connection pooling and reuse
3. **Traffic Shaping**: Implement traffic shaping and QoS
4. **Network Monitoring**: Monitor network performance and health
5. **CDN Usage**: Use CDN for content delivery optimization

## Database Resource Management
1. **Connection Pooling**: Use database connection pooling
2. **Query Optimization**: Optimize database queries for performance
3. **Index Management**: Maintain optimal database indexes
4. **Partitioning**: Implement database partitioning for large datasets
5. **Caching**: Implement database query caching

## AI Model Resource Management
1. **Model Selection**: Choose appropriate models based on resource constraints
2. **Model Quantization**: Use quantized models for better resource efficiency
3. **Batch Processing**: Process multiple requests in batches
4. **Model Caching**: Cache frequently used models
5. **Resource Scheduling**: Schedule AI model usage based on resource availability

## Cost Optimization
1. **Resource Rightsizing**: Regular review and optimization of resource allocation
2. **Spot Instances**: Use spot instances for non-critical workloads
3. **Reserved Instances**: Use reserved instances for predictable workloads
4. **Auto-Scaling**: Implement auto-scaling to match demand
5. **Cost Monitoring**: Monitor and track resource costs

## Monitoring and Analytics
1. **Resource Utilization**: Monitor resource utilization patterns
2. **Performance Metrics**: Track key performance indicators
3. **Capacity Planning**: Plan for future resource requirements
4. **Cost Analysis**: Analyze resource costs and optimization opportunities
5. **Trend Analysis**: Identify resource usage trends and patterns

## Best Practices
1. **Resource Tagging**: Use consistent resource tagging and organization
2. **Automation**: Automate resource management tasks
3. **Documentation**: Maintain comprehensive resource documentation
4. **Regular Reviews**: Regular review of resource usage and optimization
5. **Continuous Improvement**: Continuously optimize resource management strategies
"""

    def _get_predictive_maintenance_content(self) -> str:
        """Get content for predictive maintenance procedures"""
        return """
# Predictive Maintenance Procedures

## Predictive Maintenance Overview
Implement predictive maintenance to identify and address potential issues before they cause system failures.

## Data Collection
1. **Performance Metrics**: Collect comprehensive performance metrics
2. **System Logs**: Aggregate and analyze system logs
3. **Resource Usage**: Monitor resource usage patterns and trends
4. **Error Patterns**: Track error rates and patterns
5. **User Activity**: Monitor user activity and system interactions

## Predictive Analytics
1. **Trend Analysis**: Identify trends in performance metrics
2. **Anomaly Detection**: Detect anomalies in system behavior
3. **Pattern Recognition**: Recognize patterns that precede failures
4. **Machine Learning**: Use ML models for failure prediction
5. **Statistical Analysis**: Apply statistical methods for prediction

## Maintenance Scheduling
1. **Proactive Maintenance**: Schedule maintenance before failures occur
2. **Optimal Timing**: Schedule maintenance during low-traffic periods
3. **Resource Availability**: Ensure resources are available for maintenance
4. **Impact Assessment**: Assess impact of maintenance on users
5. **Communication**: Communicate maintenance schedules to stakeholders

## Predictive Models
1. **Failure Prediction**: Predict component failures based on usage patterns
2. **Performance Degradation**: Identify performance degradation trends
3. **Resource Exhaustion**: Predict resource exhaustion and capacity issues
4. **Security Threats**: Identify potential security threats and vulnerabilities
5. **Cost Optimization**: Predict cost optimization opportunities

## Automation
1. **Automated Analysis**: Automate data analysis and pattern recognition
2. **Automated Alerts**: Configure automated alerts for predicted issues
3. **Automated Maintenance**: Automate routine maintenance tasks
4. **Automated Reporting**: Generate automated maintenance reports
5. **Automated Optimization**: Automate system optimization based on predictions

## Implementation Strategy
1. **Data Infrastructure**: Build robust data collection and storage
2. **Analytics Platform**: Implement predictive analytics platform
3. **Model Development**: Develop and train prediction models
4. **Integration**: Integrate predictive maintenance with existing systems
5. **Testing**: Test predictive maintenance procedures

## Monitoring and Evaluation
1. **Model Performance**: Monitor prediction model performance
2. **Maintenance Effectiveness**: Evaluate effectiveness of maintenance actions
3. **Cost-Benefit Analysis**: Analyze cost-benefit of predictive maintenance
4. **Continuous Improvement**: Continuously improve prediction models
5. **Feedback Loop**: Implement feedback loop for model improvement

## Best Practices
1. **Data Quality**: Ensure high-quality data for accurate predictions
2. **Model Validation**: Regular validation of prediction models
3. **Human Oversight**: Maintain human oversight for critical decisions
4. **Documentation**: Comprehensive documentation of procedures
5. **Training**: Regular training for predictive maintenance procedures

## Tools and Technologies
1. **Machine Learning**: Use ML frameworks for prediction models
2. **Data Analytics**: Use data analytics tools for pattern recognition
3. **Monitoring**: Use comprehensive monitoring tools
4. **Automation**: Use automation tools for maintenance tasks
5. **Visualization**: Use data visualization for trend analysis
"""

    def _get_security_hardening_content(self) -> str:
        """Get content for security hardening guidelines"""
        return """
# Security Hardening Guidelines

## Security Overview
Implement comprehensive security measures to protect DuckBot systems and data.

## System Hardening
1. **Operating System**: Secure operating system configuration
2. **Network Security**: Implement network security measures
3. **Application Security**: Secure application development and deployment
4. **Data Security**: Protect sensitive data at rest and in transit
5. **Access Control**: Implement proper access controls

## Authentication and Authorization
1. **Multi-Factor Authentication**: Implement MFA for all administrative access
2. **Role-Based Access**: Use role-based access control
3. **Least Privilege**: Apply least privilege principle
4. **Password Policy**: Implement strong password policies
5. **Session Management**: Secure session management

## Data Protection
1. **Encryption**: Encrypt sensitive data at rest and in transit
2. **Data Classification**: Classify data based on sensitivity
3. **Backup Security**: Secure backup storage and access
4. **Data Loss Prevention**: Implement DLP measures
5. **Compliance**: Ensure compliance with relevant regulations

## Network Security
1. **Firewall Configuration**: Configure firewalls properly
2. **Intrusion Detection**: Implement intrusion detection systems
3. **Network Segmentation**: Segment network for security
4. **VPN Access**: Use VPN for remote access
5. **Network Monitoring**: Monitor network traffic for anomalies

## Application Security
1. **Secure Coding**: Follow secure coding practices
2. **Input Validation**: Validate all user inputs
3. **Error Handling**: Secure error handling and logging
4. **Dependency Management**: Manage third-party dependencies
5. **Security Testing**: Regular security testing

## Monitoring and Detection
1. **Security Monitoring**: Implement security monitoring
2. **Log Analysis**: Analyze logs for security events
3. **Anomaly Detection**: Detect security anomalies
4. **Threat Intelligence**: Use threat intelligence feeds
5. **Incident Response**: Have incident response procedures

## Backup and Recovery
1. **Backup Strategy**: Implement comprehensive backup strategy
2. **Disaster Recovery**: Have disaster recovery plans
3. **Testing**: Regular testing of backup and recovery
4. **Documentation**: Maintain security documentation
5. **Training**: Regular security training

## Compliance and Auditing
1. **Compliance Requirements**: Understand compliance requirements
2. **Regular Audits**: Conduct regular security audits
3. **Documentation**: Maintain compliance documentation
4. **Remediation**: Address compliance issues promptly
5. **Continuous Improvement**: Continuously improve security posture

## Best Practices
1. **Defense in Depth**: Implement multiple security layers
2. **Regular Updates**: Keep systems and software updated
3. **Security Awareness**: Promote security awareness
4. **Incident Response**: Have incident response procedures
5. **Continuous Monitoring**: Monitor security continuously
"""

    def _get_troubleshooting_content(self) -> str:
        """Get content for troubleshooting common issues"""
        return """
# Troubleshooting Common Issues

## Troubleshooting Methodology
Systematic approach to identifying and resolving common DuckBot issues.

## General Troubleshooting Steps
1. **Identify Symptoms**: Clearly identify the problem symptoms
2. **Gather Information**: Collect relevant information and logs
3. **Analyze Patterns**: Look for patterns in the issues
4. **Form Hypotheses**: Develop potential causes
5. **Test Solutions**: Test and implement solutions
6. **Verify Resolution**: Confirm the issue is resolved
7. **Document**: Document the troubleshooting process

## Performance Issues
### Slow System Response
1. **Check Resource Usage**: Monitor CPU, memory, disk, and network usage
2. **Identify Bottlenecks**: Find resource bottlenecks
3. **Review Logs**: Check for error messages and warnings
4. **Network Issues**: Check network connectivity and latency
5. **Database Performance**: Review database performance

### High CPU Usage
1. **Process Analysis**: Identify CPU-intensive processes
2. **Service Health**: Check service health and status
3. **Application Issues**: Review application logs and performance
4. **Configuration Issues**: Check system and application configuration
5. **Resource Contention**: Identify resource contention issues

## Service Issues
### Service Not Starting
1. **Service Status**: Check service status and error messages
2. **Dependencies**: Verify service dependencies
3. **Configuration**: Review service configuration
4. **Resource Availability**: Check resource availability
5. **Log Analysis**: Analyze service startup logs

### Service Crashes
1. **Crash Logs**: Review crash logs and stack traces
2. **Memory Issues**: Check for memory leaks or exhaustion
3. **Resource Limits**: Verify resource limits and settings
4. **Application Errors**: Review application error logs
5. **System Updates**: Check for recent system updates

## Database Issues
### Connection Issues
1. **Connection String**: Verify database connection strings
2. **Network Connectivity**: Check network connectivity
3. **Database Status**: Verify database service status
4. **Firewall Rules**: Check firewall rules
5. **Authentication**: Verify database authentication

### Performance Issues
1. **Slow Queries**: Identify and optimize slow queries
2. **Index Issues**: Check database indexes
3. **Lock Contention**: Identify lock contention issues
4. **Resource Usage**: Monitor database resource usage
5. **Configuration**: Review database configuration

## AI Model Issues
### Model Performance
1. **Model Selection**: Verify appropriate model selection
2. **Resource Usage**: Check resource usage for AI models
3. **Input Quality**: Review input data quality
4. **Configuration**: Check model configuration
5. **Cache Issues**: Check model caching

### Model Loading Issues
1. **Model Availability**: Verify model availability
2. **Resource Limits**: Check resource limits
3. **Download Issues**: Check model download status
4. **Configuration**: Review model configuration
5. **Dependencies**: Verify model dependencies

## Network Issues
### Connectivity Problems
1. **Network Configuration**: Verify network configuration
2. **Firewall Settings**: Check firewall settings
3. **DNS Issues**: Check DNS resolution
4. **Routing**: Verify network routing
5. **Service Status**: Check network service status

### Performance Issues
1. **Bandwidth**: Check network bandwidth usage
2. **Latency**: Monitor network latency
3. **Packet Loss**: Check for packet loss
4. **Configuration**: Review network configuration
5. **Hardware**: Check network hardware

## Common Error Patterns
### Memory Leaks
1. **Memory Usage**: Monitor memory usage patterns
2. **Application Analysis**: Analyze application memory usage
3. **Garbage Collection**: Review garbage collection settings
4. **Resource Cleanup**: Check for proper resource cleanup
5. **Memory Profiling**: Use memory profiling tools

### Deadlocks
1. **Thread Analysis**: Analyze thread usage and synchronization
2. **Resource Contention**: Identify resource contention
3. **Lock Analysis**: Review lock usage
4. **Timeout Settings**: Check timeout settings
5. **Application Logic**: Review application logic

## Diagnostic Tools
1. **System Monitoring**: Use system monitoring tools
2. **Log Analysis**: Use log analysis tools
3. **Network Tools**: Use network diagnostic tools
4. **Performance Profiling**: Use performance profiling tools
5. **Debugging Tools**: Use debugging tools

## Best Practices
1. **Documentation**: Maintain comprehensive documentation
2. **Logging**: Implement comprehensive logging
3. **Monitoring**: Use comprehensive monitoring
4. **Testing**: Regular testing of systems
5. **Preventive Maintenance**: Implement preventive maintenance
"""

    def add_knowledge_entry(self, entry_data: Dict[str, Any]) -> str:
        """Add a new knowledge entry to the knowledge base"""
        entry_id = entry_data.get("id", str(uuid.uuid4()))

        # Create knowledge entry object
        entry = KnowledgeEntry(
            id=entry_id,
            title=entry_data["title"],
            content=entry_data["content"],
            type=KnowledgeType(entry_data["type"]),
            level=KnowledgeLevel(entry_data.get("level", "intermediate")),
            status=KnowledgeStatus(entry_data.get("status", "active")),
            tags=entry_data.get("tags", []),
            category=entry_data["category"],
            subcategory=entry_data.get("subcategory", ""),
            prerequisites=entry_data.get("prerequisites", []),
            related_entries=entry_data.get("related_entries", []),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            author=entry_data.get("author", "system"),
            effectiveness_score=0.0,
            usage_count=0,
            last_used=None,
            metadata=entry_data.get("metadata", {})
        )

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO knowledge_entries (
                    id, title, content, type, level, status, tags, category,
                    subcategory, prerequisites, related_entries, created_at,
                    updated_at, author, effectiveness_score, usage_count,
                    last_used, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.id,
                entry.title,
                entry.content,
                entry.type.value,
                entry.level.value,
                entry.status.value,
                json.dumps(entry.tags),
                entry.category,
                entry.subcategory,
                json.dumps(entry.prerequisites),
                json.dumps(entry.related_entries),
                entry.created_at.isoformat(),
                entry.updated_at.isoformat(),
                entry.author,
                entry.effectiveness_score,
                entry.usage_count,
                entry.last_used.isoformat() if entry.last_used else None,
                json.dumps(entry.metadata)
            ))
            conn.commit()

        # Update knowledge graph
        self.knowledge_graph[entry_id] = entry

        # Update indexes
        if entry.category not in self.category_index:
            self.category_index[entry.category] = []
        self.category_index[entry.category].append(entry_id)

        for tag in entry.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(entry_id)

        # Process relationships
        self._process_relationships(entry)

        logger.info(f"Added knowledge entry: {entry.title}")

        return entry_id

    def _process_relationships(self, entry: KnowledgeEntry):
        """Process relationships between knowledge entries"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Process prerequisites (dependency relationships)
            for prereq_id in entry.prerequisites:
                if prereq_id in self.knowledge_graph:
                    cursor.execute('''
                        INSERT OR REPLACE INTO knowledge_relationships
                        (source_entry_id, target_entry_id, relationship_type, strength, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (prereq_id, entry.id, "prerequisite", 0.8, datetime.now().isoformat()))

            # Process related entries
            for related_id in entry.related_entries:
                if related_id in self.knowledge_graph:
                    cursor.execute('''
                        INSERT OR REPLACE INTO knowledge_relationships
                        (source_entry_id, target_entry_id, relationship_type, strength, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (entry.id, related_id, "related", 0.6, datetime.now().isoformat()))

            conn.commit()

    def search_knowledge(self, query: KnowledgeQuery) -> KnowledgeSearchResult:
        """Search knowledge base for relevant entries"""
        start_time = time.time()

        # Update usage stats
        self.usage_stats["total_queries"] += 1

        # Perform search
        relevant_entries = self._perform_search(query)

        # Calculate relevance scores
        relevance_scores = self._calculate_relevance_scores(query, relevant_entries)

        # Sort by relevance
        sorted_entries = sorted(
            relevant_entries,
            key=lambda x: relevance_scores.get(x.id, 0.0),
            reverse=True
        )

        # Limit results
        limited_entries = sorted_entries[:query.limit]

        # Generate suggestions
        suggestions = self._generate_search_suggestions(query, limited_entries)

        # Update usage
        for entry in limited_entries:
            self._update_entry_usage(entry.id, query.query_text)

        # Record query metrics
        query_time = (time.time() - start_time) * 1000
        self.usage_stats["successful_queries"] += 1
        self._update_usage_metrics(query_time)

        # Return search results
        return KnowledgeSearchResult(
            entries=limited_entries,
            total_results=len(relevant_entries),
            query_time_ms=query_time,
            relevance_scores=relevance_scores,
            suggestions=suggestions
        )

    def _perform_search(self, query: KnowledgeQuery) -> List[KnowledgeEntry]:
        """Perform the actual search operation"""
        results = []

        # Get all entries (filtered by criteria)
        for entry_id, entry in self.knowledge_graph.items():
            if self._matches_criteria(entry, query):
                results.append(entry)

        return results

    def _matches_criteria(self, entry: KnowledgeEntry, query: KnowledgeQuery) -> bool:
        """Check if entry matches search criteria"""
        # Check status filter
        if query.status_filter and entry.status != query.status_filter:
            return False

        # Check level filter
        if query.level_filter and entry.level != query.level_filter:
            return False

        # Check type filter
        if query.knowledge_types and entry.type not in query.knowledge_types:
            return False

        # Check category filter
        if query.categories and entry.category not in query.categories:
            return False

        # Check tag filter
        if query.tags:
            if not any(tag in entry.tags for tag in query.tags):
                return False

        # Check text query (if provided)
        if query.query_text:
            search_text = query.query_text.lower()
            entry_text = f"{entry.title} {entry.content}".lower()

            if search_text not in entry_text:
                return False

        return True

    def _calculate_relevance_scores(self, query: KnowledgeQuery,
                                   entries: List[KnowledgeEntry]) -> Dict[str, float]:
        """Calculate relevance scores for search results"""
        scores = {}

        for entry in entries:
            score = 0.0

            # Title relevance (highest weight)
            if query.query_text.lower() in entry.title.lower():
                score += 0.5

            # Content relevance
            if query.query_text.lower() in entry.content.lower():
                score += 0.3

            # Tag relevance
            query_tags = query.tags or []
            for tag in query_tags:
                if tag in entry.tags:
                    score += 0.2

            # Category relevance
            if query.categories and entry.category in query.categories:
                score += 0.1

            # Usage boost (frequently used entries get higher score)
            usage_boost = min(0.1, entry.usage_count * 0.01)
            score += usage_boost

            # Effectiveness boost (effective entries get higher score)
            effectiveness_boost = entry.effectiveness_score * 0.1
            score += effectiveness_boost

            scores[entry.id] = min(1.0, score)

        return scores

    def _generate_search_suggestions(self, query: KnowledgeQuery,
                                   results: List[KnowledgeEntry]) -> List[str]:
        """Generate search suggestions based on results"""
        suggestions = []

        if not results:
            # No results - suggest related terms
            suggestions.extend([
                "Try using more general search terms",
                "Check for typos in your search query",
                "Browse knowledge categories instead"
            ])

            # Log knowledge gap
            self._log_knowledge_gap(query.query_text, "no_results_found")

        elif len(results) < 3:
            # Few results - suggest related searches
            top_result = results[0]
            suggestions.extend([
                f"Related topics: {', '.join(top_result.tags[:3])}",
                f"Consider {top_result.category} category",
                f"Try searching for {top_result.subcategory}"
            ])

        else:
            # Good results - suggest refinement
            suggestions.extend([
                "Filter by knowledge type for more specific results",
                "Use tags to narrow down results",
                "Check related entries for more information"
            ])

        return suggestions

    def _update_entry_usage(self, entry_id: str, query_text: str):
        """Update entry usage statistics"""
        if entry_id not in self.knowledge_graph:
            return

        entry = self.knowledge_graph[entry_id]
        entry.usage_count += 1
        entry.last_used = datetime.now()

        # Update in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE knowledge_entries
                SET usage_count = ?, last_used = ?
                WHERE id = ?
            ''', (entry.usage_count, entry.last_used.isoformat(), entry_id))

            # Record usage
            cursor.execute('''
                INSERT INTO knowledge_usage (entry_id, query_text, success, execution_time_ms, timestamp, context)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (entry_id, query_text, True, 0.0, datetime.now().isoformat(), "search"))

            conn.commit()

    def _update_usage_metrics(self, query_time_ms: float):
        """Update overall usage metrics"""
        total_queries = self.usage_stats["total_queries"]
        current_avg = self.usage_stats["avg_query_time"]
        self.usage_stats["avg_query_time"] = ((current_avg * (total_queries - 1)) + query_time_ms) / total_queries

    def _log_knowledge_gap(self, query_text: str, gap_description: str):
        """Log knowledge gap for future improvement"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO knowledge_gaps (query_text, gap_description, category, priority, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (query_text, gap_description, "search", "medium", datetime.now().isoformat()))
            conn.commit()

        self.usage_stats["knowledge_gaps"].append({
            "query": query_text,
            "description": gap_description,
            "timestamp": datetime.now().isoformat()
        })

    def get_relevant_knowledge(self, situation: Dict[str, Any]) -> List[KnowledgeEntry]:
        """Get knowledge entries relevant to a specific situation"""
        # Extract keywords from situation
        keywords = self._extract_keywords_from_situation(situation)

        # Create search query
        query = KnowledgeQuery(
            query_text=" ".join(keywords),
            knowledge_types=[KnowledgeType.PROCEDURE, KnowledgeType.TROUBLESHOOTING],
            limit=5
        )

        # Search knowledge base
        search_result = self.search_knowledge(query)

        return search_result.entries

    def _extract_keywords_from_situation(self, situation: Dict[str, Any]) -> List[str]:
        """Extract relevant keywords from situation description"""
        keywords = []

        # Extract from situation type
        situation_type = situation.get("type", "").lower()
        keywords.extend(situation_type.split("_"))

        # Extract from description
        description = situation.get("description", "").lower()
        keywords.extend(description.split())

        # Extract from symptoms or issues
        symptoms = situation.get("symptoms", [])
        if isinstance(symptoms, list):
            for symptom in symptoms:
                keywords.extend(str(symptom).lower().split())

        # Clean and deduplicate keywords
        cleaned_keywords = []
        seen = set()

        for keyword in keywords:
            keyword = keyword.strip()
            if keyword and len(keyword) > 2 and keyword not in seen:
                cleaned_keywords.append(keyword)
                seen.add(keyword)

        return cleaned_keywords

    def get_procedural_knowledge(self, procedure_type: str) -> List[KnowledgeEntry]:
        """Get procedural knowledge for specific task types"""
        query = KnowledgeQuery(
            query_text=procedure_type,
            knowledge_types=[KnowledgeType.PROCEDURE],
            limit=10
        )

        search_result = self.search_knowledge(query)
        return search_result.entries

    def get_troubleshooting_knowledge(self, issue_type: str) -> List[KnowledgeEntry]:
        """Get troubleshooting knowledge for specific issue types"""
        query = KnowledgeQuery(
            query_text=issue_type,
            knowledge_types=[KnowledgeType.TROUBLESHOOTING],
            limit=10
        )

        search_result = self.search_knowledge(query)
        return search_result.entries

    def record_knowledge_effectiveness(self, entry_id: str, effectiveness_score: float,
                                    context: Dict[str, Any] = None):
        """Record effectiveness of knowledge entry usage"""
        if entry_id not in self.knowledge_graph:
            return

        entry = self.knowledge_graph[entry_id]

        # Update effectiveness score (running average)
        current_score = entry.effectiveness_score
        usage_count = entry.usage_count
        new_score = ((current_score * (usage_count - 1)) + effectiveness_score) / usage_count
        entry.effectiveness_score = new_score

        # Update in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE knowledge_entries
                SET effectiveness_score = ?
                WHERE id = ?
            ''', (new_score, entry_id))

            # Record usage with effectiveness
            cursor.execute('''
                INSERT INTO knowledge_usage (entry_id, success, execution_time_ms, user_satisfaction, timestamp, context)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (entry_id, True, 0.0, int(effectiveness_score * 5), datetime.now().isoformat(),
                  json.dumps(context or {})))

            conn.commit()

        logger.info(f"Recorded effectiveness for entry {entry_id}: {effectiveness_score:.2f}")

    def get_knowledge_insights(self) -> Dict[str, Any]:
        """Get insights about knowledge base usage and effectiveness"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get most used entries
            cursor.execute('''
                SELECT id, title, usage_count, effectiveness_score
                FROM knowledge_entries
                ORDER BY usage_count DESC
                LIMIT 10
            ''')
            most_used = [{"id": row[0], "title": row[1], "usage_count": row[2], "effectiveness": row[3]}
                       for row in cursor.fetchall()]

            # Get most effective entries
            cursor.execute('''
                SELECT id, title, effectiveness_score, usage_count
                FROM knowledge_entries
                WHERE usage_count > 0
                ORDER BY effectiveness_score DESC
                LIMIT 10
            ''')
            most_effective = [{"id": row[0], "title": row[1], "effectiveness": row[2], "usage_count": row[3]}
                            for row in cursor.fetchall()]

            # Get knowledge gaps
            cursor.execute('''
                SELECT query_text, gap_description, priority, created_at
                FROM knowledge_gaps
                WHERE resolved = FALSE
                ORDER BY created_at DESC
                LIMIT 10
            ''')
            gaps = [{"query": row[0], "description": row[1], "priority": row[2], "created_at": row[3]}
                   for row in cursor.fetchall()]

            # Get usage statistics
            cursor.execute('''
                SELECT COUNT(*) as total_usage,
                       AVG(execution_time_ms) as avg_time,
                       AVG(user_satisfaction) as avg_satisfaction
                FROM knowledge_usage
                WHERE timestamp > datetime('now', '-30 days')
            ''')
            usage_stats = cursor.fetchone()

        return {
            "usage_statistics": self.usage_stats,
            "most_used_entries": most_used,
            "most_effective_entries": most_effective,
            "knowledge_gaps": gaps,
            "recent_usage_stats": {
                "total_usage_30d": usage_stats[0] if usage_stats else 0,
                "avg_time_ms": usage_stats[1] if usage_stats else 0,
                "avg_satisfaction": usage_stats[2] if usage_stats else 0
            },
            "total_entries": len(self.knowledge_graph),
            "categories": list(self.category_index.keys()),
            "recommendations": self._generate_knowledge_recommendations()
        }

    def _generate_knowledge_recommendations(self) -> List[str]:
        """Generate recommendations for knowledge base improvement"""
        recommendations = []

        # Check for knowledge gaps
        if len(self.usage_stats["knowledge_gaps"]) > 10:
            recommendations.append("Consider adding knowledge for frequently searched but missing topics")

        # Check for low effectiveness entries
        low_effectiveness = [entry for entry in self.knowledge_graph.values()
                           if entry.usage_count > 5 and entry.effectiveness_score < 0.3]
        if low_effectiveness:
            recommendations.append("Review and improve low-effectiveness knowledge entries")

        # Check for unused entries
        unused_entries = [entry for entry in self.knowledge_graph.values()
                         if entry.usage_count == 0 and entry.status == KnowledgeStatus.ACTIVE]
        if len(unused_entries) > len(self.knowledge_graph) * 0.2:
            recommendations.append("Consider archiving or improving unused knowledge entries")

        # Check category coverage
        if len(self.category_index) < 5:
            recommendations.append("Consider adding knowledge in additional categories")

        return recommendations

# Global knowledge base instance
_knowledge_base = None

def get_knowledge_base() -> AIKnowledgeBase:
    """Get the global knowledge base instance"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = AIKnowledgeBase()
    return _knowledge_base

def search_knowledge(query: str, knowledge_types: List[str] = None,
                    category: str = None, limit: int = 10) -> Dict[str, Any]:
    """Search knowledge base with simple interface"""
    kb = get_knowledge_base()

    search_query = KnowledgeQuery(
        query_text=query,
        knowledge_types=[KnowledgeType(t) for t in knowledge_types] if knowledge_types else None,
        categories=[category] if category else None,
        limit=limit
    )

    result = kb.search_knowledge(search_query)

    return {
        "results": [
            {
                "id": entry.id,
                "title": entry.title,
                "type": entry.type.value,
                "category": entry.category,
                "tags": entry.tags,
                "relevance_score": result.relevance_scores.get(entry.id, 0.0),
                "usage_count": entry.usage_count,
                "effectiveness_score": entry.effectiveness_score
            }
            for entry in result.entries
        ],
        "total_results": result.total_results,
        "query_time_ms": result.query_time_ms,
        "suggestions": result.suggestions
    }

def get_relevant_knowledge_for_situation(situation: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get knowledge relevant to a specific situation"""
    kb = get_knowledge_base()
    entries = kb.get_relevant_knowledge(situation)

    return [
        {
            "id": entry.id,
            "title": entry.title,
            "type": entry.type.value,
            "category": entry.category,
            "content_summary": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
            "relevance_score": 1.0,  # Since it's filtered for relevance
            "tags": entry.tags
        }
        for entry in entries
    ]

def get_procedural_knowledge(procedure_type: str) -> List[Dict[str, Any]]:
    """Get procedural knowledge for specific task types"""
    kb = get_knowledge_base()
    entries = kb.get_procedural_knowledge(procedure_type)

    return [
        {
            "id": entry.id,
            "title": entry.title,
            "content": entry.content,
            "level": entry.level.value,
            "prerequisites": entry.prerequisites,
            "effectiveness_score": entry.effectiveness_score
        }
        for entry in entries
    ]

def record_knowledge_effectiveness(entry_id: str, effectiveness_score: float):
    """Record effectiveness of knowledge usage"""
    kb = get_knowledge_base()
    kb.record_knowledge_effectiveness(entry_id, effectiveness_score)

def get_knowledge_insights() -> Dict[str, Any]:
    """Get knowledge base insights and analytics"""
    kb = get_knowledge_base()
    return kb.get_knowledge_insights()

if __name__ == "__main__":
    # Test the knowledge base
    print("Testing DuckBot AI Knowledge Base")

    kb = get_knowledge_base()

    # Test search
    print("\nTesting knowledge search...")
    result = search_knowledge("performance optimization", limit=3)
    print(f"Found {result['total_results']} results in {result['query_time_ms']:.2f}ms")

    for item in result["results"]:
        print(f"- {item['title']} (relevance: {item['relevance_score']:.2f})")

    # Test situation-based knowledge retrieval
    print("\nTesting situation-based knowledge retrieval...")
    situation = {
        "type": "performance_issue",
        "description": "System is running slow with high CPU usage",
        "symptoms": ["slow_response", "high_cpu", "performance_degradation"]
    }

    relevant = get_relevant_knowledge_for_situation(situation)
    print(f"Found {len(relevant)} relevant knowledge entries")

    for item in relevant:
        print(f"- {item['title']}")

    # Get knowledge insights
    print("\nGetting knowledge insights...")
    insights = get_knowledge_insights()
    print(f"Total entries: {insights['total_entries']}")
    print(f"Categories: {len(insights['categories'])}")
    print(f"Recommendations: {len(insights['recommendations'])}")

    print("\nAI Knowledge Base test completed successfully!")