#!/usr/bin/env python3
"""
DuckBot Unified Cost Management System
Combines cost tracking, commands, and visualization into one comprehensive module
"""

import json
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging
import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import seaborn as sns
import pandas as pd
import numpy as np

# Set style for professional looking graphs
plt.style.use('dark_background')
sns.set_palette("husl")

logger = logging.getLogger(__name__)

@dataclass
class ModelPricing:
    """Pricing information for AI models"""
    provider: str
    model: str
    input_cost_per_1k: float  # Cost per 1K input tokens
    output_cost_per_1k: float  # Cost per 1K output tokens
    is_free: bool = False
    free_tier_limit: Optional[int] = None  # Tokens per month/day
    reset_period: str = "monthly"  # daily, monthly, yearly

@dataclass
class UsageRecord:
    """Individual API usage record"""
    timestamp: datetime
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_cost: float
    request_type: str  # chat, completion, etc.
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class CostSummary:
    """Cost summary for a time period"""
    total_cost: float = 0.0
    total_tokens: int = 0
    total_requests: int = 0
    by_provider: Dict[str, float] = field(default_factory=dict)
    by_model: Dict[str, float] = field(default_factory=dict)
    projected_monthly: float = 0.0

class CostTracker:
    """Core cost tracking functionality"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path(__file__).parent / "cost_tracking.db")
        self.lock = threading.Lock()
        self._init_database()
        self._load_default_pricing()

    def _init_database(self):
        """Initialize the cost tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cost_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_cost REAL NOT NULL,
                    request_type TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS pricing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_cost_per_1k REAL NOT NULL,
                    output_cost_per_1k REAL NOT NULL,
                    is_free BOOLEAN DEFAULT FALSE,
                    free_tier_limit INTEGER,
                    reset_period TEXT DEFAULT 'monthly',
                    UNIQUE(provider, model)
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_cost_records_timestamp
                ON cost_records(timestamp)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_cost_records_provider
                ON cost_records(provider)
            ''')

    def _load_default_pricing(self):
        """Load default pricing information"""
        default_pricing = [
            ModelPricing("openai", "gpt-4", 0.03, 0.06),
            ModelPricing("openai", "gpt-4-32k", 0.06, 0.12),
            ModelPricing("openai", "gpt-3.5-turbo", 0.0015, 0.002),
            ModelPricing("anthropic", "claude-instant", 0.00163, 0.00551),
            ModelPricing("anthropic", "claude-2", 0.008, 0.024),
            ModelPricing("openrouter", "openai/gpt-3.5-turbo", 0.001, 0.002),
            ModelPricing("openrouter", "anthropic/claude-instant", 0.001, 0.002),
        ]

        with sqlite3.connect(self.db_path) as conn:
            for pricing in default_pricing:
                conn.execute('''
                    INSERT OR IGNORE INTO pricing
                    (provider, model, input_cost_per_1k, output_cost_per_1k, is_free, free_tier_limit, reset_period)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (pricing.provider, pricing.model, pricing.input_cost_per_1k,
                      pricing.output_cost_per_1k, pricing.is_free, pricing.free_tier_limit,
                      pricing.reset_period))

    def record_usage(self, provider: str, model: str, input_tokens: int,
                    output_tokens: int, request_type: str, user_id: str = None,
                    session_id: str = None) -> float:
        """Record API usage and calculate cost"""
        with sqlite3.connect(self.db_path) as conn:
            # Get pricing
            cursor = conn.execute('''
                SELECT input_cost_per_1k, output_cost_per_1k, is_free, free_tier_limit, reset_period
                FROM pricing WHERE provider = ? AND model = ?
            ''', (provider, model))

            pricing = cursor.fetchone()
            if not pricing:
                logger.warning(f"No pricing found for {provider}/{model}")
                return 0.0

            input_cost_per_1k, output_cost_per_1k, is_free, free_tier_limit, reset_period = pricing

            # Check free tier limits
            if is_free and free_tier_limit:
                # Check usage within reset period
                period_start = self._get_period_start(reset_period)
                cursor = conn.execute('''
                    SELECT SUM(input_tokens + output_tokens)
                    FROM cost_records
                    WHERE provider = ? AND model = ? AND timestamp >= ?
                ''', (provider, model, period_start))

                current_usage = cursor.fetchone()[0] or 0
                if current_usage + input_tokens + output_tokens <= free_tier_limit:
                    total_cost = 0.0
                else:
                    # Charge only the excess
                    excess_tokens = current_usage + input_tokens + output_tokens - free_tier_limit
                    total_cost = (excess_tokens / 1000.0) * input_cost_per_1k
            else:
                # Calculate normal cost
                input_cost = (input_tokens / 1000.0) * input_cost_per_1k
                output_cost = (output_tokens / 1000.0) * output_cost_per_1k
                total_cost = input_cost + output_cost

            # Record usage
            conn.execute('''
                INSERT INTO cost_records
                (timestamp, provider, model, input_tokens, output_tokens, total_cost, request_type, user_id, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), provider, model, input_tokens, output_tokens,
                  total_cost, request_type, user_id, session_id))

            return total_cost

    def _get_period_start(self, reset_period: str) -> datetime:
        """Get start datetime for reset period"""
        now = datetime.now()
        if reset_period == "daily":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif reset_period == "weekly":
            days_since_monday = now.weekday()
            return now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
        elif reset_period == "monthly":
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif reset_period == "yearly":
            return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return now.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_usage_summary(self, days: int = 30) -> CostSummary:
        """Get cost summary for the specified number of days"""
        start_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            # Get overall summary
            cursor = conn.execute('''
                SELECT
                    SUM(total_cost) as total_cost,
                    SUM(input_tokens + output_tokens) as total_tokens,
                    COUNT(*) as total_requests
                FROM cost_records
                WHERE timestamp >= ?
            ''', (start_date,))

            row = cursor.fetchone()
            summary = CostSummary(
                total_cost=row[0] or 0.0,
                total_tokens=row[1] or 0,
                total_requests=row[2] or 0
            )

            # Get breakdown by provider
            cursor = conn.execute('''
                SELECT provider, SUM(total_cost) as cost
                FROM cost_records
                WHERE timestamp >= ?
                GROUP BY provider
            ''', (start_date,))

            summary.by_provider = dict(cursor.fetchall())

            # Get breakdown by model
            cursor = conn.execute('''
                SELECT model, SUM(total_cost) as cost
                FROM cost_records
                WHERE timestamp >= ?
                GROUP BY model
            ''', (start_date,))

            summary.by_model = dict(cursor.fetchall())

            # Calculate projected monthly cost
            if days > 0:
                daily_cost = summary.total_cost / days
                summary.projected_monthly = daily_cost * 30

            return summary

    def get_cost_predictions(self) -> Dict[str, Any]:
        """Generate cost predictions based on usage patterns"""
        # Get last 7 days for trend analysis
        summary_7d = self.get_usage_summary(7)
        summary_30d = self.get_usage_summary(30)

        # Simple linear projection
        if summary_30d.total_requests > 0:
            daily_trend = summary_7d.total_cost / 7
            projected_30d = daily_trend * 30
        else:
            projected_30d = summary_30d.total_cost

        return {
            "projected_30d": projected_30d,
            "current_30d": summary_30d.total_cost,
            "daily_average_7d": summary_7d.total_cost / 7 if summary_7d.total_cost > 0 else 0,
            "trend": "increasing" if projected_30d > summary_30d.total_cost else "stable"
        }

    def get_usage_by_date(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily usage data for visualization"""
        start_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT
                    DATE(timestamp) as date,
                    SUM(total_cost) as cost,
                    SUM(input_tokens + output_tokens) as tokens,
                    COUNT(*) as requests
                FROM cost_records
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            ''', (start_date,))

            return [
                {
                    "date": row[0],
                    "cost": row[1] or 0.0,
                    "tokens": row[2] or 0,
                    "requests": row[3] or 0
                }
                for row in cursor.fetchall()
            ]

