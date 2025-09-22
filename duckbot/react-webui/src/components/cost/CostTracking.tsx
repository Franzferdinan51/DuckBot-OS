import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  Target,
  BarChart3,
  PieChart,
  Download,
  Settings,
  Lightbulb,
  Calendar,
  Filter
} from 'lucide-react';

interface CostTrackingProps {
  className?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface CostData {
  totalCost: number;
  monthlyBudget: number;
  dailyAverage: number;
  todayCost: number;
  thisMonthCost: number;
  projectedMonthCost: number;
  savings: number;
  providers: Array<{
    name: string;
    cost: number;
    usage: number;
    percentage: number;
    trend: 'up' | 'down' | 'stable';
    icon: React.ReactNode;
  }>;
  categories: Array<{
    name: string;
    cost: number;
    percentage: number;
    trend: 'up' | 'down' | 'stable';
  }>;
  recommendations: Array<{
    id: string;
    type: 'cost' | 'performance' | 'efficiency';
    title: string;
    description: string;
    impact: 'high' | 'medium' | 'low';
    potentialSavings: number;
    priority: number;
  }>;
  historicalData: Array<{
    date: string;
    cost: number;
    usage: number;
  }>;
}

const CostTracking: React.FC<CostTrackingProps> = ({
  className,
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
}) => {
  const { colors } = useTheme();
  const [costData, setCostData] = useState<CostData | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedTimeframe, setSelectedTimeframe] = useState<'7d' | '30d' | '90d'>('30d');

