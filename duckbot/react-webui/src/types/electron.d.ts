// TypeScript declarations for Electron API
export interface ElectronAPI {
  // Environment validation
  validateEnvironment(): Promise<any>;

  // Port management
  scanPorts(): Promise<any>;
  getPortStatus(): Promise<any>;
  requestPort(portNum: number, serviceName: string, healthUrl?: string): Promise<boolean>;
  releasePort(portNum: number, serviceName: string): Promise<boolean>;
  resolvePortConflicts(): Promise<any>;

  // Enhanced service management
  startService(serviceConfig: any): Promise<any>;
  stopService(serviceName: string): Promise<any>;
  restartService(serviceName: string): Promise<any>;
  getServiceStatus(): Promise<any>;
  checkServiceHealth(serviceName: string): Promise<boolean>;

  // Configuration management
  loadConfigurations(): Promise<any>;
  saveConfiguration(configName: string, config: any): Promise<any>;

  // System status events
  onSystemStatusUpdated(callback: (event: any, data: any) => void): void;
  removeSystemStatusListener(callback: (event: any, data: any) => void): void;

  // Legacy compatibility
  minimizeToTray(): Promise<void>;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}

export {};