"""
Enhanced Communication System with AP2-inspired Features
Advanced agent communication with group messaging, attachments, and shared state

Features:
- Group-based agent communication
- Secure file and data attachments
- Shared conversation state management
- Real-time messaging protocols
- Message persistence and history
- Communication analytics
- Cross-agent knowledge sharing
- Event-driven architecture

Author: Enhanced Communication System Module
Version: 1.0.0
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, Set, Callable, AsyncGenerator, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import hashlib
import mimetypes
import base64
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
import websockets
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of communication messages"""
    TEXT = "text"
    FILE_ATTACHMENT = "file_attachment"
    DATA_ATTACHMENT = "data_attachment"
    SYSTEM_NOTIFICATION = "system_notification"
    TASK_UPDATE = "task_update"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"
    COLLABORATION_REQUEST = "collaboration_request"
    KNOWLEDGE_SHARE = "knowledge_share"
    COORDINATION_SIGNAL = "coordination_signal"

class CommunicationScope(Enum):
    """Communication scope levels"""
    DIRECT = "direct"  # One-to-one
    GROUP = "group"    # One-to-many
    BROADCAST = "broadcast"  # All agents
    TOPIC = "topic"    # Topic-based

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class AttachmentType(Enum):
    """Types of attachments"""
    FILE = "file"
    DATA = "data"
    IMAGE = "image"
    DOCUMENT = "document"
    CODE = "code"
    CONFIGURATION = "configuration"
    MODEL = "model"
    RESULT = "result"

@dataclass
class MessageAttachment:
    """Message attachment with metadata"""
    id: str
    type: AttachmentType
    name: str
    size: int
    content: Union[str, bytes, Dict[str, Any]]
    mime_type: str
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Access control
    access_level: str = "restricted"  # "public", "restricted", "private"
    allowed_recipients: List[str] = field(default_factory=list)

    # Lifecycle
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    download_count: int = 0
    max_downloads: Optional[int] = None

    def is_accessible(self, recipient_id: str) -> bool:
        """Check if recipient can access attachment"""
        if self.access_level == "public":
            return True
        elif self.access_level == "restricted":
            return recipient_id in self.allowed_recipients or not self.allowed_recipients
        else:  # private
            return recipient_id in self.allowed_recipients

    def can_download(self) -> bool:
        """Check if attachment can be downloaded"""
        if self.max_downloads and self.download_count >= self.max_downloads:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True

    def record_download(self):
        """Record attachment download"""
        self.download_count += 1

@dataclass
class CommunicationMessage:
    """Enhanced communication message"""
    id: str
    type: MessageType
    scope: CommunicationScope
    priority: MessagePriority

    # Message content
    content: str
    attachments: List[MessageAttachment] = field(default_factory=list)

    # Sender and recipients
    sender_id: str
    sender_type: str  # "agent", "user", "system"
    recipient_ids: List[str] = field(default_factory=list)
    group_id: Optional[str] = None
    topic: Optional[str] = None

    # Context and metadata
    context_id: Optional[str] = None
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Message state
    status: str = "sent"  # "sent", "delivered", "read", "processed"
    read_by: Set[str] = field(default_factory=set)
    delivered_to: Set[str] = field(default_factory=set)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

    # Expiration and lifecycle
    expires_at: Optional[datetime] = None
    is_persistent: bool = True

    # Thread information
    thread_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    reply_to_message_id: Optional[str] = None

    def __post_init__(self):
        """Initialize message components"""
        # Generate thread ID if this is the first message in a thread
        if not self.thread_id and not self.parent_message_id:
            self.thread_id = str(uuid.uuid4())

        # Calculate content checksum
        self.metadata["content_checksum"] = hashlib.md5(self.content.encode()).hexdigest()

    def mark_delivered(self, recipient_id: str):
        """Mark message as delivered to recipient"""
        self.delivered_to.add(recipient_id)
        if not self.delivered_at:
            self.delivered_at = datetime.now()

    def mark_read(self, recipient_id: str):
        """Mark message as read by recipient"""
        self.read_by.add(recipient_id)
        if not self.read_at:
            self.read_at = datetime.now()

    def mark_processed(self):
        """Mark message as processed"""
        self.status = "processed"
        self.processed_at = datetime.now()

    def is_expired(self) -> bool:
        """Check if message has expired"""
        return self.expires_at and datetime.now() > self.expires_at

    def get_delivery_status(self) -> Dict[str, Any]:
        """Get detailed delivery status"""
        return {
            "total_recipients": len(self.recipient_ids),
            "delivered_count": len(self.delivered_to),
            "read_count": len(self.read_by),
            "delivery_rate": len(self.delivered_to) / max(1, len(self.recipient_ids)),
            "read_rate": len(self.read_by) / max(1, len(self.recipient_ids))
        }