class CostVisualizer:
    """Cost visualization functionality"""

    def __init__(self, cost_tracker):
        self.cost_tracker = cost_tracker
        self.colors = {
            'primary': '#00D4AA',
            'secondary': '#FF6B6B',
            'accent': '#4ECDC4',
            'warning': '#FFE66D',
            'danger': '#FF6B6B',
            'success': '#00D4AA',
            'background': '#2C3E50',
            'text': '#FFFFFF'
        }

    def create_cost_dashboard(self, days: int = 30, save_path: str = "cost_dashboard.png") -> str:
        """Create comprehensive cost dashboard with multiple visualizations"""
        # Get data
        summary = self.cost_tracker.get_usage_summary(days)
        predictions = self.cost_tracker.get_cost_predictions()
        daily_data = self.cost_tracker.get_usage_by_date(days)

        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.patch.set_facecolor(self.colors['background'])

        # 1. Daily Cost Trend
        if daily_data:
            dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in daily_data]
            costs = [d['cost'] for d in daily_data]

            ax1.plot(dates, costs, color=self.colors['primary'], linewidth=2, marker='o')
            ax1.fill_between(dates, costs, alpha=0.3, color=self.colors['primary'])
            ax1.set_title('Daily Cost Trend', color=self.colors['text'], fontsize=14, fontweight='bold')
            ax1.set_ylabel('Cost ($)', color=self.colors['text'])
            ax1.tick_params(colors=self.colors['text'])
            ax1.grid(True, alpha=0.3)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

        # 2. Cost by Provider
        if summary.by_provider:
            providers = list(summary.by_provider.keys())
            costs = list(summary.by_provider.values())

            wedges, texts, autotexts = ax2.pie(costs, labels=providers, autopct='%1.1f%%',
                                               colors=[self.colors['primary'], self.colors['secondary'],
                                                     self.colors['accent'], self.colors['warning']])
            ax2.set_title('Cost by Provider', color=self.colors['text'], fontsize=14, fontweight='bold')
            for text in texts + autotexts:
                text.set_color(self.colors['text'])

        # 3. Cost by Model (Top 5)
        if summary.by_model:
            # Sort and take top 5
            sorted_models = sorted(summary.by_model.items(), key=lambda x: x[1], reverse=True)[:5]
            models = [m[0] for m in sorted_models]
            costs = [m[1] for m in sorted_models]

            bars = ax3.bar(models, costs, color=self.colors['accent'])
            ax3.set_title('Cost by Model (Top 5)', color=self.colors['text'], fontsize=14, fontweight='bold')
            ax3.set_ylabel('Cost ($)', color=self.colors['text'])
            ax3.tick_params(colors=self.colors['text'])
            ax3.tick_params(axis='x', rotation=45)

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'${height:.3f}', ha='center', va='bottom', color=self.colors['text'])

        # 4. Usage Metrics
        metrics = ['Total Cost', 'Total Tokens', 'Requests', 'Daily Avg']
        values = [
            summary.total_cost,
            summary.total_tokens / 1000,  # Convert to K tokens
            summary.total_requests,
            summary.total_cost / days
        ]

        bars = ax4.bar(metrics, values, color=[self.colors['primary'], self.colors['secondary'],
                                              self.colors['accent'], self.colors['warning']])
        ax4.set_title('Usage Metrics', color=self.colors['text'], fontsize=14, fontweight='bold')
        ax4.tick_params(colors=self.colors['text'])

        # Format y-axis labels
        ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}'))

        # Add value labels
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if i == 0:  # Cost
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'${height:.4f}', ha='center', va='bottom', color=self.colors['text'])
            elif i == 1:  # Tokens
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.0f}K', ha='center', va='bottom', color=self.colors['text'])
            else:  # Count
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.0f}', ha='center', va='bottom', color=self.colors['text'])

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()

        return save_path

    def create_provider_comparison(self, days: int = 30, save_path: str = "provider_comparison.png") -> str:
        """Create provider comparison visualization"""
        daily_data = self.cost_tracker.get_usage_by_date(days)

        if not daily_data:
            return None

        # Organize data by provider and date
        provider_data = {}
        for entry in daily_data:
            date = entry['date']

            # Get provider breakdown for this date
            start_date = datetime.strptime(date, '%Y-%m-%d')
            end_date = start_date + timedelta(days=1)

            with sqlite3.connect(self.cost_tracker.db_path) as conn:
                cursor = conn.execute('''
                    SELECT provider, SUM(total_cost) as cost
                    FROM cost_records
                    WHERE timestamp >= ? AND timestamp < ?
                    GROUP BY provider
                ''', (start_date, end_date))

                for provider, cost in cursor.fetchall():
                    if provider not in provider_data:
                        provider_data[provider] = {}
                    provider_data[provider][date] = cost

        if not provider_data:
            return None

        # Create stacked area chart
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor(self.colors['background'])

        dates = sorted(set(date for provider in provider_data.values() for date in provider.keys()))
        date_objects = [datetime.strptime(d, '%Y-%m-%d') for d in dates]

        colors = [self.colors['primary'], self.colors['secondary'], self.colors['accent'],
                 self.colors['warning'], self.colors['danger']]

        bottom = [0] * len(dates)

        for i, (provider, data) in enumerate(provider_data.items()):
            costs = [data.get(date, 0) for date in dates]
            ax.fill_between(date_objects, bottom, [bottom[j] + costs[j] for j in range(len(dates))],
                          label=provider, alpha=0.7, color=colors[i % len(colors)])
            bottom = [bottom[j] + costs[j] for j in range(len(dates))]

        ax.set_title('Cost by Provider Over Time', color=self.colors['text'], fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', color=self.colors['text'])
        ax.set_ylabel('Cost ($)', color=self.colors['text'])
        ax.tick_params(colors=self.colors['text'])
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=self.colors['background'])
        plt.close()

        return save_path

