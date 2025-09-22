import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../theme/ThemeContext';
import { DashboardLayout } from '../../types/dashboard';
import Sidebar from './Sidebar';
import Header from './Header';
import MainContent from './MainContent';

interface DashboardLayoutProps {
  children: React.ReactNode;
  layout?: DashboardLayout;
  onLayoutChange?: (layout: DashboardLayout) => void;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  layout: initialLayout,
  onLayoutChange,
}) => {
  const { colors, spacing } = useTheme();
  const [layout, setLayout] = useState<DashboardLayout>(initialLayout || {
    sidebar: { collapsed: false, width: 240 },
    panels: {
      monitoring: true,
      agents: true,
      automation: true,
      costs: true,
    },
    windows: {},
  });

  const updateLayout = (updates: Partial<DashboardLayout>) => {
    const newLayout = { ...layout, ...updates };
    setLayout(newLayout);
    onLayoutChange?.(newLayout);
  };

  const toggleSidebar = () => {
    updateLayout({
      sidebar: {
        ...layout.sidebar,
        collapsed: !layout.sidebar.collapsed,
      },
    });
  };

  const togglePanel = (panel: keyof DashboardLayout['panels']) => {
    updateLayout({
      panels: {
        ...layout.panels,
        [panel]: !layout.panels[panel],
      },
    });
  };

  return (
    <div className="h-screen flex flex-col" style={{
      backgroundColor: colors.background,
      color: colors.text,
    }}>
      {/* Header */}
      <Header
        onToggleSidebar={toggleSidebar}
        sidebarCollapsed={layout.sidebar.collapsed}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <AnimatePresence>
          {!layout.sidebar.collapsed && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: layout.sidebar.width, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="flex-shrink-0 border-r"
              style={{ borderColor: colors.border }}
            >
              <Sidebar
                panels={layout.panels}
                onTogglePanel={togglePanel}
                width={layout.sidebar.width}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Collapsed sidebar toggle button */}
        {layout.sidebar.collapsed && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleSidebar}
            className="flex items-center justify-center border-r"
            style={{
              width: spacing.lg,
              borderColor: colors.border,
              color: colors.textSecondary,
            }}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M9 18l6-6-6-6" />
            </svg>
          </motion.button>
        )}

        {/* Main Content Area */}
        <MainContent layout={layout}>
          {children}
        </MainContent>
      </div>
    </div>
  );
};

export default DashboardLayout;