@dataclass
class CommunicationGroup:
    """Agent communication group"""
    id: str
    name: str
    description: str
    created_by: str
    created_at: datetime = field(default_factory=datetime.now)

    # Group membership
    members: Set[str] = field(default_factory=set)
    admins: Set[str] = field(default_factory=set)
    moderators: Set[str] = field(default_factory=set)

    # Group settings
    is_public: bool = False
    is_moderated: bool = True
    allow_invites: bool = True
    message_history_limit: int = 1000
    max_members: Optional[int] = None

    # Group state
    is_active: bool = True
    last_activity: Optional[datetime] = None
    message_count: int = 0

    # Group metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_member(self, agent_id: str, role: str = "member"):
        """Add member to group"""
        if self.max_members and len(self.members) >= self.max_members:
            raise ValueError(f"Group {self.id} has reached maximum capacity")

        self.members.add(agent_id)
        if role == "admin":
            self.admins.add(agent_id)
        elif role == "moderator":
            self.moderators.add(agent_id)

    def remove_member(self, agent_id: str):
        """Remove member from group"""
        self.members.discard(agent_id)
        self.admins.discard(agent_id)
        self.moderators.discard(agent_id)

    def is_member(self, agent_id: str) -> bool:
        """Check if agent is group member"""
        return agent_id in self.members

    def is_admin(self, agent_id: str) -> bool:
        """Check if agent is group admin"""
        return agent_id in self.admins

    def is_moderator(self, agent_id: str) -> bool:
        """Check if agent is group moderator"""
        return agent_id in self.moderators or agent_id in self.admins

    def can_send_message(self, agent_id: str) -> bool:
        """Check if agent can send message to group"""
        if not self.is_member(agent_id):
            return False
        if self.is_moderated and not (self.is_admin(agent_id) or self.is_moderator(agent_id)):
            return False
        return True

@dataclass
class ConversationState:
    """Shared conversation state"""
    id: str
    participants: Set[str]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Shared data
    shared_variables: Dict[str, Any] = field(default_factory=dict)
    shared_context: Dict[str, Any] = field(default_factory=dict)
    shared_knowledge: Dict[str, Any] = field(default_factory=dict)

    # Conversation history
    message_history: List[str] = field(default_factory=list)  # message IDs
    max_history_size: int = 100

    # State synchronization
    version: int = 0
    last_sync: Optional[datetime] = None

    # Access control
    is_public: bool = False
    read_access: Set[str] = field(default_factory=set)
    write_access: Set[str] = field(default_factory=set)

    def update_state(self, updates: Dict[str, Any], agent_id: str):
        """Update conversation state"""
        if agent_id not in self.write_access and not self.is_public:
            raise PermissionError(f"Agent {agent_id} does not have write access")

        self.shared_variables.update(updates)
        self.version += 1
        self.updated_at = datetime.now()

    def get_state(self) -> Dict[str, Any]:
        """Get current conversation state"""
        return {
            "variables": self.shared_variables.copy(),
            "context": self.shared_context.copy(),
            "knowledge": self.shared_knowledge.copy(),
            "version": self.version,
            "updated_at": self.updated_at.isoformat()
        }

    def add_message(self, message_id: str):
        """Add message to conversation history"""
        self.message_history.append(message_id)
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size:]

