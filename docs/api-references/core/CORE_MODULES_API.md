# DuckBot v4.2 Core API Reference

## Table of Contents
- [Core Module APIs](#core-module-apis)
- [Service APIs](#service-apis)
- [Integration APIs](#integration-apis)
- [Platform APIs](#platform-apis)
- [Agent APIs](#agent-apis)
- [WebUI APIs](#webui-apis)
- [REST API Endpoints](#rest-api-endpoints)
- [WebSocket API](#websocket-api)
- [GraphQL API](#graphql-api)

## Core Module APIs

### 1. AI Provider Manager

```python
from duckbot.core.ai_provider_manager import AIProviderManager

class AIProviderManager:
    """Unified AI provider management and routing"""

    def __init__(self):
        self.providers = {}
        self.router = None
        self.cache = None

    async def initialize(self):
        """Initialize AI provider manager"""
        pass

    async def route_request(self, prompt: str, task_type: str, **kwargs) -> str:
        """
        Route AI request to appropriate provider

        Args:
            prompt: User prompt/question
            task_type: Type of task (code, reasoning, creative, etc.)
            **kwargs: Additional parameters

        Returns:
            str: AI response
        """
        pass

    async def add_provider(self, name: str, provider: BaseAIProvider):
        """Add new AI provider"""
        pass

    async def get_provider_status(self, name: str) -> dict:
        """Get provider status and health"""
        pass
```

#### Usage Examples

```python
# Initialize AI provider manager
ai_manager = AIProviderManager()
await ai_manager.initialize()

# Route request
response = await ai_manager.route_request(
    prompt="Write a Python function to calculate fibonacci",
    task_type="code",
    model="qwen3-coder",
    temperature=0.2
)

# Add custom provider
from duckbot.core.ai_provider import BaseAIProvider

class CustomProvider(BaseAIProvider):
    async def generate_response(self, prompt, **kwargs):
        # Custom AI implementation
        return "Custom response"

await ai_manager.add_provider("custom", CustomProvider())
```

### 2. Service Manager

```python
from duckbot.core.service_manager import ServiceManager

class ServiceManager:
    """Unified service lifecycle management"""

    def __init__(self):
        self.services = {}
        self.health_checks = {}

    async def start_service(self, service_name: str, **kwargs) -> bool:
        """
        Start a service

        Args:
            service_name: Name of service to start
            **kwargs: Service-specific parameters

        Returns:
            bool: Success status
        """
        pass

    async def stop_service(self, service_name: str) -> bool:
        """Stop a service"""
        pass

    async def restart_service(self, service_name: str) -> bool:
        """Restart a service"""
        pass

    async def get_service_status(self, service_name: str) -> dict:
        """Get service status"""
        pass

    async def list_services(self) -> list:
        """List all registered services"""
        pass

    async def monitor_services(self):
        """Monitor all services"""
        pass
```

#### Usage Examples

```python
# Initialize service manager
service_manager = ServiceManager()

# Start WebUI service
await service_manager.start_service(
    "webui",
    host="127.0.0.1",
    port=8787,
    debug=False
)

# Start monitoring service
await service_manager.start_service("monitoring")

# Get service status
status = await service_manager.get_service_status("webui")
print(f"WebUI status: {status}")

# List all services
services = await service_manager.list_services()
print(f"Running services: {services}")
```

### 3. Dynamic Model Manager

```python
from duckbot.core.dynamic_model_manager import DynamicModelManager

class DynamicModelManager:
    """Dynamic AI model loading and unloading"""

    def __init__(self):
        self.loaded_models = {}
        self.model_queue = []
        self.resource_monitor = None

    async def load_model(self, model_name: str, **kwargs) -> bool:
        """
        Load AI model

        Args:
            model_name: Name of model to load
            **kwargs: Model-specific parameters

        Returns:
            bool: Success status
        """
        pass

    async def unload_model(self, model_name: str) -> bool:
        """Unload AI model"""
        pass

    async def get_loaded_models(self) -> dict:
        """Get currently loaded models"""
        pass

    async def optimize_memory_usage(self):
        """Optimize memory usage by unloading unused models"""
        pass

    async def get_model_recommendations(self, task_type: str, system_resources: dict) -> list:
        """Get model recommendations based on task and resources"""
        pass
```

#### Usage Examples

```python
# Initialize model manager
model_manager = DynamicModelManager()

# Load a model
await model_manager.load_model(
    "qwen3-30b",
    path="/path/to/model",
    ram_required=16,
    vram_required=8
)

# Get loaded models
models = await model_manager.get_loaded_models()
print(f"Loaded models: {models}")

# Get recommendations
recommendations = await model_manager.get_model_recommendations(
    task_type="code",
    system_resources={"ram_gb": 16, "vram_gb": 8}
)
```

### 4. Hardware Detector

```python
from duckbot.core.hardware_detector import HardwareDetector

class HardwareDetector:
    """System hardware detection and monitoring"""

    def __init__(self):
        self.system_info = {}
        self.gpu_info = {}
        self.monitoring = False

    async def detect_hardware(self) -> dict:
        """Detect system hardware"""
        pass

    async def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        pass

    async def get_memory_usage(self) -> dict:
        """Get memory usage information"""
        pass

    async def get_gpu_usage(self) -> dict:
        """Get GPU usage information"""
        pass

    async def get_system_temperature(self) -> dict:
        """Get system temperature information"""
        pass

    async def start_monitoring(self, interval: int = 5):
        """Start hardware monitoring"""
        pass

    async def stop_monitoring(self):
        """Stop hardware monitoring"""
        pass
```

#### Usage Examples

```python
# Initialize hardware detector
hardware = HardwareDetector()

# Detect hardware
system_info = await hardware.detect_hardware()
print(f"System info: {system_info}")

# Get current usage
cpu_usage = await hardware.get_cpu_usage()
memory_usage = await hardware.get_memory_usage()
gpu_usage = await hardware.get_gpu_usage()

print(f"CPU: {cpu_usage}%, Memory: {memory_usage['used']}/{memory_usage['total']}GB")

# Start monitoring
await hardware.start_monitoring(interval=5)
```

### 5. Cost Management

```python
from duckbot.core.cost_management import CostManager

class CostManager:
    """AI usage cost tracking and management"""

    def __init__(self):
        self.usage_data = {}
        self.cost_cache = {}
        self.budget_limits = {}

    async def track_usage(self, provider: str, model: str, tokens: int, cost: float):
        """Track AI usage and cost"""
        pass

    async def get_usage_stats(self, timeframe: str = "day") -> dict:
        """Get usage statistics"""
        pass

    async def get_cost_breakdown(self) -> dict:
        """Get cost breakdown by provider and model"""
        pass

    async def check_budget_limits(self) -> dict:
        """Check budget limits and alerts"""
        pass

    async def set_budget_limit(self, category: str, limit: float):
        """Set budget limit for category"""
        pass

    async def export_usage_data(self, format: str = "csv") -> str:
        """Export usage data"""
        pass
```

#### Usage Examples

```python
# Initialize cost manager
cost_manager = CostManager()

# Track usage
await cost_manager.track_usage(
    provider="openrouter",
    model="qwen3-coder",
    tokens=1000,
    cost=0.002
)

# Get usage stats
stats = await cost_manager.get_usage_stats(timeframe="week")
print(f"Weekly usage: {stats}")

# Check budget
budget_status = await cost_manager.check_budget_limits()
if budget_status['over_budget']:
    print("Warning: Over budget!")

# Export data
csv_data = await cost_manager.export_usage_data(format="csv")
```

### 6. Rate Limiting

```python
from duckbot.core.rate_limit import RateLimiter

class RateLimiter:
    """API rate limiting and throttling"""

    def __init__(self):
        self.limits = {}
        self.counters = {}

    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """
        Check if request is within rate limit

        Args:
            key: Rate limit key (user_id, ip, etc.)
            limit: Number of requests allowed
            window: Time window in seconds

        Returns:
            bool: True if within limit, False otherwise
        """
        pass

    async def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for key"""
        pass

    async def reset_counter(self, key: str):
        """Reset rate limit counter for key"""
        pass

    async def set_limit(self, key: str, limit: int, window: int):
        """Set rate limit for key"""
        pass
```

#### Usage Examples

```python
# Initialize rate limiter
rate_limiter = RateLimiter()

# Check rate limit
user_id = "user123"
if await rate_limiter.check_rate_limit(user_id, limit=100, window=3600):
    # Process request
    print("Request allowed")
else:
    print("Rate limit exceeded")

# Get remaining requests
remaining = await rate_limiter.get_remaining_requests(user_id)
print(f"Remaining requests: {remaining}")

# Set custom limit
await rate_limiter.set_limit("api_endpoint", limit=10, window=60)
```

### 7. Logging System

```python
from duckbot.core.logging_setup import DuckBotLogger

class DuckBotLogger:
    """Unified logging system for DuckBot"""

    def __init__(self, name: str):
        self.name = name
        self.logger = None

    async def initialize(self):
        """Initialize logger"""
        pass

    async def log_info(self, message: str, **kwargs):
        """Log info message"""
        pass

    async def log_warning(self, message: str, **kwargs):
        """Log warning message"""
        pass

    async def log_error(self, message: str, **kwargs):
        """Log error message"""
        pass

    async def log_debug(self, message: str, **kwargs):
        """Log debug message"""
        pass

    async def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        pass
```

#### Usage Examples

```python
# Initialize logger
logger = DuckBotLogger("my_module")
await logger.initialize()

# Log messages
await logger.log_info("Starting operation", user_id="user123")
await logger.log_warning("High memory usage", memory_percent=85)
await logger.log_error("Failed to connect", error_code=500)

# Log performance
import time
start_time = time.time()
# ... perform operation ...
duration = time.time() - start_time
await logger.log_performance("data_processing", duration)
```

### 8. Context Manager

```python
from duckbot.core.context_manager import ContextManager

class ContextManager:
    """Conversation context and memory management"""

    def __init__(self):
        self.contexts = {}
        self.memory_store = None

    async def create_context(self, context_id: str, initial_data: dict = None) -> str:
        """Create new conversation context"""
        pass

    async def update_context(self, context_id: str, data: dict):
        """Update conversation context"""
        pass

    async def get_context(self, context_id: str) -> dict:
        """Get conversation context"""
        pass

    async def add_message(self, context_id: str, role: str, content: str):
        """Add message to context"""
        pass

    async def get_context_history(self, context_id: str, limit: int = 50) -> list:
        """Get context message history"""
        pass

    async def clear_context(self, context_id: str):
        """Clear conversation context"""
        pass
```

#### Usage Examples

```python
# Initialize context manager
context_manager = ContextManager()

# Create context
context_id = await context_manager.create_context(
    initial_data={"user_id": "user123", "session_id": "session456"}
)

# Update context
await context_manager.update_context(context_id, {"current_task": "coding"})

# Add messages
await context_manager.add_message(context_id, "user", "Hello, how are you?")
await context_manager.add_message(context_id, "assistant", "I'm doing well, thank you!")

# Get context
context = await context_manager.get_context(context_id)
print(f"Context: {context}")

# Get history
history = await context_manager.get_context_history(context_id, limit=10)
print(f"History: {history}")
```

### 9. Utilities

```python
from duckbot.core.utilities import DuckBotUtilities

class DuckBotUtilities:
    """Utility functions for DuckBot"""

    @staticmethod
    async def validate_config(config: dict) -> bool:
        """Validate configuration dictionary"""
        pass

    @staticmethod
    async def sanitize_input(input_text: str) -> str:
        """Sanitize user input"""
        pass

    @staticmethod
    async def format_duration(seconds: int) -> str:
        """Format duration in human readable format"""
        pass

    @staticmethod
    async def calculate_checksum(file_path: str) -> str:
        """Calculate file checksum"""
        pass

    @staticmethod
    async def compress_data(data: dict) -> bytes:
        """Compress data"""
        pass

    @staticmethod
    async def decompress_data(compressed_data: bytes) -> dict:
        """Decompress data"""
        pass

    @staticmethod
    async def retry_operation(operation, max_retries: int = 3, delay: float = 1.0):
        """Retry operation with exponential backoff"""
        pass
```

#### Usage Examples

```python
# Use utilities
from duckbot.core.utilities import DuckBotUtilities

# Validate config
config = {"key": "value"}
is_valid = await DuckBotUtilities.validate_config(config)

# Sanitize input
clean_input = await DuckBotUtilities.sanitize_input("user input with <script>alert('xss')</script>")

# Format duration
duration_str = await DuckBotUtilities.format_duration(3661)  # "1h 1m 1s"

# Calculate checksum
checksum = await DuckBotUtilities.calculate_checksum("file.txt")

# Retry operation
async def my_operation():
    # Operation that might fail
    return "success"

result = await DuckBotUtilities.retry_operation(my_operation, max_retries=3)
```

## Service APIs

### 1. WebUI Service

```python
from duckbot.services.webui_service import WebUIService

class WebUIService:
    """WebUI service management"""

    def __init__(self):
        self.app = None
        self.host = "127.0.0.1"
        self.port = 8787
        self.token = None

    async def start(self, host: str = "127.0.0.1", port: int = 8787, **kwargs):
        """Start WebUI service"""
        pass

    async def stop(self):
        """Stop WebUI service"""
        pass

    async def restart(self):
        """Restart WebUI service"""
        pass

    async def get_status(self) -> dict:
        """Get WebUI service status"""
        pass

    async def generate_token(self) -> str:
        """Generate new access token"""
        pass

    async def validate_token(self, token: str) -> bool:
        """Validate access token"""
        pass
```

#### Usage Examples

```python
# Initialize WebUI service
webui = WebUIService()

# Start service
await webui.start(host="127.0.0.1", port=8787)

# Get status
status = await webui.get_status()
print(f"WebUI status: {status}")

# Generate token
token = await webui.generate_token()
print(f"Access token: {token}")

# Validate token
is_valid = await webui.validate_token(token)
print(f"Token valid: {is_valid}")
```

### 2. Monitoring Service

```python
from duckbot.services.monitoring_service import MonitoringService

class MonitoringService:
    """System monitoring service"""

    def __init__(self):
        self.metrics = {}
        self.alerts = []
        self.thresholds = {}

    async def start(self, host: str = "127.0.0.1", port: int = 8789):
        """Start monitoring service"""
        pass

    async def collect_metrics(self):
        """Collect system metrics"""
        pass

    async def check_thresholds(self):
        """Check metric thresholds"""
        pass

    async def send_alert(self, alert_type: str, message: str, severity: str):
        """Send alert"""
        pass

    async def get_metrics(self) -> dict:
        """Get current metrics"""
        pass

    async def get_alerts(self) -> list:
        """Get active alerts"""
        pass

    async def set_threshold(self, metric: str, warning: float, critical: float):
        """Set metric threshold"""
        pass
```

#### Usage Examples

```python
# Initialize monitoring service
monitoring = MonitoringService()

# Start service
await monitoring.start(host="127.0.0.1", port=8789)

# Set thresholds
await monitoring.set_threshold("cpu_usage", 80.0, 95.0)
await monitoring.set_threshold("memory_usage", 85.0, 95.0)

# Get metrics
metrics = await monitoring.get_metrics()
print(f"Current metrics: {metrics}")

# Get alerts
alerts = await monitoring.get_alerts()
print(f"Active alerts: {alerts}")
```

### 3. API Service

```python
from duckbot.services.api_service import APIService

class APIService:
    """REST API service"""

    def __init__(self):
        self.app = None
        self.host = "127.0.0.1"
        self.port = 8790
        self.routes = {}

    async def start(self, host: str = "127.0.0.1", port: int = 8790):
        """Start API service"""
        pass

    async def stop(self):
        """Stop API service"""
        pass

    async def register_route(self, method: str, path: str, handler):
        """Register API route"""
        pass

    async def register_middleware(self, middleware):
        """Register middleware"""
        pass

    async def get_status(self) -> dict:
        """Get API service status"""
        pass
```

#### Usage Examples

```python
# Initialize API service
api_service = APIService()

# Start service
await api_service.start(host="127.0.0.1", port=8790)

# Register route
async def hello_world(request):
    return {"message": "Hello, World!"}

await api_service.register_route("GET", "/hello", hello_world)

# Get status
status = await api_service.get_status()
print(f"API status: {status}")
```

## Integration APIs

### 1. Memento Integration

```python
from duckbot.integrations.memento_integration import MementoIntegration

class MementoIntegration:
    """Memory and learning system integration"""

    def __init__(self):
        self.memory_store = {}
        self.learning_engine = None

    async def initialize(self):
        """Initialize Memento system"""
        pass

    async def store_memory(self, key: str, value: dict, metadata: dict = None):
        """Store memory entry"""
        pass

    async def retrieve_memory(self, key: str) -> dict:
        """Retrieve memory entry"""
        pass

    async def search_memory(self, query: str, limit: int = 10) -> list:
        """Search memory entries"""
        pass

    async def learn_from_interaction(self, interaction: dict):
        """Learn from user interaction"""
        pass

    async def get_learning_progress(self) -> dict:
        """Get learning progress"""
        pass

    async def optimize_memory_usage(self):
        """Optimize memory usage"""
        pass
```

#### Usage Examples

```python
# Initialize Memento
memento = MementoIntegration()
await memento.initialize()

# Store memory
await memento.store_memory(
    key="user_preferences",
    value={"theme": "dark", "language": "en"},
    metadata={"user_id": "user123"}
)

# Retrieve memory
preferences = await memento.retrieve_memory("user_preferences")
print(f"User preferences: {preferences}")

# Search memory
results = await memento.search_memory("preferences", limit=5)
print(f"Search results: {results}")

# Learn from interaction
interaction = {
    "user_input": "How do I create a Python function?",
    "ai_response": "Here's how to create a Python function...",
    "satisfaction_score": 0.9
}
await memento.learn_from_interaction(interaction)
```

### 2. Archon Integration

```python
from duckbot.integrations.archon_integration import ArchonIntegration

class ArchonIntegration:
    """Multi-agent framework integration"""

    def __init__(self):
        self.agents = {}
        self.coordinator = None

    async def initialize(self):
        """Initialize Archon system"""
        pass

    async def deploy_agent(self, agent_type: str, config: dict) -> str:
        """Deploy new agent"""
        pass

    async def coordinate_agents(self, agents: list, task: str) -> dict:
        """Coordinate multiple agents"""
        pass

    async def get_agent_status(self, agent_id: str) -> dict:
        """Get agent status"""
        pass

    async def list_agents(self) -> list:
        """List all agents"""
        pass

    async def stop_agent(self, agent_id: str) -> bool:
        """Stop agent"""
        pass
```

#### Usage Examples

```python
# Initialize Archon
archon = ArchonIntegration()
await archon.initialize()

# Deploy agent
agent_id = await archon.deploy_agent(
    agent_type="code_agent",
    config={"model": "qwen3-coder", "max_tasks": 5}
)

# Coordinate agents
result = await archon.coordinate_agents(
    agents=[agent_id, "research_agent"],
    task="Analyze and optimize this Python code"
)

# Get agent status
status = await archon.get_agent_status(agent_id)
print(f"Agent status: {status}")

# List agents
agents = await archon.list_agents()
print(f"Available agents: {agents}")
```

### 3. ByteBot Integration

```python
from duckbot.integrations.bytebot_integration import ByteBotIntegration

class ByteBotIntegration:
    """Desktop automation integration"""

    def __init__(self):
        self.automation_engine = None
        self.ui_controller = None

    async def initialize(self):
        """Initialize ByteBot system"""
        pass

    async def execute_task(self, task_description: str) -> dict:
        """Execute automation task"""
        pass

    async def start_interactive_mode(self):
        """Start interactive mode"""
        pass

    async def take_screenshot(self) -> bytes:
        """Take screenshot"""
        pass

    async def click_element(self, selector: str):
        """Click UI element"""
        pass

    async def type_text(self, text: str):
        """Type text"""
        pass

    async def open_application(self, app_path: str):
        """Open application"""
        pass
```

#### Usage Examples

```python
# Initialize ByteBot
bytebot = ByteBotIntegration()
await bytebot.initialize()

# Execute task
result = await bytebot.execute_task("Open Notepad and type 'Hello World'")
print(f"Task result: {result}")

# Take screenshot
screenshot = await bytebot.take_screenshot()

# Interactive mode
await bytebot.start_interactive_mode()

# Direct control
await bytebot.open_application("notepad.exe")
await bytebot.type_text("Hello from DuckBot!")
```

### 4. Discord Bot Integration

```python
from duckbot.integrations.discord_integration import DiscordIntegration

class DiscordIntegration:
    """Discord bot integration"""

    def __init__(self, token: str):
        self.token = token
        self.bot = None
        self.commands = {}

    async def initialize(self):
        """Initialize Discord bot"""
        pass

    async def register_command(self, name: str, handler, description: str = ""):
        """Register bot command"""
        pass

    async def send_message(self, channel_id: str, message: str):
        """Send message to channel"""
        pass

    async def send_embed(self, channel_id: str, title: str, description: str, **kwargs):
        """Send embed message"""
        pass

    async def get_bot_status(self) -> dict:
        """Get bot status"""
        pass
```

#### Usage Examples

```python
# Initialize Discord bot
discord = DiscordIntegration("your_discord_token")
await discord.initialize()

# Register command
async def hello_command(ctx, *, name: str = None):
    name = name or ctx.author.name
    await ctx.send(f"Hello, {name}!")

await discord.register_command("hello", hello_command, "Say hello!")

# Send message
await discord.send_message("channel_id", "Hello from DuckBot!")

# Get bot status
status = await discord.get_bot_status()
print(f"Bot status: {status}")
```

## Platform APIs

### 1. WSL Integration

```python
from duckbot.platforms.wsl_integration import WSLIntegration

class WSLIntegration:
    """Windows Subsystem for Linux integration"""

    def __init__(self):
        self.wsl_available = False
        self.distribution = None

    async def initialize(self):
        """Initialize WSL integration"""
        pass

    async def execute_command(self, command: str, distribution: str = None) -> str:
        """Execute Linux command"""
        pass

    async def copy_file(self, source: str, destination: str):
        """Copy file between Windows and Linux"""
        pass

    async def start_service(self, service_name: str, distribution: str = None):
        """Start Linux service"""
        pass

    async def get_wsl_status(self) -> dict:
        """Get WSL status"""
        pass
```

#### Usage Examples

```python
# Initialize WSL
wsl = WSLIntegration()
await wsl.initialize()

# Execute command
result = await wsl.execute_command("ls -la /home")
print(f"Command result: {result}")

# Start service
await wsl.start_service("nginx")

# Get status
status = await wsl.get_wsl_status()
print(f"WSL status: {status}")
```

### 2. Local Privacy Mode

```python
from duckbot.platforms.local_privacy_mode import LocalPrivacyMode

class LocalPrivacyMode:
    """Local-only privacy mode"""

    def __init__(self):
        self.enabled = False
        self.local_models = {}

    async def enable(self):
        """Enable local-only mode"""
        pass

    async def disable(self):
        """Disable local-only mode"""
        pass

    async def is_enabled(self) -> bool:
        """Check if local-only mode is enabled"""
        pass

    async def get_local_models(self) -> list:
        """Get available local models"""
        pass

    async def process_request(self, prompt: str) -> str:
        """Process request using local models only"""
        pass
```

#### Usage Examples

```python
# Initialize local privacy mode
privacy_mode = LocalPrivacyMode()

# Enable mode
await privacy_mode.enable()

# Check status
is_local = await privacy_mode.is_enabled()
print(f"Local-only mode: {is_local}")

# Get local models
models = await privacy_mode.get_local_models()
print(f"Available models: {models}")

# Process request
response = await privacy_mode.process_request("Hello, how are you?")
print(f"Response: {response}")
```

## Agent APIs

### 1. Intelligent Agents

```python
from duckbot.agents.intelligent_agents import IntelligentAgents

class IntelligentAgents:
    """Multi-agent coordination system"""

    def __init__(self):
        self.agents = {}
        self.task_queue = []
        self.coordinator = None

    async def initialize(self):
        """Initialize agent system"""
        pass

    async def create_agent(self, agent_type: str, config: dict) -> str:
        """Create new agent"""
        pass

    async def assign_task(self, agent_id: str, task: dict) -> dict:
        """Assign task to agent"""
        pass

    async def coordinate_agents(self, task: str, agent_ids: list = None) -> dict:
        """Coordinate multiple agents"""
        pass

    async def get_agent_status(self, agent_id: str) -> dict:
        """Get agent status"""
        pass

    async def list_agents(self) -> list:
        """List all agents"""
        pass
```

#### Usage Examples

```python
# Initialize agents
agents = IntelligentAgents()
await agents.initialize()

# Create agent
agent_id = await agents.create_agent(
    agent_type="research_agent",
    config={"model": "qwen3-coder", "specialty": "research"}
)

# Assign task
task_result = await agents.assign_task(
    agent_id,
    {"type": "research", "topic": "AI trends", "deadline": "2024-01-01"}
)

# Coordinate agents
coord_result = await agents.coordinate_agents(
    task="Create comprehensive AI report",
    agent_ids=["research_agent", "writing_agent"]
)
```

### 2. Mining Agent

```python
from duckbot.agents.mining_agent import MiningAgent

class MiningAgent:
    """Cryptocurrency mining agent"""

    def __init__(self):
        self.mining_status = {}
        self.wallet_address = None
        self.pool_url = None

    async def initialize(self, wallet_address: str, pool_url: str):
        """Initialize mining agent"""
        pass

    async def start_mining(self, algorithm: str, pool_url: str = None) -> bool:
        """Start mining"""
        pass

    async def stop_mining(self) -> bool:
        """Stop mining"""
        pass

    async def get_mining_stats(self) -> dict:
        """Get mining statistics"""
        pass

    async def switch_algorithm(self, algorithm: str):
        """Switch mining algorithm"""
        pass
```

#### Usage Examples

```python
# Initialize mining agent
mining = MiningAgent()
await mining.initialize(
    wallet_address="your_wallet_address",
    pool_url="stratum+tcp://pool.example.com:3333"
)

# Start mining
await mining.start_mining(algorithm="ethash")

# Get stats
stats = await mining.get_mining_stats()
print(f"Mining stats: {stats}")

# Stop mining
await mining.stop_mining()
```

## WebUI APIs

### 1. Enhanced WebUI

```python
from duckbot.enhanced_webui import EnhancedWebUI

class EnhancedWebUI:
    """Enhanced WebUI application"""

    def __init__(self):
        self.app = None
        self.routes = {}
        self.middleware = []

    async def create_app(self) -> FastAPI:
        """Create FastAPI application"""
        pass

    async def register_route(self, path: str, handler, methods: list = ["GET"]):
        """Register route"""
        pass

    async def register_middleware(self, middleware):
        """Register middleware"""
        pass

    async def register_websocket_route(self, path: str, handler):
        """Register WebSocket route"""
        pass

    async def start(self, host: str = "127.0.0.1", port: int = 8787):
        """Start WebUI"""
        pass

    async def stop(self):
        """Stop WebUI"""
        pass
```

#### Usage Examples

```python
# Create WebUI application
webui = EnhancedWebUI()
app = await webui.create_app()

# Register route
async def dashboard(request):
    return {"message": "Welcome to DuckBot Dashboard"}

await webui.register_route("/dashboard", dashboard)

# Start WebUI
await webui.start(host="127.0.0.1", port=8787)
```

## REST API Endpoints

### 1. Authentication Endpoints

```python
# Generate access token
POST /api/v1/auth/token
Response: {"token": "access_token", "expires_in": 3600}

# Validate token
POST /api/v1/auth/validate
Request: {"token": "access_token"}
Response: {"valid": true, "user_id": "user123"}
```

### 2. AI Endpoints

```python
# Chat with AI
POST /api/v1/chat
Request: {
    "message": "Hello, how are you?",
    "model": "qwen3-coder",
    "stream": false
}
Response: {
    "response": "I'm doing well, thank you!",
    "model": "qwen3-coder",
    "tokens_used": 15
}

# Generate image
POST /api/v1/generate/image
Request: {
    "prompt": "A beautiful sunset",
    "width": 512,
    "height": 512
}
Response: {
    "image_url": "http://localhost:8787/images/generated_image.png",
    "prompt": "A beautiful sunset"
}
```

### 3. System Endpoints

```python
# Get system status
GET /api/v1/system/status
Response: {
    "status": "healthy",
    "uptime": 3600,
    "services": {
        "webui": {"status": "running", "port": 8787},
        "monitoring": {"status": "running", "port": 8789}
    }
}

# Get system metrics
GET /api/v1/system/metrics
Response: {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "gpu_usage": 12.3,
    "disk_usage": 45.6
}
```

### 4. Model Endpoints

```python
# List models
GET /api/v1/models
Response: {
    "models": [
        {"name": "qwen3-coder", "type": "local", "status": "loaded"},
        {"name": "gpt-4", "type": "openai", "status": "available"}
    ]
}

# Load model
POST /api/v1/models/load
Request: {"name": "qwen3-coder"}
Response: {"success": true, "message": "Model loaded successfully"}

# Unload model
POST /api/v1/models/unload
Request: {"name": "qwen3-coder"}
Response: {"success": true, "message": "Model unloaded successfully"}
```

### 5. Agent Endpoints

```python
# List agents
GET /api/v1/agents
Response: {
    "agents": [
        {"id": "agent1", "type": "research", "status": "active"},
        {"id": "agent2", "type": "code", "status": "idle"}
    ]
}

# Create agent
POST /api/v1/agents
Request: {
    "type": "research",
    "config": {"model": "qwen3-coder", "max_tasks": 5}
}
Response: {"agent_id": "agent3", "status": "created"}

# Assign task to agent
POST /api/v1/agents/{agent_id}/tasks
Request: {
    "task": "Research AI trends",
    "priority": "high"
}
Response: {"task_id": "task1", "status": "assigned"}
```

### 6. Service Endpoints

```python
# List services
GET /api/v1/services
Response: {
    "services": [
        {"name": "webui", "status": "running", "port": 8787},
        {"name": "monitoring", "status": "running", "port": 8789}
    ]
}

# Start service
POST /api/v1/services/{service_name}/start
Response: {"success": true, "message": "Service started"}

# Stop service
POST /api/v1/services/{service_name}/stop
Response: {"success": true, "message": "Service stopped"}
```

## WebSocket API

### 1. Connection

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8787/ws');

// Connection established
ws.onopen = () => {
    console.log('Connected to DuckBot WebSocket');

    // Send authentication
    ws.send(JSON.stringify({
        type: 'auth',
        token: 'your_access_token'
    }));
};

// Receive messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// Handle errors
ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};
```

### 2. Message Types

```python
# Authentication
{
    "type": "auth",
    "token": "access_token"
}

# Chat message
{
    "type": "chat",
    "message": "Hello, how are you?",
    "model": "qwen3-coder"
}

# System status
{
    "type": "status",
    "data": {
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "services": ["webui", "monitoring"]
    }
}

# Agent update
{
    "type": "agent_update",
    "agent_id": "agent1",
    "status": "active",
    "current_task": "research"
}
```

## GraphQL API

### 1. Schema

```graphql
type Query {
    # System queries
    systemStatus: SystemStatus!
    systemMetrics: SystemMetrics!

    # Model queries
    models: [Model!]!
    model(name: String!): Model

    # Agent queries
    agents: [Agent!]!
    agent(id: ID!): Agent

    # Chat queries
    conversations(userId: String!): [Conversation!]!
    conversation(id: ID!): Conversation
}

type Mutation {
    # Chat mutations
    sendMessage(message: String!, model: String): Message!

    # Model mutations
    loadModel(name: String!): Model!
    unloadModel(name: String!): Boolean!

    # Agent mutations
    createAgent(type: String!, config: AgentConfig!): Agent!
    assignTask(agentId: ID!, task: TaskInput!): Task!
}

type Subscription {
    # System subscriptions
    systemStatusUpdated: SystemStatus!
    systemMetricsUpdated: SystemMetrics!

    # Agent subscriptions
    agentStatusUpdated(agentId: ID!): Agent!
    taskProgressUpdated(taskId: ID!): Task!

    # Chat subscriptions
    newMessage(conversationId: ID!): Message!
}
```

### 2. Query Examples

```graphql
# Get system status
query {
    systemStatus {
        status
        uptime
        services {
            name
            status
            port
        }
    }
}

# Get models
query {
    models {
        name
        type
        status
        size
    }
}

# Get agents
query {
    agents {
        id
        type
        status
        currentTask
    }
}
```

### 3. Mutation Examples

```graphql
# Send message
mutation {
    sendMessage(message: "Hello, how are you?", model: "qwen3-coder") {
        id
        content
        role
        timestamp
    }
}

# Load model
mutation {
    loadModel(name: "qwen3-coder") {
        name
        status
        loadedAt
    }
}

# Create agent
mutation {
    createAgent(type: "research", config: {model: "qwen3-coder", maxTasks: 5}) {
        id
        type
        status
        createdAt
    }
}
```

### 4. Subscription Examples

```graphql
# Subscribe to system status updates
subscription {
    systemStatusUpdated {
        status
        uptime
        services {
            name
            status
        }
    }
}

# Subscribe to agent status updates
subscription {
    agentStatusUpdated(agentId: "agent1") {
        id
        status
        currentTask
        lastActivity
    }
}

# Subscribe to new messages
subscription {
    newMessage(conversationId: "conv1") {
        id
        content
        role
        timestamp
    }
}
```

This comprehensive API reference covers all core modules, services, integrations, and platform APIs available in DuckBot v4.2. Each API includes detailed documentation, usage examples, and integration patterns for developers.