class CostCommands(commands.Cog):
    """Cost tracking commands for Discord"""

    def __init__(self, bot):
        self.bot = bot
        self.cost_tracker = CostTracker()
        self.visualizer = CostVisualizer(self.cost_tracker)

    @app_commands.command(name="cost_summary", description="Get AI usage cost summary")
    @app_commands.describe(days="Number of days to analyze (default: 30)")
    async def cost_summary(self, interaction: discord.Interaction, days: int = 30):
        """Show cost summary with key metrics"""
        await interaction.response.defer()

        try:
            summary = self.cost_tracker.get_usage_summary(days)
            predictions = self.cost_tracker.get_cost_predictions()

            embed = discord.Embed(
                title="💰 DuckBot Cost Summary",
                description=f"Analysis for the last {days} days",
                color=0x00D4AA,
                timestamp=datetime.now()
            )

            # Main metrics
            embed.add_field(
                name="📊 Current Period",
                value=f"**Total Cost:** ${summary.total_cost:.4f}\n"
                      f"**Total Tokens:** {summary.total_tokens:,}\n"
                      f"**Total Requests:** {summary.total_requests:,}\n"
                      f"**Daily Average:** ${summary.total_cost/days:.4f}",
                inline=False
            )

            # Predictions
            embed.add_field(
                name="🔮 Predictions",
                value=f"**Projected Monthly:** ${predictions['projected_30d']:.4f}\n"
                      f"**Current Monthly:** ${predictions['current_30d']:.4f}\n"
                      f"**Trend:** {predictions['trend'].title()}",
                inline=False
            )

            # Top providers
            if summary.by_provider:
                top_providers = sorted(summary.by_provider.items(), key=lambda x: x[1], reverse=True)[:3]
                provider_text = "\n".join([f"**{provider}:** ${cost:.4f}" for provider, cost in top_providers])
                embed.add_field(name="🏆 Top Providers", value=provider_text, inline=False)

            # Top models
            if summary.by_model:
                top_models = sorted(summary.by_model.items(), key=lambda x: x[1], reverse=True)[:3]
                model_text = "\n".join([f"**{model}:** ${cost:.4f}" for model, cost in top_models])
                embed.add_field(name="🤖 Top Models", value=model_text, inline=False)

            embed.set_footer(text="DuckBot Cost Management System")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in cost_summary command: {e}")
            await interaction.followup.send("❌ Error generating cost summary", ephemeral=True)

    @app_commands.command(name="cost_chart", description="Generate cost visualization chart")
    @app_commands.describe(days="Number of days to analyze (default: 30)")
    async def cost_chart(self, interaction: discord.Interaction, days: int = 30):
        """Generate and display cost chart"""
        await interaction.response.defer()

        try:
            # Generate chart
            chart_path = self.visualizer.create_cost_dashboard(days)

            if not chart_path or not os.path.exists(chart_path):
                await interaction.followup.send("❌ No cost data available for chart generation", ephemeral=True)
                return

            # Send chart
            with open(chart_path, 'rb') as f:
                file = discord.File(f, filename="cost_dashboard.png")

                embed = discord.Embed(
                    title="📈 DuckBot Cost Dashboard",
                    description=f"Cost analysis for the last {days} days",
                    color=0x00D4AA,
                    timestamp=datetime.now()
                )

                await interaction.followup.send(embed=embed, file=file)

        except Exception as e:
            logger.error(f"Error in cost_chart command: {e}")
            await interaction.followup.send("❌ Error generating cost chart", ephemeral=True)

    @app_commands.command(name="cost_predict", description="Get cost predictions and trends")
    async def cost_predict(self, interaction: discord.Interaction):
        """Show cost predictions and trends"""
        await interaction.response.defer()

        try:
            predictions = self.cost_tracker.get_cost_predictions()
            summary_7d = self.cost_tracker.get_usage_summary(7)
            summary_30d = self.cost_tracker.get_usage_summary(30)

            embed = discord.Embed(
                title="🔮 DuckBot Cost Predictions",
                description="AI usage cost forecasts based on current trends",
                color=0x4ECDC4,
                timestamp=datetime.now()
            )

            # Trend analysis
            trend_emoji = "📈" if predictions['trend'] == "increasing" else "➡️"
            embed.add_field(
                name=f"{trend_emoji} Cost Trend",
                value=f"**Current Trend:** {predictions['trend'].title()}\n"
                      f"**Daily Average (7D):** ${predictions['daily_average_7d']:.4f}\n"
                      f"**Monthly Projection:** ${predictions['projected_30d']:.4f}\n"
                      f"**Current Monthly:** ${predictions['current_30d']:.4f}",
                inline=False
            )

            # Comparison
            if summary_30d.total_requests > 0:
                cost_per_request = summary_30d.total_cost / summary_30d.total_requests
                tokens_per_request = summary_30d.total_tokens / summary_30d.total_requests

                embed.add_field(
                    name="📊 Efficiency Metrics",
                    value=f"**Cost per Request:** ${cost_per_request:.6f}\n"
                          f"**Tokens per Request:** {tokens_per_request:.0f}\n"
                          f"**Cost per 1K Tokens:** ${(summary_30d.total_cost / summary_30d.total_tokens * 1000):.6f}",
                    inline=False
                )

            # Recommendations
            recommendations = []
            if predictions['projected_30d'] > predictions['current_30d'] * 1.1:
                recommendations.append("⚠️ Usage is increasing rapidly - monitor closely")
            if summary_30d.total_cost > 10:
                recommendations.append("💡 Consider cost optimization strategies")
            if len(summary_30d.by_provider) > 1:
                recommendations.append("🔄 Compare provider costs for optimization")

            if recommendations:
                embed.add_field(
                    name="💭 Recommendations",
                    value="\n".join(recommendations),
                    inline=False
                )

            embed.set_footer(text="Predictions based on recent usage patterns")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in cost_predict command: {e}")
            await interaction.followup.send("❌ Error generating cost predictions", ephemeral=True)

# For backward compatibility
CostTracker = CostTracker
CostVisualizer = CostVisualizer
CostCommands = CostCommands