class MessageRouter:
    """Advanced message routing and delivery"""

    def __init__(self):
        self.agent_endpoints: Dict[str, str] = {}  # agent_id -> endpoint
        self.group_memberships: Dict[str, Set[str]] = defaultdict(set)  # group_id -> agent_ids
        self.topic_subscribers: Dict[str, Set[str]] = defaultdict(set)  # topic -> agent_ids
        self.delivery_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "sent": 0,
            "delivered": 0,
            "failed": 0,
            "avg_delivery_time": 0.0
        })

    def register_agent(self, agent_id: str, endpoint: str):
        """Register agent endpoint"""
        self.agent_endpoints[agent_id] = endpoint
        logger.info(f"Registered agent {agent_id} at {endpoint}")

    def unregister_agent(self, agent_id: str):
        """Unregister agent endpoint"""
        if agent_id in self.agent_endpoints:
            del self.agent_endpoints[agent_id]
            logger.info(f"Unregistered agent {agent_id}")

    async def route_message(self, message: CommunicationMessage) -> List[str]:
        """Route message to appropriate recipients"""
        delivered_to = []

        try:
            if message.scope == CommunicationScope.DIRECT:
                # Direct message
                for recipient_id in message.recipient_ids:
                    if await self._deliver_to_agent(message, recipient_id):
                        delivered_to.append(recipient_id)

            elif message.scope == CommunicationScope.GROUP:
                # Group message
                if message.group_id:
                    group_members = self.group_memberships.get(message.group_id, set())
                    for member_id in group_members:
                        if member_id != message.sender_id:  # Don't send to sender
                            if await self._deliver_to_agent(message, member_id):
                                delivered_to.append(member_id)

            elif message.scope == CommunicationScope.BROADCAST:
                # Broadcast to all agents
                for agent_id in self.agent_endpoints:
                    if agent_id != message.sender_id:
                        if await self._deliver_to_agent(message, agent_id):
                            delivered_to.append(agent_id)

            elif message.scope == CommunicationScope.TOPIC:
                # Topic-based message
                if message.topic:
                    subscribers = self.topic_subscribers.get(message.topic, set())
                    for subscriber_id in subscribers:
                        if subscriber_id != message.sender_id:
                            if await self._deliver_to_agent(message, subscriber_id):
                                delivered_to.append(subscriber_id)

            # Update delivery stats
            self._update_delivery_stats(message, delivered_to)

            return delivered_to

        except Exception as e:
            logger.error(f"Error routing message {message.id}: {e}")
            return delivered_to

    async def _deliver_to_agent(self, message: CommunicationMessage, agent_id: str) -> bool:
        """Deliver message to specific agent"""
        endpoint = self.agent_endpoints.get(agent_id)
        if not endpoint:
            logger.warning(f"No endpoint found for agent {agent_id}")
            return False

        try:
            # In a real implementation, this would use actual communication protocols
            # For now, simulate delivery
            await asyncio.sleep(0.001)  # Simulate network delay

            # Mark message as delivered
            message.mark_delivered(agent_id)

            logger.debug(f"Delivered message {message.id} to agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to deliver message {message.id} to agent {agent_id}: {e}")
            return False

    def _update_delivery_stats(self, message: CommunicationMessage, delivered_to: List[str]):
        """Update delivery statistics"""
        sender_id = message.sender_id
        stats = self.delivery_stats[sender_id]

        stats["sent"] += 1
        stats["delivered"] += len(delivered_to)
        stats["failed"] += len(message.recipient_ids) - len(delivered_to)

        # Update average delivery time (simplified)
        if message.delivered_at and message.created_at:
            delivery_time = (message.delivered_at - message.created_at).total_seconds()
            total_delivered = stats["delivered"]
            stats["avg_delivery_time"] = (
                (stats["avg_delivery_time"] * (total_delivered - 1) + delivery_time) / total_delivered
            )

    def subscribe_to_topic(self, agent_id: str, topic: str):
        """Subscribe agent to topic"""
        self.topic_subscribers[topic].add(agent_id)
        logger.info(f"Agent {agent_id} subscribed to topic {topic}")

    def unsubscribe_from_topic(self, agent_id: str, topic: str):
        """Unsubscribe agent from topic"""
        self.topic_subscribers[topic].discard(agent_id)
        logger.info(f"Agent {agent_id} unsubscribed from topic {topic}")

    def join_group(self, agent_id: str, group_id: str):
        """Add agent to group"""
        self.group_memberships[group_id].add(agent_id)
        logger.info(f"Agent {agent_id} joined group {group_id}")

    def leave_group(self, agent_id: str, group_id: str):
        """Remove agent from group"""
        self.group_memberships[group_id].discard(agent_id)
        logger.info(f"Agent {agent_id} left group {group_id}")

