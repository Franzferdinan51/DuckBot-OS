import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import { useTheme } from '../../theme/ThemeContext';

interface MetricsChartProps {
  type: 'line' | 'area' | 'bar' | 'pie';
  data: any[];
  title: string;
  description?: string;
  dataKeys: Array<{
    key: string;
    name: string;
    color: string;
    type?: 'monotone' | 'linear';
    strokeWidth?: number;
    fill?: boolean;
  }>;
  xAxisKey?: string;
  height?: number;
  showLegend?: boolean;
  showGrid?: boolean;
  unit?: string;
  threshold?: {
    value: number;
    color: string;
    label: string;
  };
}

const MetricsChart: React.FC<MetricsChartProps> = ({
  type,
  data,
  title,
  description,
  dataKeys,
  xAxisKey = 'time',
  height = 300,
  showLegend = true,
  showGrid = true,
  unit,
  threshold,
}) => {
  const { colors } = useTheme();
  const [chartData, setChartData] = useState(data);

  useEffect(() => {
    setChartData(data);
  }, [data]);

  const formatXAxisLabel = (value: string) => {
    try {
      const date = new Date(value);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return value;
    }
  };

  const formatTooltipLabel = (label: string) => {
    try {
      const date = new Date(label);
      return date.toLocaleString();
    } catch {
      return label;
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="p-3 rounded-lg border shadow-lg"
             style={{
               backgroundColor: colors.surface,
               borderColor: colors.border,
             }}>
          <p className="font-medium text-sm mb-2" style={{ color: colors.text }}>
            {formatTooltipLabel(label)}
          </p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between mb-1">
              <div className="flex items-center space-x-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-xs" style={{ color: colors.textSecondary }}>
                  {entry.name}:
                </span>
              </div>
              <span className="text-xs font-medium" style={{ color: colors.text }}>
                {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
                {unit}
              </span>
            </div>
          ))}
          {threshold && (
            <div className="mt-2 pt-2 border-t" style={{ borderColor: colors.border }}>
              <div className="flex items-center justify-between">
                <span className="text-xs" style={{ color: colors.textSecondary }}>
                  {threshold.label}:
                </span>
                <span className="text-xs font-medium" style={{ color: threshold.color }}>
                  {threshold.value}{unit}
                </span>
              </div>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    const commonProps = {
      width: undefined,
      height,
      data: chartData,
      margin: { top: 10, right: 30, left: 0, bottom: 0 },
    };

    const axisProps = {
      dataKey: xAxisKey,
      tick: { fontSize: 12, fill: colors.textSecondary },
      axisLine: { stroke: colors.border },
      tickLine: { stroke: colors.border },
    };

    const yAxisProps = {
      tick: { fontSize: 12, fill: colors.textSecondary },
      axisLine: { stroke: colors.border },
      tickLine: { stroke: colors.border },
    };

    const gridProps = showGrid ? {
      stroke: colors.border,
      strokeDasharray: '3 3',
    } : false;

    switch (type) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />}
            <XAxis {...axisProps} tickFormatter={formatXAxisLabel} />
            <YAxis {...yAxisProps} />
            <Tooltip content={<CustomTooltip />} />
            {showLegend && <Legend />}
            {threshold && (
              <Line
                type="monotone"
                dataKey={() => threshold.value}
                stroke={threshold.color}
                strokeDasharray="5 5"
                strokeWidth={2}
                dot={false}
                name={threshold.label}
              />
            )}
            {dataKeys.map((dataKey) => (
              <Line
                key={dataKey.key}
                type={dataKey.type || 'monotone'}
                dataKey={dataKey.key}
                name={dataKey.name}
                stroke={dataKey.color}
                strokeWidth={dataKey.strokeWidth || 2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            ))}
          </LineChart>
        );

      case 'area':
        return (
          <AreaChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />}
            <XAxis {...axisProps} tickFormatter={formatXAxisLabel} />
            <YAxis {...yAxisProps} />
            <Tooltip content={<CustomTooltip />} />
            {showLegend && <Legend />}
            {dataKeys.map((dataKey) => (
              <Area
                key={dataKey.key}
                type={dataKey.type || 'monotone'}
                dataKey={dataKey.key}
                name={dataKey.name}
                stroke={dataKey.color}
                fill={dataKey.color}
                fillOpacity={0.3}
                strokeWidth={dataKey.strokeWidth || 2}
              />
            ))}
          </AreaChart>
        );

      case 'bar':
        return (
          <BarChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />}
            <XAxis {...axisProps} />
            <YAxis {...yAxisProps} />
            <Tooltip content={<CustomTooltip />} />
            {showLegend && <Legend />}
            {dataKeys.map((dataKey) => (
              <Bar
                key={dataKey.key}
                dataKey={dataKey.key}
                name={dataKey.name}
                fill={dataKey.color}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        );

      case 'pie':
        return (
          <PieChart {...commonProps}>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
              nameKey="name"
            >
              {chartData.map((entry: any, index: number) => (
                <Cell key={`cell-${index}`} fill={dataKeys[index]?.color || colors.primary} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            {showLegend && <Legend />}
          </PieChart>
        );

      default:
        return null;
    }
  };

  return (
    <div className="w-full">
      {(title || description) && (
        <div className="mb-4">
          {title && (
            <h3 className="text-lg font-semibold" style={{ color: colors.text }}>
              {title}
            </h3>
          )}
          {description && (
            <p className="text-sm mt-1" style={{ color: colors.textSecondary }}>
              {description}
            </p>
          )}
        </div>
      )}

      <div className="w-full" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default MetricsChart;