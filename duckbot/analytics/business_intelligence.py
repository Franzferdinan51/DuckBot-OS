#!/usr/bin/env python3
"""
DuckBot Business Intelligence & ROI Analysis
Advanced cost analysis, ROI calculations, and strategic business insights
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from pathlib import Path
import uuid

from analytics_engine import AnalyticsEngine, AnalyticsEvent, AnalyticsEventType

logger = logging.getLogger(__name__)

class CostCategory(Enum):
    """Cost categories for analysis"""
    COMPUTE_COSTS = "compute_costs"
    API_COSTS = "api_costs"
    STORAGE_COSTS = "storage_costs"
    NETWORK_COSTS = "network_costs"
    MAINTENANCE_COSTS = "maintenance_costs"
    OVERHEAD_COSTS = "overhead_costs"

class ROI_Metric(Enum):
    """ROI measurement metrics"""
    USER_ACQUISITION_COST = "user_acquisition_cost"
    LIFETIME_VALUE = "lifetime_value"
    COST_PER_SESSION = "cost_per_session"
    REVENUE_PER_USER = "revenue_per_user"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    RESOURCE_UTILIZATION = "resource_utilization"

class InsightType(Enum):
    """Types of business insights"""
    COST_OPTIMIZATION = "cost_optimization"
    EFFICIENCY_GAIN = "efficiency_gain"
    ROI_IMPROVEMENT = "roi_improvement"
    RESOURCE_ALLOCATION = "resource_allocation"
    STRATEGIC_RECOMMENDATION = "strategic_recommendation"

@dataclass
class CostBreakdown:
    """Detailed cost breakdown"""
    category: CostCategory
    amount: float
    percentage: float
    trend: str  # "increasing", "decreasing", "stable"
    period_amount: float  # Current period amount
    previous_period_amount: float  # Previous period amount
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ROIAnalysis:
    """ROI analysis results"""
    metric: ROI_Metric
    current_value: float
    previous_value: float
    change_percent: float
    trend: str
    confidence_level: float
    factors: List[str]
    recommendations: List[str]

@dataclass
class BusinessInsight:
    """Business insight with recommendations"""
    insight_id: str
    insight_type: InsightType
    title: str
    description: str
    impact_score: float  # 0-100
    confidence_score: float  # 0-100
    cost_savings_potential: float
    implementation_effort: str  # "low", "medium", "high"
    recommendations: List[str]
    data_points: Dict[str, Any]
    created_at: datetime

@dataclass
class FinancialForecast:
    """Financial forecast data"""
    forecast_id: str
    metric_name: str
    time_period: str
    forecast_values: List[float]
    confidence_intervals: List[Tuple[float, float]]
    methodology: str
    accuracy_score: float
    created_at: datetime

class BusinessIntelligenceEngine:
    """Advanced business intelligence and ROI analysis engine"""

    def __init__(self, analytics_engine: AnalyticsEngine):
        self.analytics_engine = analytics_engine
        self.db_path = analytics_engine.db.db_path
        self.cost_breakdowns: Dict[str, CostBreakdown] = {}
        self.roi_analyses: Dict[str, ROIAnalysis] = {}
        self.business_insights: List[BusinessInsight] = []
        self.forecasts: Dict[str, FinancialForecast] = {}
        self._initialize_bi_engine()

    def _initialize_bi_engine(self):
        """Initialize the business intelligence engine"""
        # Create database tables
        self._create_database_tables()
        # Load existing data
        self._load_existing_data()
        # Start periodic analysis
        asyncio.create_task(self._periodic_analysis())

    def _create_database_tables(self):
        """Create business intelligence database tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Cost breakdown table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cost_breakdowns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    percentage REAL,
                    trend TEXT,
                    period_amount REAL,
                    previous_period_amount REAL,
                    details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ROI analysis table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS roi_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric TEXT NOT NULL,
                    current_value REAL,
                    previous_value REAL,
                    change_percent REAL,
                    trend TEXT,
                    confidence_level REAL,
                    factors TEXT,
                    recommendations TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Business insights table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS business_insights (
                    insight_id TEXT PRIMARY KEY,
                    insight_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    impact_score REAL,
                    confidence_score REAL,
                    cost_savings_potential REAL,
                    implementation_effort TEXT,
                    recommendations TEXT,
                    data_points TEXT,
                    created_at DATETIME NOT NULL
                )
            ''')

            # Financial forecasts table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS financial_forecasts (
                    forecast_id TEXT PRIMARY KEY,
                    metric_name TEXT NOT NULL,
                    time_period TEXT NOT NULL,
                    forecast_values TEXT,
                    confidence_intervals TEXT,
                    methodology TEXT,
                    accuracy_score REAL,
                    created_at DATETIME NOT NULL
                )
            ''')

            # Cost optimization opportunities table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cost_optimization_opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    opportunity_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    potential_savings REAL,
                    implementation_cost REAL,
                    roi REAL,
                    priority INTEGER,
                    status TEXT DEFAULT 'identified',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Business metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS business_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    metric_unit TEXT,
                    time_period TEXT,
                    comparison_type TEXT,
                    comparison_value REAL,
                    trend TEXT,
                    insights TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_cost_breakdowns_category ON cost_breakdowns(category)',
                'CREATE INDEX IF NOT EXISTS idx_roi_analyses_metric ON roi_analyses(metric)',
                'CREATE INDEX IF NOT EXISTS idx_insights_type ON business_insights(insight_type)',
                'CREATE INDEX IF NOT EXISTS idx_forecasts_metric ON financial_forecasts(metric_name)',
                'CREATE INDEX IF NOT EXISTS idx_opportunities_priority ON cost_optimization_opportunities(priority)'
            ]

            for index_sql in indexes:
                conn.execute(index_sql)

    def _load_existing_data(self):
        """Load existing business intelligence data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Load cost breakdowns
                cursor = conn.execute('SELECT * FROM cost_breakdowns ORDER BY created_at DESC LIMIT 10')
                for row in cursor.fetchall():
                    breakdown = CostBreakdown(
                        category=CostCategory(row[1]),
                        amount=row[2],
                        percentage=row[3],
                        trend=row[4],
                        period_amount=row[5],
                        previous_period_amount=row[6],
                        details=json.loads(row[7]) if row[7] else {}
                    )
                    self.cost_breakdowns[breakdown.category.value] = breakdown

                # Load ROI analyses
                cursor = conn.execute('SELECT * FROM roi_analyses ORDER BY created_at DESC')
                for row in cursor.fetchall():
                    roi = ROIAnalysis(
                        metric=ROI_Metric(row[1]),
                        current_value=row[2],
                        previous_value=row[3],
                        change_percent=row[4],
                        trend=row[5],
                        confidence_level=row[6],
                        factors=json.loads(row[7]) if row[7] else [],
                        recommendations=json.loads(row[8]) if row[8] else []
                    )
                    self.roi_analyses[roi.metric.value] = roi

                # Load business insights
                cursor = conn.execute('SELECT * FROM business_insights ORDER BY created_at DESC LIMIT 50')
                for row in cursor.fetchall():
                    insight = BusinessInsight(
                        insight_id=row[0],
                        insight_type=InsightType(row[1]),
                        title=row[2],
                        description=row[3],
                        impact_score=row[4],
                        confidence_score=row[5],
                        cost_savings_potential=row[6],
                        implementation_effort=row[7],
                        recommendations=json.loads(row[8]) if row[8] else [],
                        data_points=json.loads(row[9]) if row[9] else {},
                        created_at=datetime.fromisoformat(row[10])
                    )
                    self.business_insights.append(insight)

        except Exception as e:
            logger.error(f"Error loading existing BI data: {e}")

    async def _periodic_analysis(self):
        """Run periodic business intelligence analysis"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._analyze_cost_structure()
                await self._calculate_roi_metrics()
                await self._generate_business_insights()
                await self._update_financial_forecasts()
            except Exception as e:
                logger.error(f"Error in periodic BI analysis: {e}")

    async def _analyze_cost_structure(self):
        """Analyze current cost structure"""
        try:
            # Get cost data from analytics
            cost_summary = self.analytics_engine.get_usage_summary(30)

            # Analyze by category
            categories = await self._categorize_costs(cost_summary)

            # Create cost breakdowns
            for category, data in categories.items():
                breakdown = CostBreakdown(
                    category=CostCategory(category),
                    amount=data['amount'],
                    percentage=data['percentage'],
                    trend=data['trend'],
                    period_amount=data['current_period'],
                    previous_period_amount=data['previous_period'],
                    details=data['details']
                )

                self.cost_breakdowns[category] = breakdown
                self._store_cost_breakdown(breakdown)

        except Exception as e:
            logger.error(f"Error analyzing cost structure: {e}")

    async def _categorize_costs(self, cost_summary) -> Dict[str, Any]:
        """Categorize costs by type"""
        try:
            # Get detailed cost data
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT provider, model, SUM(total_cost) as total_cost,
                           SUM(input_tokens + output_tokens) as total_tokens
                    FROM cost_records
                    WHERE timestamp >= datetime('now', '-30 days')
                    GROUP BY provider, model
                ''')

                provider_costs = cursor.fetchall()

            # Calculate category breakdowns
            total_cost = cost_summary.total_cost
            categories = {}

            # API costs (model usage)
            api_costs = sum(row[2] for row in provider_costs)
            categories['api_costs'] = {
                'amount': api_costs,
                'percentage': (api_costs / total_cost * 100) if total_cost > 0 else 0,
                'trend': self._calculate_cost_trend('api_costs'),
                'current_period': api_costs,
                'previous_period': self._get_previous_period_cost('api_costs'),
                'details': {
                    'providers': [{'provider': row[0], 'model': row[1], 'cost': row[2]}
                                 for row in provider_costs]
                }
            }

            # Compute costs (estimated based on resource usage)
            compute_costs = total_cost * 0.3  # Assume 30% is compute
            categories['compute_costs'] = {
                'amount': compute_costs,
                'percentage': 30.0,
                'trend': self._calculate_cost_trend('compute_costs'),
                'current_period': compute_costs,
                'previous_period': self._get_previous_period_cost('compute_costs'),
                'details': {
                    'cpu_allocation': 'estimated',
                    'memory_allocation': 'estimated'
                }
            }

            # Other costs
            other_costs = total_cost - api_costs - compute_costs
            categories['overhead_costs'] = {
                'amount': other_costs,
                'percentage': (other_costs / total_cost * 100) if total_cost > 0 else 0,
                'trend': self._calculate_cost_trend('overhead_costs'),
                'current_period': other_costs,
                'previous_period': self._get_previous_period_cost('overhead_costs'),
                'details': {
                    'miscellaneous_costs': 'calculated'
                }
            }

            return categories

        except Exception as e:
            logger.error(f"Error categorizing costs: {e}")
            return {}

    def _calculate_cost_trend(self, category: str) -> str:
        """Calculate cost trend for a category"""
        try:
            current_cost = self._get_current_period_cost(category)
            previous_cost = self._get_previous_period_cost(category)

            if previous_cost == 0:
                return "stable"

            change_percent = ((current_cost - previous_cost) / previous_cost) * 100

            if change_percent > 10:
                return "increasing"
            elif change_percent < -10:
                return "decreasing"
            else:
                return "stable"

        except Exception as e:
            logger.error(f"Error calculating cost trend for {category}: {e}")
            return "stable"

    def _get_current_period_cost(self, category: str) -> float:
        """Get current period cost for a category"""
        # This would be implemented with actual cost tracking
        return 0.0

    def _get_previous_period_cost(self, category: str) -> float:
        """Get previous period cost for a category"""
        # This would be implemented with actual cost tracking
        return 0.0

    def _store_cost_breakdown(self, breakdown: CostBreakdown):
        """Store cost breakdown in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO cost_breakdowns
                    (category, amount, percentage, trend, period_amount,
                     previous_period_amount, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    breakdown.category.value,
                    breakdown.amount,
                    breakdown.percentage,
                    breakdown.trend,
                    breakdown.period_amount,
                    breakdown.previous_period_amount,
                    json.dumps(breakdown.details)
                ))
        except Exception as e:
            logger.error(f"Error storing cost breakdown: {e}")

    async def _calculate_roi_metrics(self):
        """Calculate ROI metrics"""
        try:
            # Get user and cost data
            cost_summary = self.analytics_engine.get_usage_summary(30)

            with sqlite3.connect(self.db_path) as conn:
                # Get user metrics
                cursor = conn.execute('''
                    SELECT COUNT(DISTINCT user_id) as active_users,
                           COUNT(*) as total_sessions,
                           AVG(total_cost) as avg_cost_per_session
                    FROM user_sessions
                    WHERE start_time >= datetime('now', '-30 days')
                ''')

                user_metrics = cursor.fetchone()

            active_users = user_metrics[0] or 0
            total_sessions = user_metrics[1] or 0
            avg_cost_per_session = user_metrics[2] or 0.0

            # Calculate ROI metrics
            roi_metrics = []

            # User acquisition cost
            if active_users > 0:
                uac = cost_summary.total_cost / active_users
                roi_metrics.append(ROIAnalysis(
                    metric=ROI_Metric.USER_ACQUISITION_COST,
                    current_value=uac,
                    previous_value=self._get_previous_roi_value('user_acquisition_cost'),
                    change_percent=self._calculate_change(uac, self._get_previous_roi_value('user_acquisition_cost')),
                    trend=self._calculate_trend(uac, self._get_previous_roi_value('user_acquisition_cost')),
                    confidence_level=0.85,
                    factors=['active_users', 'total_cost'],
                    recommendations=[
                        'Optimize user onboarding costs',
                        'Improve user retention to reduce CAC',
                        'Focus on high-value user segments'
                    ]
                ))

            # Cost per session
            if total_sessions > 0:
                cps = cost_summary.total_cost / total_sessions
                roi_metrics.append(ROIAnalysis(
                    metric=ROI_Metric.COST_PER_SESSION,
                    current_value=cps,
                    previous_value=self._get_previous_roi_value('cost_per_session'),
                    change_percent=self._calculate_change(cps, self._get_previous_roi_value('cost_per_session')),
                    trend=self._calculate_trend(cps, self._get_previous_roi_value('cost_per_session')),
                    confidence_level=0.90,
                    factors=['total_cost', 'total_sessions'],
                    recommendations=[
                        'Reduce session costs through optimization',
                        'Increase session value and engagement',
                        'Implement session caching'
                    ]
                ))

            # Store ROI metrics
            for roi in roi_metrics:
                self.roi_analyses[roi.metric.value] = roi
                self._store_roi_analysis(roi)

        except Exception as e:
            logger.error(f"Error calculating ROI metrics: {e}")

    def _get_previous_roi_value(self, metric: str) -> float:
        """Get previous period ROI value"""
        # This would query historical data
        return 0.0

    def _calculate_change(self, current: float, previous: float) -> float:
        """Calculate percentage change"""
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100

    def _calculate_trend(self, current: float, previous: float) -> str:
        """Calculate trend direction"""
        if previous == 0:
            return "stable"

        change = ((current - previous) / previous) * 100
        if change > 5:
            return "increasing"
        elif change < -5:
            return "decreasing"
        else:
            return "stable"

    def _store_roi_analysis(self, roi: ROIAnalysis):
        """Store ROI analysis in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO roi_analyses
                    (metric, current_value, previous_value, change_percent,
                     trend, confidence_level, factors, recommendations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    roi.metric.value,
                    roi.current_value,
                    roi.previous_value,
                    roi.change_percent,
                    roi.trend,
                    roi.confidence_level,
                    json.dumps(roi.factors),
                    json.dumps(roi.recommendations)
                ))
        except Exception as e:
            logger.error(f"Error storing ROI analysis: {e}")

    async def _generate_business_insights(self):
        """Generate business insights and recommendations"""
        try:
            insights = []

            # Cost optimization insights
            cost_insights = await self._generate_cost_optimization_insights()
            insights.extend(cost_insights)

            # Efficiency insights
            efficiency_insights = await self._generate_efficiency_insights()
            insights.extend(efficiency_insights)

            # Strategic insights
            strategic_insights = await self._generate_strategic_insights()
            insights.extend(strategic_insights)

            # Store insights
            for insight in insights:
                self.business_insights.append(insight)
                self._store_business_insight(insight)

            # Keep only recent insights
            if len(self.business_insights) > 100:
                self.business_insights = self.business_insights[-50:]

        except Exception as e:
            logger.error(f"Error generating business insights: {e}")

    async def _generate_cost_optimization_insights(self) -> List[BusinessInsight]:
        """Generate cost optimization insights"""
        insights = []

        try:
            # Analyze cost breakdowns
            if self.cost_breakdowns:
                # Check for high API costs
                api_breakdown = self.cost_breakdowns.get('api_costs')
                if api_breakdown and api_breakdown.amount > 100:
                    insights.append(BusinessInsight(
                        insight_id=str(uuid.uuid4()),
                        insight_type=InsightType.COST_OPTIMIZATION,
                        title="High API Cost Detected",
                        description=f"API costs are ${api_breakdown.amount:.2f}, {api_breakdown.percentage:.1f}% of total costs",
                        impact_score=85,
                        confidence_score=90,
                        cost_savings_potential=api_breakdown.amount * 0.3,  # 30% savings potential
                        implementation_effort="medium",
                        recommendations=[
                            "Implement request caching",
                            "Optimize model selection for cost efficiency",
                            "Use batch processing for multiple requests",
                            "Consider model fine-tuning for specific tasks"
                        ],
                        data_points={
                            'current_api_cost': api_breakdown.amount,
                            'percentage_of_total': api_breakdown.percentage,
                            'trend': api_breakdown.trend
                        },
                        created_at=datetime.now()
                    ))

                # Check for inefficient provider usage
                if 'api_costs' in self.cost_breakdowns:
                    provider_details = self.cost_breakdowns['api_costs'].details.get('providers', [])
                    if provider_details:
                        most_expensive = max(provider_details, key=lambda x: x['cost'])
                        if most_expensive['cost'] > 50:
                            insights.append(BusinessInsight(
                                insight_id=str(uuid.uuid4()),
                                insight_type=InsightType.COST_OPTIMIZATION,
                                title=f"Expensive Provider: {most_expensive['provider']}",
                                description=f"Provider {most_expensive['provider']} costs ${most_expensive['cost']:.2f} for model {most_expensive['model']}",
                                impact_score=70,
                                confidence_score=80,
                                cost_savings_potential=most_expensive['cost'] * 0.2,
                                implementation_effort="low",
                                recommendations=[
                                    "Consider switching to more cost-effective models",
                                    "Compare alternative providers",
                                    "Implement provider failover for cost optimization"
                                ],
                                data_points={
                                    'provider': most_expensive['provider'],
                                    'model': most_expensive['model'],
                                    'cost': most_expensive['cost']
                                },
                                created_at=datetime.now()
                            ))

        except Exception as e:
            logger.error(f"Error generating cost optimization insights: {e}")

        return insights

    async def _generate_efficiency_insights(self) -> List[BusinessInsight]:
        """Generate efficiency insights"""
        insights = []

        try:
            # Get usage efficiency metrics
            cost_summary = self.analytics_engine.get_usage_summary(30)

            if cost_summary.total_requests > 0:
                cost_per_request = cost_summary.total_cost / cost_summary.total_requests
                tokens_per_request = cost_summary.total_tokens / cost_summary.total_requests

                # Check for low efficiency
                if cost_per_request > 0.1:  # More than 10 cents per request
                    insights.append(BusinessInsight(
                        insight_id=str(uuid.uuid4()),
                        insight_type=InsightType.EFFICIENCY_GAIN,
                        title="Low Request Efficiency",
                        description=f"Average cost per request is ${cost_per_request:.4f}",
                        impact_score=75,
                        confidence_score=85,
                        cost_savings_potential=cost_summary.total_cost * 0.25,
                        implementation_effort="medium",
                        recommendations=[
                            "Implement request batching",
                            "Use more efficient models for simple tasks",
                            "Add result caching",
                            "Optimize prompt engineering"
                        ],
                        data_points={
                            'cost_per_request': cost_per_request,
                            'tokens_per_request': tokens_per_request,
                            'total_requests': cost_summary.total_requests,
                            'total_cost': cost_summary.total_cost
                        },
                        created_at=datetime.now()
                    ))

                # Check token efficiency
                if tokens_per_request < 100:  # Less than 100 tokens per request
                    insights.append(BusinessInsight(
                        insight_id=str(uuid.uuid4()),
                        insight_type=InsightType.EFFICIENCY_GAIN,
                        title="Low Token Utilization",
                        description=f"Average {tokens_per_request:.0f} tokens per request suggests underutilization",
                        impact_score=60,
                        confidence_score=75,
                        cost_savings_potential=cost_summary.total_cost * 0.15,
                        implementation_effort="low",
                        recommendations=[
                            "Combine multiple small requests",
                            "Use context more effectively",
                            "Increase request complexity"
                        ],
                        data_points={
                            'tokens_per_request': tokens_per_request,
                            'cost_per_request': cost_per_request,
                            'efficiency_score': tokens_per_request / 1000
                        },
                        created_at=datetime.now()
                    ))

        except Exception as e:
            logger.error(f"Error generating efficiency insights: {e}")

        return insights

    async def _generate_strategic_insights(self) -> List[BusinessInsight]:
        """Generate strategic business insights"""
        insights = []

        try:
            # Get user growth trends
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT DATE(start_time) as date, COUNT(DISTINCT user_id) as new_users
                    FROM user_sessions
                    WHERE start_time >= datetime('now', '-30 days')
                    GROUP BY date
                    ORDER BY date
                ''')

                user_growth = cursor.fetchall()

            if len(user_growth) >= 7:
                recent_users = sum(row[1] for row in user_growth[-7:])
                previous_users = sum(row[1] for row in user_growth[-14:-7])

                if previous_users > 0:
                    growth_rate = ((recent_users - previous_users) / previous_users) * 100

                    if growth_rate < 0:
                        insights.append(BusinessInsight(
                            insight_id=str(uuid.uuid4()),
                            insight_type=InsightType.STRATEGIC_RECOMMENDATION,
                            title="Declining User Growth",
                            description=f"User growth rate is {growth_rate:.1f}% (negative)",
                            impact_score=90,
                            confidence_score=80,
                            cost_savings_potential=0,  # This is about growth, not cost
                            implementation_effort="high",
                            recommendations=[
                                "Review user acquisition strategies",
                                "Improve user onboarding experience",
                                "Add new features to attract users",
                                "Consider marketing campaigns"
                            ],
                            data_points={
                                'growth_rate': growth_rate,
                                'recent_users': recent_users,
                                'previous_users': previous_users
                            },
                            created_at=datetime.now()
                        ))

        except Exception as e:
            logger.error(f"Error generating strategic insights: {e}")

        return insights

    def _store_business_insight(self, insight: BusinessInsight):
        """Store business insight in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO business_insights
                    (insight_id, insight_type, title, description, impact_score,
                     confidence_score, cost_savings_potential, implementation_effort,
                     recommendations, data_points, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    insight.insight_id,
                    insight.insight_type.value,
                    insight.title,
                    insight.description,
                    insight.impact_score,
                    insight.confidence_score,
                    insight.cost_savings_potential,
                    insight.implementation_effort,
                    json.dumps(insight.recommendations),
                    json.dumps(insight.data_points),
                    insight.created_at
                ))
        except Exception as e:
            logger.error(f"Error storing business insight: {e}")

    async def _update_financial_forecasts(self):
        """Update financial forecasts"""
        try:
            # Forecast costs for next 30 days
            cost_forecast = await self._forecast_costs(30)
            self.forecasts['cost_forecast'] = cost_forecast
            self._store_forecast(cost_forecast)

            # Forecast user growth
            user_forecast = await self._forecast_user_growth(30)
            self.forecasts['user_forecast'] = user_forecast
            self._store_forecast(user_forecast)

        except Exception as e:
            logger.error(f"Error updating financial forecasts: {e}")

    async def _forecast_costs(self, days: int) -> FinancialForecast:
        """Forecast costs for the specified period"""
        try:
            # Get historical cost data
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT DATE(timestamp) as date, SUM(total_cost) as daily_cost
                    FROM cost_records
                    WHERE timestamp >= datetime('now', '-30 days')
                    GROUP BY date
                    ORDER BY date
                ''')

                historical_costs = cursor.fetchall()

            if not historical_costs:
                return FinancialForecast(
                    forecast_id=str(uuid.uuid4()),
                    metric_name="total_cost",
                    time_period=f"next_{days}_days",
                    forecast_values=[0.0] * days,
                    confidence_intervals=[(0.0, 0.0)] * days,
                    methodology="insufficient_data",
                    accuracy_score=0.0,
                    created_at=datetime.now()
                )

            # Simple linear trend forecast
            daily_costs = [row[1] for row in historical_costs]
            avg_daily_cost = np.mean(daily_costs)
            trend = np.polyfit(range(len(daily_costs)), daily_costs, 1)[0]

            # Generate forecast
            forecast_values = []
            confidence_intervals = []

            for i in range(days):
                forecast_value = avg_daily_cost + (trend * i)
                forecast_values.append(max(0, forecast_value))

                # Simple confidence interval (±20%)
                ci_lower = forecast_value * 0.8
                ci_upper = forecast_value * 1.2
                confidence_intervals.append((ci_lower, ci_upper))

            return FinancialForecast(
                forecast_id=str(uuid.uuid4()),
                metric_name="total_cost",
                time_period=f"next_{days}_days",
                forecast_values=forecast_values,
                confidence_intervals=confidence_intervals,
                methodology="linear_trend",
                accuracy_score=0.75,  # Estimated accuracy
                created_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error forecasting costs: {e}")
            return FinancialForecast(
                forecast_id=str(uuid.uuid4()),
                metric_name="total_cost",
                time_period=f"next_{days}_days",
                forecast_values=[0.0] * days,
                confidence_intervals=[(0.0, 0.0)] * days,
                methodology="error",
                accuracy_score=0.0,
                created_at=datetime.now()
            )

    async def _forecast_user_growth(self, days: int) -> FinancialForecast:
        """Forecast user growth"""
        try:
            # Get historical user data
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT DATE(start_time) as date, COUNT(DISTINCT user_id) as daily_users
                    FROM user_sessions
                    WHERE start_time >= datetime('now', '-30 days')
                    GROUP BY date
                    ORDER BY date
                ''')

                historical_users = cursor.fetchall()

            if not historical_users:
                return FinancialForecast(
                    forecast_id=str(uuid.uuid4()),
                    metric_name="daily_active_users",
                    time_period=f"next_{days}_days",
                    forecast_values=[0] * days,
                    confidence_intervals=[(0, 0)] * days,
                    methodology="insufficient_data",
                    accuracy_score=0.0,
                    created_at=datetime.now()
                )

            # Simple average-based forecast
            daily_users = [row[1] for row in historical_users]
            avg_daily_users = np.mean(daily_users)

            # Generate forecast with some random variation
            forecast_values = []
            confidence_intervals = []

            for i in range(days):
                # Add some random variation (±10%)
                variation = np.random.normal(0, 0.1)
                forecast_value = avg_daily_users * (1 + variation)
                forecast_values.append(max(0, int(forecast_value)))

                # Confidence interval
                ci_lower = forecast_value * 0.7
                ci_upper = forecast_value * 1.3
                confidence_intervals.append((int(ci_lower), int(ci_upper)))

            return FinancialForecast(
                forecast_id=str(uuid.uuid4()),
                metric_name="daily_active_users",
                time_period=f"next_{days}_days",
                forecast_values=forecast_values,
                confidence_intervals=confidence_intervals,
                methodology="average_with_variation",
                accuracy_score=0.65,
                created_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error forecasting user growth: {e}")
            return FinancialForecast(
                forecast_id=str(uuid.uuid4()),
                metric_name="daily_active_users",
                time_period=f"next_{days}_days",
                forecast_values=[0] * days,
                confidence_intervals=[(0, 0)] * days,
                methodology="error",
                accuracy_score=0.0,
                created_at=datetime.now()
            )

    def _store_forecast(self, forecast: FinancialForecast):
        """Store forecast in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO financial_forecasts
                    (forecast_id, metric_name, time_period, forecast_values,
                     confidence_intervals, methodology, accuracy_score, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    forecast.forecast_id,
                    forecast.metric_name,
                    forecast.time_period,
                    json.dumps(forecast.forecast_values),
                    json.dumps(forecast.confidence_intervals),
                    forecast.methodology,
                    forecast.accuracy_score,
                    forecast.created_at
                ))
        except Exception as e:
            logger.error(f"Error storing forecast: {e}")

    # Public API Methods
    def get_cost_breakdown(self, days: int = 30) -> Dict[str, Any]:
        """Get detailed cost breakdown"""
        return {
            category: {
                'amount': breakdown.amount,
                'percentage': breakdown.percentage,
                'trend': breakdown.trend,
                'details': breakdown.details
            }
            for category, breakdown in self.cost_breakdowns.items()
        }

    def get_roi_metrics(self) -> Dict[str, Any]:
        """Get ROI analysis metrics"""
        return {
            metric: {
                'current_value': roi.current_value,
                'previous_value': roi.previous_value,
                'change_percent': roi.change_percent,
                'trend': roi.trend,
                'confidence_level': roi.confidence_level,
                'recommendations': roi.recommendations
            }
            for metric, roi in self.roi_analyses.items()
        }

    def get_business_insights(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get business insights sorted by impact"""
        recent_insights = sorted(self.business_insights,
                                key=lambda x: (x.impact_score, x.confidence_score),
                                reverse=True)[:limit]

        return [
            {
                'insight_id': insight.insight_id,
                'type': insight.insight_type.value,
                'title': insight.title,
                'description': insight.description,
                'impact_score': insight.impact_score,
                'confidence_score': insight.confidence_score,
                'cost_savings_potential': insight.cost_savings_potential,
                'implementation_effort': insight.implementation_effort,
                'recommendations': insight.recommendations,
                'data_points': insight.data_points,
                'created_at': insight.created_at.isoformat()
            }
            for insight in recent_insights
        ]

    def get_financial_forecasts(self) -> Dict[str, Any]:
        """Get financial forecasts"""
        return {
            forecast_name: {
                'metric_name': forecast.metric_name,
                'time_period': forecast.time_period,
                'forecast_values': forecast.forecast_values,
                'confidence_intervals': forecast.confidence_intervals,
                'methodology': forecast.methodology,
                'accuracy_score': forecast.accuracy_score,
                'created_at': forecast.created_at.isoformat()
            }
            for forecast_name, forecast in self.forecasts.items()
        }

    def get_cost_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Get cost optimization opportunities"""
        opportunities = []

        # Analyze cost breakdowns for optimization opportunities
        for category, breakdown in self.cost_breakdowns.items():
            if breakdown.amount > 50:  # Significant cost category
                opportunities.append({
                    'category': category,
                    'current_cost': breakdown.amount,
                    'potential_savings': breakdown.amount * 0.25,  # 25% savings potential
                    'priority': 'high' if breakdown.amount > 100 else 'medium',
                    'difficulty': 'medium',
                    'estimated_timeline': '30-60 days',
                    'actions': [
                        f"Optimize {category.replace('_', ' ')} usage",
                        "Implement cost monitoring",
                        "Consider alternative solutions"
                    ]
                })

        return sorted(opportunities, key=lambda x: x['potential_savings'], reverse=True)

    def get_strategic_recommendations(self) -> List[Dict[str, Any]]:
        """Get strategic business recommendations"""
        recommendations = []

        # Analyze insights for strategic recommendations
        for insight in self.business_insights:
            if insight.insight_type == InsightType.STRATEGIC_RECOMMENDATION:
                recommendations.append({
                    'priority': 'high' if insight.impact_score > 80 else 'medium',
                    'category': 'strategic',
                    'title': insight.title,
                    'description': insight.description,
                    'expected_impact': insight.impact_score,
                    'implementation_effort': insight.implementation_effort,
                    'actions': insight.recommendations,
                    'data_support': insight.data_points
                })

        return recommendations

    def calculate_roi(self, investment: float, returns: float, period_days: int) -> Dict[str, Any]:
        """Calculate ROI for a specific investment"""
        try:
            roi_percentage = ((returns - investment) / investment) * 100 if investment > 0 else 0
            annualized_roi = roi_percentage * (365 / period_days)

            return {
                'investment': investment,
                'returns': returns,
                'net_gain': returns - investment,
                'roi_percentage': roi_percentage,
                'annualized_roi': annualized_roi,
                'payback_period_days': period_days * (investment / returns) if returns > 0 else float('inf'),
                'profitability_index': returns / investment if investment > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error calculating ROI: {e}")
            return {}

    def cleanup_old_data(self, retention_days: int = 90):
        """Clean up old business intelligence data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            with sqlite3.connect(self.db_path) as conn:
                tables = ['cost_breakdowns', 'roi_analyses', 'business_insights']
                for table in tables:
                    conn.execute(f'DELETE FROM {table} WHERE created_at < ?', (cutoff_date,))

            logger.info(f"Cleaned up BI data older than {retention_days} days")

        except Exception as e:
            logger.error(f"Error cleaning up BI data: {e}")