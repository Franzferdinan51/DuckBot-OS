#!/usr/bin/env python3
"""
DuckBot Cost Visualization System
Creates beautiful graphs and charts for cost tracking and analysis
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import sqlite3
from pathlib import Path
import json
import logging

# Set style for professional looking graphs
plt.style.use('dark_background')
sns.set_palette("husl")

logger = logging.getLogger(__name__)

class CostVisualizer:
    """
    Creates beautiful, informative cost tracking visualizations
    """
    
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
        """
        Create comprehensive cost dashboard with multiple visualizations
        """
        # Get data
        summary = self.cost_tracker.get_usage_summary(days)
        predictions = self.cost_tracker.get_cost_predictions()
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 12))
        fig.suptitle(f'[DUCKBOT] DuckBot Cost Dashboard - Last {days} Days', 
                    fontsize=20, fontweight='bold', color=self.colors['text'])
        
        # 1. Daily cost trend
        ax1 = plt.subplot(2, 3, 1)
        self._plot_daily_trends(ax1, days)
        
        # 2. Cost by provider pie chart
        ax2 = plt.subplot(2, 3, 2)
        self._plot_provider_costs(ax2, summary)
        
        # 3. Token usage by model
        ax3 = plt.subplot(2, 3, 3)
        self._plot_token_usage(ax3, summary)
        
        # 4. Free tier usage gauges
        ax4 = plt.subplot(2, 3, 4)
        self._plot_free_tier_status(ax4, predictions)
        
        # 5. Cost predictions
        ax5 = plt.subplot(2, 3, 5)
        self._plot_cost_projections(ax5, predictions)
        
        # 6. Model efficiency comparison
        ax6 = plt.subplot(2, 3, 6)
        self._plot_model_efficiency(ax6, predictions)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor=self.colors['background'], edgecolor='none')
        
        return save_path
    
    def _plot_daily_trends(self, ax, days: int):
        """Plot daily cost trends"""
        # Get daily costs from database
        start_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.cost_tracker.db_path) as conn:
            query = """
                SELECT date(timestamp) as day, SUM(total_cost) as daily_cost
                FROM usage_records 
                WHERE timestamp >= ?
                GROUP BY date(timestamp)
                ORDER BY day
            """
            df = pd.read_sql_query(query, conn, params=[start_date.isoformat()])
        
        if not df.empty:
            df['day'] = pd.to_datetime(df['day'])
            
            ax.plot(df['day'], df['daily_cost'], 
                   color=self.colors['primary'], linewidth=2, marker='o', markersize=4)
            ax.fill_between(df['day'], df['daily_cost'], 
                           alpha=0.3, color=self.colors['primary'])
            
            # Add trend line
            z = np.polyfit(mdates.date2num(df['day']), df['daily_cost'], 1)
            p = np.poly1d(z)
            ax.plot(df['day'], p(mdates.date2num(df['day'])), 
                   "--", color=self.colors['warning'], alpha=0.8, linewidth=2)
        
        ax.set_title('[STATS] Daily Cost Trends', fontsize=12, fontweight='bold')
        ax.set_ylabel('Cost ($)')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def _plot_provider_costs(self, ax, summary):
        """Plot costs by provider as pie chart"""
        if summary.by_provider:
            providers = list(summary.by_provider.keys())
            costs = list(summary.by_provider.values())
            
            # Create custom colors
            colors = [self.colors['primary'], self.colors['secondary'], 
                     self.colors['accent'], self.colors['warning']]
            
            wedges, texts, autotexts = ax.pie(costs, labels=providers, autopct='%1.1f%%',
                                            colors=colors[:len(providers)],
                                            textprops={'color': 'white', 'fontweight': 'bold'})
            
            # Add cost values to labels
            for i, (provider, cost) in enumerate(summary.by_provider.items()):
                texts[i].set_text(f'{provider}\n${cost:.2f}')
        else:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)
        
        ax.set_title('[EMOJI] Cost by Provider', fontsize=12, fontweight='bold')
    
    def _plot_token_usage(self, ax, summary):
        """Plot token usage by model as horizontal bar chart"""
        if summary.free_tier_usage:
            models = list(summary.free_tier_usage.keys())
            tokens = list(summary.free_tier_usage.values())
            
            # Truncate model names for display
            display_names = [name.split('/')[-1].replace(':free', '') for name in models]
            
            bars = ax.barh(display_names, tokens, color=self.colors['accent'])
            
            # Add value labels on bars
            for i, (bar, token_count) in enumerate(zip(bars, tokens)):
                width = bar.get_width()
                ax.text(width + max(tokens) * 0.01, bar.get_y() + bar.get_height()/2,
                       f'{token_count:,}', ha='left', va='center', fontweight='bold')
        
        ax.set_title('[FOCUS] Token Usage by Model', fontsize=12, fontweight='bold')
        ax.set_xlabel('Tokens')
    
    def _plot_free_tier_status(self, ax, predictions):
        """Plot free tier usage as gauge charts"""
        free_tier_data = predictions.get('free_tier_status', {})
        
        if free_tier_data:
            # Create gauge-style visualization
            models = list(free_tier_data.keys())
            n_models = len(models)
            
            if n_models > 0:
                # Create circular gauges
                angles = np.linspace(0, 2*np.pi, n_models, endpoint=False)
                
                for i, (model, data) in enumerate(free_tier_data.items()):
                    usage_percent = min(data['usage_percent'], 100) / 100
                    
                    # Draw outer circle
                    circle = plt.Circle((0.5 + 0.3*np.cos(angles[i]), 
                                       0.5 + 0.3*np.sin(angles[i])), 
                                      0.15, fill=False, color='white', linewidth=2)
                    ax.add_patch(circle)
                    
                    # Draw usage arc
                    if usage_percent > 0:
                        arc_angle = usage_percent * 360
                        color = (self.colors['success'] if usage_percent < 0.5 
                               else self.colors['warning'] if usage_percent < 0.8 
                               else self.colors['danger'])
                        
                        wedge = plt.matplotlib.patches.Wedge(
                            (0.5 + 0.3*np.cos(angles[i]), 0.5 + 0.3*np.sin(angles[i])),
                            0.15, 90, 90-arc_angle, 
                            facecolor=color, alpha=0.7
                        )
                        ax.add_patch(wedge)
                    
                    # Add labels
                    model_name = model.split('/')[-1].replace(':free', '')
                    ax.text(0.5 + 0.3*np.cos(angles[i]), 
                           0.5 + 0.3*np.sin(angles[i]) - 0.25,
                           f'{model_name}\n{usage_percent*100:.1f}%',
                           ha='center', va='center', fontsize=8, fontweight='bold')
                
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_aspect('equal')
                ax.axis('off')
        
        ax.set_title('[EMOJI] Free Tier Usage', fontsize=12, fontweight='bold')
    
    def _plot_cost_projections(self, ax, predictions):
        """Plot cost projections"""
        trends = predictions.get('current_trends', {})
        
        if trends:
            periods = ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly']
            costs = [
                trends.get('daily_avg_cost', 0),
                trends.get('weekly_avg_cost', 0),
                trends.get('monthly_projected', 0),
                trends.get('quarterly_projected', 0),
                trends.get('yearly_projected', 0)
            ]
            
            bars = ax.bar(periods, costs, 
                         color=[self.colors['primary'], self.colors['accent'], 
                               self.colors['secondary'], self.colors['warning'],
                               self.colors['danger']])
            
            # Add value labels on bars
            for bar, cost in zip(bars, costs):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + max(costs) * 0.01,
                       f'${cost:.2f}', ha='center', va='bottom', fontweight='bold')
        
        ax.set_title('[METRICS] Cost Projections', fontsize=12, fontweight='bold')
        ax.set_ylabel('Cost ($)')
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def _plot_model_efficiency(self, ax, predictions):
        """Plot model efficiency (cost per 1K tokens)"""
        efficiency = predictions.get('token_efficiency', {})
        
        if efficiency:
            models = list(efficiency.keys())
            costs_per_1k = [data['cost_per_1k_tokens'] for data in efficiency.values()]
            
            # Truncate model names
            display_names = [name.split('/')[-1].replace(':free', '') for name in models]
            
            bars = ax.bar(display_names, costs_per_1k, color=self.colors['accent'])
            
            # Add value labels
            for bar, cost in zip(bars, costs_per_1k):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + max(costs_per_1k) * 0.01,
                       f'${cost:.4f}', ha='center', va='bottom', fontweight='bold', fontsize=8)
        
        ax.set_title('[FAST] Model Efficiency', fontsize=12, fontweight='bold')
        ax.set_ylabel('Cost per 1K tokens ($)')
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def create_budget_alert_graph(self, save_path: str = "budget_alert.png") -> Optional[str]:
        """Create budget status visualization"""
        budget_status = self.cost_tracker.check_budget_status()
        
        if budget_status.get("status") == "no_budget_set":
            return None
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        fig.suptitle('[FOCUS] Budget Monitoring Dashboard', fontsize=16, fontweight='bold')
        
        # Budget gauge
        budget = budget_status['monthly_budget']
        current = budget_status['current_spending']
        projected = budget_status['projected_monthly']
        usage_percent = budget_status['usage_percent']
        
        # Create gauge chart
        theta = np.linspace(0, np.pi, 100)
        
        # Background arc
        ax1.plot(np.cos(theta), np.sin(theta), color='gray', linewidth=10, alpha=0.3)
        
        # Usage arc
        usage_theta = theta[: int(usage_percent)]
        color = (self.colors['success'] if usage_percent < 50 
                else self.colors['warning'] if usage_percent < 80 
                else self.colors['danger'])
        
        ax1.plot(np.cos(usage_theta), np.sin(usage_theta), color=color, linewidth=10)
        
        # Add text
        ax1.text(0, -0.3, f'${current:.2f} / ${budget:.2f}', 
                ha='center', va='center', fontsize=14, fontweight='bold')
        ax1.text(0, -0.5, f'{usage_percent:.1f}% Used', 
                ha='center', va='center', fontsize=12)
        
        ax1.set_xlim(-1.2, 1.2)
        ax1.set_ylim(-0.6, 1.2)
        ax1.set_aspect('equal')
        ax1.axis('off')
        ax1.set_title('Current Month Budget', fontsize=12, fontweight='bold')
        
        # Projection comparison
        categories = ['Current\nSpending', 'Projected\nMonthly', 'Budget\nLimit']
        values = [current, projected, budget]
        colors = [self.colors['primary'], self.colors['warning'], self.colors['success']]
        
        bars = ax2.bar(categories, values, color=colors)
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + max(values) * 0.01,
                    f'${value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Add warning line if over budget
        if projected > budget:
            ax2.axhline(y=budget, color=self.colors['danger'], linestyle='--', linewidth=2)
            ax2.text(len(categories)/2, budget + max(values) * 0.05, 'BUDGET LIMIT', 
                    ha='center', color=self.colors['danger'], fontweight='bold')
        
        ax2.set_title('Budget vs Projections', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Cost ($)')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor=self.colors['background'], edgecolor='none')
        
        return save_path
    
    def create_model_comparison_chart(self, save_path: str = "model_comparison.png") -> str:
        """Create detailed model cost comparison chart"""
        predictions = self.cost_tracker.get_cost_predictions()
        comparisons = predictions.get('cost_comparisons', {})
        
        if not comparisons:
            return None
        
        # Prepare data
        models = []
        costs_per_1k = []
        monthly_costs = []
        
        for model, data in comparisons.items():
            models.append(model.split('/')[-1])  # Clean model name
            costs_per_1k.append(data['cost_per_1k_tokens'])
            monthly_costs.append(data['estimated_monthly_cost'])
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle('[SEARCH] Model Cost Comparison Analysis', fontsize=16, fontweight='bold')
        
        # Cost per 1K tokens
        bars1 = ax1.bar(models, costs_per_1k, color=self.colors['primary'])
        ax1.set_title('Cost per 1,000 Tokens by Model', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Cost ($)')
        
        # Add value labels
        for bar, cost in zip(bars1, costs_per_1k):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + max(costs_per_1k) * 0.01,
                    f'${cost:.4f}', ha='center', va='bottom', fontweight='bold', rotation=45)
        
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Estimated monthly costs
        bars2 = ax2.bar(models, monthly_costs, color=self.colors['secondary'])
        ax2.set_title('Estimated Monthly Costs (Based on Current Usage)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Monthly Cost ($)')
        ax2.set_xlabel('Model')
        
        # Add value labels
        for bar, cost in zip(bars2, monthly_costs):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + max(monthly_costs) * 0.01,
                    f'${cost:.2f}', ha='center', va='bottom', fontweight='bold', rotation=45)
        
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor=self.colors['background'], edgecolor='none')
        
        return save_path
    
    def create_usage_heatmap(self, days: int = 30, save_path: str = "usage_heatmap.png") -> str:
        """Create usage heatmap showing patterns over time"""
        start_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.cost_tracker.db_path) as conn:
            query = """
                SELECT 
                    date(timestamp) as day,
                    strftime('%H', timestamp) as hour,
                    SUM(input_tokens + output_tokens) as tokens,
                    SUM(total_cost) as cost,
                    COUNT(*) as requests
                FROM usage_records 
                WHERE timestamp >= ?
                GROUP BY date(timestamp), strftime('%H', timestamp)
                ORDER BY day, hour
            """
            df = pd.read_sql_query(query, conn, params=[start_date.isoformat()])
        
        if df.empty:
            return None
        
        # Create pivot table for heatmap
        df['day'] = pd.to_datetime(df['day'])
        df['hour'] = df['hour'].astype(int)
        
        # Create heatmap data
        pivot_requests = df.pivot(index='day', columns='hour', values='requests').fillna(0)
        pivot_cost = df.pivot(index='day', columns='hour', values='cost').fillna(0)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
        fig.suptitle('[EMOJI] Usage Patterns Heatmap', fontsize=16, fontweight='bold')
        
        # Requests heatmap
        sns.heatmap(pivot_requests, ax=ax1, cmap='YlOrRd', annot=False, fmt='.0f',
                   cbar_kws={'label': 'Number of Requests'})
        ax1.set_title('API Requests by Hour and Day', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Hour of Day')
        ax1.set_ylabel('Date')
        
        # Cost heatmap
        sns.heatmap(pivot_cost, ax=ax2, cmap='Reds', annot=False, fmt='.3f',
                   cbar_kws={'label': 'Cost ($)'})
        ax2.set_title('API Costs by Hour and Day', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Hour of Day')
        ax2.set_ylabel('Date')
        
        # Format date labels
        for ax in [ax1, ax2]:
            ax.set_yticklabels([d.strftime('%m/%d') for d in pivot_requests.index[::max(1, len(pivot_requests)//10)]])
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor=self.colors['background'], edgecolor='none')
        
        return save_path
    
    def generate_cost_report_with_graphs(self, days: int = 30) -> Dict[str, str]:
        """Generate comprehensive cost report with all visualizations"""
        graphs = {}
        
        try:
            graphs['dashboard'] = self.create_cost_dashboard(days)
            logger.info("[OK] Created cost dashboard")
        except Exception as e:
            logger.error(f"[ERROR] Dashboard creation failed: {e}")
        
        try:
            budget_graph = self.create_budget_alert_graph()
            if budget_graph:
                graphs['budget'] = budget_graph
                logger.info("[OK] Created budget alert graph")
        except Exception as e:
            logger.error(f"[ERROR] Budget graph creation failed: {e}")
        
        try:
            comparison_graph = self.create_model_comparison_chart()
            if comparison_graph:
                graphs['comparison'] = comparison_graph
                logger.info("[OK] Created model comparison chart")
        except Exception as e:
            logger.error(f"[ERROR] Comparison chart creation failed: {e}")
        
        try:
            heatmap = self.create_usage_heatmap(days)
            if heatmap:
                graphs['heatmap'] = heatmap
                logger.info("[OK] Created usage heatmap")
        except Exception as e:
            logger.error(f"[ERROR] Heatmap creation failed: {e}")
        
        return graphs