import React, { useState, useCallback, useRef, useEffect } from 'react'
import {
  WorkflowStep,
  StepAction,
  StepPosition,
  AutomationWorkflow,
  DropZone,
} from '@types/index'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Badge } from './ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog'
import {
  Bot,
  Monitor,
  Network,
  Server,
  Database,
  FileText,
  Cpu,
  Wrench,
  Plus,
  Settings,
  Trash2,
  GripVertical,
  Play,
  Pause,
  Square,
  Copy,
  Save,
  X,
  Eye,
  Edit,
  MoreHorizontal,
} from 'lucide-react'

interface WorkflowBuilderProps {
  workflow: AutomationWorkflow
  isEditing: boolean
  onWorkflowChange: (workflow: AutomationWorkflow) => void
  onSave: () => void
  onExecute: () => void
}

interface StepTemplate {
  type: StepAction['type']
  name: string
  icon: React.ReactNode
  description: string
  defaultCommand: string
  defaultParameters: Record<string, any>
}

const STEP_TEMPLATES: StepTemplate[] = [
  {
    type: 'bytebot',
    name: 'ByteBot Task',
    icon: <Bot className="h-5 w-5" />,
    description: 'Execute natural language task with ByteBot',
    defaultCommand: 'execute_task',
    defaultParameters: { task: 'Describe your task here' },
  },
  {
    type: 'ui_tars',
    name: 'UI Automation',
    icon: <Monitor className="h-5 w-5" />,
    description: 'Automate UI interactions with UI-TARS',
    defaultCommand: 'detect_elements',
    defaultParameters: { action: 'click_element' },
  },
  {
    type: 'browser_use',
    name: 'Browser Automation',
    icon: <Network className="h-5 w-5" />,
    description: 'Automate web browser actions',
    defaultCommand: 'navigate_to',
    defaultParameters: { url: 'https://example.com' },
  },
  {
    type: 'system',
    name: 'System Command',
    icon: <Server className="h-5 w-5" />,
    description: 'Execute system commands',
    defaultCommand: 'execute_command',
    defaultParameters: { command: 'echo "Hello World"' },
  },
  {
    type: 'api',
    name: 'API Call',
    icon: <Database className="h-5 w-5" />,
    description: 'Make HTTP API requests',
    defaultCommand: 'http_request',
    defaultParameters: { method: 'GET', url: 'https://api.example.com' },
  },
  {
    type: 'file',
    name: 'File Operation',
    icon: <FileText className="h-5 w-5" />,
    description: 'File and directory operations',
    defaultCommand: 'read_file',
    defaultParameters: { path: '/path/to/file.txt' },
  },
  {
    type: 'ai',
    name: 'AI Processing',
    icon: <Cpu className="h-5 w-5" />,
    description: 'AI-powered text processing',
    defaultCommand: 'process_text',
    defaultParameters: { text: 'Process this text' },
  },
  {
    type: 'custom',
    name: 'Custom Script',
    icon: <Wrench className="h-5 w-5" />,
    description: 'Execute custom automation script',
    defaultCommand: 'run_script',
    defaultParameters: { script: 'print("Hello World")' },
  },
]

interface Connection {
  id: string
  fromStep: string
  fromOutput: string
  toStep: string
  toInput: string
}

