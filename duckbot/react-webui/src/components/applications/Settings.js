import React, { useState, useEffect, useCallback } from 'react';
import {
  Settings, Monitor, Palette, Cpu, Network, User, Info,
  Moon, Sun, Monitor as MonitorIcon, Volume2, VolumeX,
  Wifi, WifiOff, Shield, HardDrive, Download, Upload,
  Bell, BellOff, Eye, EyeOff, Zap, Database, Globe,
  RefreshCw, Check, X, Save, Sliders, Keyboard, Mouse,
  Brain, Code, FileText, Key, Activity, TestTube
} from 'lucide-react';

const EnhancedSettings = ({ onClose }) => {
  const [activeSection, setActiveSection] = useState('appearance');
  const [settings, setSettings] = useState({
    // Appearance
    theme: 'dark',
    accentColor: 'blue',
    transparency: true,
    animations: true,
    compactMode: false,
    fontSize: 'medium',
    wallpaper: 'default',

    // Display
    resolution: '1920x1080',
    scaling: 100,
    refreshRate: 60,
    multipleMonitors: false,
    nightLight: false,
    nightLightIntensity: 50,

    // Sound
    masterVolume: 80,
    notificationVolume: 70,
    systemSounds: true,
    muteAll: false,
    outputDevice: 'default',
    inputDevice: 'default',

    // System
    autoStart: true,
    backgroundServices: true,
    hardwareAcceleration: true,
    developerMode: false,
    experimentalFeatures: false,
    autoUpdates: true,

    // Network
    wifiEnabled: true,
    ethernetEnabled: true,
    proxyEnabled: false,
    proxySettings: { host: '', port: '', username: '', password: '' },
    vpnEnabled: false,

    // Accounts
    currentUser: 'DuckBot User',
    userAvatar: '',
    syncSettings: true,
    cloudBackup: true,

    // Privacy
    analytics: false,
    errorReporting: true,
    locationServices: false,
    microphoneAccess: true,
    cameraAccess: false,

    // Notifications
    desktopNotifications: true,
    soundAlerts: true,
    notificationPreview: true,
    doNotDisturb: false,

    // Storage
    cacheSize: 0,
    totalStorage: 0,
    usedStorage: 0,
    autoCleanup: true,
    backupEnabled: true,

    // About
    version: '4.2.0',
    buildNumber: '20240916',
    lastUpdate: '2024-09-16',

    // DeepCode
    deepcode: {
      enabled: true,
      serverHost: 'localhost',
      serverPort: 8790,
      useHttps: false,
      defaultModel: 'qwen3-coder',
      fallbackModel: 'gpt-4',
      temperature: 0.2,
      maxTokens: 4000,
      enableAuth: true,
      apiKeyRequired: false,
      enableCaching: true,
      maxConcurrentJobs: 5,
      autoStart: false,
      notifications: true,
      advancedMode: false
    },

    // LM Studio
    lmstudio: {
      enabled: false,
      serverHost: 'localhost',
      serverPort: 1234,
      useHttps: false,
      defaultModel: 'auto',
      temperature: 0.7,
      maxTokens: 2000,
      enableAuth: false,
      apiKeyRequired: false,
      autoConnect: false,
      checkHealth: true,
      fallbackToCloud: true
    }
  });

  const [hasChanges, setHasChanges] = useState(false);
  const [isScanning, setIsScanning] = useState(false);

  // Mock system information
  const systemInfo = {
    os: 'DuckBotOS v4.2 Enhanced',
    cpu: 'Intel Core i7-10750H',
    ram: '16 GB DDR4',
    gpu: 'NVIDIA GeForce RTX 3060',
    storage: '512 GB NVMe SSD',
    network: 'Wi-Fi 6, Gigabit Ethernet',
    uptime: '2 days, 14 hours'
  };

  // Handle settings changes
  const handleSettingChange = useCallback((key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  }, []);

  // Handle proxy settings changes
  const handleProxyChange = useCallback((field, value) => {
    setSettings(prev => ({
      ...prev,
      proxySettings: { ...prev.proxySettings, [field]: value }
    }));
    setHasChanges(true);
  }, []);

  // Handle DeepCode settings changes
  const handleDeepCodeChange = useCallback((field, value) => {
    setSettings(prev => ({
      ...prev,
      deepcode: { ...prev.deepcode, [field]: value }
    }));
    setHasChanges(true);
  }, []);

  // Handle LM Studio settings changes
  const handleLMStudioChange = useCallback((field, value) => {
    setSettings(prev => ({
      ...prev,
      lmstudio: { ...prev.lmstudio, [field]: value }
    }));
    setHasChanges(true);
  }, []);

  // Save settings
  const handleSave = useCallback(() => {
    // Simulate saving to localStorage or backend
    localStorage.setItem('duckbot-settings', JSON.stringify(settings));
    setHasChanges(false);

    // Show success feedback
    console.log('Settings saved successfully');
  }, [settings]);

  // Reset settings to defaults
  const handleReset = useCallback(() => {
    setSettings({
      theme: 'dark',
      accentColor: 'blue',
      transparency: true,
      animations: true,
      compactMode: false,
      fontSize: 'medium',
      wallpaper: 'default',
      resolution: '1920x1080',
      scaling: 100,
      refreshRate: 60,
      multipleMonitors: false,
      nightLight: false,
      nightLightIntensity: 50,
      masterVolume: 80,
      notificationVolume: 70,
      systemSounds: true,
      muteAll: false,
      outputDevice: 'default',
      inputDevice: 'default',
      autoStart: true,
      backgroundServices: true,
      hardwareAcceleration: true,
      developerMode: false,
      experimentalFeatures: false,
      autoUpdates: true,
      wifiEnabled: true,
      ethernetEnabled: true,
      proxyEnabled: false,
      proxySettings: { host: '', port: '', username: '', password: '' },
      vpnEnabled: false,
      currentUser: 'DuckBot User',
      userAvatar: '',
      syncSettings: true,
      cloudBackup: true,
      analytics: false,
      errorReporting: true,
      locationServices: false,
      microphoneAccess: true,
      cameraAccess: false,
      desktopNotifications: true,
      soundAlerts: true,
      notificationPreview: true,
      doNotDisturb: false,
      cacheSize: 0,
      totalStorage: 0,
      usedStorage: 0,
      autoCleanup: true,
      backupEnabled: true,
      version: '4.2.0',
      buildNumber: '20240916',
      lastUpdate: '2024-09-16',
      deepcode: {
        enabled: true,
        serverHost: 'localhost',
        serverPort: 8790,
        useHttps: false,
        defaultModel: 'qwen3-coder',
        fallbackModel: 'gpt-4',
        temperature: 0.2,
        maxTokens: 4000,
        enableAuth: true,
        apiKeyRequired: false,
        enableCaching: true,
        maxConcurrentJobs: 5,
        autoStart: false,
        notifications: true,
        advancedMode: false
      },
      lmstudio: {
        enabled: false,
        serverHost: 'localhost',
        serverPort: 1234,
        useHttps: false,
        defaultModel: 'auto',
        temperature: 0.7,
        maxTokens: 2000,
        enableAuth: false,
        apiKeyRequired: false,
        autoConnect: false,
        checkHealth: true,
        fallbackToCloud: true
      }
    });
    setHasChanges(true);
  }, []);

  // Scan for storage
  const scanStorage = useCallback(async () => {
    setIsScanning(true);
    // Simulate scanning
    await new Promise(resolve => setTimeout(resolve, 2000));

    setSettings(prev => ({
      ...prev,
      cacheSize: Math.floor(Math.random() * 1000),
      totalStorage: 512,
      usedStorage: Math.floor(Math.random() * 400)
    }));
    setIsScanning(false);
  }, []);

  // Load settings on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('duckbot-settings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  }, []);

  // Settings sections
  const sections = [
    { id: 'appearance', icon: Palette, label: 'Appearance', description: 'Theme and display settings' },
    { id: 'display', icon: Monitor, label: 'Display', description: 'Screen and monitor settings' },
    { id: 'sound', icon: Volume2, label: 'Sound', description: 'Audio and volume controls' },
    { id: 'system', icon: Cpu, label: 'System', description: 'System preferences and performance' },
    { id: 'network', icon: Network, label: 'Network', description: 'Network and internet settings' },
    { id: 'accounts', icon: User, label: 'Accounts', description: 'User and sync settings' },
    { id: 'privacy', icon: Shield, label: 'Privacy', description: 'Privacy and security settings' },
    { id: 'notifications', icon: Bell, label: 'Notifications', description: 'Alert and notification preferences' },
    { id: 'storage', icon: HardDrive, label: 'Storage', description: 'Storage and disk management' },
    { id: 'deepcode', icon: Brain, label: 'DeepCode', description: 'AI code generation and configuration' },
    { id: 'lmstudio', icon: Cpu, label: 'LM Studio', description: 'Local AI model configuration' },
    { id: 'about', icon: Info, label: 'About', description: 'System information and version' }
  ];

  // Render current section
  const renderSection = () => {
    const Icon = sections.find(s => s.id === activeSection)?.icon || Settings;

    switch (activeSection) {
      case 'appearance':
        return (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Icon className="w-5 h-5 mr-2" />
                Theme Settings
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => handleSettingChange('theme', 'light')}
                  className={`p-4 rounded-lg border-2 transition-colors ${
                    settings.theme === 'light' ? 'border-blue-500 bg-blue-500/20' : 'border-gray-600 hover:border-gray-500'
                  }`}
                >
                  <Sun className="w-8 h-8 mx-auto mb-2 text-yellow-400" />
                  <div className="text-white text-sm">Light</div>
                </button>
                <button
                  onClick={() => handleSettingChange('theme', 'dark')}
                  className={`p-4 rounded-lg border-2 transition-colors ${
                    settings.theme === 'dark' ? 'border-blue-500 bg-blue-500/20' : 'border-gray-600 hover:border-gray-500'
                  }`}
                >
                  <Moon className="w-8 h-8 mx-auto mb-2 text-blue-400" />
                  <div className="text-white text-sm">Dark</div>
                </button>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">Accent Color</h3>
              <div className="grid grid-cols-4 gap-2">
                {['blue', 'green', 'purple', 'red', 'orange', 'pink', 'cyan', 'yellow'].map(color => (
                  <button
                    key={color}
                    onClick={() => handleSettingChange('accentColor', color)}
                    className={`h-10 rounded-lg border-2 transition-colors ${
                      settings.accentColor === color ? 'border-white' : 'border-gray-600 hover:border-gray-500'
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">Interface Options</h3>
              <div className="space-y-3">
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.transparency}
                      onChange={(e) => handleSettingChange('transparency', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Transparency Effects</span>
                  </div>
                </label>
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.animations}
                      onChange={(e) => handleSettingChange('animations', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Animations</span>
                  </div>
                </label>
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.compactMode}
                      onChange={(e) => handleSettingChange('compactMode', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Compact Mode</span>
                  </div>
                </label>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">Font Size</h3>
              <select
                value={settings.fontSize}
                onChange={(e) => handleSettingChange('fontSize', e.target.value)}
                className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
              >
                <option value="small">Small</option>
                <option value="medium">Medium</option>
                <option value="large">Large</option>
                <option value="x-large">Extra Large</option>
              </select>
            </div>
          </div>
        );

      case 'display':
        return (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <MonitorIcon className="w-5 h-5 mr-2" />
                Display Settings
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-gray-300 text-sm mb-2">Resolution</label>
                  <select
                    value={settings.resolution}
                    onChange={(e) => handleSettingChange('resolution', e.target.value)}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  >
                    <option value="1920x1080">1920x1080 (Recommended)</option>
                    <option value="2560x1440">2560x1440</option>
                    <option value="3840x2160">3840x2160 (4K)</option>
                    <option value="1366x768">1366x768</option>
                  </select>
                </div>

                <div>
                  <label className="block text-gray-300 text-sm mb-2">Scaling</label>
                  <div className="flex items-center space-x-4">
                    <input
                      type="range"
                      min="100"
                      max="200"
                      step="25"
                      value={settings.scaling}
                      onChange={(e) => handleSettingChange('scaling', parseInt(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-white text-sm w-12">{settings.scaling}%</span>
                  </div>
                </div>

                <div>
                  <label className="block text-gray-300 text-sm mb-2">Refresh Rate</label>
                  <select
                    value={settings.refreshRate}
                    onChange={(e) => handleSettingChange('refreshRate', parseInt(e.target.value))}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  >
                    <option value="60">60 Hz</option>
                    <option value="120">120 Hz</option>
                    <option value="144">144 Hz</option>
                    <option value="240">240 Hz</option>
                  </select>
                </div>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={settings.multipleMonitors}
                    onChange={(e) => handleSettingChange('multipleMonitors', e.target.checked)}
                    className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300">Multiple Displays</span>
                </label>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Moon className="w-5 h-5 mr-2" />
                Night Light
              </h3>
              <div className="space-y-4">
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.nightLight}
                      onChange={(e) => handleSettingChange('nightLight', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Enable Night Light</span>
                  </div>
                </label>

                {settings.nightLight && (
                  <div>
                    <label className="block text-gray-300 text-sm mb-2">Intensity</label>
                    <div className="flex items-center space-x-4">
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={settings.nightLightIntensity}
                        onChange={(e) => handleSettingChange('nightLightIntensity', parseInt(e.target.value))}
                        className="flex-1"
                      />
                      <span className="text-white text-sm w-12">{settings.nightLightIntensity}%</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      case 'sound':
        return (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                {settings.muteAll ? <VolumeX className="w-5 h-5 mr-2" /> : <Volume2 className="w-5 h-5 mr-2" />}
                Volume Controls
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Master Volume</span>
                  <div className="flex items-center space-x-4 flex-1 ml-4">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={settings.masterVolume}
                      onChange={(e) => handleSettingChange('masterVolume', parseInt(e.target.value))}
                      className="flex-1"
                      disabled={settings.muteAll}
                    />
                    <span className="text-white text-sm w-12">{settings.masterVolume}%</span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Notifications</span>
                  <div className="flex items-center space-x-4 flex-1 ml-4">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={settings.notificationVolume}
                      onChange={(e) => handleSettingChange('notificationVolume', parseInt(e.target.value))}
                      className="flex-1"
                      disabled={settings.muteAll}
                    />
                    <span className="text-white text-sm w-12">{settings.notificationVolume}%</span>
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={settings.muteAll}
                        onChange={(e) => handleSettingChange('muteAll', e.target.checked)}
                        className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                      />
                      <span className="text-gray-300">Mute All</span>
                    </div>
                  </label>

                  <label className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={settings.systemSounds}
                        onChange={(e) => handleSettingChange('systemSounds', e.target.checked)}
                        className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                        disabled={settings.muteAll}
                      />
                      <span className="text-gray-300">System Sounds</span>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">Audio Devices</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-gray-300 text-sm mb-2">Output Device</label>
                  <select
                    value={settings.outputDevice}
                    onChange={(e) => handleSettingChange('outputDevice', e.target.value)}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  >
                    <option value="default">Default Device</option>
                    <option value="speakers">Speakers</option>
                    <option value="headphones">Headphones</option>
                    <option value="bluetooth">Bluetooth Audio</option>
                  </select>
                </div>

                <div>
                  <label className="block text-gray-300 text-sm mb-2">Input Device</label>
                  <select
                    value={settings.inputDevice}
                    onChange={(e) => handleSettingChange('inputDevice', e.target.value)}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  >
                    <option value="default">Default Device</option>
                    <option value="microphone">Microphone</option>
                    <option value="headset-mic">Headset Microphone</option>
                    <option value="bluetooth-mic">Bluetooth Microphone</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        );

      case 'system':
        return (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Cpu className="w-5 h-5 mr-2" />
                System Preferences
              </h3>
              <div className="space-y-3">
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.autoStart}
                      onChange={(e) => handleSettingChange('autoStart', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Start on System Boot</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.backgroundServices}
                      onChange={(e) => handleSettingChange('backgroundServices', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Background Services</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.hardwareAcceleration}
                      onChange={(e) => handleSettingChange('hardwareAcceleration', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Hardware Acceleration</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.autoUpdates}
                      onChange={(e) => handleSettingChange('autoUpdates', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Automatic Updates</span>
                  </div>
                </label>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Zap className="w-5 h-5 mr-2" />
                Advanced Options
              </h3>
              <div className="space-y-3">
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.developerMode}
                      onChange={(e) => handleSettingChange('developerMode', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Developer Mode</span>
                  </div>
                  <span className="text-gray-500 text-xs">Enables debugging features</span>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.experimentalFeatures}
                      onChange={(e) => handleSettingChange('experimentalFeatures', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Experimental Features</span>
                  </div>
                  <span className="text-gray-500 text-xs">Early access to new features</span>
                </label>
              </div>
            </div>
          </div>
        );

      case 'network':
        return (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                {settings.wifiEnabled ? <Wifi className="w-5 h-5 mr-2" /> : <WifiOff className="w-5 h-5 mr-2" />}
                Network Connections
              </h3>
              <div className="space-y-3">
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.wifiEnabled}
                      onChange={(e) => handleSettingChange('wifiEnabled', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Wi-Fi</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.ethernetEnabled}
                      onChange={(e) => handleSettingChange('ethernetEnabled', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Ethernet</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.vpnEnabled}
                      onChange={(e) => handleSettingChange('vpnEnabled', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">VPN</span>
                  </div>
                </label>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">Proxy Settings</h3>
              <div className="space-y-4">
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.proxyEnabled}
                      onChange={(e) => handleSettingChange('proxyEnabled', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Enable Proxy</span>
                  </div>
                </label>

                {settings.proxyEnabled && (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-gray-300 text-sm mb-1">Host</label>
                      <input
                        type="text"
                        value={settings.proxySettings.host}
                        onChange={(e) => handleProxyChange('host', e.target.value)}
                        placeholder="proxy.example.com"
                        className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                      />
                    </div>
                    <div>
                      <label className="block text-gray-300 text-sm mb-1">Port</label>
                      <input
                        type="number"
                        value={settings.proxySettings.port}
                        onChange={(e) => handleProxyChange('port', e.target.value)}
                        placeholder="8080"
                        className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                      />
                    </div>
                    <div>
                      <label className="block text-gray-300 text-sm mb-1">Username</label>
                      <input
                        type="text"
                        value={settings.proxySettings.username}
                        onChange={(e) => handleProxyChange('username', e.target.value)}
                        placeholder="username"
                        className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                      />
                    </div>
                    <div>
                      <label className="block text-gray-300 text-sm mb-1">Password</label>
                      <input
                        type="password"
                        value={settings.proxySettings.password}
                        onChange={(e) => handleProxyChange('password', e.target.value)}
                        placeholder="password"
                        className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      case 'accounts':
        return (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <User className="w-5 h-5 mr-2" />
                User Account
              </h3>
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
                    <User className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <div className="text-white font-medium">{settings.currentUser}</div>
                    <div className="text-gray-400 text-sm">Administrator</div>
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={settings.syncSettings}
                        onChange={(e) => handleSettingChange('syncSettings', e.target.checked)}
                        className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                      />
                      <span className="text-gray-300">Sync Settings</span>
                    </div>
                  </label>

                  <label className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={settings.cloudBackup}
                        onChange={(e) => handleSettingChange('cloudBackup', e.target.checked)}
                        className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                      />
                      <span className="text-gray-300">Cloud Backup</span>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">Account Management</h3>
              <div className="space-y-3">
                <button className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
                  Change Password
                </button>
                <button className="w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors">
                  Two-Factor Authentication
                </button>
                <button className="w-full bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors">
                  Export Account Data
                </button>
              </div>
            </div>
          </div>
        );

      case 'privacy':
        return (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Shield className="w-5 h-5 mr-2" />
                Privacy Settings
              </h3>
              <div className="space-y-3">
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.analytics}
                      onChange={(e) => handleSettingChange('analytics', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Analytics Collection</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.errorReporting}
                      onChange={(e) => handleSettingChange('errorReporting', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Error Reporting</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.locationServices}
                      onChange={(e) => handleSettingChange('locationServices', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Location Services</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.microphoneAccess}
                      onChange={(e) => handleSettingChange('microphoneAccess', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Microphone Access</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.cameraAccess}
                      onChange={(e) => handleSettingChange('cameraAccess', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Camera Access</span>
                  </div>
                </label>
              </div>
            </div>
          </div>
        );

      case 'notifications':
        return (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                {settings.doNotDisturb ? <BellOff className="w-5 h-5 mr-2" /> : <Bell className="w-5 h-5 mr-2" />}
                Notification Settings
              </h3>
              <div className="space-y-3">
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.desktopNotifications}
                      onChange={(e) => handleSettingChange('desktopNotifications', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                      disabled={settings.doNotDisturb}
                    />
                    <span className="text-gray-300">Desktop Notifications</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.soundAlerts}
                      onChange={(e) => handleSettingChange('soundAlerts', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                      disabled={settings.doNotDisturb}
                    />
                    <span className="text-gray-300">Sound Alerts</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.notificationPreview}
                      onChange={(e) => handleSettingChange('notificationPreview', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                      disabled={settings.doNotDisturb}
                    />
                    <span className="text-gray-300">Notification Preview</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.doNotDisturb}
                      onChange={(e) => handleSettingChange('doNotDisturb', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Do Not Disturb</span>
                  </div>
                </label>
              </div>
            </div>
          </div>
        );

      case 'deepcode':
        return (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Brain className="w-5 h-5 mr-2" />
                DeepCode Configuration
              </h3>
              <div className="space-y-4">
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.deepcode.enabled}
                      onChange={(e) => handleDeepCodeChange('enabled', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Enable DeepCode</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.deepcode.autoStart}
                      onChange={(e) => handleDeepCodeChange('autoStart', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Auto-start DeepCode Service</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.deepcode.notifications}
                      onChange={(e) => handleDeepCodeChange('notifications', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Enable Notifications</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.deepcode.advancedMode}
                      onChange={(e) => handleDeepCodeChange('advancedMode', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Advanced Mode</span>
                  </div>
                  <span className="text-gray-500 text-xs">Show advanced options</span>
                </label>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Server className="w-5 h-5 mr-2" />
                Server Settings
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-300 text-sm mb-2">Host</label>
                  <input
                    type="text"
                    value={settings.deepcode.serverHost}
                    onChange={(e) => handleDeepCodeChange('serverHost', e.target.value)}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 text-sm mb-2">Port</label>
                  <input
                    type="number"
                    value={settings.deepcode.serverPort}
                    onChange={(e) => handleDeepCodeChange('serverPort', parseInt(e.target.value))}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  />
                </div>
              </div>
              <div className="mt-4">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={settings.deepcode.useHttps}
                    onChange={(e) => handleDeepCodeChange('useHttps', e.target.checked)}
                    className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300">Use HTTPS</span>
                </label>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Code className="w-5 h-5 mr-2" />
                AI Model Settings
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-300 text-sm mb-2">Default Model</label>
                  <select
                    value={settings.deepcode.defaultModel}
                    onChange={(e) => handleDeepCodeChange('defaultModel', e.target.value)}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  >
                    <option value="qwen3-coder">Qwen3 Coder</option>
                    <option value="gpt-4">GPT-4</option>
                    <option value="claude-3">Claude 3</option>
                    <option value="gemini-pro">Gemini Pro</option>
                  </select>
                </div>
                <div>
                  <label className="block text-gray-300 text-sm mb-2">Fallback Model</label>
                  <select
                    value={settings.deepcode.fallbackModel}
                    onChange={(e) => handleDeepCodeChange('fallbackModel', e.target.value)}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  >
                    <option value="gpt-4">GPT-4</option>
                    <option value="qwen3-coder">Qwen3 Coder</option>
                    <option value="claude-3">Claude 3</option>
                    <option value="gemini-pro">Gemini Pro</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="block text-gray-300 text-sm mb-2">Temperature</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    value={settings.deepcode.temperature}
                    onChange={(e) => handleDeepCodeChange('temperature', parseFloat(e.target.value))}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 text-sm mb-2">Max Tokens</label>
                  <input
                    type="number"
                    value={settings.deepcode.maxTokens}
                    onChange={(e) => handleDeepCodeChange('maxTokens', parseInt(e.target.value))}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  />
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Shield className="w-5 h-5 mr-2" />
                Security & Performance
              </h3>
              <div className="space-y-4">
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.deepcode.enableAuth}
                      onChange={(e) => handleDeepCodeChange('enableAuth', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Enable Authentication</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.deepcode.apiKeyRequired}
                      onChange={(e) => handleDeepCodeChange('apiKeyRequired', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Require API Key</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.deepcode.enableCaching}
                      onChange={(e) => handleDeepCodeChange('enableCaching', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Enable Caching</span>
                  </div>
                </label>

                <div>
                  <label className="block text-gray-300 text-sm mb-2">Max Concurrent Jobs</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={settings.deepcode.maxConcurrentJobs}
                    onChange={(e) => handleDeepCodeChange('maxConcurrentJobs', parseInt(e.target.value))}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  />
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">DeepCode Actions</h3>
              <div className="space-y-3">
                <button className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-2">
                  <TestTube className="w-4 h-4" />
                  <span>Test Connection</span>
                </button>
                <button className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-2">
                  <Activity className="w-4 h-4" />
                  <span>View DeepCode Dashboard</span>
                </button>
                <button className="w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-2">
                  <Settings className="w-4 h-4" />
                  <span>Advanced Configuration</span>
                </button>
              </div>
            </div>
          </div>
        );

      case 'lmstudio':
        return (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Cpu className="w-5 h-5 mr-2" />
                LM Studio Configuration
              </h3>
              <div className="space-y-4">
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.lmstudio.enabled}
                      onChange={(e) => handleLMStudioChange('enabled', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Enable LM Studio</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.lmstudio.autoConnect}
                      onChange={(e) => handleLMStudioChange('autoConnect', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Auto-connect on Startup</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.lmstudio.checkHealth}
                      onChange={(e) => handleLMStudioChange('checkHealth', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Health Check</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.lmstudio.fallbackToCloud}
                      onChange={(e) => handleLMStudioChange('fallbackToCloud', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Fallback to Cloud if Unavailable</span>
                  </div>
                </label>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Network className="w-5 h-5 mr-2" />
                Server Settings
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-300 text-sm mb-2">Host</label>
                  <input
                    type="text"
                    value={settings.lmstudio.serverHost}
                    onChange={(e) => handleLMStudioChange('serverHost', e.target.value)}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 text-sm mb-2">Port</label>
                  <input
                    type="number"
                    value={settings.lmstudio.serverPort}
                    onChange={(e) => handleLMStudioChange('serverPort', parseInt(e.target.value))}
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  />
                </div>
              </div>
              <div className="mt-4">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={settings.lmstudio.useHttps}
                    onChange={(e) => handleLMStudioChange('useHttps', e.target.checked)}
                    className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300">Use HTTPS</span>
                </label>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Brain className="w-5 h-5 mr-2" />
                Model Settings
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-gray-300 text-sm mb-2">Default Model</label>
                  <input
                    type="text"
                    value={settings.lmstudio.defaultModel}
                    onChange={(e) => handleLMStudioChange('defaultModel', e.target.value)}
                    placeholder="auto or specific model name"
                    className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-gray-300 text-sm mb-2">Temperature</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      value={settings.lmstudio.temperature}
                      onChange={(e) => handleLMStudioChange('temperature', parseFloat(e.target.value))}
                      className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                    />
                  </div>
                  <div>
                    <label className="block text-gray-300 text-sm mb-2">Max Tokens</label>
                    <input
                      type="number"
                      value={settings.lmstudio.maxTokens}
                      onChange={(e) => handleLMStudioChange('maxTokens', parseInt(e.target.value))}
                      className="w-full bg-gray-700 text-white rounded px-3 py-2 border border-gray-600"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Shield className="w-5 h-5 mr-2" />
                Security Settings
              </h3>
              <div className="space-y-4">
                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.lmstudio.enableAuth}
                      onChange={(e) => handleLMStudioChange('enableAuth', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Enable Authentication</span>
                  </div>
                </label>

                <label className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.lmstudio.apiKeyRequired}
                      onChange={(e) => handleLMStudioChange('apiKeyRequired', e.target.checked)}
                      className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                    />
                    <span className="text-gray-300">Require API Key</span>
                  </div>
                </label>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">LM Studio Actions</h3>
              <div className="space-y-3">
                <button className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-2">
                  <Activity className="w-4 h-4" />
                  <span>Test Connection</span>
                </button>
                <button className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-2">
                  <RefreshCw className="w-4 h-4" />
                  <span>Refresh Available Models</span>
                </button>
                <button className="w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-2">
                  <Settings className="w-4 h-4" />
                  <span>Open LM Studio</span>
                </button>
              </div>
            </div>
          </div>
        );

      case 'storage':
        return (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <HardDrive className="w-5 h-5 mr-2" />
                Storage Management
              </h3>
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-300">Total Storage</span>
                    <span className="text-white">{settings.totalStorage} GB</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${(settings.usedStorage / settings.totalStorage) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-400">
                    <span>{settings.usedStorage} GB used</span>
                    <span>{settings.totalStorage - settings.usedStorage} GB free</span>
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={settings.autoCleanup}
                        onChange={(e) => handleSettingChange('autoCleanup', e.target.checked)}
                        className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                      />
                      <span className="text-gray-300">Automatic Cleanup</span>
                    </div>
                  </label>

                  <label className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={settings.backupEnabled}
                        onChange={(e) => handleSettingChange('backupEnabled', e.target.checked)}
                        className="rounded w-4 h-4 text-blue-600 bg-gray-700 border-gray-600"
                      />
                      <span className="text-gray-300">Enable Backups</span>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">Cache & Temporary Files</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Cache Size</span>
                  <div className="flex items-center space-x-3">
                    <span className="text-white">{settings.cacheSize} MB</span>
                    <button
                      onClick={scanStorage}
                      disabled={isScanning}
                      className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                    >
                      <RefreshCw className={`w-4 h-4 text-gray-300 ${isScanning ? 'animate-spin' : ''}`} />
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <button className="w-full bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors">
                    Clear Cache
                  </button>
                  <button className="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors">
                    Clear Temporary Files
                  </button>
                </div>
              </div>
            </div>
          </div>
        );

      case 'about':
        return (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4 flex items-center">
                <Info className="w-5 h-5 mr-2" />
                System Information
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-300">Version</span>
                  <span className="text-white">{settings.version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Build</span>
                  <span className="text-white">{settings.buildNumber}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Last Update</span>
                  <span className="text-white">{settings.lastUpdate}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Uptime</span>
                  <span className="text-white">{systemInfo.uptime}</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">Hardware Information</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-300">Operating System</span>
                  <span className="text-white">{systemInfo.os}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Processor</span>
                  <span className="text-white">{systemInfo.cpu}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Memory</span>
                  <span className="text-white">{systemInfo.ram}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Graphics</span>
                  <span className="text-white">{systemInfo.gpu}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Storage</span>
                  <span className="text-white">{systemInfo.storage}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Network</span>
                  <span className="text-white">{systemInfo.network}</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">Updates</h3>
              <div className="space-y-3">
                <button className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-2">
                  <RefreshCw className="w-4 h-4" />
                  <span>Check for Updates</span>
                </button>
                <button className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors">
                  View Release Notes
                </button>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">About DuckBotOS</h3>
              <div className="text-gray-300 text-sm space-y-2">
                <p>DuckBotOS is an enhanced AI-powered operating system that brings advanced artificial intelligence capabilities to your desktop environment.</p>
                <p>Built with cutting-edge technologies including React, Three.js, and advanced AI integration, DuckBotOS provides a seamless, intelligent computing experience.</p>
                <div className="pt-2 text-xs text-gray-400">
                  © 2024 DuckBot Project. Licensed under MIT License.
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return (
          <div className="text-center py-8">
            <Settings className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-white text-lg font-medium mb-2">Settings</h3>
            <p className="text-gray-400">Select a category to configure your system preferences.</p>
          </div>
        );
    }
  };

  return (
    <div className="h-full bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Settings className="w-6 h-6 text-blue-400" />
            <h2 className="text-white text-xl font-semibold">DuckBotOS Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 bg-gray-800 border-r border-gray-700 overflow-y-auto">
          <div className="p-2 space-y-1">
            {sections.map(section => {
              const Icon = section.icon;
              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full text-left p-3 rounded-lg flex items-center space-x-3 transition-colors ${
                    activeSection === section.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm">{section.label}</div>
                    <div className="text-xs opacity-75 truncate">{section.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Section Header */}
          <div className="p-4 border-b border-gray-700 bg-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-white text-lg font-semibold">
                  {sections.find(s => s.id === activeSection)?.label}
                </h3>
                <p className="text-gray-400 text-sm">
                  {sections.find(s => s.id === activeSection)?.description}
                </p>
              </div>
              {hasChanges && (
                <div className="flex items-center space-x-2">
                  <span className="text-yellow-400 text-sm">● Unsaved changes</span>
                </div>
              )}
            </div>
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {renderSection()}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-gray-700 bg-gray-800">
            <div className="flex items-center justify-between">
              <div className="flex space-x-3">
                <button
                  onClick={handleReset}
                  className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
                >
                  Reset to Defaults
                </button>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={!hasChanges}
                  className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                    hasChanges
                      ? 'bg-blue-600 hover:bg-blue-700 text-white'
                      : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  <Save className="w-4 h-4" />
                  <span>Save Changes</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedSettings;