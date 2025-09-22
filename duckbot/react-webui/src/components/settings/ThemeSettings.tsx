import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import {
  Sun,
  Moon,
  Monitor,
  Palette,
  Type,
  Layout,
  Zap,
  Settings
} from 'lucide-react';

const ThemeSettings: React.FC = () => {
  const { theme, updateTheme, currentTheme, colors } = useTheme();

  const themeOptions = [
    { value: 'light', label: 'Light', icon: Sun },
    { value: 'dark', label: 'Dark', icon: Moon },
    { value: 'system', label: 'System', icon: Monitor },
  ] as const;

  const accentColors = [
    { name: 'Teal', value: '#4fd1c7' },
    { name: 'Blue', value: '#3b82f6' },
    { name: 'Purple', value: '#8b5cf6' },
    { name: 'Green', value: '#10b981' },
    { name: 'Orange', value: '#f59e0b' },
    { name: 'Red', value: '#ef4444' },
  ];

  const fontSizeOptions = [
    { value: 'small', label: 'Small', preview: 'Aa' },
    { value: 'medium', label: 'Medium', preview: 'Aa' },
    { value: 'large', label: 'Large', preview: 'Aa' },
  ] as const;

  const densityOptions = [
    { value: 'compact', label: 'Compact', icon: '≡' },
    { value: 'comfortable', label: 'Comfortable', icon: '≡≡' },
    { value: 'spacious', label: 'Spacious', icon: '≡≡≡' },
  ] as const;

  const handleAccentColorChange = (color: string) => {
    updateTheme({ accent: color });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-lg"
             style={{ backgroundColor: `${colors.primary}20` }}>
          <Palette size={24} style={{ color: colors.primary }} />
        </div>
        <div>
          <h2 className="text-xl font-bold" style={{ color: colors.text }}>
            Theme Settings
          </h2>
          <p className="text-sm" style={{ color: colors.textSecondary }}>
            Customize the appearance and behavior of the interface
          </p>
        </div>
      </div>

      {/* Theme Mode */}
      <div className="p-4 rounded-lg border"
           style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
        <div className="flex items-center space-x-3 mb-4">
          <Sun size={20} style={{ color: colors.textSecondary }} />
          <h3 className="font-semibold" style={{ color: colors.text }}>
            Theme Mode
          </h3>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {themeOptions.map((option) => {
            const Icon = option.icon;
            const isSelected = theme.mode === option.value;

            return (
              <motion.button
                key={option.value}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => updateTheme({ mode: option.value })}
                className={`p-4 rounded-lg border-2 text-center transition-all ${
                  isSelected ? 'border-opacity-100' : 'border-opacity-20 hover:border-opacity-50'
                }`}
                style={{
                  backgroundColor: isSelected ? `${colors.primary}10` : colors.background,
                  borderColor: isSelected ? colors.primary : colors.border,
                  color: isSelected ? colors.primary : colors.text,
                }}
              >
                <Icon size={24} className="mx-auto mb-2" />
                <span className="text-sm font-medium">{option.label}</span>
                {option.value === 'system' && (
                  <p className="text-xs mt-1" style={{ color: colors.textSecondary }}>
                    {currentTheme === 'dark' ? 'Dark' : 'Light'}
                  </p>
                )}
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Accent Color */}
      <div className="p-4 rounded-lg border"
           style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
        <div className="flex items-center space-x-3 mb-4">
          <Palette size={20} style={{ color: colors.textSecondary }} />
          <h3 className="font-semibold" style={{ color: colors.text }}>
            Accent Color
          </h3>
        </div>
        <div className="grid grid-cols-6 gap-3">
          {accentColors.map((color) => (
            <motion.button
              key={color.value}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => handleAccentColorChange(color.value)}
              className="w-full aspect-square rounded-lg border-2 transition-all"
              style={{
                backgroundColor: color.value,
                borderColor: theme.accent === color.value ? colors.text : 'transparent',
                boxShadow: theme.accent === color.value ? `0 0 0 3px ${color.value}40` : 'none',
              }}
              title={color.name}
            >
              {theme.accent === color.value && (
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="white"
                  strokeWidth="3"
                  className="mx-auto"
                >
                  <path d="M5 13l4 4L19 7" />
                </svg>
              )}
            </motion.button>
          ))}
        </div>
      </div>

      {/* Font Size */}
      <div className="p-4 rounded-lg border"
           style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
        <div className="flex items-center space-x-3 mb-4">
          <Type size={20} style={{ color: colors.textSecondary }} />
          <h3 className="font-semibold" style={{ color: colors.text }}>
            Font Size
          </h3>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {fontSizeOptions.map((option) => {
            const isSelected = theme.fontSize === option.value;
            const sizeMap = {
              small: 'text-sm',
              medium: 'text-base',
              large: 'text-lg',
            };

            return (
              <motion.button
                key={option.value}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => updateTheme({ fontSize: option.value })}
                className={`p-4 rounded-lg border-2 text-center transition-all ${
                  isSelected ? 'border-opacity-100' : 'border-opacity-20 hover:border-opacity-50'
                }`}
                style={{
                  backgroundColor: isSelected ? `${colors.primary}10` : colors.background,
                  borderColor: isSelected ? colors.primary : colors.border,
                  color: isSelected ? colors.primary : colors.text,
                }}
              >
                <span className={`font-bold ${sizeMap[option.value]}`}>
                  {option.preview}
                </span>
                <p className="text-sm mt-1">{option.label}</p>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Layout Density */}
      <div className="p-4 rounded-lg border"
           style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
        <div className="flex items-center space-x-3 mb-4">
          <Layout size={20} style={{ color: colors.textSecondary }} />
          <h3 className="font-semibold" style={{ color: colors.text }}>
            Layout Density
          </h3>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {densityOptions.map((option) => {
            const isSelected = theme.density === option.value;

            return (
              <motion.button
                key={option.value}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => updateTheme({ density: option.value })}
                className={`p-4 rounded-lg border-2 text-center transition-all ${
                  isSelected ? 'border-opacity-100' : 'border-opacity-20 hover:border-opacity-50'
                }`}
                style={{
                  backgroundColor: isSelected ? `${colors.primary}10` : colors.background,
                  borderColor: isSelected ? colors.primary : colors.border,
                  color: isSelected ? colors.primary : colors.text,
                }}
              >
                <span className="text-2xl mb-1 block">{option.icon}</span>
                <span className="text-sm font-medium">{option.label}</span>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Animations */}
      <div className="p-4 rounded-lg border"
           style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Zap size={20} style={{ color: colors.textSecondary }} />
            <div>
              <h3 className="font-semibold" style={{ color: colors.text }}>
                Animations
              </h3>
              <p className="text-sm" style={{ color: colors.textSecondary }}>
                Enable smooth animations and transitions
              </p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={theme.animations}
              onChange={(e) => updateTheme({ animations: e.target.checked })}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer-checked:bg-blue-600"
                 style={{
                   backgroundColor: theme.animations ? colors.primary : colors.border,
                 }} />
          </label>
        </div>
      </div>

      {/* Preview */}
      <div className="p-4 rounded-lg border"
           style={{ backgroundColor: colors.surface, borderColor: colors.border }}>
        <h3 className="font-semibold mb-4" style={{ color: colors.text }}>
          Preview
        </h3>
        <div className="space-y-3">
          <div className="p-3 rounded"
               style={{ backgroundColor: colors.background }}>
            <h4 className="font-medium mb-1" style={{ color: colors.text }}>
              Sample Heading
            </h4>
            <p className="text-sm" style={{ color: colors.textSecondary }}>
              This is a sample text to preview your theme settings. The interface will adapt to your preferences.
            </p>
          </div>
          <div className="flex space-x-2">
            <button className="px-3 py-1 rounded text-sm font-medium"
                    style={{
                      backgroundColor: colors.primary,
                      color: colors.background,
                    }}>
              Primary Button
            </button>
            <button className="px-3 py-1 rounded text-sm font-medium border"
                    style={{
                      backgroundColor: 'transparent',
                      borderColor: colors.border,
                      color: colors.text,
                    }}>
              Secondary Button
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThemeSettings;