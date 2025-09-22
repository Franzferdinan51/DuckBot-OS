import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ThemeSettings } from '../types/dashboard';

interface ThemeContextType {
  theme: ThemeSettings;
  updateTheme: (updates: Partial<ThemeSettings>) => void;
  currentTheme: 'dark' | 'light';
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    success: string;
    warning: string;
    error: string;
    info: string;
  };
  spacing: Record<string, number>;
  typography: {
    fontFamily: string;
    fontSize: Record<string, number>;
    fontWeight: Record<string, number>;
  };
}

const defaultTheme: ThemeSettings = {
  mode: 'dark',
  accent: '#4fd1c7',
  fontSize: 'medium',
  animations: true,
  density: 'comfortable',
};

const darkColors = {
  primary: '#4fd1c7',
  secondary: '#667eea',
  background: '#0f172a',
  surface: '#1e293b',
  surfaceLight: '#334155',
  text: '#f1f5f9',
  textSecondary: '#94a3b8',
  border: '#334155',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',
};

const lightColors = {
  primary: '#0891b2',
  secondary: '#7c3aed',
  background: '#ffffff',
  surface: '#f8fafc',
  surfaceLight: '#f1f5f9',
  text: '#0f172a',
  textSecondary: '#64748b',
  border: '#e2e8f0',
  success: '#059669',
  warning: '#d97706',
  error: '#dc2626',
  info: '#2563eb',
};

const spacing = {
  xs: 2,
  sm: 4,
  md: 8,
  lg: 16,
  xl: 24,
  '2xl': 32,
  '3xl': 48,
  '4xl': 64,
};

const typography = {
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  fontSize: {
    xs: 11,
    sm: 12,
    base: 14,
    lg: 16,
    xl: 18,
    '2xl': 20,
    '3xl': 24,
    '4xl': 28,
    '5xl': 32,
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: ReactNode;
  initialTheme?: Partial<ThemeSettings>;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  initialTheme
}) => {
  const [theme, setTheme] = useState<ThemeSettings>({
    ...defaultTheme,
    ...initialTheme,
  });

  const [currentTheme, setCurrentTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    const handleSystemThemeChange = (e: MediaQueryListEvent) => {
      if (theme.mode === 'system') {
        setCurrentTheme(e.matches ? 'dark' : 'light');
      }
    };

    if (theme.mode === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      setCurrentTheme(mediaQuery.matches ? 'dark' : 'light');
      mediaQuery.addEventListener('change', handleSystemThemeChange);
      return () => mediaQuery.removeEventListener('change', handleSystemThemeChange);
    } else {
      setCurrentTheme(theme.mode);
    }
  }, [theme.mode]);

  useEffect(() => {
    document.documentElement.style.setProperty('--color-primary', colors.primary);
    document.documentElement.style.setProperty('--color-secondary', colors.secondary);
    document.documentElement.style.setProperty('--color-background', colors.background);
    document.documentElement.style.setProperty('--color-surface', colors.surface);
    document.documentElement.style.setProperty('--color-surface-light', colors.surfaceLight);
    document.documentElement.style.setProperty('--color-text', colors.text);
    document.documentElement.style.setProperty('--color-text-secondary', colors.textSecondary);
    document.documentElement.style.setProperty('--color-border', colors.border);
    document.documentElement.style.setProperty('--color-success', colors.success);
    document.documentElement.style.setProperty('--color-warning', colors.warning);
    document.documentElement.style.setProperty('--color-error', colors.error);
    document.documentElement.style.setProperty('--color-info', colors.info);

    // Apply font size
    const fontSizeMap = {
      small: 0.875,
      medium: 1,
      large: 1.125,
    };
    document.documentElement.style.fontSize = `${fontSizeMap[theme.fontSize]}rem`;

    // Apply density
    const densityMap = {
      compact: 0.75,
      comfortable: 1,
      spacious: 1.25,
    };
    const density = densityMap[theme.density];
    Object.entries(spacing).forEach(([key, value]) => {
      document.documentElement.style.setProperty(`--spacing-${key}`, `${value * density}px`);
    });

    // Apply animations
    if (!theme.animations) {
      document.documentElement.style.setProperty('--animation-duration', '0s');
    } else {
      document.documentElement.style.setProperty('--animation-duration', '0.3s');
    }
  }, [theme, colors]);

  const colors = currentTheme === 'dark' ? darkColors : lightColors;

  const updateTheme = (updates: Partial<ThemeSettings>) => {
    setTheme(prev => ({ ...prev, ...updates }));
  };

  const value: ThemeContextType = {
    theme,
    updateTheme,
    currentTheme,
    colors,
    spacing,
    typography,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};