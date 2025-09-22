import React from 'react';
import DuckBotOSEnhanced from './components/DuckBotOSEnhanced.tsx';

const AppDesktop: React.FC = () => {
  return (
    <div className="w-screen h-screen">
      <DuckBotOSEnhanced
        wallpaperUrl="https://picsum.photos/1920/1080?grayscale&blur=1&seed=duckbot-enhanced"
        enableElectronFeatures={true}
      />
    </div>
  );
};

export default AppDesktop;