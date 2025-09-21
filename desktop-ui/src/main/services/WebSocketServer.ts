import { Server as SocketIOServer, Socket } from 'socket.io'
import { createServer } from 'http'
import { DuckBotServiceManager } from './DuckBotServiceManager'

export class WebSocketServer {
  private io: SocketIOServer
  private server: any
  private port: number = 9000
  private serviceManager: DuckBotServiceManager

  constructor(serviceManager: DuckBotServiceManager) {
    this.serviceManager = serviceManager
    this.server = createServer()
    this.io = new SocketIOServer(this.server, {
      cors: {
        origin: "*",
        methods: ["GET", "POST"]
      }
    })
    this.setupEventHandlers()
  }

  private setupEventHandlers(): void {
    this.io.on('connection', (socket: Socket) => {
      console.log('Client connected:', socket.id)

      // Send initial system status
      this.sendSystemStatus(socket)

      // Handle client events
      socket.on('start-service', async (serviceName: string) => {
        try {
          const result = await this.serviceManager.startService(serviceName)
          socket.emit('service-started', { service: serviceName, result })
        } catch (error) {
          socket.emit('service-error', { service: serviceName, error: error instanceof Error ? error.message : 'Unknown error' })
        }
      })

      socket.on('stop-service', async (serviceName: string) => {
        try {
          const result = await this.serviceManager.stopService(serviceName)
          socket.emit('service-stopped', { service: serviceName, result })
        } catch (error) {
          socket.emit('service-error', { service: serviceName, error: error instanceof Error ? error.message : 'Unknown error' })
        }
      })

      socket.on('restart-service', async (serviceName: string) => {
        try {
          const result = await this.serviceManager.restartService(serviceName)
          socket.emit('service-restarted', { service: serviceName, result })
        } catch (error) {
          socket.emit('service-error', { service: serviceName, error: error instanceof Error ? error.message : 'Unknown error' })
        }
      })

      socket.on('get-system-metrics', async () => {
        const metrics = await this.serviceManager.getSystemMetrics()
        socket.emit('system-metrics', metrics)
      })

      socket.on('get-cost-data', async () => {
        const costData = await this.serviceManager.getCostData()
        socket.emit('cost-data', costData)
      })

      socket.on('execute-automation', async (command: string, params?: any) => {
        try {
          const result = await this.serviceManager.executeAutomation(command, params)
          socket.emit('automation-result', { command, result })
        } catch (error) {
          socket.emit('automation-error', { command, error: error instanceof Error ? error.message : 'Unknown error' })
        }
      })

      socket.on('send-message', async (message: string, provider?: string) => {
        try {
          const result = await this.serviceManager.sendMessage(message, provider)
          socket.emit('message-response', { message, result })
        } catch (error) {
          socket.emit('message-error', { message, error: error instanceof Error ? error.message : 'Unknown error' })
        }
      })

      socket.on('control-agent', async (agentId: string, action: string, params?: any) => {
        try {
          const result = await this.serviceManager.controlAgent(agentId, action, params)
          socket.emit('agent-control-result', { agentId, action, result })
        } catch (error) {
          socket.emit('agent-control-error', { agentId, action, error: error instanceof Error ? error.message : 'Unknown error' })
        }
      })

      socket.on('disconnect', () => {
        console.log('Client disconnected:', socket.id)
      })
    })

    // Listen to service manager events
    this.serviceManager.on('service-update', (service) => {
      this.io.emit('service-update', service)
    })

    this.serviceManager.on('service-started', (data) => {
      this.io.emit('service-started', data)
    })

    this.serviceManager.on('service-stopped', (data) => {
      this.io.emit('service-stopped', data)
    })

    this.serviceManager.on('service-error', (data) => {
      this.io.emit('service-error', data)
    })

    this.serviceManager.on('metrics-update', (metrics) => {
      this.io.emit('system-metrics', metrics)
    })

    this.serviceManager.on('log', (log) => {
      this.io.emit('log-update', log)
    })

    this.serviceManager.on('config-updated', (config) => {
      this.io.emit('config-updated', config)
    })

    this.serviceManager.on('agent-update', (data) => {
      this.io.emit('agent-update', data)
    })
  }

  private async sendSystemStatus(socket: Socket): Promise<void> {
    const status = await this.serviceManager.getSystemStatus()
    socket.emit('system-status', status)
  }

  async start(): Promise<void> {
    return new Promise((resolve) => {
      this.server.listen(this.port, () => {
        console.log(`WebSocket server started on port ${this.port}`)
        resolve()
      })
    })
  }

  stop(): void {
    this.server.close()
    this.io.close()
  }
}