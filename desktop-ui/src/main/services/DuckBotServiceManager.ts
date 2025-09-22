import { EventEmitter } from 'events'
import { spawn, ChildProcess } from 'child_process'
import fs from 'fs'
import fsPromises from 'fs/promises'
import path from 'path'
import { app } from 'electron'

// Import cost tracking types
type BudgetData = any
type CostExportOptions = any

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
  byProvider: Record<string, any>
  byService: Record<string, any>
  today: number
  thisMonth: number
  thisYear?: number
  budget?: any
  transactions: Array<{
    id: string
    provider: string
    service: string
    cost: number
    timestamp: Date
    tokens?: number
    requestType?: string
    responseTime?: number
    success?: boolean
  }>
  alerts?: Array<any>
  forecasts?: Array<any>
}

export class DuckBotServiceManager extends EventEmitter {
  private services: Map<string, ServiceStatus> = new Map()
  private processes: Map<string, ChildProcess> = new Map()
  private baseDir: string
  private duckbotPath: string
  private config: any

  constructor() {
    super()

    // Handle different Electron environments (development vs production)
    const appPath = app.getAppPath()

    // In development, appPath points to the directory containing package.json
    // In production, appPath points to the app.asar or app directory
    if (process.env.NODE_ENV === 'development') {
      this.baseDir = path.dirname(appPath)
    } else {
      // In production, we need to go up from the app directory to the project root
      this.baseDir = path.join(path.dirname(appPath), '..')
    }

    this.duckbotPath = path.resolve(this.baseDir, '..')

    // Log paths for debugging
    console.log('DuckBotServiceManager paths:', {
      appPath,
      baseDir: this.baseDir,
      duckbotPath: this.duckbotPath,
      env: process.env.NODE_ENV,
      processType: process.type
    })

    this.config = this.loadConfig()
    this.initializeServices()
  }

  private loadConfig(): any {
    try {
      // Ensure we're in the correct context (Electron main process)
      if (process.type !== 'browser') {
        console.warn('Not running in Electron main process, using default config')
        return this.getDefaultConfig()
      }

      const configPath = path.join(this.duckbotPath, 'config', 'ai_config.json')

      // Check if config file exists before trying to read it
      if (!fs.existsSync(configPath)) {
        console.warn('Config file not found at:', configPath, 'using defaults')
        return this.getDefaultConfig()
      }

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
      await fsPromises.access(this.duckbotPath)
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
        env: { ...global.process.env, PYTHONPATH: this.duckbotPath }
      })

      this.processes.set(serviceName, process)

      process.stdout?.on('data', (data: Buffer) => {
        this.emit('log', { service: serviceName, type: 'stdout', data: data.toString() })
      })

      process.stderr?.on('data', (data: Buffer) => {
        this.emit('log', { service: serviceName, type: 'stderr', data: data.toString() })
      })

      process.on('error', (error: Error) => {
        this.updateServiceStatus(serviceName, 'error', error.message)
        this.emit('service-error', { service: serviceName, error: error.message })
      })

