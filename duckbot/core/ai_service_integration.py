"""
AI Service Integration Module

Provides enhanced API endpoints and service integrations for AI capabilities:
- REST API endpoints for AI system control
- WebSocket real-time communication
- Service discovery and registration
- AI service hooks and callbacks
- External AI provider integration
- Event-driven service architecture

Author: Claude for DuckBot Enhanced v4.2
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import sqlite3
import threading
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from .ai_orchestrator import AIOrchestrator, OrchestratorConfig, OrchestratorMode
from .ai_system_controller import AICommand, AICommandType
from .ai_decision_maker import DecisionCategory, DecisionContext
from .ai_knowledge_base import KnowledgeQuery, KnowledgeCategory
from .monitoring_system import AlertSeverity

logger = logging.getLogger(__name__)

class ServiceType(Enum):
    """Types of AI services"""
    ORCHESTRATOR = "orchestrator"
    MONITORING = "monitoring"
    DECISION_MAKER = "decision_maker"
    KNOWLEDGE_BASE = "knowledge_base"
    SYSTEM_CONTROLLER = "system_controller"
    SYSTEM_MANAGER = "system_manager"

class EventType(Enum):
    """Event types for service communication"""
    SYSTEM_STATUS_UPDATE = "system_status_update"
    OPERATION_CREATED = "operation_created"
    OPERATION_APPROVED = "operation_approved"
    OPERATION_COMPLETED = "operation_completed"
    ALERT_TRIGGERED = "alert_triggered"
    DECISION_MADE = "decision_made"
    KNOWLEDGE_UPDATED = "knowledge_updated"
    HEALTH_CHECK = "health_check"

@dataclass
class ServiceEndpoint:
    """Represents a service endpoint"""
    service_type: ServiceType
    name: str
    url: str
    health_check_url: Optional[str] = None
    version: str = "1.0.0"
    status: str = "active"
    last_heartbeat: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ServiceEvent:
    """Represents a service event"""
    event_id: str
    event_type: EventType
    source_service: str
    target_service: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 1-10

# Pydantic models for API
class AICommandRequest(BaseModel):
    command_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 5
    requires_approval: bool = False

class AICommandResponse(BaseModel):
    success: bool
    command_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

class SystemStatusResponse(BaseModel):
    status: str
    mode: str
    autonomy_level: float
    health_score: float
    performance_score: float
    active_operations: int
    pending_approvals: int
    uptime: str

class OperationRequest(BaseModel):
    operation_type: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 5
    requires_approval: Optional[bool] = None

class OperationResponse(BaseModel):
    operation_id: str
    status: str
    message: str

class DecisionRequest(BaseModel):
    category: str
    context: Dict[str, Any]
    objectives: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)

class DecisionResponse(BaseModel):
    decision_id: str
    action: str
    confidence_score: float
    reasoning: str
    parameters: Dict[str, Any]

class KnowledgeQueryRequest(BaseModel):
    query_text: str
    category: Optional[str] = None
    limit: int = 10
    filters: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeQueryResponse(BaseModel):
    query_id: str
    results: List[Dict[str, Any]]
    total_results: int
    query_time: float

class ServiceRegistrationRequest(BaseModel):
    service_type: str
    name: str
    url: str
    health_check_url: Optional[str] = None
    version: str = "1.0.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ServiceStatusResponse(BaseModel):
    service_id: str
    service_type: str
    status: str
    version: str
    last_heartbeat: str
    uptime: str
    metadata: Dict[str, Any]

class AIIntegrationService:
    """Main AI Service Integration layer"""

    def __init__(self, orchestrator: AIOrchestrator, host: str = "127.0.0.1", port: int = 8790):
        self.orchestrator = orchestrator
        self.host = host
        self.port = port

        # FastAPI app
        self.app = FastAPI(
            title="DuckBot AI Integration Service",
            description="API endpoints for AI system control and monitoring",
            version="1.0.0"
        )

        # Service registry
        self.services: Dict[str, ServiceEndpoint] = {}
        self.service_events: List[ServiceEvent] = []

        # WebSocket connections
        self.websocket_connections: List[WebSocket] = []

        # Performance tracking
        self.service_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "websocket_connections": 0,
            "events_processed": 0
        }

        # Database setup
        self.db_path = Path("duckbot_ai_service_integration.db")
        self._init_database()

        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()

        # Background tasks
        self._running = False
        self._background_tasks: List[asyncio.Task] = []

        # Event handlers
        self.event_handlers: Dict[EventType, List[Callable]] = {}

        logger.info("AI Integration Service initialized")

    def _init_database(self):
        """Initialize service integration database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Services table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS services (
                        service_id TEXT PRIMARY KEY,
                        service_type TEXT,
                        name TEXT,
                        url TEXT,
                        health_check_url TEXT,
                        version TEXT,
                        status TEXT,
                        last_heartbeat TEXT,
                        metadata TEXT
                    )
                """)

                # Events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS service_events (
                        event_id TEXT PRIMARY KEY,
                        event_type TEXT,
                        source_service TEXT,
                        target_service TEXT,
                        timestamp TEXT,
                        data TEXT,
                        priority INTEGER
                    )
                """)

                # API requests table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_requests (
                        request_id TEXT PRIMARY KEY,
                        endpoint TEXT,
                        method TEXT,
                        timestamp TEXT,
                        response_time REAL,
                        status_code INTEGER,
                        request_data TEXT,
                        response_data TEXT
                    )
                """)

                conn.commit()
                logger.info("Service integration database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize service integration database: {e}")

    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Request logging middleware
        @self.app.middleware("http")
        async def log_requests(request, call_next):
            start_time = time.time()
            request_id = f"req_{int(time.time() * 1000)}"

            # Process request
            response = await call_next(request)

            # Calculate response time
            response_time = time.time() - start_time

            # Log request
            self._log_api_request(
                request_id,
                request.url.path,
                request.method,
                response_time,
                response.status_code
            )

            return response

    def _setup_routes(self):
        """Setup API routes"""

        # Health check
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        # System status
        @self.app.get("/system/status", response_model=SystemStatusResponse)
        async def get_system_status():
            try:
                status = self.orchestrator.get_orchestrator_status()
                monitoring_status = status.get("monitoring_status", {})

                return SystemStatusResponse(
                    status="running" if status.get("running", False) else "stopped",
                    mode=status.get("mode", "unknown"),
                    autonomy_level=status.get("autonomy_level", 0.0),
                    health_score=monitoring_status.get("health_score", 0.0),
                    performance_score=monitoring_status.get("performance_score", 0.0),
                    active_operations=status.get("active_operations", 0),
                    pending_approvals=status.get("pending_approvals", 0),
                    uptime=self._get_uptime()
                )
            except Exception as e:
                logger.error(f"Error getting system status: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # AI Commands
        @self.app.post("/ai/commands", response_model=AICommandResponse)
        async def execute_ai_command(request: AICommandRequest):
            try:
                # Map command type
                command_type_map = {
                    "system_monitoring": AICommandType.SYSTEM_MONITORING,
                    "health_management": AICommandType.HEALTH_MANAGEMENT,
                    "performance_optimization": AICommandType.PERFORMANCE_OPTIMIZATION,
                    "error_recovery": AICommandType.ERROR_RECOVERY,
                    "service_control": AICommandType.SERVICE_CONTROL,
                    "resource_management": AICommandType.RESOURCE_MANAGEMENT,
                    "predictive_maintenance": AICommandType.PREDICTIVE_MAINTENANCE,
                    "agent_management": AICommandType.AGENT_MANAGEMENT
                }

                command_type = command_type_map.get(request.command_type)
                if not command_type:
                    raise HTTPException(status_code=400, detail=f"Unknown command type: {request.command_type}")

                # Create command
                command = AICommand(
                    command_type=command_type,
                    parameters=request.parameters
                )

                # Execute command
                start_time = time.time()
                result = await self.orchestrator.ai_controller.process_command(command)
                execution_time = time.time() - start_time

                return AICommandResponse(
                    success=result.success,
                    command_id=command.id,
                    result=result.result,
                    error=result.error,
                    execution_time=execution_time
                )

            except Exception as e:
                logger.error(f"Error executing AI command: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Operations
        @self.app.post("/operations", response_model=OperationResponse)
        async def create_operation(request: OperationRequest):
            try:
                operation_id = await self.orchestrator.request_operation(
                    operation_type=request.operation_type,
                    description=request.description,
                    parameters=request.parameters,
                    priority=request.priority,
                    requires_approval=request.requires_approval
                )

                return OperationResponse(
                    operation_id=operation_id,
                    status="created",
                    message="Operation created successfully"
                )

            except Exception as e:
                logger.error(f"Error creating operation: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/operations/pending")
        async def get_pending_operations():
            try:
                return self.orchestrator.get_pending_operations()
            except Exception as e:
                logger.error(f"Error getting pending operations: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/operations/recent")
        async def get_recent_operations(limit: int = 10):
            try:
                return self.orchestrator.get_recent_operations(limit)
            except Exception as e:
                logger.error(f"Error getting recent operations: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/operations/{operation_id}/approve")
        async def approve_operation(operation_id: str, approved_by: str = "api_user"):
            try:
                success = await self.orchestrator.approve_operation(operation_id, approved_by)
                if not success:
                    raise HTTPException(status_code=404, detail="Operation not found or not pending")
                return {"success": True, "message": "Operation approved"}
            except Exception as e:
                logger.error(f"Error approving operation: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/operations/{operation_id}/reject")
        async def reject_operation(operation_id: str, reason: str = "Rejected via API"):
            try:
                success = await self.orchestrator.reject_operation(operation_id, reason)
                if not success:
                    raise HTTPException(status_code=404, detail="Operation not found or not pending")
                return {"success": True, "message": "Operation rejected"}
            except Exception as e:
                logger.error(f"Error rejecting operation: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Decision Making
        @self.app.post("/ai/decisions", response_model=DecisionResponse)
        async def make_decision(request: DecisionRequest):
            try:
                # Map category
                category_map = {
                    "system_management": DecisionCategory.SYSTEM_MANAGEMENT,
                    "error_recovery": DecisionCategory.ERROR_RECOVERY,
                    "performance_optimization": DecisionCategory.PERFORMANCE_OPTIMIZATION,
                    "resource_management": DecisionCategory.RESOURCE_MANAGEMENT,
                    "security_analysis": DecisionCategory.SECURITY_ANALYSIS
                }

                category = category_map.get(request.category)
                if not category:
                    raise HTTPException(status_code=400, detail=f"Unknown decision category: {request.category}")

                # Create context
                context = DecisionContext(
                    system_state=request.context.get("system_state", {}),
                    performance_metrics=request.context.get("performance_metrics", {}),
                    constraints=request.constraints,
                    objectives=request.objectives
                )

                # Make decision
                decision = await self.orchestrator.decision_maker.make_decision(category, context)

                return DecisionResponse(
                    decision_id=decision.id,
                    action=decision.action,
                    confidence_score=decision.confidence_score,
                    reasoning=decision.reasoning,
                    parameters=decision.parameters
                )

            except Exception as e:
                logger.error(f"Error making decision: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Knowledge Base
        @self.app.post("/knowledge/query", response_model=KnowledgeQueryResponse)
        async def query_knowledge(request: KnowledgeQueryRequest):
            try:
                # Map category
                category_map = {
                    "system_health_monitoring": KnowledgeCategory.SYSTEM_HEALTH_MONITORING,
                    "performance_optimization": KnowledgeCategory.PERFORMANCE_OPTIMIZATION,
                    "error_recovery": KnowledgeCategory.ERROR_RECOVERY,
                    "service_management": KnowledgeCategory.SERVICE_MANAGEMENT,
                    "resource_management": KnowledgeCategory.RESOURCE_MANAGEMENT,
                    "predictive_maintenance": KnowledgeCategory.PREDICTIVE_MAINTENANCE,
                    "security_hardening": KnowledgeCategory.SECURITY_HARDENING,
                    "troubleshooting": KnowledgeCategory.TROUBLESHOOTING
                }

                category = None
                if request.category:
                    category = category_map.get(request.category)
                    if not category:
                        raise HTTPException(status_code=400, detail=f"Unknown knowledge category: {request.category}")

                # Create query
                query = KnowledgeQuery(
                    query_text=request.query_text,
                    category=category,
                    limit=request.limit,
                    filters=request.filters
                )

                # Execute query
                start_time = time.time()
                result = self.orchestrator.knowledge_base.search_knowledge(query)
                query_time = time.time() - start_time

                # Format results
                results = [
                    {
                        "entry_id": entry.id,
                        "title": entry.title,
                        "content": entry.content,
                        "category": entry.category.value,
                        "tags": entry.tags,
                        "relevance_score": score,
                        "created_at": entry.created_at.isoformat(),
                        "metadata": entry.metadata
                    }
                    for entry, score in result.entries
                ]

                return KnowledgeQueryResponse(
                    query_id=f"query_{int(time.time())}",
                    results=results,
                    total_results=len(results),
                    query_time=query_time
                )

            except Exception as e:
                logger.error(f"Error querying knowledge base: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/knowledge/add")
        async def add_knowledge(
            title: str,
            content: str,
            category: str,
            tags: List[str] = [],
            metadata: Dict[str, Any] = {}
        ):
            try:
                # Map category
                category_map = {
                    "system_health_monitoring": KnowledgeCategory.SYSTEM_HEALTH_MONITORING,
                    "performance_optimization": KnowledgeCategory.PERFORMANCE_OPTIMIZATION,
                    "error_recovery": KnowledgeCategory.ERROR_RECOVERY,
                    "service_management": KnowledgeCategory.SERVICE_MANAGEMENT,
                    "resource_management": KnowledgeCategory.RESOURCE_MANAGEMENT,
                    "predictive_maintenance": KnowledgeCategory.PREDICTIVE_MAINTENANCE,
                    "security_hardening": KnowledgeCategory.SECURITY_HARDENING,
                    "troubleshooting": KnowledgeCategory.TROUBLESHOOTING
                }

                knowledge_category = category_map.get(category)
                if not knowledge_category:
                    raise HTTPException(status_code=400, detail=f"Unknown knowledge category: {category}")

                # Create knowledge entry
                from .ai_knowledge_base import KnowledgeEntry
                entry = KnowledgeEntry(
                    category=knowledge_category,
                    title=title,
                    content=content,
                    tags=tags,
                    metadata=metadata
                )

                # Add to knowledge base
                entry_id = self.orchestrator.knowledge_base.add_knowledge(entry)

                return {"success": True, "entry_id": entry_id, "message": "Knowledge added successfully"}

            except Exception as e:
                logger.error(f"Error adding knowledge: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Service Registry
        @self.app.post("/services/register", response_model=ServiceStatusResponse)
        async def register_service(request: ServiceRegistrationRequest):
            try:
                # Map service type
                service_type_map = {
                    "orchestrator": ServiceType.ORCHESTRATOR,
                    "monitoring": ServiceType.MONITORING,
                    "decision_maker": ServiceType.DECISION_MAKER,
                    "knowledge_base": ServiceType.KNOWLEDGE_BASE,
                    "system_controller": ServiceType.SYSTEM_CONTROLLER,
                    "system_manager": ServiceType.SYSTEM_MANAGER
                }

                service_type = service_type_map.get(request.service_type)
                if not service_type:
                    raise HTTPException(status_code=400, detail=f"Unknown service type: {request.service_type}")

                # Create service endpoint
                service_id = f"{request.service_type}_{request.name}_{int(time.time())}"
                service = ServiceEndpoint(
                    service_id=service_id,
                    service_type=service_type,
                    name=request.name,
                    url=request.url,
                    health_check_url=request.health_check_url,
                    version=request.version,
                    metadata=request.metadata
                )

                # Register service
                self.services[service_id] = service
                self._store_service(service)

                logger.info(f"Registered service: {service_id}")

                return ServiceStatusResponse(
                    service_id=service_id,
                    service_type=service.service_type.value,
                    status=service.status,
                    version=service.version,
                    last_heartbeat=service.last_heartbeat.isoformat(),
                    uptime="0s",
                    metadata=service.metadata
                )

            except Exception as e:
                logger.error(f"Error registering service: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/services")
        async def get_services():
            try:
                return [
                    {
                        "service_id": service_id,
                        "service_type": service.service_type.value,
                        "name": service.name,
                        "url": service.url,
                        "status": service.status,
                        "version": service.version,
                        "last_heartbeat": service.last_heartbeat.isoformat(),
                        "uptime": self._calculate_uptime(service.last_heartbeat),
                        "metadata": service.metadata
                    }
                    for service_id, service in self.services.items()
                ]
            except Exception as e:
                logger.error(f"Error getting services: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/services/{service_id}", response_model=ServiceStatusResponse)
        async def get_service_status(service_id: str):
            try:
                if service_id not in self.services:
                    raise HTTPException(status_code=404, detail="Service not found")

                service = self.services[service_id]

                return ServiceStatusResponse(
                    service_id=service_id,
                    service_type=service.service_type.value,
                    status=service.status,
                    version=service.version,
                    last_heartbeat=service.last_heartbeat.isoformat(),
                    uptime=self._calculate_uptime(service.last_heartbeat),
                    metadata=service.metadata
                )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting service status: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/services/{service_id}")
        async def unregister_service(service_id: str):
            try:
                if service_id not in self.services:
                    raise HTTPException(status_code=404, detail="Service not found")

                del self.services[service_id]
                self._remove_service(service_id)

                logger.info(f"Unregistered service: {service_id}")
                return {"success": True, "message": "Service unregistered"}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error unregistering service: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Reports
        @self.app.get("/reports/comprehensive")
        async def get_comprehensive_report():
            try:
                return await self.orchestrator.generate_comprehensive_report()
            except Exception as e:
                logger.error(f"Error generating comprehensive report: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/stats")
        async def get_service_stats():
            try:
                return {
                    "service_stats": self.service_stats,
                    "orchestrator_stats": self.orchestrator.get_orchestrator_status().get("stats", {}),
                    "registered_services": len(self.services),
                    "active_websockets": len(self.websocket_connections),
                    "events_processed": len(self.service_events)
                }
            except Exception as e:
                logger.error(f"Error getting service stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # WebSocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.websocket_connections.append(websocket)
            self.service_stats["websocket_connections"] = len(self.websocket_connections)

            try:
                # Send initial status
                await websocket.send_json({
                    "type": "connection_established",
                    "timestamp": datetime.now().isoformat(),
                    "message": "WebSocket connection established"
                })

                # Keep connection alive and handle messages
                while True:
                    try:
                        # Wait for messages
                        data = await websocket.receive_text()
                        message = json.loads(data)

                        # Handle different message types
                        await self._handle_websocket_message(websocket, message)

                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.error(f"Error handling WebSocket message: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "timestamp": datetime.now().isoformat(),
                            "error": str(e)
                        })

            except WebSocketDisconnect:
                pass
            finally:
                # Clean up connection
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
                self.service_stats["websocket_connections"] = len(self.websocket_connections)

    async def _handle_websocket_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle WebSocket messages"""
        try:
            message_type = message.get("type")

            if message_type == "subscribe":
                # Subscribe to specific events
                events = message.get("events", [])
                for event_type in events:
                    self.add_event_handler(EventType(event_type), lambda data: websocket.send_json({
                        "type": "event",
                        "event_type": event_type,
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }))

                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "events": events,
                    "timestamp": datetime.now().isoformat()
                })

            elif message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

            elif message_type == "get_status":
                status = self.orchestrator.get_orchestrator_status()
                await websocket.send_json({
                    "type": "status_update",
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                })

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await websocket.send_json({
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    async def start_service(self):
        """Start the AI Integration Service"""
        if self._running:
            logger.warning("AI Integration Service is already running")
            return

        self._running = True
        logger.info(f"Starting AI Integration Service on {self.host}:{self.port}")

        # Start background tasks
        self._background_tasks = [
            asyncio.create_task(self._service_health_check_loop()),
            asyncio.create_task(self._event_processing_loop()),
            asyncio.create_task(self._broadcast_system_status_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]

        # Setup orchestrator event handlers
        self._setup_orchestrator_event_handlers()

        # Start FastAPI server
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info")
        server = uvicorn.Server(config)

        # Run server in background task
        self._background_tasks.append(asyncio.create_task(server.serve()))

        logger.info("AI Integration Service started successfully")

    async def stop_service(self):
        """Stop the AI Integration Service"""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping AI Integration Service")

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()

        logger.info("AI Integration Service stopped successfully")

    def _setup_orchestrator_event_handlers(self):
        """Setup event handlers for orchestrator events"""
        self.orchestrator.add_event_handler("operation_completed", self._on_operation_completed)
        self.orchestrator.add_event_handler("operation_approved", self._on_operation_approved)
        self.orchestrator.add_event_handler("system_status_update", self._on_system_status_update)

    async def _on_operation_completed(self, event_data: Dict[str, Any]):
        """Handle operation completed event"""
        await self._broadcast_event(EventType.OPERATION_COMPLETED, event_data)

    async def _on_operation_approved(self, event_data: Dict[str, Any]):
        """Handle operation approved event"""
        await self._broadcast_event(EventType.OPERATION_APPROVED, event_data)

    async def _on_system_status_update(self, event_data: Dict[str, Any]):
        """Handle system status update event"""
        await self._broadcast_event(EventType.SYSTEM_STATUS_UPDATE, event_data)

    async def _broadcast_event(self, event_type: EventType, data: Dict[str, Any]):
        """Broadcast event to WebSocket clients"""
        try:
            event = ServiceEvent(
                event_id=f"event_{int(time.time() * 1000)}",
                event_type=event_type,
                source_service="ai_integration_service",
                data=data
            )

            self.service_events.append(event)
            self.service_stats["events_processed"] += 1

            # Broadcast to WebSocket clients
            message = {
                "type": "event",
                "event_type": event_type.value,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            for websocket in self.websocket_connections[:]:  # Copy list to avoid modification during iteration
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to WebSocket: {e}")
                    # Remove broken connection
                    if websocket in self.websocket_connections:
                        self.websocket_connections.remove(websocket)

            # Store event
            self._store_event(event)

        except Exception as e:
            logger.error(f"Error broadcasting event: {e}")

    async def _service_health_check_loop(self):
        """Periodic service health check loop"""
        while self._running:
            try:
                for service_id, service in list(self.services.items()):
                    if service.health_check_url:
                        try:
                            # Perform health check
                            import aiohttp
                            async with aiohttp.ClientSession() as session:
                                async with session.get(service.health_check_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                                    if response.status == 200:
                                        service.status = "active"
                                        service.last_heartbeat = datetime.now()
                                    else:
                                        service.status = "unhealthy"

                        except Exception as e:
                            logger.warning(f"Health check failed for service {service_id}: {e}")
                            service.status = "unhealthy"

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in service health check loop: {e}")
                await asyncio.sleep(30)

    async def _event_processing_loop(self):
        """Event processing loop"""
        while self._running:
            try:
                # Process recent events
                recent_events = self.service_events[-100:]  # Last 100 events

                for event in recent_events:
                    if event.event_type in self.event_handlers:
                        for handler in self.event_handlers[event.event_type]:
                            try:
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(event)
                                else:
                                    handler(event)
                            except Exception as e:
                                logger.error(f"Error in event handler: {e}")

                await asyncio.sleep(5)  # Process every 5 seconds

            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(10)

    async def _broadcast_system_status_loop(self):
        """Broadcast system status updates"""
        while self._running:
            try:
                status = self.orchestrator.get_orchestrator_status()

                await self._broadcast_event(EventType.SYSTEM_STATUS_UPDATE, {
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                })

                await asyncio.sleep(30)  # Broadcast every 30 seconds

            except Exception as e:
                logger.error(f"Error broadcasting system status: {e}")
                await asyncio.sleep(15)

    async def _cleanup_loop(self):
        """Cleanup loop for old data"""
        while self._running:
            try:
                # Clean up old events (keep last 1000)
                if len(self.service_events) > 1000:
                    self.service_events = self.service_events[-1000:]

                # Clean up old service registrations (remove inactive for >1 hour)
                cutoff_time = datetime.now() - timedelta(hours=1)
                inactive_services = [
                    service_id for service_id, service in self.services.items()
                    if service.last_heartbeat < cutoff_time and service.status == "inactive"
                ]

                for service_id in inactive_services:
                    del self.services[service_id]
                    logger.info(f"Removed inactive service: {service_id}")

                await asyncio.sleep(300)  # Cleanup every 5 minutes

            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)

    def _store_service(self, service: ServiceEndpoint):
        """Store service in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO services
                    (service_id, service_type, name, url, health_check_url, version, status, last_heartbeat, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    service.service_id,
                    service.service_type.value,
                    service.name,
                    service.url,
                    service.health_check_url,
                    service.version,
                    service.status,
                    service.last_heartbeat.isoformat(),
                    json.dumps(service.metadata)
                ))
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing service: {e}")

    def _remove_service(self, service_id: str):
        """Remove service from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM services WHERE service_id = ?", (service_id,))
                conn.commit()

        except Exception as e:
            logger.error(f"Error removing service: {e}")

    def _store_event(self, event: ServiceEvent):
        """Store event in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO service_events
                    (event_id, event_type, source_service, target_service, timestamp, data, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.event_type.value,
                    event.source_service,
                    event.target_service,
                    event.timestamp.isoformat(),
                    json.dumps(event.data),
                    event.priority
                ))
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing event: {e}")

    def _log_api_request(self, request_id: str, endpoint: str, method: str,
                        response_time: float, status_code: int):
        """Log API request"""
        try:
            self.service_stats["total_requests"] += 1
            if status_code < 400:
                self.service_stats["successful_requests"] += 1
            else:
                self.service_stats["failed_requests"] += 1

            # Update average response time
            total_time = self.service_stats["average_response_time"] * (self.service_stats["total_requests"] - 1)
            self.service_stats["average_response_time"] = (total_time + response_time) / self.service_stats["total_requests"]

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO api_requests
                    (request_id, endpoint, method, timestamp, response_time, status_code)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    request_id,
                    endpoint,
                    method,
                    datetime.now().isoformat(),
                    response_time,
                    status_code
                ))
                conn.commit()

        except Exception as e:
            logger.error(f"Error logging API request: {e}")

    def _get_uptime(self) -> str:
        """Get service uptime"""
        # This would need to be implemented with actual start time tracking
        return "N/A"

    def _calculate_uptime(self, since: datetime) -> str:
        """Calculate uptime duration"""
        delta = datetime.now() - since
        seconds = delta.total_seconds()

        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m"
        else:
            return f"{int(seconds // 3600)}h"

    def add_event_handler(self, event_type: EventType, handler: Callable):
        """Add event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: EventType, handler: Callable):
        """Remove event handler"""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass  # Handler not found

    async def emit_service_event(self, event_type: EventType, source_service: str,
                               data: Dict[str, Any], target_service: Optional[str] = None,
                               priority: int = 5):
        """Emit a service event"""
        try:
            event = ServiceEvent(
                event_id=f"service_event_{int(time.time() * 1000)}",
                event_type=event_type,
                source_service=source_service,
                target_service=target_service,
                data=data,
                priority=priority
            )

            self.service_events.append(event)
            await self._broadcast_event(event_type, data)

        except Exception as e:
            logger.error(f"Error emitting service event: {e}")

    def get_service_status(self) -> Dict[str, Any]:
        """Get service integration status"""
        return {
            "running": self._running,
            "host": self.host,
            "port": self.port,
            "registered_services": len(self.services),
            "active_services": len([s for s in self.services.values() if s.status == "active"]),
            "websocket_connections": len(self.websocket_connections),
            "events_processed": self.service_stats["events_processed"],
            "service_stats": self.service_stats
        }