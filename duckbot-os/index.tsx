
import React from 'react';
import ReactDOM from 'react-dom/client';
import DuckBotOS from './DuckBotOS';
import App from './App';

// Check if user wants the comprehensive DuckBot OS experience or just the 3D Avatar
const urlParams = new URLSearchParams(window.location.search);
const mode = urlParams.get('mode') || 'duckbot-os'; // Default to full DuckBot OS

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);

// Render the appropriate component based on mode
if (mode === 'avatar-only') {
  // Just the 3D Avatar interface
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} else {
  // Full DuckBot OS experience with ALL features
  root.render(
    <React.StrictMode>
      <DuckBotOS />
    </React.StrictMode>
  );
}