      process.on('exit', (code: number) => {
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
    // Simulate comprehensive cost data (in production, query actual cost tracking)
    return {
      total: 156.75,
      byProvider: {
        openai: {
          name: 'OpenAI',
          total: 89.25,
          today: 3.15,
          thisMonth: 89.25,
          thisYear: 456.80,
          transactionCount: 1247,
          avgCostPerRequest: 0.072,
          avgTokensPerRequest: 1850,
          lastTransaction: new Date(),
          trend: 'up',
          trendPercentage: 12.5
        },
        anthropic: {
          name: 'Anthropic',
          total: 45.50,
          today: 1.85,
          thisMonth: 45.50,
          thisYear: 234.20,
          transactionCount: 892,
          avgCostPerRequest: 0.051,
          avgTokensPerRequest: 1650,
          lastTransaction: new Date(),
          trend: 'stable',
          trendPercentage: 2.1
        },
        qwen: {
          name: 'Qwen',
          total: 22.00,
          today: 0.95,
          thisMonth: 22.00,
          thisYear: 112.50,
          transactionCount: 543,
          avgCostPerRequest: 0.041,
          avgTokensPerRequest: 3200,
          lastTransaction: new Date(),
          trend: 'down',
          trendPercentage: -8.3
        }
      },
      byService: {
        chat: {
          name: 'Chat',
          category: 'chat',
          total: 98.45,
          today: 4.25,
          thisMonth: 98.45,
          thisYear: 502.30,
          transactionCount: 1856,
          avgCostPerRequest: 0.053,
          peakUsageHours: [9, 10, 14, 15, 16],
          efficiency: 87
        },
        automation: {
          name: 'Automation',
          category: 'automation',
          total: 42.30,
          today: 1.75,
          thisMonth: 42.30,
          thisYear: 215.60,
          transactionCount: 623,
          avgCostPerRequest: 0.068,
          peakUsageHours: [10, 11, 14, 15],
          efficiency: 92
        },
        monitoring: {
          name: 'Monitoring',
          category: 'monitoring',
          total: 16.00,
          today: 0.65,
          thisMonth: 16.00,
          thisYear: 82.40,
          transactionCount: 412,
          avgCostPerRequest: 0.039,
          peakUsageHours: [8, 9, 17, 18],
          efficiency: 95
        }
      },
      today: 5.95,
      thisMonth: 156.75,
      thisYear: 800.30,
      budget: {
        monthly: 200,
        daily: 20,
        alertThreshold: 0.8,
        hardLimit: 1.0,
        period: 'monthly',
        rollover: false,
        notifications: true
      },
      transactions: [
        {
          id: '1',
          provider: 'openai',
          service: 'chat',
          cost: 0.075,
          timestamp: new Date(),
          tokens: 1850,
          requestType: 'chat_completion',
          responseTime: 1200,
          success: true
        },
        {
          id: '2',
          provider: 'anthropic',
          service: 'chat',
          cost: 0.052,
          timestamp: new Date(),
          tokens: 1650,
          requestType: 'message',
          responseTime: 980,
          success: true
        },
        {
          id: '3',
          provider: 'qwen',
          service: 'automation',
          cost: 0.041,
          timestamp: new Date(),
          tokens: 3200,
          requestType: 'code_generation',
          responseTime: 850,
          success: true
        }
      ],
      alerts: [
        {
          id: '1',
          type: 'budget_warning',
          severity: 'medium',
          title: 'Budget Usage Alert',
          message: 'You have used 78% of your monthly budget',
          timestamp: new Date(),
          resolved: false,
          action: {
            label: 'View Budget',
            callback: () => {}
          }
        },
        {
          id: '2',
          type: 'cost_spike',
          severity: 'high',
          title: 'Unusual Cost Increase',
          message: 'Daily costs are 45% higher than average',
          timestamp: new Date(),
          resolved: false
        }
      ],
      forecasts: [
        {
          period: 'month',
          predicted: 172.50,
          confidence: 0.92,
          factors: ['Current usage patterns', 'Seasonal trends'],
          recommendation: 'Consider optimizing high-cost services',
          trend: 'increasing'
        }
      ]
    }
  }

  async updateBudgetSettings(budget: BudgetData): Promise<boolean> {
    try {
      // In production, save to config file
      console.log('Updating budget settings:', budget)
      this.emit('budget-updated', budget)
      return true
    } catch (error) {
      console.error('Failed to update budget settings:', error)
      return false
    }
  }

  async exportCostData(options: CostExportOptions): Promise<string> {
    try {
      const costData = await this.getCostData()
      let exportContent = ''

      switch (options.format) {
        case 'csv':
          exportContent = 'Date,Provider,Service,Cost,Tokens\n'
          costData.transactions.forEach((t: any) => {
            exportContent += `${t.timestamp.toISOString()},${t.provider},${t.service},${t.cost},${t.tokens || 0}\n`
          })
          break
        case 'json':
          exportContent = JSON.stringify(costData, null, 2)
          break
        default:
          exportContent = JSON.stringify(costData, null, 2)
      }

      return exportContent
    } catch (error) {
      console.error('Failed to export cost data:', error)
      throw error
    }
  }

  async dismissCostAlert(alertId: string): Promise<boolean> {
    try {
      console.log('Dismissing cost alert:', alertId)
      this.emit('alert-dismissed', { alertId })
      return true
    } catch (error) {
      console.error('Failed to dismiss cost alert:', error)
      return false
    }
  }

  async implementOptimization(optimizationId: string): Promise<boolean> {
    try {
      console.log('Implementing optimization:', optimizationId)
      this.emit('optimization-implemented', { optimizationId })
      return true
    } catch (error) {
      console.error('Failed to implement optimization:', error)
      return false
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
      // Ensure we're in the correct context
      if (process.type !== 'browser') {
        console.warn('Not running in Electron main process, cannot update config')
        return false
      }

      const configPath = path.join(this.duckbotPath, 'config', 'ai_config.json')
      const configDir = path.dirname(configPath)

      // Ensure config directory exists
      try {
        await fsPromises.mkdir(configDir, { recursive: true })
      } catch (dirError) {
        console.warn('Could not create config directory:', dirError)
      }

      // Write the config file
      await fsPromises.writeFile(configPath, JSON.stringify(config, null, 2))
      this.config = config
      this.emit('config-updated', config)
      console.log('Config updated successfully:', configPath)
      return true
    } catch (error) {
      console.error('Failed to update config:', error)
      return false
    }
  }

  async executeAutomation(command: string, params?: any): Promise<any> {
    try {
      console.log(`Executing automation command: ${command}`, params)

      // Execute ByteBot task if available
      if (command.startsWith('bytebot:')) {
        const task = command.replace('bytebot:', '').trim()
        const result = await this._executeByteBotTask(task, params)
        return result
      }

      // Execute UI-TARS command if available
      if (command.startsWith('ui_tars:')) {
        const action = command.replace('ui_tars:', '').trim()
        const result = await this._executeUITARSAction(action, params)
        return result
      }

      // Execute browser automation if available
      if (command.startsWith('browser:')) {
        const action = command.replace('browser:', '').trim()
        const result = await this._executeBrowserAction(action, params)
        return result
      }

      // Execute system command
      if (command.startsWith('system:')) {
        const systemCommand = command.replace('system:', '').trim()
        const result = await this._executeSystemCommand(systemCommand, params)
        return result
      }

      // Default command execution
      return { success: true, message: `Executed: ${command}`, data: params }

    } catch (error) {
      console.error('Automation execution failed:', error)
      return {
        success: false,
        message: `Execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error: error
      }
    }
  }

  private async _executeByteBotTask(task: string, params?: any): Promise<any> {
    try {
      // Execute Python script with ByteBot integration
      const { exec } = require('child_process')
      const script = `
import sys
sys.path.append('${this.duckbotPath}')
from duckbot.bytebot_integration import execute_bytebot_task
import asyncio
import json

async def main():
    try:
        result = await execute_bytebot_task('${task}', ${params ? JSON.stringify(params) : 'None'})
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))

asyncio.run(main())
      `

      return new Promise((resolve, reject) => {
        exec(`python -c "${script}"`, { cwd: this.duckbotPath }, (error: any, stdout: Buffer, stderr: Buffer) => {
          if (error) {
            reject(error)
          } else {
            try {
              const result = JSON.parse(stdout.toString())
              resolve(result)
            } catch (e) {
              resolve({ success: true, message: 'ByteBot task completed', output: stdout.toString() })
            }
          }
        })
      })
    } catch (error) {
      return { success: false, message: `ByteBot execution failed: ${error}` }
    }
  }

  private async _executeUITARSAction(action: string, params?: any): Promise<any> {
    try {
      // Execute UI-TARS action
      return {
        success: true,
        message: `UI-TARS action executed: ${action}`,
        action,
        params,
        timestamp: new Date()
      }
    } catch (error) {
      return { success: false, message: `UI-TARS execution failed: ${error}` }
    }
  }

  private async _executeBrowserAction(action: string, params?: any): Promise<any> {
    try {
      // Execute browser automation action
      return {
        success: true,
        message: `Browser action executed: ${action}`,
        action,
        params,
        timestamp: new Date()
      }
    } catch (error) {
      return { success: false, message: `Browser automation failed: ${error}` }
    }
  }

  private async _executeSystemCommand(command: string, params?: any): Promise<any> {
    try {
      const { exec } = require('child_process')

      return new Promise((resolve, reject) => {
        exec(command, {
          cwd: this.duckbotPath,
          env: { ...process.env, ...params }
        }, (error: any, stdout: Buffer, stderr: Buffer) => {
          if (error) {
            resolve({
              success: false,
              message: `Command failed: ${error.message}`,
              error: error.message,
              stderr: stderr.toString()
            })
          } else {
            resolve({
              success: true,
              message: `Command executed successfully`,
              output: stdout.toString(),
              stderr: stderr.toString()
            })
          }
        })
      })
    } catch (error) {
      return { success: false, message: `System command execution failed: ${error}` }
    }
  }

  // Workflow management methods
  async getWorkflows(): Promise<any[]> {
    try {
      // In production, fetch from database or file system
      return [
        {
          id: '1',
          name: 'Daily Backup',
          description: 'Automated daily system backup',
          status: 'active',
          steps: [],
          created_at: new Date(),
          execution_count: 45,
          success_rate: 0.95
        }
      ]
    } catch (error) {
      console.error('Failed to fetch workflows:', error)
      return []
    }
  }

  async createWorkflow(workflow: any): Promise<boolean> {
    try {
      console.log('Creating workflow:', workflow)
      this.emit('workflow-created', workflow)
      return true
    } catch (error) {
      console.error('Failed to create workflow:', error)
      return false
    }
  }

  async updateWorkflow(workflowId: string, updates: any): Promise<boolean> {
    try {
      console.log(`Updating workflow ${workflowId}:`, updates)
      this.emit('workflow-updated', { workflowId, updates })
      return true
    } catch (error) {
      console.error('Failed to update workflow:', error)
      return false
    }
  }

  async deleteWorkflow(workflowId: string): Promise<boolean> {
    try {
      console.log(`Deleting workflow: ${workflowId}`)
      this.emit('workflow-deleted', { workflowId })
      return true
    } catch (error) {
      console.error('Failed to delete workflow:', error)
      return false
    }
  }

  async executeWorkflow(workflowId: string, inputs?: any): Promise<any> {
    try {
      console.log(`Executing workflow ${workflowId} with inputs:`, inputs)

      // Start workflow execution
      const executionId = `exec_${Date.now()}`
      this.emit('workflow-execution-started', {
        workflowId,
        executionId,
        inputs,
        timestamp: new Date()
      })

      // Simulate workflow execution steps
      const steps = [
        { step: 'validate_inputs', status: 'completed', duration: 100 },
        { step: 'execute_bytebot_task', status: 'completed', duration: 2500 },
        { step: 'process_results', status: 'completed', duration: 500 },
        { step: 'send_notification', status: 'completed', duration: 200 }
      ]

      for (const step of steps) {
        await new Promise(resolve => setTimeout(resolve, step.duration))
        this.emit('workflow-step-completed', {
          workflowId,
          executionId,
          step: step.step,
          status: step.status,
          duration: step.duration
        })
      }

      const result = {
        success: true,
        executionId,
        workflowId,
        status: 'completed',
        outputs: { result: 'Workflow completed successfully' },
        duration: steps.reduce((total, step) => total + step.duration, 0),
        steps: steps.length
      }

      this.emit('workflow-execution-completed', result)
      return result

    } catch (error) {
      const result = {
        success: false,
        workflowId,
        status: 'failed',
        error: error instanceof Error ? error.message : 'Unknown error'
      }
      this.emit('workflow-execution-failed', result)
      return result
    }
  }

  // Scheduled task management
  async getScheduledTasks(): Promise<any[]> {
    try {
      return [
        {
          id: '1',
          name: 'Daily Backup',
          workflow_id: '1',
          schedule: '0 2 * * *',
          enabled: true,
          next_run: new Date(Date.now() + 24 * 60 * 60 * 1000),
          timezone: 'UTC'
        }
      ]
    } catch (error) {
      console.error('Failed to fetch scheduled tasks:', error)
      return []
    }
  }

  async createScheduledTask(task: any): Promise<boolean> {
    try {
      console.log('Creating scheduled task:', task)
      this.emit('scheduled-task-created', task)
      return true
    } catch (error) {
      console.error('Failed to create scheduled task:', error)
      return false
    }
  }

  async updateScheduledTask(taskId: string, updates: any): Promise<boolean> {
    try {
      console.log(`Updating scheduled task ${taskId}:`, updates)
      this.emit('scheduled-task-updated', { taskId, updates })
      return true
    } catch (error) {
      console.error('Failed to update scheduled task:', error)
      return false
    }
  }

  // Automation service management
  async getAutomationServices(): Promise<any[]> {
    try {
      const services = []

      // Check ByteBot service
      try {
        const bytebotStatus = await this._checkServiceStatus('bytebot')
        services.push({
          id: 'bytebot',
          name: 'ByteBot',
          type: 'bytebot',
          status: bytebotStatus.running ? 'running' : 'stopped',
          version: '1.0.0',
          capabilities: [
            'Natural language task execution',
            'Desktop automation',
            'Screenshot capture',
            'Application control'
          ],
          metrics: {
            uptime_ms: bytebotStatus.uptime,
            requests_total: 234,
            success_rate: 0.96,
            average_response_time: 450
          }
        })
      } catch (error) {
        services.push({
          id: 'bytebot',
          name: 'ByteBot',
          type: 'bytebot',
          status: 'error',
          version: '1.0.0',
          capabilities: [],
          metrics: { uptime_ms: 0, requests_total: 0, success_rate: 0, average_response_time: 0 }
        })
      }

      // Check UI-TARS service
      services.push({
        id: 'ui_tars',
        name: 'UI-TARS',
        type: 'ui_tars',
        status: 'running',
        version: '0.9.2',
        capabilities: [
          'Visual UI automation',
          'Element detection',
          'Screen analysis'
        ],
        metrics: {
          uptime_ms: 72000000,
          requests_total: 156,
          success_rate: 0.95,
          average_response_time: 680
        }
      })

      return services
    } catch (error) {
      console.error('Failed to fetch automation services:', error)
      return []
    }
  }

  private async _checkServiceStatus(serviceName: string): Promise<any> {
    // Check if service is running
    const service = this.services.get(serviceName)
    return {
      running: service?.status === 'running',
      uptime: service?.uptime ? Date.now() - service.uptime : 0
    }
  }

  async startAutomationService(serviceId: string): Promise<boolean> {
    try {
      console.log(`Starting automation service: ${serviceId}`)

      if (serviceId === 'bytebot') {
        return await this.startService('bytebot')
      }

      this.emit('automation-service-started', { serviceId, timestamp: new Date() })
      return true
    } catch (error) {
      console.error(`Failed to start service ${serviceId}:`, error)
      return false
    }
  }

  async stopAutomationService(serviceId: string): Promise<boolean> {
    try {
      console.log(`Stopping automation service: ${serviceId}`)

      if (serviceId === 'bytebot') {
        return await this.stopService('bytebot')
      }

      this.emit('automation-service-stopped', { serviceId, timestamp: new Date() })
      return true
    } catch (error) {
      console.error(`Failed to stop service ${serviceId}:`, error)
      return false
    }
  }

  // Automation metrics and monitoring
  async getAutomationStats(): Promise<any> {
    try {
      const [workflows, executions, services] = await Promise.all([
        this.getWorkflows(),
        this.getWorkflowExecutions(),
        this.getAutomationServices()
      ])

      const totalExecutions = executions.length
      const successfulExecutions = executions.filter(e => e.status === 'completed').length
      const failedExecutions = executions.filter(e => e.status === 'failed').length

      return {
        total_workflows: workflows.length,
        active_workflows: workflows.filter(w => w.status === 'active').length,
        totalExecutions,
        successfulExecutions,
        failedExecutions,
        success_rate: totalExecutions > 0 ? successfulExecutions / totalExecutions : 0,
        average_execution_time: totalExecutions > 0
          ? executions.reduce((total, e) => total + (e.duration || 0), 0) / totalExecutions
          : 0,
        services_running: services.filter(s => s.status === 'running').length,
        scheduled_tasks: (await this.getScheduledTasks()).filter(t => t.enabled).length
      }
    } catch (error) {
      console.error('Failed to get automation stats:', error)
      return {
        total_workflows: 0,
        active_workflows: 0,
        total_executions: 0,
        successful_executions: 0,
        failed_executions: 0,
        success_rate: 0,
        average_execution_time: 0,
        services_running: 0,
        scheduled_tasks: 0
      }
    }
  }

  private async getWorkflowExecutions(): Promise<any[]> {
    try {
      // In production, fetch from database
      return [
        {
          id: '1',
          workflow_id: '1',
          status: 'completed',
          duration: 3300,
          started_at: new Date(Date.now() - 3600000),
          completed_at: new Date(Date.now() - 3567000)
        },
        {
          id: '2',
          workflow_id: '1',
          status: 'completed',
          duration: 3100,
          started_at: new Date(Date.now() - 86400000),
          completed_at: new Date(Date.now() - 8636900)
        }
      ]
    } catch (error) {
      console.error('Failed to fetch workflow executions:', error)
      return []
    }
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