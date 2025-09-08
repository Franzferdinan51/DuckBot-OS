#!/usr/bin/env python3
"""
Discord Commands for Cost Tracking
"""

import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import logging

from .cost_tracker import CostTracker
from .cost_visualizer import CostVisualizer

logger = logging.getLogger(__name__)

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
                title="[EMOJI] DuckBot Cost Summary",
                description=f"Analysis for the last {days} days",
                color=0x00D4AA,
                timestamp=datetime.now()
            )
            
            # Main metrics
            embed.add_field(
                name="[METRICS] Current Period", 
                value=f"**Total Cost:** ${summary.total_cost:.4f}\n"
                      f"**Total Tokens:** {summary.total_tokens:,}\n"
                      f"**Total Requests:** {summary.total_requests:,}",
                inline=True
            )
            
            # Projections
            trends = predictions.get('current_trends', {})
            embed.add_field(
                name="[STATS] Projections",
                value=f"**Monthly:** ${trends.get('monthly_projected', 0):.2f}\n"
                      f"**Daily Avg:** ${trends.get('daily_avg_cost', 0):.4f}\n"
                      f"**Yearly:** ${trends.get('yearly_projected', 0):.2f}",
                inline=True
            )
            
            # Free tier status
            free_status = predictions.get('free_tier_status', {})
            if free_status:
                free_info = []
                for model, status in free_status.items():
                    model_name = model.split('/')[-1].replace(':free', '')
                    usage_pct = status['usage_percent']
                    emoji = "[EMOJI]" if usage_pct < 50 else "[EMOJI]" if usage_pct < 80 else "[EMOJI]"
                    free_info.append(f"{emoji} {model_name}: {usage_pct:.1f}%")
                
                embed.add_field(
                    name="[EMOJI] Free Tier Usage",
                    value="\n".join(free_info[:5]),  # Limit to 5 models
                    inline=False
                )
            
            # Top cost drivers
            if summary.by_model:
                top_models = sorted(summary.by_model.items(), key=lambda x: x[1], reverse=True)[:3]
                model_info = []
                for model, cost in top_models:
                    model_name = model.split('/')[-1]
                    model_info.append(f"• {model_name}: ${cost:.4f}")
                
                embed.add_field(
                    name="[EMOJI] Top Cost Drivers",
                    value="\n".join(model_info),
                    inline=False
                )
            
            # Recommendations
            recommendations = predictions.get('recommendations', [])
            if recommendations:
                embed.add_field(
                    name="[TIP] Recommendations",
                    value="\n".join([f"• {rec}" for rec in recommendations[:3]]),
                    inline=False
                )
            
            embed.set_footer(text="Use /cost_dashboard for visual graphs")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in cost_summary: {e}")
            await interaction.followup.send(f"[ERROR] Error generating cost summary: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="cost_dashboard", description="Generate visual cost dashboard")
    @app_commands.describe(days="Number of days to analyze (default: 30)")
    async def cost_dashboard(self, interaction: discord.Interaction, days: int = 30):
        """Generate and send visual cost dashboard"""
        await interaction.response.defer()
        
        try:
            # Generate dashboard
            dashboard_path = self.visualizer.create_cost_dashboard(days)
            
            embed = discord.Embed(
                title="[METRICS] DuckBot Cost Dashboard",
                description=f"Visual analysis for the last {days} days",
                color=0x00D4AA,
                timestamp=datetime.now()
            )
            
            # Send the dashboard image
            file = discord.File(dashboard_path, filename="cost_dashboard.png")
            embed.set_image(url="attachment://cost_dashboard.png")
            
            # Clean up file after sending
            await interaction.followup.send(embed=embed, file=file)
            
            # Schedule cleanup
            asyncio.create_task(self._cleanup_file(dashboard_path, 60))
            
        except Exception as e:
            logger.error(f"Error in cost_dashboard: {e}")
            await interaction.followup.send(f"[ERROR] Error generating dashboard: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="set_budget", description="Set monthly budget alert")
    @app_commands.describe(
        budget="Monthly budget in USD",
        alert_threshold="Alert percentage (default: 80%)"
    )
    async def set_budget(self, interaction: discord.Interaction, budget: float, alert_threshold: int = 80):
        """Set budget alerts"""
        if budget <= 0:
            await interaction.response.send_message("[ERROR] Budget must be greater than $0", ephemeral=True)
            return
        
        if alert_threshold <= 0 or alert_threshold > 100:
            await interaction.response.send_message("[ERROR] Alert threshold must be between 1-100%", ephemeral=True)
            return
        
        try:
            self.cost_tracker.set_budget_alert(budget, alert_threshold / 100)
            
            embed = discord.Embed(
                title="[FOCUS] Budget Alert Set",
                description="Your budget monitoring is now active!",
                color=0x00D4AA
            )
            
            embed.add_field(name="Monthly Budget", value=f"${budget:.2f}", inline=True)
            embed.add_field(name="Alert Threshold", value=f"{alert_threshold}%", inline=True)
            embed.add_field(name="Alert Cost", value=f"${budget * alert_threshold / 100:.2f}", inline=True)
            
            embed.add_field(
                name="[STATS] What happens next?",
                value="• You'll get alerts when reaching the threshold\n"
                      "• Use `/budget_status` to check current usage\n"
                      "• Budget resets monthly automatically",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error setting budget: {e}")
            await interaction.response.send_message(f"[ERROR] Error setting budget: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="budget_status", description="Check current budget status")
    async def budget_status(self, interaction: discord.Interaction):
        """Check budget status and generate alert if needed"""
        await interaction.response.defer()
        
        try:
            status = self.cost_tracker.check_budget_status()
            
            if status.get("status") == "no_budget_set":
                embed = discord.Embed(
                    title="[FOCUS] No Budget Set",
                    description="Set up budget monitoring to track your spending!",
                    color=0xFFE66D
                )
                embed.add_field(
                    name="[TIP] Get Started",
                    value="Use `/set_budget <amount>` to set your monthly budget",
                    inline=False
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Create budget status embed
            budget = status['monthly_budget']
            current = status['current_spending']
            usage_pct = status['usage_percent']
            projected = status['projected_monthly']
            
            # Color based on status
            if status['over_budget']:
                color = 0xFF6B6B  # Red
                status_emoji = "[EMOJI]"
                status_text = "OVER BUDGET"
            elif status['needs_alert']:
                color = 0xFFE66D  # Yellow
                status_emoji = "[WARNING]"
                status_text = "APPROACHING LIMIT"
            else:
                color = 0x00D4AA  # Green
                status_emoji = "[OK]"
                status_text = "ON TRACK"
            
            embed = discord.Embed(
                title=f"{status_emoji} Budget Status: {status_text}",
                color=color,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="[METRICS] Current Month",
                value=f"**Spent:** ${current:.2f} / ${budget:.2f}\n"
                      f"**Usage:** {usage_pct:.1f}%\n"
                      f"**Remaining:** ${budget - current:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="[STATS] Projections",
                value=f"**Projected Monthly:** ${projected:.2f}\n"
                      f"**Over Budget:** {'Yes' if projected > budget else 'No'}\n"
                      f"**Est. Overage:** ${max(0, projected - budget):.2f}",
                inline=True
            )
            
            # Progress bar
            progress_chars = 20
            filled = int((usage_pct / 100) * progress_chars)
            empty = progress_chars - filled
            progress_bar = "█" * filled + "░" * empty
            
            embed.add_field(
                name="Progress",
                value=f"`{progress_bar}` {usage_pct:.1f}%",
                inline=False
            )
            
            # Generate budget graph if needed
            try:
                budget_graph = self.visualizer.create_budget_alert_graph()
                if budget_graph:
                    file = discord.File(budget_graph, filename="budget_status.png")
                    embed.set_image(url="attachment://budget_status.png")
                    await interaction.followup.send(embed=embed, file=file)
                    asyncio.create_task(self._cleanup_file(budget_graph, 60))
                else:
                    await interaction.followup.send(embed=embed)
            except:
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in budget_status: {e}")
            await interaction.followup.send(f"[ERROR] Error checking budget: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="cost_comparison", description="Compare model costs")
    async def cost_comparison(self, interaction: discord.Interaction):
        """Generate model cost comparison chart"""
        await interaction.response.defer()
        
        try:
            comparison_path = self.visualizer.create_model_comparison_chart()
            
            if not comparison_path:
                await interaction.followup.send("[ERROR] No cost comparison data available", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="[SEARCH] Model Cost Comparison",
                description="Compare costs across different AI models",
                color=0x00D4AA,
                timestamp=datetime.now()
            )
            
            # Add usage tips
            embed.add_field(
                name="[TIP] How to Read This",
                value="• **Top Chart:** Cost per 1,000 tokens\n"
                      "• **Bottom Chart:** Estimated monthly cost\n"
                      "• **Lower is Better:** for cost optimization",
                inline=False
            )
            
            file = discord.File(comparison_path, filename="cost_comparison.png")
            embed.set_image(url="attachment://cost_comparison.png")
            
            await interaction.followup.send(embed=embed, file=file)
            asyncio.create_task(self._cleanup_file(comparison_path, 60))
            
        except Exception as e:
            logger.error(f"Error in cost_comparison: {e}")
            await interaction.followup.send(f"[ERROR] Error generating comparison: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="usage_patterns", description="Show usage patterns heatmap")
    @app_commands.describe(days="Number of days to analyze (default: 30)")
    async def usage_patterns(self, interaction: discord.Interaction, days: int = 30):
        """Generate usage patterns heatmap"""
        await interaction.response.defer()
        
        try:
            heatmap_path = self.visualizer.create_usage_heatmap(days)
            
            if not heatmap_path:
                await interaction.followup.send("[ERROR] No usage pattern data available", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="[EMOJI] Usage Patterns",
                description=f"API usage patterns for the last {days} days",
                color=0x00D4AA,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="[METRICS] What This Shows",
                value="• **Darker Colors:** Higher usage\n"
                      "• **Top Chart:** Number of requests\n"
                      "• **Bottom Chart:** Cost distribution\n"
                      "• **Time Patterns:** Peak usage hours",
                inline=False
            )
            
            file = discord.File(heatmap_path, filename="usage_patterns.png")
            embed.set_image(url="attachment://usage_patterns.png")
            
            await interaction.followup.send(embed=embed, file=file)
            asyncio.create_task(self._cleanup_file(heatmap_path, 60))
            
        except Exception as e:
            logger.error(f"Error in usage_patterns: {e}")
            await interaction.followup.send(f"[ERROR] Error generating patterns: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="export_costs", description="Export detailed cost report")
    @app_commands.describe(
        days="Number of days to include (default: 30)",
        format="Export format (json or csv)"
    )
    @app_commands.choices(format=[
        app_commands.Choice(name="JSON", value="json"),
        app_commands.Choice(name="CSV", value="csv")
    ])
    async def export_costs(self, interaction: discord.Interaction, days: int = 30, format: str = "json"):
        """Export detailed cost report"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            report_data = self.cost_tracker.export_cost_report(days, format)
            
            # Save to file
            filename = f"duckbot_cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            with open(filename, "w") as f:
                f.write(report_data)
            
            embed = discord.Embed(
                title="[EMOJI] Cost Report Export",
                description=f"Detailed {format.upper()} report for the last {days} days",
                color=0x00D4AA,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="[METRICS] Report Contents",
                value="• Usage summary\n• Cost predictions\n• Model pricing data\n• Recommendations",
                inline=False
            )
            
            file = discord.File(filename)
            await interaction.followup.send(embed=embed, file=file, ephemeral=True)
            
            # Cleanup
            asyncio.create_task(self._cleanup_file(filename, 60))
            
        except Exception as e:
            logger.error(f"Error in export_costs: {e}")
            await interaction.followup.send(f"[ERROR] Error exporting report: {str(e)}", ephemeral=True)
    
    async def _cleanup_file(self, filepath: str, delay: int = 60):
        """Clean up temporary files after delay"""
        await asyncio.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            logger.error(f"Error cleaning up file {filepath}: {e}")

# Function to add these commands to existing Discord bot
async def setup_cost_commands(bot):
    """Add cost tracking commands to bot"""
    await bot.add_cog(CostCommands(bot))