class AttachmentManager:
    """Manage message attachments and file sharing"""

    def __init__(self, storage_path: str = "data/attachments"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.attachments: Dict[str, MessageAttachment] = {}
        self.content_cache: Dict[str, Union[str, bytes]] = {}

    async def create_attachment(self, content: Union[str, bytes, Dict[str, Any]],
                             attachment_type: AttachmentType, name: str,
                             mime_type: str = None, access_level: str = "restricted",
                             allowed_recipients: List[str] = None,
                             expires_in: timedelta = None) -> MessageAttachment:
        """Create new attachment"""
        attachment_id = str(uuid.uuid4())

        # Determine MIME type
        if not mime_type:
            if attachment_type == AttachmentType.FILE:
                mime_type, _ = mimetypes.guess_type(name)
            elif attachment_type == AttachmentType.DATA:
                mime_type = "application/json"
            else:
                mime_type = "application/octet-stream"

        # Calculate checksum and size
        if isinstance(content, str):
            content_bytes = content.encode()
        elif isinstance(content, dict):
            content_bytes = json.dumps(content).encode()
        else:
            content_bytes = content

        checksum = hashlib.sha256(content_bytes).hexdigest()
        size = len(content_bytes)

        # Create attachment
        attachment = MessageAttachment(
            id=attachment_id,
            type=attachment_type,
            name=name,
            size=size,
            content=content,
            mime_type=mime_type,
            checksum=checksum,
            access_level=access_level,
            allowed_recipients=allowed_recipients or [],
            expires_at=datetime.now() + expires_in if expires_in else None
        )

        # Store attachment
        self.attachments[attachment_id] = attachment
        self.content_cache[attachment_id] = content

        # Save to disk if it's a file
        if attachment_type == AttachmentType.FILE and isinstance(content, bytes):
            file_path = self.storage_path / attachment_id
            with open(file_path, 'wb') as f:
                f.write(content)

        logger.info(f"Created attachment {attachment_id}: {name} ({size} bytes)")
        return attachment

    async def get_attachment(self, attachment_id: str, requester_id: str) -> Optional[MessageAttachment]:
        """Get attachment if accessible"""
        attachment = self.attachments.get(attachment_id)
        if not attachment:
            return None

        if not attachment.is_accessible(requester_id):
            return None

        if not attachment.can_download():
            return None

        # Record download
        attachment.record_download()
        return attachment

    async def get_attachment_content(self, attachment_id: str, requester_id: str) -> Optional[Union[str, bytes]]:
        """Get attachment content"""
        attachment = await self.get_attachment(attachment_id, requester_id)
        if not attachment:
            return None

        # Return cached content if available
        if attachment_id in self.content_cache:
            return self.content_cache[attachment_id]

        # Load from disk if it's a file
        if attachment.type == AttachmentType.FILE:
            file_path = self.storage_path / attachment_id
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    content = f.read()
                    self.content_cache[attachment_id] = content
                    return content

        return attachment.content

    async def cleanup_expired_attachments(self):
        """Clean up expired attachments"""
        now = datetime.now()
        expired_attachments = [
            att_id for att_id, attachment in self.attachments.items()
            if attachment.expires_at and attachment.expires_at <= now
        ]

        for attachment_id in expired_attachments:
            attachment = self.attachments.pop(attachment_id, None)
            if attachment_id in self.content_cache:
                del self.content_cache[attachment_id]

            # Remove file if it exists
            file_path = self.storage_path / attachment_id
            if file_path.exists():
                file_path.unlink()

        if expired_attachments:
            logger.info(f"Cleaned up {len(expired_attachments)} expired attachments")

class EnhancedCommunicationManager:
    """Enhanced communication manager with AP2-inspired features"""

    def __init__(self):
        self.messages: Dict[str, CommunicationMessage] = {}
        self.groups: Dict[str, CommunicationGroup] = {}
        self.conversation_states: Dict[str, ConversationState] = {}

        # Core components
        self.message_router = MessageRouter()
        self.attachment_manager = AttachmentManager()
        self.websocket_server = None

        # Event handlers
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        self.group_event_handlers: List[Callable] = []

        # Analytics and metrics
        self.communication_stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "attachments_created": 0,
            "groups_created": 0,
            "active_conversations": 0,
            "avg_message_size": 0.0,
            "peak_messages_per_minute": 0
        }

        # Background services
        self.message_processor = MessageProcessor(self)
        self.state_synchronizer = StateSynchronizer(self)
        self.analytics_collector = AnalyticsCollector(self)

        # Configuration
        self.enable_persistence = True
        self.enable_real_time = True
        self.max_message_size = 10 * 1024 * 1024  # 10MB
        self.enable_attachment_compression = True

    async def initialize(self) -> bool:
        """Initialize communication manager"""
        try:
            # Start background services
            await self.message_processor.start()
            await self.state_synchronizer.start()
            await self.analytics_collector.start()

            # Start WebSocket server if real-time is enabled
            if self.enable_real_time:
                await self._start_websocket_server()

            # Create default groups
            await self._create_default_groups()

            logger.info("Enhanced Communication Manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize communication manager: {e}")
            return False

    async def send_message(self, message_type: MessageType, content: str, sender_id: str,
                          recipient_ids: List[str] = None, scope: CommunicationScope = CommunicationScope.DIRECT,
                          group_id: str = None, topic: str = None, **kwargs) -> str:
        """Send communication message"""
        message_id = str(uuid.uuid4())

        message = CommunicationMessage(
            id=message_id,
            type=message_type,
            scope=scope,
            priority=kwargs.get("priority", MessagePriority.NORMAL),
            content=content,
            sender_id=sender_id,
            sender_type=kwargs.get("sender_type", "agent"),
            recipient_ids=recipient_ids or [],
            group_id=group_id,
            topic=topic,
            context_id=kwargs.get("context_id"),
            task_id=kwargs.get("task_id"),
            metadata=kwargs.get("metadata", {}),
            expires_at=kwargs.get("expires_at"),
            thread_id=kwargs.get("thread_id"),
            parent_message_id=kwargs.get("parent_message_id"),
            reply_to_message_id=kwargs.get("reply_to_message_id")
        )

        # Validate message
        if not await self._validate_message(message):
            raise ValueError("Invalid message")

        # Store message
        self.messages[message_id] = message

        # Route message
        delivered_to = await self.message_router.route_message(message)

        # Update stats
        self.communication_stats["messages_sent"] += 1
        self.communication_stats["messages_delivered"] += len(delivered_to)

        # Trigger message handlers
        await self._trigger_message_handlers(message)

        logger.info(f"Sent message {message_id} from {sender_id} to {len(delivered_to)} recipients")
        return message_id

    async def send_group_notification(self, group_id: str, content: str, sender_id: str,
                                  priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Send notification to group members"""
        group = self.groups.get(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        if not group.can_send_message(sender_id):
            raise PermissionError(f"Sender {sender_id} cannot send to group {group_id}")

        # Get group members
        recipient_ids = list(group.members - {sender_id})

        return await self.send_message(
            MessageType.SYSTEM_NOTIFICATION,
            content,
            sender_id,
            recipient_ids=recipient_ids,
            scope=CommunicationScope.GROUP,
            group_id=group_id,
            priority=priority
        )

    async def share_attachments_with_selection(self, content: Union[str, bytes, Dict[str, Any]],
                                           attachment_type: AttachmentType, name: str,
                                           recipient_ids: List[str], **kwargs) -> str:
        """Share attachments with specific recipients"""
        # Create attachment
        attachment = await self.attachment_manager.create_attachment(
            content=content,
            attachment_type=attachment_type,
            name=name,
            access_level=kwargs.get("access_level", "restricted"),
            allowed_recipients=recipient_ids,
            expires_in=kwargs.get("expires_in")
        )

        # Create message with attachment
        message_content = f"Shared attachment: {name}"
        message = await self.send_message(
            MessageType.FILE_ATTACHMENT,
            message_content,
            kwargs.get("sender_id", "system"),
            recipient_ids=recipient_ids,
            attachments=[attachment]
        )

        self.communication_stats["attachments_created"] += 1
        return message

    async def read_shared_conversation(self, conversation_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
        """Read shared conversation state"""
        conversation = self.conversation_states.get(conversation_id)
        if not conversation:
            return None

        # Check read access
        if not conversation.is_public and agent_id not in conversation.read_access:
            return None

        return conversation.get_state()

    async def create_group(self, name: str, description: str, creator_id: str,
                          members: List[str] = None, **kwargs) -> CommunicationGroup:
        """Create new communication group"""
        group_id = str(uuid.uuid4())

        group = CommunicationGroup(
            id=group_id,
            name=name,
            description=description,
            created_by=creator_id,
            is_public=kwargs.get("is_public", False),
            is_moderated=kwargs.get("is_moderated", True),
            max_members=kwargs.get("max_members")
        )

        # Add creator as admin
        group.add_member(creator_id, "admin")

        # Add initial members
        for member_id in members or []:
            group.add_member(member_id, "member")

        # Store group
        self.groups[group_id] = group

        # Update router group memberships
        for member_id in group.members:
            self.message_router.join_group(member_id, group_id)

        # Update stats
        self.communication_stats["groups_created"] += 1

        # Trigger group event handlers
        await self._trigger_group_event_handlers("group_created", group)

        logger.info(f"Created group {group_id}: {name}")
        return group

    async def join_group(self, group_id: str, agent_id: str) -> bool:
        """Join agent to group"""
        group = self.groups.get(group_id)
        if not group:
            return False

        group.add_member(agent_id)
        self.message_router.join_group(agent_id, group_id)

        # Notify group members
        await self.send_group_notification(
            group_id,
            f"Agent {agent_id} joined the group",
            "system"
        )

        logger.info(f"Agent {agent_id} joined group {group_id}")
        return True

    async def leave_group(self, group_id: str, agent_id: str) -> bool:
        """Remove agent from group"""
        group = self.groups.get(group_id)
        if not group:
            return False

        group.remove_member(agent_id)
        self.message_router.leave_group(agent_id, group_id)

        # Notify group members
        await self.send_group_notification(
            group_id,
            f"Agent {agent_id} left the group",
            "system"
        )

        logger.info(f"Agent {agent_id} left group {group_id}")
        return True

    async def create_conversation_state(self, participants: Set[str], initial_state: Dict[str, Any] = None) -> str:
        """Create shared conversation state"""
        conversation_id = str(uuid.uuid4())

        conversation = ConversationState(
            id=conversation_id,
            participants=participants.copy(),
            shared_variables=initial_state or {},
            read_access=participants.copy(),
            write_access=participants.copy()
        )

        self.conversation_states[conversation_id] = conversation
        self.communication_stats["active_conversations"] += 1

        logger.info(f"Created conversation state {conversation_id} with {len(participants)} participants")
        return conversation_id

    async def update_conversation_state(self, conversation_id: str, updates: Dict[str, Any], agent_id: str):
        """Update shared conversation state"""
        conversation = self.conversation_states.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        conversation.update_state(updates, agent_id)

        # Notify participants of state change
        await self._notify_conversation_update(conversation, agent_id)

    async def _notify_conversation_update(self, conversation: ConversationState, updater_id: str):
        """Notify conversation participants of state update"""
        message_content = f"Conversation state updated by {updater_id}"

        for participant_id in conversation.participants:
            if participant_id != updater_id:
                await self.send_message(
                    MessageType.SYSTEM_NOTIFICATION,
                    message_content,
                    "system",
                    recipient_ids=[participant_id],
                    scope=CommunicationScope.DIRECT,
                    metadata={"conversation_id": conversation.id, "version": conversation.version}
                )

    async def _validate_message(self, message: CommunicationMessage) -> bool:
        """Validate message before sending"""
        # Check size
        content_size = len(message.content.encode())
        if content_size > self.max_message_size:
            logger.warning(f"Message {message.id} exceeds size limit: {content_size} bytes")
            return False

        # Check recipient validity
        if not message.recipient_ids and message.scope == CommunicationScope.DIRECT:
            logger.warning(f"Message {message.id} has no recipients")
            return False

        # Check group validity
        if message.group_id and message.group_id not in self.groups:
            logger.warning(f"Message {message.id} references invalid group {message.group_id}")
            return False

        return True

    async def _trigger_message_handlers(self, message: CommunicationMessage):
        """Trigger message type-specific handlers"""
        handlers = self.message_handlers.get(message.type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")

    async def _trigger_group_event_handlers(self, event_type: str, group: CommunicationGroup):
        """Trigger group event handlers"""
        for handler in self.group_event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, group)
                else:
                    handler(event_type, group)
            except Exception as e:
                logger.error(f"Error in group event handler: {e}")

    async def _start_websocket_server(self):
        """Start WebSocket server for real-time communication"""
        # This is a placeholder for WebSocket server implementation
        logger.info("WebSocket server would be started here")

    async def _create_default_groups(self):
        """Create default communication groups"""
        # Create general discussion group
        await self.create_group(
            "general",
            "General discussion and announcements",
            "system",
            is_public=True,
            is_moderated=True
        )

        # Create technical discussion group
        await self.create_group(
            "technical",
            "Technical discussions and problem solving",
            "system",
            is_public=True,
            is_moderated=True
        )

        logger.info("Created default communication groups")

    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register handler for specific message type"""
        self.message_handlers[message_type].append(handler)

    def register_group_event_handler(self, handler: Callable):
        """Register handler for group events"""
        self.group_event_handlers.append(handler)

    async def get_communication_status(self) -> Dict[str, Any]:
        """Get communication system status"""
        return {
            "messages": {
                "total": len(self.messages),
                "sent_today": len([m for m in self.messages.values()
                                 if m.created_at.date() == datetime.now().date()]),
                "pending_delivery": len([m for m in self.messages.values()
                                      if len(m.delivered_to) < len(m.recipient_ids)])
            },
            "groups": {
                "total": len(self.groups),
                "active": len([g for g in self.groups.values() if g.is_active]),
                "total_members": sum(len(g.members) for g in self.groups.values())
            },
            "conversations": len(self.conversation_states),
            "attachments": {
                "total": len(self.attachment_manager.attachments),
                "cache_size": len(self.attachment_manager.content_cache)
            },
            "stats": self.communication_stats,
            "router": {
                "registered_agents": len(self.message_router.agent_endpoints),
                "active_topics": len(self.message_router.topic_subscribers)
            }
        }

class MessageProcessor:
    """Background message processing service"""

    def __init__(self, comm_manager: EnhancedCommunicationManager):
        self.comm_manager = comm_manager
        self.is_running = False

    async def start(self):
        """Start message processor"""
        self.is_running = True
        asyncio.create_task(self._processing_loop())
        logger.info("Message Processor started")

    async def stop(self):
        """Stop message processor"""
        self.is_running = False
        logger.info("Message Processor stopped")

    async def _processing_loop(self):
        """Main processing loop"""
        while self.is_running:
            try:
                await asyncio.sleep(5)  # Process every 5 seconds

                # Process expired messages
                await self._process_expired_messages()

                # Process message delivery failures
                await self._process_delivery_failures()

                # Update conversation states
                await self._update_conversation_states()

            except Exception as e:
                logger.error(f"Error in message processing loop: {e}")

    async def _process_expired_messages(self):
        """Process expired messages"""
        now = datetime.now()
        expired_messages = [
            message_id for message_id, message in self.comm_manager.messages.items()
            if message.is_expired()
        ]

        for message_id in expired_messages:
            message = self.comm_manager.messages.pop(message_id, None)
            if message:
                logger.debug(f"Removed expired message {message_id}")

    async def _process_delivery_failures(self):
        """Process message delivery failures"""
        failed_messages = [
            message for message in self.comm_manager.messages.values()
            if (len(message.recipient_ids) > 0 and
                len(message.delivered_to) == 0 and
                (datetime.now() - message.created_at).total_seconds() > 60)  # 60 seconds timeout
        ]

        for message in failed_messages:
            logger.warning(f"Message {message.id} delivery failed - no recipients reachable")
            # Mark as failed
            message.status = "failed"

    async def _update_conversation_states(self):
        """Update conversation state metadata"""
        for conversation in self.comm_manager.conversation_states.values():
            conversation.updated_at = datetime.now()

class StateSynchronizer:
    """Conversation state synchronization service"""

    def __init__(self, comm_manager: EnhancedCommunicationManager):
        self.comm_manager = comm_manager
        self.is_running = False

    async def start(self):
        """Start state synchronizer"""
        self.is_running = True
        asyncio.create_task(self._synchronization_loop())
        logger.info("State Synchronizer started")

    async def stop(self):
        """Stop state synchronizer"""
        self.is_running = False
        logger.info("State Synchronizer stopped")

    async def _synchronization_loop(self):
        """Main synchronization loop"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Synchronize every 30 seconds

                # Synchronize conversation states
                await self._synchronize_conversation_states()

                # Clean up inactive conversations
                await self._cleanup_inactive_conversations()

            except Exception as e:
                logger.error(f"Error in state synchronization loop: {e}")

    async def _synchronize_conversation_states(self):
        """Synchronize conversation states between participants"""
        for conversation in self.comm_manager.conversation_states.values():
            conversation.last_sync = datetime.now()

    async def _cleanup_inactive_conversations(self):
        """Clean up inactive conversations"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        inactive_conversations = [
            conv_id for conv_id, conv in self.comm_manager.conversation_states.items()
            if conv.updated_at < cutoff_time and len(conv.participants) == 0
        ]

        for conv_id in inactive_conversations:
            self.comm_manager.conversation_states.pop(conv_id, None)
            logger.debug(f"Removed inactive conversation {conv_id}")