  // Generate mock cost data
  const generateMockCostData = (): CostData => {
    const baseCost = 150;
    const budget = 500;

    return {
      totalCost: baseCost,
      monthlyBudget: budget,
      dailyAverage: baseCost / 30,
      todayCost: 5.20,
      thisMonthCost: baseCost,
      projectedMonthCost: baseCost * 1.15,
      savings: 45.30,
      providers: [
        {
          name: 'OpenAI',
          cost: 89.50,
          usage: 125000,
          percentage: 59.7,
          trend: 'up',
          icon: <Zap size={16} style={{ color: colors.primary }} />
        },
        {
          name: 'Anthropic',
          cost: 32.10,
          usage: 45000,
          percentage: 21.4,
          trend: 'stable',
          icon: <Target size={16} style={{ color: colors.success }} />
        },
        {
          name: 'Qwen',
          cost: 18.90,
          usage: 28000,
          percentage: 12.6,
          trend: 'down',
          icon: <Lightbulb size={16} style={{ color: colors.warning }} />
        },
        {
          name: 'Others',
          cost: 9.50,
          usage: 15000,
          percentage: 6.3,
          trend: 'up',
          icon: <BarChart3 size={16} style={{ color: colors.textSecondary }} />
        }
      ],
      categories: [
        { name: 'Chat & Conversations', cost: 67.80, percentage: 45.2, trend: 'up' },
        { name: 'Code Generation', cost: 42.30, percentage: 28.2, trend: 'stable' },
        { name: 'Analysis & Insights', cost: 25.90, percentage: 17.3, trend: 'down' },
        { name: 'Automation', cost: 14.00, percentage: 9.3, trend: 'up' }
      ],
      recommendations: [
        {
          id: '1',
          type: 'cost',
          title: 'Switch to Local Models for Routine Tasks',
          description: 'Move 40% of routine requests to local Qwen models to reduce cloud costs by ~$35/month',
          impact: 'high',
          potentialSavings: 35.00,
          priority: 1
        },
        {
          id: '2',
          type: 'efficiency',
          title: 'Optimize Prompt Length',
          description: 'Reduce average prompt length by 15% through template optimization',
          impact: 'medium',
          potentialSavings: 12.50,
          priority: 2
        },
        {
          id: '3',
          type: 'performance',
          title: 'Implement Response Caching',
          description: 'Cache repetitive queries to reduce API calls by 25%',
          impact: 'medium',
          potentialSavings: 18.75,
          priority: 3
        },
        {
          id: '4',
          type: 'cost',
          title: 'Batch Processing for Analysis',
          description: 'Group analysis requests during off-peak hours for better rates',
          impact: 'low',
          potentialSavings: 8.20,
          priority: 4
        }
      ],
      historicalData: Array.from({ length: 30 }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (29 - i));
        return {
          date: date.toISOString().split('T')[0],
          cost: Math.random() * 8 + 2,
          usage: Math.random() * 10000 + 5000
        };
      })
    };
  };

  const refreshCostData = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      setCostData(generateMockCostData());
    } catch (error) {
      console.error('Error refreshing cost data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshCostData();
    if (autoRefresh) {
      const interval = setInterval(refreshCostData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, selectedTimeframe]);

  const budgetUtilization = costData ? (costData.thisMonthCost / costData.monthlyBudget) * 100 : 0;
  const isOverBudget = budgetUtilization > 100;
  const daysRemaining = Math.ceil((new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <DollarSign size={24} style={{ color: colors.primary }} />
          <div>
            <h2 className="text-xl font-bold" style={{ color: colors.text }}>
              Cost Tracking & Optimization
            </h2>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              Monitor AI costs and optimize resource usage
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Timeframe Selector */}
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value as any)}
            className="px-3 py-2 rounded-lg border text-sm"
            style={{
              backgroundColor: colors.background,
              borderColor: colors.border,
              color: colors.text,
            }}
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>

          {/* Export Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center space-x-2 px-3 py-2 rounded-lg border text-sm"
            style={{
              backgroundColor: colors.background,
              borderColor: colors.border,
              color: colors.text,
            }}
          >
            <Download size={16} />
            <span>Export</span>
          </motion.button>

          {/* Settings Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="p-2 rounded-lg border"
            style={{
              backgroundColor: colors.background,
              borderColor: colors.border,
              color: colors.textSecondary,
            }}
          >
            <Settings size={18} />
          </motion.button>
        </div>
      </div>

      {/* Budget Overview Cards */}
      {costData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Total Cost */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-lg border"
            style={{ backgroundColor: colors.surface, borderColor: colors.border }}
          >
            <div className="flex items-center justify-between mb-2">
              <DollarSign size={20} style={{ color: colors.primary }} />
              <span className="text-xs font-medium px-2 py-1 rounded-full"
                    style={{
                      backgroundColor: costData.savings > 0 ? `${colors.success}20` : `${colors.error}20`,
                      color: costData.savings > 0 ? colors.success : colors.error,
                    }}>
                    {costData.savings > 0 ? `-$${costData.savings.toFixed(2)}` : `+$${Math.abs(costData.savings).toFixed(2)}`}
                  </span>
            </div>
            <h3 className="text-lg font-bold" style={{ color: colors.text }}>
              ${costData.totalCost.toFixed(2)}
            </h3>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              Total Cost
            </p>
          </motion.div>

          {/* Budget Utilization */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="p-4 rounded-lg border"
            style={{ backgroundColor: colors.surface, borderColor: colors.border }}
          >
            <div className="flex items-center justify-between mb-2">
              <Target size={20} style={{ color: isOverBudget ? colors.error : colors.success }} />
              <span className="text-xs font-medium px-2 py-1 rounded-full"
                    style={{
                      backgroundColor: isOverBudget ? `${colors.error}20` : `${colors.success}20`,
                      color: isOverBudget ? colors.error : colors.success,
                    }}>
                    {budgetUtilization.toFixed(1)}%
                  </span>
            </div>
            <h3 className="text-lg font-bold" style={{ color: colors.text }}>
              ${costData.thisMonthCost.toFixed(2)}
            </h3>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              of ${costData.monthlyBudget} budget
            </p>
            {/* Progress bar */}
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2" style={{ backgroundColor: colors.border }}>
              <div
                className="h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${Math.min(budgetUtilization, 100)}%`,
                  backgroundColor: isOverBudget ? colors.error : colors.success
                }}
              />
            </div>
          </motion.div>

          {/* Daily Average */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="p-4 rounded-lg border"
            style={{ backgroundColor: colors.surface, borderColor: colors.border }}
          >
            <div className="flex items-center justify-between mb-2">
              <Clock size={20} style={{ color: colors.warning }} />
              <span className="text-xs font-medium px-2 py-1 rounded-full"
                    style={{
                      backgroundColor: `${colors.warning}20`,
                      color: colors.warning,
                    }}>
                    {daysRemaining} days left
                  </span>
            </div>
            <h3 className="text-lg font-bold" style={{ color: colors.text }}>
              ${costData.dailyAverage.toFixed(2)}
            </h3>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              Daily Average
            </p>
          </motion.div>

          {/* Projected Cost */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="p-4 rounded-lg border"
            style={{ backgroundColor: colors.surface, borderColor: colors.border }}
          >
            <div className="flex items-center justify-between mb-2">
              <TrendingUp size={20} style={{ color: costData.projectedMonthCost > costData.monthlyBudget ? colors.error : colors.success }} />
              <span className="text-xs font-medium px-2 py-1 rounded-full"
                    style={{
                      backgroundColor: costData.projectedMonthCost > costData.monthlyBudget ? `${colors.error}20` : `${colors.success}20`,
                      color: costData.projectedMonthCost > costData.monthlyBudget ? colors.error : colors.success,
                    }}>
                    {((costData.projectedMonthCost - costData.monthlyBudget) / costData.monthlyBudget * 100).toFixed(1)}% over
                  </span>
            </div>
            <h3 className="text-lg font-bold" style={{ color: colors.text }}>
              ${costData.projectedMonthCost.toFixed(2)}
            </h3>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              Projected Monthly
            </p>
          </motion.div>
        </div>
      )}

      {/* Provider Breakdown */}
      {costData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Provider Costs */}
          <div className="p-4 rounded-lg border"
               style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
            <h3 className="text-lg font-semibold mb-4" style={{ color: colors.text }}>
              Provider Breakdown
            </h3>
            <div className="space-y-4">
              {costData.providers.map((provider, index) => (
                <div key={provider.name} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {provider.icon}
                    <div>
                      <p className="font-medium text-sm" style={{ color: colors.text }}>
                        {provider.name}
                      </p>
                      <p className="text-xs" style={{ color: colors.textSecondary }}>
                        {provider.usage.toLocaleString()} tokens
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-sm" style={{ color: colors.text }}>
                      ${provider.cost.toFixed(2)}
                    </p>
                    <div className="flex items-center space-x-1">
                      <span className="text-xs" style={{ color: colors.textSecondary }}>
                        {provider.percentage.toFixed(1)}%
                      </span>
                      {provider.trend === 'up' && <TrendingUp size={12} style={{ color: colors.error }} />}
                      {provider.trend === 'down' && <TrendingDown size={12} style={{ color: colors.success }} />}
                      {provider.trend === 'stable' && <div className="w-3 h-0.5 rounded-full" style={{ backgroundColor: colors.textSecondary }} />}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Category Breakdown */}
          <div className="p-4 rounded-lg border"
               style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
            <h3 className="text-lg font-semibold mb-4" style={{ color: colors.text }}>
              Category Breakdown
            </h3>
            <div className="space-y-4">
              {costData.categories.map((category, index) => (
                <div key={category.name} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm" style={{ color: colors.text }}>
                      {category.name}
                    </p>
                    <div className="flex items-center space-x-2 mt-1">
                      <div className="w-24 bg-gray-200 rounded-full h-2" style={{ backgroundColor: colors.border }}>
                        <div
                          className="h-2 rounded-full"
                          style={{
                            width: `${category.percentage}%`,
                            backgroundColor: colors.primary
                          }}
                        />
                      </div>
                      <span className="text-xs" style={{ color: colors.textSecondary }}>
                        {category.percentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-sm" style={{ color: colors.text }}>
                      ${category.cost.toFixed(2)}
                    </p>
                    <div className="flex items-center justify-end space-x-1">
                      {category.trend === 'up' && <TrendingUp size={12} style={{ color: colors.error }} />}
                      {category.trend === 'down' && <TrendingDown size={12} style={{ color: colors.success }} />}
                      {category.trend === 'stable' && <div className="w-3 h-0.5 rounded-full" style={{ backgroundColor: colors.textSecondary }} />}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* AI Recommendations */}
      {costData && (
        <div className="p-4 rounded-lg border"
             style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold" style={{ color: colors.text }}>
              AI Optimization Recommendations
            </h3>
            <div className="flex items-center space-x-2">
              <span className="text-sm" style={{ color: colors.textSecondary }}>
                Total Potential Savings:
              </span>
              <span className="font-bold text-sm" style={{ color: colors.success }}>
                ${costData.recommendations.reduce((sum, rec) => sum + rec.potentialSavings, 0).toFixed(2)}
              </span>
            </div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {costData.recommendations.map((rec, index) => (
              <motion.div
                key={rec.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-4 rounded-lg border-l-4"
                style={{
                  backgroundColor: colors.background,
                  borderLeftColor: rec.impact === 'high' ? colors.error :
                                  rec.impact === 'medium' ? colors.warning : colors.info,
                  borderColor: 'transparent',
                }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      {rec.type === 'cost' && <DollarSign size={14} style={{ color: colors.primary }} />}
                      {rec.type === 'performance' && <Zap size={14} style={{ color: colors.warning }} />}
                      {rec.type === 'efficiency' && <Target size={14} style={{ color: colors.success }} />}
                      <h4 className="font-medium text-sm" style={{ color: colors.text }}>
                        {rec.title}
                      </h4>
                    </div>
                    <p className="text-xs" style={{ color: colors.textSecondary }}>
                      {rec.description}
                    </p>
                  </div>
                  <div className="text-right ml-4">
                    <span className="text-xs font-medium px-2 py-1 rounded-full"
                          style={{
                            backgroundColor: rec.impact === 'high' ? `${colors.error}20` :
                                            rec.impact === 'medium' ? `${colors.warning}20` : `${colors.info}20`,
                            color: rec.impact === 'high' ? colors.error :
                                   rec.impact === 'medium' ? colors.warning : colors.info,
                          }}>
                          {rec.impact.toUpperCase()}
                        </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div>
                      <p className="text-xs" style={{ color: colors.textSecondary }}>
                        Potential Savings
                      </p>
                      <p className="font-bold text-sm" style={{ color: colors.success }}>
                        ${rec.potentialSavings.toFixed(2)}/mo
                      </p>
                    </div>
                    <div>
                      <p className="text-xs" style={{ color: colors.textSecondary }}>
                        Priority
                      </p>
                      <p className="font-medium text-sm" style={{ color: colors.text }}>
                        #{rec.priority}
                      </p>
                    </div>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-3 py-1 rounded text-xs font-medium"
                    style={{
                      backgroundColor: colors.primary,
                      color: colors.background,
                    }}
                  >
                    Apply
                  </motion.button>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Cost Trend Chart */}
      {costData && (
        <div className="p-4 rounded-lg border"
             style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold" style={{ color: colors.text }}>
              Cost Trends
            </h3>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: colors.primary }} />
                <span style={{ color: colors.textSecondary }}>Daily Cost</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: colors.success }} />
                <span style={{ color: colors.textSecondary }}>Moving Average</span>
              </div>
            </div>
          </div>

          {/* Simple line chart visualization */}
          <div className="relative h-48">
            <div className="absolute inset-0 flex items-end justify-between">
              {costData.historicalData.slice(-14).map((day, index) => {
                const maxCost = Math.max(...costData.historicalData.map(d => d.cost));
                const height = (day.cost / maxCost) * 100;

                return (
                  <div key={day.date} className="flex flex-col items-center flex-1">
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: `${height}%` }}
                      transition={{ delay: index * 0.05, duration: 0.5 }}
                      className="w-full max-w-8 rounded-t"
                      style={{ backgroundColor: colors.primary }}
                    />
                    <span className="text-xs mt-2" style={{ color: colors.textSecondary }}>
                      {new Date(day.date).getDate()}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CostTracking;