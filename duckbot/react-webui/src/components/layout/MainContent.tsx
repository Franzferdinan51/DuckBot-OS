import React from 'react';
import { useTheme } from '../../theme/ThemeContext';
import { DashboardLayout } from '../../types/dashboard';

interface MainContentProps {
  children: React.ReactNode;
  layout: DashboardLayout;
}

const MainContent: React.FC<MainContentProps> = ({ children, layout }) => {
  const { colors, spacing } = useTheme();

  return (
    <main className="flex-1 overflow-auto p-6">
      <div className="max-w-7xl mx-auto">
        {/* Grid Container */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {React.Children.map(children, (child, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="rounded-lg border"
              style={{
                backgroundColor: colors.surface,
                borderColor: colors.border,
              }}
            >
              {child}
            </motion.div>
          ))}
        </div>

        {/* Full-width sections */}
        <div className="mt-6 space-y-6">
          {React.Children.map(children, (child, index) => {
            // This would be better handled by passing a prop to indicate full-width components
            return null;
          })}
        </div>
      </div>
    </main>
  );
};

export default MainContent;