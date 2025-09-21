import { EventEmitter } from 'events'
import { spawn, ChildProcess } from 'child_process'
import fs from 'fs/promises'
import path from 'path'
import { app } from 'electron'

export interface ServiceStatus {
  name: string
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping'
  pid?: number
  port?: number
  uptime: number
  lastError?: string
  cpu?: number
  memory?: number
}

export interface SystemMetrics {
  cpu: {
    usage: number
    cores: number
    temperature?: number
  }
  memory: {
    total: number
    used: number
    available: number
    percentage: number
  }
  disk: {
    total: number
    used: number
    available: number
    percentage: number
  }
  network: {
    download: number
    upload: number
    latency: number
  }
  timestamp: Date
}

export interface CostData {
  total: number
  byProvider: Record<string, number>
  byService: Record<string, number>
  today: number
  thisMonth: number
  transactions: Array<{
    id: string
    provider: string
    service: string
    cost: number
    timestamp: Date
    tokens?: number
  }>
}

export class DuckBotServiceManager extends EventEmitter {
  private services: Map<string, ServiceStatus> = new Map()
  private processes: Map<string, ChildProcess> = new Map()
  private baseDir: string
  private duckbotPath: string
  private config: any

  constructor() {
    super()
    this.baseDir = path.dirname(app.getAppPath())
    this.duckbotPath = path.join(this.baseDir, '..')
    this.config = this.loadConfig()
    this.initializeServices()
  }

  private loadConfig(): any {
    try {
      const configPath = path.join(this.duckbotPath, 'config', 'ai_config.json')
      const configData = fs.readFileSync(configPath, 'utf-8')
      return JSON.parse(configData)
    } catch (error) {
      console.warn('Failed to load config, using defaults:', error)
      return this.getDefaultConfig()
    }
  }

  private getDefaultConfig(): any {
    return {
      providers: {
        openai: { enabled: false },
        anthropic: { enabled: false },
        qwen: { enabled: true, local: true },
        lm_studio: { enabled: true, url: 'http://localhost:1234' }
      },
      services: {
        webui: { port: 8787 },
        monitoring: { port: 8789 },
        automation: { enabled: true }
      }
    }
  }

  private initializeServices(): void {
    const coreServices = [
      { name: 'lm_studio', port: 1234, command: 'lm-studio' },
      { name: 'webui', port: 8787, command: 'python', args: ['-m', 'duckbot.webui'] },
      { name: 'monitoring', port: 8789, command: 'python', args: ['ai_ecosystem_manager.py'] },
      { name: 'ai_router', port: null, command: 'python', args: ['-c', 'from duckbot.core.ai_provider_manager import AIProviderManager; import asyncio; asyncio.run(AIProviderManager().start())'] },
      { name: 'bytebot', port: null, command: 'python', args: ['-c', 'from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_service())'] },
      { name: 'archon', port: null, command: 'python', args: ['-c', 'from duckbot.integrations.archon_integration import ArchonIntegration; import asyncio; asyncio.run(ArchonIntegration().start_service())'] },
      { name: 'mcp_server', port: null, command: 'python', args: ['-c', 'from duckbot.integrations.mcp_server import MCPServer; import asyncio; asyncio.run(MCPServer().start())'] }
    ]

    coreServices.forEach(service => {
      this.services.set(service.name, {
        name: service.name,
        status: 'stopped',
        uptime: 0,
        port: service.port || undefined
      })
    })
  }

  async initialize(): Promise<void> {
    console.log('Initializing DuckBot Service Manager...')
    await this.checkPrerequisites()
    this.startMetricsCollection()
  }

  private async checkPrerequisites(): Promise<void> {
    // Check if Python is available
    try {
      const { exec } = require('child_process')
      await new Promise((resolve, reject) => {
        exec('python --version', (error: any, stdout: string) => {
          if (error) reject(error)
          else resolve(stdout)
        })
      })
      console.log('Python is available')
    } catch (error) {
      console.warn('Python not found, some services may not work:', error)
    }

    // Check if DuckBot directory exists
    try {
      await fs.access(this.duckbotPath)
      console.log('DuckBot directory found:', this.duckbotPath)
    } catch (error) {
      console.warn('DuckBot directory not found:', error)
    }
  }

