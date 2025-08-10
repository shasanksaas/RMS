"""
Dependency Container for Hexagonal Architecture
Implements dependency injection for handlers and services
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

# Domain Services
from ...domain.services.return_eligibility_service import ReturnEligibilityService

# Application Handlers
from ...application.handlers.command_handlers import (
    CreateReturnRequestHandler, CreateReturnDraftHandler, ApproveReturnHandler,
    RejectReturnHandler, ApproveDraftAndConvertHandler
)
from ...application.handlers.query_handlers import (
    GetReturnByIdHandler, SearchReturnsHandler, GetPendingDraftsHandler,
    LookupOrderForReturnHandler, GetEligibleItemsForReturnHandler,
    GetPolicyPreviewHandler, GetReturnAuditLogHandler
)

# Infrastructure - Repositories
from ..repositories.mongo_return_repository import MongoReturnRepository
from ..repositories.mongo_return_draft_repository import MongoReturnDraftRepository
from ..repositories.mongo_order_repository import MongoOrderRepository

# Infrastructure - Services
from ..services.shopify_service_adapter import ShopifyServiceAdapter
from ..services.notification_service_adapter import NotificationServiceAdapter
from ..services.policy_service_adapter import PolicyServiceAdapter
from ..services.label_service_adapter import LabelServiceAdapter
from ..services.event_publisher_adapter import InMemoryEventPublisher

# Existing services
from ...services.shopify_service import ShopifyService
from ...services.email_service import EmailService
from ...services.label_service import LabelService


class DependencyContainer:
    """Dependency injection container for Elite Returns system"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self._handlers = {}
        self._services = {}
        self._repositories = {}
        
        # Initialize repositories
        self._init_repositories()
        
        # Initialize services
        self._init_services()
        
        # Initialize handlers
        self._init_handlers()
    
    def _init_repositories(self):
        """Initialize repository implementations"""
        self._repositories['return_repository'] = MongoReturnRepository(self.database)
        self._repositories['return_draft_repository'] = MongoReturnDraftRepository(self.database)
        self._repositories['order_repository'] = MongoOrderRepository(self.database)
    
    def _init_services(self):
        """Initialize service implementations"""
        # Wrap existing services with adapters
        existing_shopify_service = ShopifyService()
        existing_email_service = EmailService()
        existing_label_service = LabelService()
        
        self._services['shopify_service'] = ShopifyServiceAdapter(existing_shopify_service)
        self._services['notification_service'] = NotificationServiceAdapter(existing_email_service)
        self._services['label_service'] = LabelServiceAdapter(existing_label_service)
        self._services['policy_service'] = PolicyServiceAdapter(self.database)
        self._services['event_publisher'] = InMemoryEventPublisher()
        
        # Domain services
        self._services['eligibility_service'] = ReturnEligibilityService()
    
    def _init_handlers(self):
        """Initialize command and query handlers"""
        # Command handlers
        self._handlers['create_return_handler'] = CreateReturnRequestHandler(
            return_repository=self._repositories['return_repository'],
            order_repository=self._repositories['order_repository'],
            policy_service=self._services['policy_service'],
            eligibility_service=self._services['eligibility_service'],
            notification_service=self._services['notification_service'],
            event_publisher=self._services['event_publisher'],
            shopify_service=self._services['shopify_service']
        )
        
        self._handlers['create_draft_handler'] = CreateReturnDraftHandler(
            draft_repository=self._repositories['return_draft_repository'],
            event_publisher=self._services['event_publisher']
        )
        
        self._handlers['approve_return_handler'] = ApproveReturnHandler(
            return_repository=self._repositories['return_repository'],
            notification_service=self._services['notification_service'],
            label_service=self._services['label_service'],
            event_publisher=self._services['event_publisher']
        )
        
        self._handlers['reject_return_handler'] = RejectReturnHandler(
            return_repository=self._repositories['return_repository'],
            notification_service=self._services['notification_service'],
            event_publisher=self._services['event_publisher']
        )
        
        self._handlers['approve_draft_handler'] = ApproveDraftAndConvertHandler(
            draft_repository=self._repositories['return_draft_repository'],
            return_repository=self._repositories['return_repository'],
            order_repository=self._repositories['order_repository'],
            policy_service=self._services['policy_service'],
            event_publisher=self._services['event_publisher']
        )
        
        # Query handlers
        self._handlers['return_by_id_handler'] = GetReturnByIdHandler(
            return_repository=self._repositories['return_repository']
        )
        
        self._handlers['search_returns_handler'] = SearchReturnsHandler(
            return_repository=self._repositories['return_repository']
        )
        
        self._handlers['pending_drafts_handler'] = GetPendingDraftsHandler(
            draft_repository=self._repositories['return_draft_repository']
        )
        
        self._handlers['lookup_order_handler'] = LookupOrderForReturnHandler(
            order_repository=self._repositories['order_repository'],
            shopify_service=self._services['shopify_service']
        )
        
        self._handlers['eligible_items_handler'] = GetEligibleItemsForReturnHandler(
            order_repository=self._repositories['order_repository'],
            return_repository=self._repositories['return_repository']
        )
        
        self._handlers['policy_preview_handler'] = GetPolicyPreviewHandler(
            policy_service=self._services['policy_service'],
            eligibility_service=self._services['eligibility_service'],
            order_repository=self._repositories['order_repository']
        )
        
        self._handlers['audit_log_handler'] = GetReturnAuditLogHandler(
            return_repository=self._repositories['return_repository']
        )
    
    # Command Handler Getters
    def get_create_return_handler(self) -> CreateReturnRequestHandler:
        return self._handlers['create_return_handler']
    
    def get_create_draft_handler(self) -> CreateReturnDraftHandler:
        return self._handlers['create_draft_handler']
    
    def get_approve_return_handler(self) -> ApproveReturnHandler:
        return self._handlers['approve_return_handler']
    
    def get_reject_return_handler(self) -> RejectReturnHandler:
        return self._handlers['reject_return_handler']
    
    def get_approve_draft_handler(self) -> ApproveDraftAndConvertHandler:
        return self._handlers['approve_draft_handler']
    
    # Query Handler Getters
    def get_return_by_id_handler(self) -> GetReturnByIdHandler:
        return self._handlers['return_by_id_handler']
    
    def get_search_returns_handler(self) -> SearchReturnsHandler:
        return self._handlers['search_returns_handler']
    
    def get_pending_drafts_handler(self) -> GetPendingDraftsHandler:
        return self._handlers['pending_drafts_handler']
    
    def get_lookup_order_handler(self) -> LookupOrderForReturnHandler:
        return self._handlers['lookup_order_handler']
    
    def get_eligible_items_handler(self) -> GetEligibleItemsForReturnHandler:
        return self._handlers['eligible_items_handler']
    
    def get_policy_preview_handler(self) -> GetPolicyPreviewHandler:
        return self._handlers['policy_preview_handler']
    
    def get_audit_log_handler(self) -> GetReturnAuditLogHandler:
        return self._handlers['audit_log_handler']
    
    # Service Getters (for direct access if needed)
    def get_event_publisher(self):
        return self._services['event_publisher']
    
    def get_eligibility_service(self) -> ReturnEligibilityService:
        return self._services['eligibility_service']


# Global container instance
_container: Optional[DependencyContainer] = None


def initialize_container(database: AsyncIOMotorDatabase) -> DependencyContainer:
    """Initialize the global dependency container"""
    global _container
    _container = DependencyContainer(database)
    return _container


def get_container() -> DependencyContainer:
    """Get the global dependency container"""
    global _container
    if _container is None:
        raise RuntimeError("Dependency container not initialized. Call initialize_container() first.")
    return _container