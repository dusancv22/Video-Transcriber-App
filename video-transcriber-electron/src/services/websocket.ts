/**
 * WebSocket service for real-time updates from the FastAPI backend
 */

import { WebSocketEvent, WebSocketEventType } from '../types/api'

export type WebSocketConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'

export interface WebSocketServiceOptions {
  url?: string
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
}

export interface WebSocketEventHandler {
  (event: WebSocketEvent): void
}

export class WebSocketService {
  private ws: WebSocket | null = null
  private url: string
  private reconnectInterval: number
  private maxReconnectAttempts: number
  private heartbeatInterval: number
  private reconnectAttempts: number = 0
  private heartbeatTimer: NodeJS.Timeout | null = null
  private reconnectTimer: NodeJS.Timeout | null = null
  private eventHandlers: Map<WebSocketEventType | 'connection', WebSocketEventHandler[]> = new Map()
  private connectionState: WebSocketConnectionState = 'disconnected'

  constructor(options: WebSocketServiceOptions = {}) {
    this.url = options.url || 'ws://127.0.0.1:8000/ws'
    this.reconnectInterval = options.reconnectInterval || 5000
    this.maxReconnectAttempts = options.maxReconnectAttempts || 10
    this.heartbeatInterval = options.heartbeatInterval || 30000
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      this.connectionState = 'connecting'
      this.notifyConnectionStateChange()

      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.connectionState = 'connected'
          this.reconnectAttempts = 0
          this.startHeartbeat()
          this.notifyConnectionStateChange()
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data: WebSocketEvent = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason)
          this.connectionState = 'disconnected'
          this.stopHeartbeat()
          this.notifyConnectionStateChange()
          
          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect()
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.connectionState = 'error'
          this.notifyConnectionStateChange()
          reject(new Error('WebSocket connection failed'))
        }

      } catch (error) {
        this.connectionState = 'error'
        this.notifyConnectionStateChange()
        reject(error)
      }
    })
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    this.stopHeartbeat()

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }

    this.connectionState = 'disconnected'
    this.reconnectAttempts = 0
    this.notifyConnectionStateChange()
  }

  /**
   * Send message to WebSocket server
   */
  send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, cannot send message:', message)
    }
  }

  /**
   * Subscribe to WebSocket events
   */
  on(eventType: WebSocketEventType | 'connection', handler: WebSocketEventHandler): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, [])
    }
    this.eventHandlers.get(eventType)!.push(handler)
  }

  /**
   * Unsubscribe from WebSocket events
   */
  off(eventType: WebSocketEventType | 'connection', handler?: WebSocketEventHandler): void {
    if (!this.eventHandlers.has(eventType)) {
      return
    }

    if (handler) {
      const handlers = this.eventHandlers.get(eventType)!
      const index = handlers.indexOf(handler)
      if (index !== -1) {
        handlers.splice(index, 1)
      }
    } else {
      this.eventHandlers.delete(eventType)
    }
  }

  /**
   * Get current connection state
   */
  getConnectionState(): WebSocketConnectionState {
    return this.connectionState
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(event: WebSocketEvent): void {
    console.log('WebSocket message received:', event.type, event)

    // Notify specific event handlers
    const handlers = this.eventHandlers.get(event.type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(event)
        } catch (error) {
          console.error(`Error in WebSocket event handler for ${event.type}:`, error)
        }
      })
    }
  }

  /**
   * Notify connection state changes
   */
  private notifyConnectionStateChange(): void {
    const connectionEvent: any = {
      type: 'connection',
      state: this.connectionState,
      timestamp: new Date().toISOString()
    }

    const handlers = this.eventHandlers.get('connection')
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(connectionEvent)
        } catch (error) {
          console.error('Error in connection state handler:', error)
        }
      })
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()
    
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'heartbeat', timestamp: new Date().toISOString() })
      }
    }, this.heartbeatInterval)
  }

  /**
   * Stop heartbeat timer
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return
    }

    this.reconnectAttempts++
    const delay = Math.min(this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1), 30000)

    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`)

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.connect().catch(error => {
        console.error('Reconnection failed:', error)
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect()
        }
      })
    }, delay)
  }
}

/**
 * Singleton WebSocket service instance
 */
export const websocketService = new WebSocketService()

/**
 * WebSocket event utilities
 */
export class WebSocketEventUtils {
  
  /**
   * Create a typed event handler
   */
  static createEventHandler<T extends WebSocketEvent>(
    handler: (event: T) => void
  ): WebSocketEventHandler {
    return (event: WebSocketEvent) => {
      handler(event as T)
    }
  }

  /**
   * Filter events by type
   */
  static filterEventsByType<T extends WebSocketEvent>(
    events: WebSocketEvent[],
    type: WebSocketEventType
  ): T[] {
    return events.filter(event => event.type === type) as T[]
  }

  /**
   * Get latest event of specific type
   */
  static getLatestEvent<T extends WebSocketEvent>(
    events: WebSocketEvent[],
    type: WebSocketEventType
  ): T | null {
    const filtered = WebSocketEventUtils.filterEventsByType<T>(events, type)
    return filtered.length > 0 ? filtered[filtered.length - 1] : null
  }
}

export default WebSocketService