  async startService(serviceName: string): Promise<boolean> {
    const service = this.services.get(serviceName)
    if (!service) {
      throw new Error(`Service ${serviceName} not found`)
    }

    if (service.status === 'running') {
      return true
    }

    this.updateServiceStatus(serviceName, 'starting')

    try {
      const command = this.getServiceCommand(serviceName)
      if (!command) {
        throw new Error(`No command defined for service ${serviceName}`)
      }

      const process = spawn(command.command, command.args || [], {
        cwd: this.duckbotPath,
        stdio: 'pipe',
        env: { ...process.env, PYTHONPATH: this.duckbotPath }
      })

      this.processes.set(serviceName, process)

      process.stdout?.on('data', (data) => {
        this.emit('log', { service: serviceName, type: 'stdout', data: data.toString() })
      })

      process.stderr?.on('data', (data) => {
        this.emit('log', { service: serviceName, type: 'stderr', data: data.toString() })
      })

      process.on('error', (error) => {
        this.updateServiceStatus(serviceName, 'error', error.message)
        this.emit('service-error', { service: serviceName, error: error.message })
      })

      process.on('exit', (code) => {
        if (code !== 0) {
          this.updateServiceStatus(serviceName, 'error', `Process exited with code ${code}`)
        } else {
          this.updateServiceStatus(serviceName, 'stopped')
        }
        this.processes.delete(serviceName)
      })

      // Wait for service to start
      await new Promise((resolve) => setTimeout(resolve, 2000))

      if (process.pid) {
        this.updateServiceStatus(serviceName, 'running')
        this.emit('service-started', { service: serviceName, pid: process.pid })
        return true
      }

      return false
    } catch (error) {
      this.updateServiceStatus(serviceName, 'error', error instanceof Error ? error.message : 'Unknown error')
      throw error
    }
  }

  async stopService(serviceName: string): Promise<boolean> {
    const service = this.services.get(serviceName)
    if (!service) {
      throw new Error(`Service ${serviceName} not found`)
    }

    if (service.status !== 'running') {
      return true
    }

    this.updateServiceStatus(serviceName, 'stopping')

    const process = this.processes.get(serviceName)
    if (process) {
      process.kill('SIGTERM')

      // Wait for graceful shutdown
      await new Promise((resolve) => setTimeout(resolve, 5000))

      if (this.processes.has(serviceName)) {
        process.kill('SIGKILL')
      }

      this.processes.delete(serviceName)
    }

    this.updateServiceStatus(serviceName, 'stopped')
    this.emit('service-stopped', { service: serviceName })
    return true
  }

  async restartService(serviceName: string): Promise<boolean> {
    await this.stopService(serviceName)
    return await this.startService(serviceName)
  }

  private updateServiceStatus(serviceName: string, status: ServiceStatus['status'], error?: string): void {
    const service = this.services.get(serviceName)
    if (service) {
      const updated = {
        ...service,
        status,
        lastError: error,
        uptime: status === 'running' ? Date.now() : service.uptime
      }
      this.services.set(serviceName, updated)
      this.emit('service-update', updated)
    }
  }

  private getServiceCommand(serviceName: string): { command: string; args?: string[] } | null {
    const commands: Record<string, { command: string; args?: string[] }> = {
      lm_studio: { command: 'lm-studio' },
      webui: { command: 'python', args: ['-m', 'duckbot.webui', '--port', '8787'] },
      monitoring: { command: 'python', args: ['ai_ecosystem_manager.py', '--port', '8789'] },
      ai_router: { command: 'python', args: ['-c', 'from duckbot.core.ai_provider_manager import AIProviderManager; import asyncio; asyncio.run(AIProviderManager().start())'] },
      bytebot: { command: 'python', args: ['-c', 'from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_service())'] },
      archon: { command: 'python', args: ['-c', 'from duckbot.integrations.archon_integration import ArchonIntegration; import asyncio; asyncio.run(ArchonIntegration().start_service())'] },
      mcp_server: { command: 'python', args: ['-c', 'from duckbot.integrations.mcp_server import MCPServer; import asyncio; asyncio.run(MCPServer().start())'] }
    }

    return commands[serviceName] || null
  }

