import { useEffect, useRef, useState } from 'react'
import { io, Socket } from 'socket.io-client'
import { useAppStore } from '@stores/useAppStore'

interface UseWebSocketOptions {
  url?: string
  autoConnect?: boolean
  reconnection?: boolean
  reconnectionDelay?: number
  reconnectionAttempts?: number
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    url = 'http://localhost:9000',
    autoConnect = true,
    reconnection = true,
    reconnectionDelay = 1000,
    reconnectionAttempts = 5
  } = options

  const socketRef = useRef<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const {
    updateService,
    updateMetrics,
    updateAgent,
    addAlert,
    updateCostData
  } = useAppStore()

  useEffect(() => {
    if (!autoConnect) return

    // Initialize socket connection
    socketRef.current = io(url, {
      reconnection,
      reconnectionDelay,
      reconnectionAttempts,
      transports: ['websocket', 'polling']
    })

    const socket = socketRef.current

    // Connection events
    socket.on('connect', () => {
      setIsConnected(true)
      setConnectionError(null)
      console.log('WebSocket connected')
    })

    socket.on('disconnect', (reason) => {
      setIsConnected(false)
      console.log('WebSocket disconnected:', reason)
    })

    socket.on('connect_error', (error) => {
      setConnectionError(error.message)
      console.error('WebSocket connection error:', error)
    })

    // Service events
    socket.on('service-update', (service) => {
      updateService(service)
    })

    socket.on('service-started', (data) => {
      updateService(data.service)
      addAlert({
        type: 'success',
        title: 'Service Started',
        message: `${data.service} started successfully`
      })
    })

    socket.on('service-stopped', (data) => {
      updateService(data.service)
      addAlert({
        type: 'info',
        title: 'Service Stopped',
        message: `${data.service} has been stopped`
      })
    })

    socket.on('service-restarted', (data) => {
      updateService(data.service)
      addAlert({
        type: 'success',
        title: 'Service Restarted',
        message: `${data.service} restarted successfully`
      })
    })

    socket.on('service-error', (data) => {
      updateService({ ...data.service, status: 'error', lastError: data.error })
      addAlert({
        type: 'error',
        title: 'Service Error',
        message: `${data.service}: ${data.error}`
      })
    })

    // System metrics events
    socket.on('system-metrics', (metrics) => {
      updateMetrics(metrics)
    })

    // Cost data events
    socket.on('cost-data', (costData) => {
      updateCostData(costData)
    })

    // Agent events
    socket.on('agent-update', (data) => {
      updateAgent(data.agent)
    })

    socket.on('agent-control-result', (data) => {
      addAlert({
        type: 'success',
        title: 'Agent Action Completed',
        message: `Agent ${data.agentId} ${data.action} completed successfully`
      })
    })

    socket.on('agent-control-error', (data) => {
      addAlert({
        type: 'error',
        title: 'Agent Action Failed',
        message: `Agent ${data.agentId} ${data.action} failed: ${data.error}`
      })
    })

    // Log events
    socket.on('log-update', (log) => {
      // Handle log updates if needed
      console.log(`Log from ${log.service}:`, log.data)
    })

    // Automation events
    socket.on('automation-result', (data) => {
      addAlert({
        type: 'success',
        title: 'Automation Completed',
        message: `Command "${data.command}" executed successfully`
      })
    })

    socket.on('automation-error', (data) => {
      addAlert({
        type: 'error',
        title: 'Automation Failed',
        message: `Command "${data.command}" failed: ${data.error}`
      })
    })

    // Chat events
    socket.on('message-response', (data) => {
      // Handle chat responses
      console.log('Message response:', data)
    })

    socket.on('message-error', (data) => {
      addAlert({
        type: 'error',
        title: 'Message Failed',
        message: `Failed to send message: ${data.error}`
      })
    })

    return () => {
      socket.disconnect()
      socketRef.current = null
    }
  }, [url, autoConnect, reconnection, reconnectionDelay, reconnectionAttempts])

  // Send methods
  const send = (event: string, data?: any) => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit(event, data)
    } else {
      console.warn('WebSocket not connected, cannot send:', event)
    }
  }

  const startService = (serviceName: string) => {
    send('start-service', serviceName)
  }

  const stopService = (serviceName: string) => {
    send('stop-service', serviceName)
  }

  const restartService = (serviceName: string) => {
    send('restart-service', serviceName)
  }

  const requestSystemMetrics = () => {
    send('get-system-metrics')
  }

  const requestCostData = () => {
    send('get-cost-data')
  }

  const executeAutomation = (command: string, params?: any) => {
    send('execute-automation', command, params)
  }

  const sendMessage = (message: string, provider?: string) => {
    send('send-message', message, provider)
  }

  const controlAgent = (agentId: string, action: string, params?: any) => {
    send('control-agent', agentId, action, params)
  }

  return {
    isConnected,
    connectionError,
    send,
    startService,
    stopService,
    restartService,
    requestSystemMetrics,
    requestCostData,
    executeAutomation,
    sendMessage,
    controlAgent
  }
}