export function WorkflowBuilder({
  workflow,
  isEditing,
  onWorkflowChange,
  onSave,
  onExecute,
}: WorkflowBuilderProps) {
  const [selectedStep, setSelectedStep] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [dragTemplate, setDragTemplate] = useState<StepTemplate | null>(null)
  const [connections, setConnections] = useState<Connection[]>([])
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isPanning, setIsPanning] = useState(false)
  const [showGrid, setShowGrid] = useState(true)
  const [snapToGrid, setSnapToGrid] = useState(true)

  const canvasRef = useRef<HTMLDivElement>(null)
  const panStartRef = useRef({ x: 0, y: 0 })

  // Step operations
  const addStep = useCallback(
    (template: StepTemplate, position: StepPosition) => {
      const newStep: WorkflowStep = {
        id: `step_${Date.now()}`,
        name: template.name,
        type: 'action',
        action: {
          type: template.type,
          service: template.type,
          command: template.defaultCommand,
          parameters: template.defaultParameters,
        },
        inputs: {},
        outputs: {},
        conditions: [],
        timeout_ms: 30000,
        position: snapToGrid ? {
          x: Math.round(position.x / 20) * 20,
          y: Math.round(position.y / 20) * 20,
        } : position,
        dependencies: [],
        on_success: [],
        on_failure: [],
      }

      onWorkflowChange({
        ...workflow,
        steps: [...workflow.steps, newStep],
        updated_at: new Date(),
      })
    },
    [workflow, onWorkflowChange, snapToGrid]
  )

  const updateStep = useCallback(
    (stepId: string, updates: Partial<WorkflowStep>) => {
      onWorkflowChange({
        ...workflow,
        steps: workflow.steps.map((step) =>
          step.id === stepId ? { ...step, ...updates } : step
        ),
        updated_at: new Date(),
      })
    },
    [workflow, onWorkflowChange]
  )

  const deleteStep = useCallback(
    (stepId: string) => {
      // Remove step and its connections
      const newSteps = workflow.steps.filter((step) => step.id !== stepId)
      const newConnections = connections.filter(
        (conn) => conn.fromStep !== stepId && conn.toStep !== stepId
      )

      onWorkflowChange({
        ...workflow,
        steps: newSteps,
        updated_at: new Date(),
      })
      setConnections(newConnections)

      if (selectedStep === stepId) {
        setSelectedStep(null)
      }
    },
    [workflow, connections, selectedStep, onWorkflowChange]
  )

  const duplicateStep = useCallback(
    (stepId: string) => {
      const step = workflow.steps.find((s) => s.id === stepId)
      if (!step) return

      const duplicatedStep: WorkflowStep = {
        ...step,
        id: `step_${Date.now()}`,
        position: {
          x: step.position.x + 20,
          y: step.position.y + 20,
        },
        dependencies: [],
        on_success: [],
        on_failure: [],
      }

      onWorkflowChange({
        ...workflow,
        steps: [...workflow.steps, duplicatedStep],
        updated_at: new Date(),
      })
    },
    [workflow, onWorkflowChange]
  )

  // Drag and drop handlers
  const handleDragStart = useCallback((template: StepTemplate) => {
    setIsDragging(true)
    setDragTemplate(template)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)

      if (!dragTemplate || !canvasRef.current) return

      const rect = canvasRef.current.getBoundingClientRect()
      const x = (e.clientX - rect.left - pan.x) / zoom
      const y = (e.clientY - rect.top - pan.y) / zoom

      addStep(dragTemplate, { x, y })
      setDragTemplate(null)
    },
    [dragTemplate, addStep, pan, zoom]
  )

  // Pan and zoom handlers
  const handlePanStart = useCallback((e: React.MouseEvent) => {
    if (e.button !== 1 && !e.ctrlKey) return // Middle mouse or Ctrl+click for pan
    setIsPanning(true)
    panStartRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y }
  }, [pan])

  const handlePanMove = useCallback((e: React.MouseEvent) => {
    if (!isPanning) return
    setPan({
      x: e.clientX - panStartRef.current.x,
      y: e.clientY - panStartRef.current.y,
    })
  }, [isPanning])

  const handlePanEnd = useCallback(() => {
    setIsPanning(false)
  }, [])

  const handleZoom = useCallback((delta: number) => {
    setZoom((prev) => Math.max(0.1, Math.min(3, prev + delta)))
  }, [])

  // Canvas keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case '=':
          case '+':
            e.preventDefault()
            handleZoom(0.1)
            break
          case '-':
            e.preventDefault()
            handleZoom(-0.1)
            break
          case '0':
            e.preventDefault()
            setZoom(1)
            setPan({ x: 0, y: 0 })
            break
        }
      }

      // Delete selected step
      if (e.key === 'Delete' && selectedStep) {
        deleteStep(selectedStep)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedStep, deleteStep, handleZoom])

  // Mouse wheel zoom
  useEffect(() => {
    const handleWheel = (e: WheelEvent) => {
      if (e.ctrlKey) {
        e.preventDefault()
        handleZoom(e.deltaY > 0 ? -0.1 : 0.1)
      }
    }

    const canvas = canvasRef.current
    if (canvas) {
      canvas.addEventListener('wheel', handleWheel, { passive: false })
    }
    return () => canvas?.removeEventListener('wheel', handleWheel)
  }, [handleZoom])

  // Step dragging
  const handleStepDragStart = useCallback(
    (e: React.DragEvent, stepId: string) => {
      e.dataTransfer.setData('text/plain', stepId)
    },
    []
  )

  const handleStepDragOver = useCallback((e: React.DragEvent, stepId: string) => {
    e.preventDefault()
  }, [])

  const handleStepDrop = useCallback(
    (e: React.DragEvent, targetStepId: string) => {
      e.preventDefault()
      const draggedStepId = e.dataTransfer.getData('text/plain')
      if (draggedStepId === targetStepId) return

      // Create connection between steps
      const newConnection: Connection = {
        id: `conn_${Date.now()}`,
        fromStep: draggedStepId,
        fromOutput: 'output',
        toStep: targetStepId,
        toInput: 'input',
      }

      setConnections((prev) => [...prev, newConnection])

      // Add dependency
      const targetStep = workflow.steps.find((s) => s.id === targetStepId)
      if (targetStep && !targetStep.dependencies.includes(draggedStepId)) {
        updateStep(targetStepId, {
          dependencies: [...targetStep.dependencies, draggedStepId],
        })
      }
    },
    [workflow.steps, updateStep]
  )

  const getStepIcon = (action: StepAction) => {
    const template = STEP_TEMPLATES.find((t) => t.type === action.type)
    return template?.icon || <Wrench className="h-4 w-4" />
  }

  const getStatusColor = (stepType: string) => {
    switch (stepType) {
      case 'bytebot':
        return 'bg-blue-100 text-blue-700 border-blue-300'
      case 'ui_tars':
        return 'bg-purple-100 text-purple-700 border-purple-300'
      case 'browser_use':
        return 'bg-green-100 text-green-700 border-green-300'
      case 'system':
        return 'bg-gray-100 text-gray-700 border-gray-300'
      case 'api':
        return 'bg-orange-100 text-orange-700 border-orange-300'
      case 'file':
        return 'bg-yellow-100 text-yellow-700 border-yellow-300'
      case 'ai':
        return 'bg-pink-100 text-pink-700 border-pink-300'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300'
    }
  }

  return (
    <div className="flex h-full">
      {/* Step Library Panel */}
      <div className="w-64 border-r bg-muted/50 p-4 overflow-y-auto">
        <h3 className="font-medium mb-4">Step Library</h3>
        <div className="space-y-2">
          {STEP_TEMPLATES.map((template) => (
            <Card
              key={template.type}
              draggable
              onDragStart={() => handleDragStart(template)}
              className="cursor-move hover:shadow-md transition-shadow"
            >
              <CardContent className="p-3">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">{template.icon}</div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-sm">{template.name}</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      {template.description}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Controls */}
        <div className="mt-6 space-y-4">
          <div>
            <h4 className="font-medium text-sm mb-2">View Options</h4>
            <div className="space-y-2">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={showGrid}
                  onChange={(e) => setShowGrid(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm">Show Grid</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={snapToGrid}
                  onChange={(e) => setSnapToGrid(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm">Snap to Grid</span>
              </label>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-sm mb-2">Zoom Controls</h4>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleZoom(-0.1)}
                disabled={zoom <= 0.1}
              >
                -
              </Button>
              <span className="text-sm w-12 text-center">
                {Math.round(zoom * 100)}%
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleZoom(0.1)}
                disabled={zoom >= 3}
              >
                +
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setZoom(1)
                  setPan({ x: 0, y: 0 })
                }}
              >
                Reset
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Canvas */}
      <div className="flex-1 relative overflow-hidden">
        <div
          ref={canvasRef}
          className="w-full h-full cursor-move"
          onMouseDown={handlePanStart}
          onMouseMove={handlePanMove}
          onMouseUp={handlePanEnd}
          onMouseLeave={handlePanEnd}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          style={{
            backgroundImage: showGrid
              ? 'linear-gradient(rgba(0,0,0,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.1) 1px, transparent 1px)'
              : 'none',
            backgroundSize: '20px 20px',
            transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
            transformOrigin: '0 0',
          }}
        >
          {/* Drop zones visual feedback */}
          {isDragging && (
            <div className="absolute inset-0 bg-blue-50 border-2 border-dashed border-blue-400 pointer-events-none">
              <div className="flex items-center justify-center h-full text-blue-600">
                Drop to add {dragTemplate?.name}
              </div>
            </div>
          )}

          {/* Render workflow steps */}
          {workflow.steps.map((step) => (
            <div
              key={step.id}
              draggable={isEditing}
              onDragStart={(e) => handleStepDragStart(e, step.id)}
              onDragOver={(e) => handleStepDragOver(e, step.id)}
              onDrop={(e) => handleStepDrop(e, step.id)}
              className={`absolute w-48 cursor-move transition-all ${
                selectedStep === step.id ? 'ring-2 ring-blue-500 z-10' : 'z-0'
              }`}
              style={{
                left: step.position.x,
                top: step.position.y,
              }}
              onClick={() => setSelectedStep(step.id)}
            >
              <Card
                className={`${getStatusColor(step.action.type)} ${
                  isEditing ? 'hover:shadow-lg cursor-move' : ''
                }`}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getStepIcon(step.action)}
                      <CardTitle className="text-sm">{step.name}</CardTitle>
                    </div>
                    {isEditing && (
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            duplicateStep(step.id)
                          }}
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteStep(step.id)
                          }}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="text-xs text-muted-foreground mb-2">
                    {step.action.type} • {step.action.command}
                  </div>

                  {/* Connection points */}
                  <div className="flex justify-between items-center mt-2">
                    <div className="w-3 h-3 rounded-full bg-blue-500 cursor-crosshair" />
                    <div className="w-3 h-3 rounded-full bg-green-500 cursor-crosshair" />
                  </div>

                  {/* Dependencies */}
                  {step.dependencies.length > 0 && (
                    <div className="mt-2">
                      <div className="text-xs text-muted-foreground">Dependencies:</div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {step.dependencies.map((depId) => {
                          const depStep = workflow.steps.find((s) => s.id === depId)
                          return (
                            <Badge key={depId} variant="outline" className="text-xs">
                              {depStep?.name || depId}
                            </Badge>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ))}

          {/* Render connections */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            {connections.map((connection) => {
              const fromStep = workflow.steps.find((s) => s.id === connection.fromStep)
              const toStep = workflow.steps.find((s) => s.id === connection.toStep)

              if (!fromStep || !toStep) return null

              const fromX = fromStep.position.x + 192 // Step width
              const fromY = fromStep.position.y + 60
              const toX = toStep.position.x
              const toY = toStep.position.y + 60

              // Create curved path
              const midX = (fromX + toX) / 2
              const controlY = fromY - 30

              return (
                <path
                  key={connection.id}
                  d={`M ${fromX} ${fromY} Q ${midX} ${controlY} ${toX} ${toY}`}
                  stroke="#3b82f6"
                  strokeWidth="2"
                  fill="none"
                  markerEnd="url(#arrowhead)"
                />
              )
            })}
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon points="0 0, 10 3.5, 0 7" fill="#3b82f6" />
              </marker>
            </defs>
          </svg>
        </div>

        {/* Canvas controls overlay */}
        <div className="absolute top-4 right-4 flex flex-col gap-2">
          <Button variant="outline" size="sm">
            <Play className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm">
            <Pause className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm">
            <Square className="h-4 w-4" />
          </Button>
        </div>

        {/* Step properties panel */}
        {selectedStep && isEditing && (
          <div className="absolute right-0 top-0 h-full w-80 border-l bg-background shadow-lg">
            <div className="p-4 h-full overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium">Step Properties</h3>
                <Button variant="ghost" size="sm" onClick={() => setSelectedStep(null)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {(() => {
                const step = workflow.steps.find((s) => s.id === selectedStep)
                if (!step) return null

                return (
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">Name</label>
                      <Input
                        value={step.name}
                        onChange={(e) => updateStep(step.id, { name: e.target.value })}
                      />
                    </div>

                    <div>
                      <label className="text-sm font-medium">Command</label>
                      <Input
                        value={step.action.command}
                        onChange={(e) =>
                          updateStep(step.id, {
                            action: { ...step.action, command: e.target.value },
                          })
                        }
                      />
                    </div>

                    <div>
                      <label className="text-sm font-medium">Timeout (ms)</label>
                      <Input
                        type="number"
                        value={step.timeout_ms}
                        onChange={(e) =>
                          updateStep(step.id, { timeout_ms: parseInt(e.target.value) || 30000 })
                        }
                      />
                    </div>

                    <div>
                      <label className="text-sm font-medium">Position</label>
                      <div className="grid grid-cols-2 gap-2">
                        <Input
                          type="number"
                          placeholder="X"
                          value={step.position.x}
                          onChange={(e) =>
                            updateStep(step.id, {
                              position: {
                                ...step.position,
                                x: parseInt(e.target.value) || 0,
                              },
                            })
                          }
                        />
                        <Input
                          type="number"
                          placeholder="Y"
                          value={step.position.y}
                          onChange={(e) =>
                            updateStep(step.id, {
                              position: {
                                ...step.position,
                                y: parseInt(e.target.value) || 0,
                              },
                            })
                          }
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-sm font-medium mb-2 block">Parameters</label>
                      <div className="space-y-2">
                        {Object.entries(step.action.parameters).map(([key, value]) => (
                          <div key={key} className="flex items-center gap-2">
                            <Input
                              placeholder={key}
                              value={String(value)}
                              onChange={(e) =>
                                updateStep(step.id, {
                                  action: {
                                    ...step.action,
                                    parameters: {
                                      ...step.action.parameters,
                                      [key]: e.target.value,
                                    },
                                  },
                                })
                              }
                            />
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                const newParams = { ...step.action.parameters }
                                delete newParams[key]
                                updateStep(step.id, {
                                  action: {
                                    ...step.action,
                                    parameters: newParams,
                                  },
                                })
                              }}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                        ))}
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full"
                          onClick={() => {
                            const newParamName = `param_${Date.now()}`
                            updateStep(step.id, {
                              action: {
                                ...step.action,
                                parameters: {
                                  ...step.action.parameters,
                                  [newParamName]: '',
                                },
                              },
                            })
                          }}
                        >
                          <Plus className="h-3 w-3 mr-2" />
                          Add Parameter
                        </Button>
                      </div>
                    </div>
                  </div>
                )
              })()}
            </div>
          </div>
        )}

        {/* Empty state */}
        {workflow.steps.length === 0 && !isDragging && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center text-muted-foreground">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-lg font-medium mb-2">Start Building Your Workflow</h3>
              <p className="mb-4">Drag steps from the library to create your automation</p>
              <div className="flex justify-center gap-2">
                {STEP_TEMPLATES.slice(0, 3).map((template) => (
                  <Badge key={template.type} variant="outline" className="px-3 py-1">
                    {template.icon}
                    <span className="ml-1">{template.name}</span>
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}