  async getSystemStatus(): Promise<Record<string, ServiceStatus>> {
    const status: Record<string, ServiceStatus> = {}
    this.services.forEach((service, name) => {
      status[name] = { ...service }
    })
    return status
  }

  async getSystemMetrics(): Promise<SystemMetrics> {
    const { exec } = require('child_process')

    // Simulate metrics collection (in production, use system-specific APIs)
    return {
      cpu: {
        usage: Math.random() * 100,
        cores: 8,
        temperature: 45 + Math.random() * 20
      },
      memory: {
        total: 16 * 1024 * 1024 * 1024,
        used: (8 + Math.random() * 4) * 1024 * 1024 * 1024,
        available: (8 - Math.random() * 4) * 1024 * 1024 * 1024,
        percentage: 50 + Math.random() * 25
      },
      disk: {
        total: 512 * 1024 * 1024 * 1024,
        used: (256 + Math.random() * 128) * 1024 * 1024 * 1024,
        available: (256 - Math.random() * 128) * 1024 * 1024 * 1024,
        percentage: 50 + Math.random() * 25
      },
      network: {
        download: Math.random() * 100 * 1024 * 1024,
        upload: Math.random() * 50 * 1024 * 1024,
        latency: Math.random() * 50
      },
      timestamp: new Date()
    }
  }

  async getCostData(): Promise<CostData> {
    // Simulate cost data (in production, query actual cost tracking)
    return {
      total: 12.50,
      byProvider: {
        openai: 8.25,
        anthropic: 3.75,
        qwen: 0.50
      },
      byService: {
        chat: 7.50,
        automation: 3.25,
        monitoring: 1.75
      },
      today: 2.25,
      thisMonth: 12.50,
      transactions: [
        { id: '1', provider: 'openai', service: 'chat', cost: 0.05, timestamp: new Date(), tokens: 1500 },
        { id: '2', provider: 'anthropic', service: 'chat', cost: 0.03, timestamp: new Date(), tokens: 1200 }
      ]
    }
  }

  async getServiceLogs(serviceName: string): Promise<Array<{ type: string; data: string; timestamp: Date }>> {
    // Return recent logs for the service
    return []
  }

  async getAIConfig(): Promise<any> {
    return this.config
  }

  async updateAIConfig(config: any): Promise<boolean> {
    try {
      const configPath = path.join(this.duckbotPath, 'config', 'ai_config.json')
      await fs.writeFile(configPath, JSON.stringify(config, null, 2))
      this.config = config
      this.emit('config-updated', config)
      return true
    } catch (error) {
      console.error('Failed to update config:', error)
      return false
    }
  }

  async executeAutomation(command: string, params?: any): Promise<any> {
    // Implement automation command execution
    return { success: true, message: `Executed: ${command}` }
  }

  async getConversations(): Promise<Array<any>> {
    // Return conversation history
    return []
  }

  async sendMessage(message: string, provider?: string): Promise<any> {
    // Send message to AI provider
    return { response: 'AI response to: ' + message }
  }

  async getAgents(): Promise<Array<any>> {
    // Return active agents
    return [
      { id: '1', name: 'Code Assistant', type: 'coding', status: 'active' },
      { id: '2', name: 'Research Agent', type: 'research', status: 'idle' },
      { id: '3', name: 'Automation Agent', type: 'automation', status: 'active' }
    ]
  }

  async controlAgent(agentId: string, action: string, params?: any): Promise<boolean> {
    this.emit('agent-update', { agentId, action, params })
    return true
  }

  private startMetricsCollection(): void {
    setInterval(() => {
      this.getSystemMetrics().then(metrics => {
        this.emit('metrics-update', metrics)
      })
    }, 5000)
  }

  cleanup(): void {
    // Stop all services
    const stopPromises = Array.from(this.services.keys()).map(name =>
      this.stopService(name).catch(error => {
        console.error(`Failed to stop service ${name}:`, error)
      })
    )

    Promise.all(stopPromises).then(() => {
      console.log('All services stopped')
    })
  }
}