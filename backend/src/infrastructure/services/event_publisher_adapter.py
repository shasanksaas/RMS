"""
Event Publisher Adapter
Concrete implementation for publishing domain events
"""

from typing import List, Any
import json
import asyncio
from datetime import datetime

from ...domain.ports.services import EventPublisher as EventPublisherPort


class InMemoryEventPublisher(EventPublisherPort):
    """In-memory event publisher for development and testing"""
    
    def __init__(self):
        self.published_events = []
    
    async def publish(self, event: Any) -> None:
        """Publish a single domain event"""
        event_data = {
            "event_type": event.get_event_type(),
            "data": self._serialize_event(event),
            "published_at": datetime.utcnow(),
            "correlation_id": getattr(event, 'correlation_id', None)
        }
        
        self.published_events.append(event_data)
        
        # Log event for debugging
        print(f"Published event: {event.get_event_type()}")
    
    async def publish_batch(self, events: List[Any]) -> None:
        """Publish multiple domain events"""
        for event in events:
            await self.publish(event)
    
    def _serialize_event(self, event: Any) -> dict:
        """Serialize event to dictionary"""
        result = {}
        for key, value in event.__dict__.items():
            if key.startswith('_'):
                continue
            
            # Handle different value types
            if hasattr(value, 'value'):  # Value objects
                result[key] = value.value
            elif hasattr(value, '__dict__'):  # Complex objects
                result[key] = self._serialize_event(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        
        return result
    
    def get_published_events(self) -> List[dict]:
        """Get all published events (for testing)"""
        return self.published_events.copy()
    
    def clear_events(self) -> None:
        """Clear published events (for testing)"""
        self.published_events.clear()


class AsyncEventPublisher(EventPublisherPort):
    """Async event publisher with queue processing"""
    
    def __init__(self):
        self.event_queue = asyncio.Queue()
        self.processed_events = []
        self._processing = False
    
    async def publish(self, event: Any) -> None:
        """Publish a single domain event"""
        await self.event_queue.put(event)
        
        if not self._processing:
            asyncio.create_task(self._process_events())
    
    async def publish_batch(self, events: List[Any]) -> None:
        """Publish multiple domain events"""
        for event in events:
            await self.event_queue.put(event)
        
        if not self._processing:
            asyncio.create_task(self._process_events())
    
    async def _process_events(self) -> None:
        """Process events from queue"""
        self._processing = True
        
        try:
            while not self.event_queue.empty():
                event = await self.event_queue.get()
                await self._handle_event(event)
                self.event_queue.task_done()
        finally:
            self._processing = False
    
    async def _handle_event(self, event: Any) -> None:
        """Handle individual event"""
        event_data = {
            "event_type": event.get_event_type(),
            "data": self._serialize_event(event),
            "processed_at": datetime.utcnow(),
            "correlation_id": getattr(event, 'correlation_id', None)
        }
        
        self.processed_events.append(event_data)
        
        # Here you could add integrations with:
        # - Message queues (RabbitMQ, Redis)
        # - Event stores
        # - Webhooks
        # - Analytics systems
        
        print(f"Processed event: {event.get_event_type()}")
    
    def _serialize_event(self, event: Any) -> dict:
        """Serialize event to dictionary"""
        result = {}
        for key, value in event.__dict__.items():
            if key.startswith('_'):
                continue
            
            # Handle different value types
            if hasattr(value, 'value'):  # Value objects
                result[key] = value.value
            elif hasattr(value, '__dict__'):  # Complex objects
                result[key] = self._serialize_event(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        
        return result