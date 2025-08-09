"""
Custom exception classes
"""
from fastapi import HTTPException


class TenantNotFoundError(HTTPException):
    """Raised when tenant is not found"""
    def __init__(self, tenant_id: str):
        super().__init__(status_code=404, detail=f"Tenant {tenant_id} not found")


class ReturnNotFoundError(HTTPException):
    """Raised when return request is not found"""
    def __init__(self, return_id: str):
        super().__init__(status_code=404, detail=f"Return request {return_id} not found")


class OrderNotFoundError(HTTPException):
    """Raised when order is not found"""
    def __init__(self, order_id: str):
        super().__init__(status_code=404, detail=f"Order {order_id} not found")


class InvalidReturnStatusError(HTTPException):
    """Raised when trying to set invalid return status"""
    def __init__(self, current_status: str, new_status: str):
        super().__init__(
            status_code=400, 
            detail=f"Cannot change status from {current_status} to {new_status}"
        )