class AnalyticsCollector:
    """Communication analytics collection service"""

    def __init__(self, comm_manager: EnhancedCommunicationManager):
        self.comm_manager = comm_manager
        self.is_running = False

    async def start(self):
        """Start analytics collector"""
        self.is_running = True
        asyncio.create_task(self._analytics_loop())
        logger.info("Analytics Collector started")

    async def stop(self):
        """Stop analytics collector"""
        self.is_running = False
        logger.info("Analytics Collector stopped")

    async def _analytics_loop(self):
        """Main analytics collection loop"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Collect every minute

                # Collect message metrics
                await self._collect_message_metrics()

                # Collect group activity metrics
                await self._collect_group_metrics()

                # Update peak messages per minute
                await self._update_peak_metrics()

            except Exception as e:
                logger.error(f"Error in analytics collection loop: {e}")

    async def _collect_message_metrics(self):
        """Collect message-related metrics"""
        recent_messages = [
            message for message in self.comm_manager.messages.values()
            if (datetime.now() - message.created_at).total_seconds() < 60
        ]

        if recent_messages:
            total_size = sum(len(m.content.encode()) for m in recent_messages)
            self.comm_manager.communication_stats["avg_message_size"] = total_size / len(recent_messages)

    async def _collect_group_metrics(self):
        """Collect group activity metrics"""
        for group in self.comm_manager.groups.values():
            recent_messages = [
                message for message in self.comm_manager.messages.values()
                if (message.group_id == group.id and
                    (datetime.now() - message.created_at).total_seconds() < 300)
            ]

            group.last_activity = max([m.created_at for m in recent_messages]) if recent_messages else group.last_activity
            group.message_count = len(recent_messages)

    async def _update_peak_metrics(self):
        """Update peak performance metrics"""
        recent_messages = [
            message for message in self.comm_manager.messages.values()
            if (datetime.now() - message.created_at).total_seconds() < 60
        ]

        messages_per_minute = len(recent_messages)
        current_peak = self.comm_manager.communication_stats["peak_messages_per_minute"]
        self.comm_manager.communication_stats["peak_messages_per_minute"] = max(current_peak, messages_per_minute)

# Global communication manager instance
enhanced_communication_manager = EnhancedCommunicationManager()

# Convenience functions
async def initialize_enhanced_communication() -> bool:
    """Initialize enhanced communication system"""
    return await enhanced_communication_manager.initialize()

async def send_agent_message(content: str, sender_id: str, recipient_ids: List[str],
                           message_type: MessageType = MessageType.TEXT, **kwargs) -> str:
    """Send message between agents"""
    return await enhanced_communication_manager.send_message(
        message_type, content, sender_id, recipient_ids, **kwargs
    )

async def create_agent_group(name: str, description: str, creator_id: str,
                           members: List[str] = None, **kwargs) -> CommunicationGroup:
    """Create agent communication group"""
    return await enhanced_communication_manager.create_group(name, description, creator_id, members, **kwargs)

async def share_agent_attachment(content: Union[str, bytes, Dict[str, Any]],
                              attachment_type: AttachmentType, name: str,
                              recipient_ids: List[str], **kwargs) -> str:
    """Share attachment with agents"""
    return await enhanced_communication_manager.share_attachments_with_selection(
        content, attachment_type, name, recipient_ids, **kwargs
    )

async def get_communication_status() -> Dict[str, Any]:
    """Get communication system status"""
    return await enhanced_communication_manager.get_communication_status()

if __name__ == "__main__":
    # Test the enhanced communication system
    import asyncio

    async def test():
        print("Enhanced Communication System Test")
        print("===================================")

        # Initialize communication system
        if await initialize_enhanced_communication():
            print("✅ Enhanced communication system initialized")

            # Register test agents
            enhanced_communication_manager.message_router.register_agent("agent1", "ws://localhost:8001")
            enhanced_communication_manager.message_router.register_agent("agent2", "ws://localhost:8002")

            # Test direct message
            message_id = await send_agent_message(
                "Hello from agent1!",
                "agent1",
                ["agent2"]
            )
            print(f"✅ Sent message: {message_id}")

            # Test group creation
            group = await create_agent_group(
                "Test Group",
                "Group for testing communication features",
                "agent1",
                members=["agent2"]
            )
            print(f"✅ Created group: {group.id}")

            # Test group notification
            notification_id = await enhanced_communication_manager.send_group_notification(
                group.id,
                "Welcome to the test group!",
                "agent1"
            )
            print(f"✅ Sent group notification: {notification_id}")

            # Test attachment sharing
            attachment_id = await share_agent_attachment(
                {"test": "data", "value": 42},
                AttachmentType.DATA,
                "test_data.json",
                ["agent1", "agent2"]
            )
            print(f"✅ Shared attachment: {attachment_id}")

            # Test conversation state
            conv_id = await enhanced_communication_manager.create_conversation_state(
                {"agent1", "agent2"},
                {"shared_counter": 0, "shared_data": []}
            )
            print(f"✅ Created conversation state: {conv_id}")

            # Show status
            status = await get_communication_status()
            print(f"Communication Status: {json.dumps(status, indent=2, default=str)}")
        else:
            print("❌ Failed to initialize enhanced communication system")

    asyncio.run(test())