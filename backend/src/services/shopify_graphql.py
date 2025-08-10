"""
Shopify GraphQL Admin API Service
Handles GraphQL operations for returns, orders, and other Shopify resources
"""

import json
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ShopifyGraphQLService:
    """GraphQL service for Shopify Admin API operations"""
    
    def __init__(self, shop: str, access_token: str, api_version: str = "2025-07"):
        self.shop = shop
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"https://{shop}.myshopify.com/admin/api/{api_version}/graphql.json"
        
    async def execute_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a GraphQL query"""
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if "errors" in result:
                        logger.error(f"GraphQL errors: {result['errors']}")
                        raise Exception(f"GraphQL query failed: {result['errors']}")
                    return result.get("data", {})
                else:
                    error_text = await response.text()
                    logger.error(f"GraphQL request failed: {response.status} - {error_text}")
                    raise Exception(f"GraphQL request failed: {response.status}")

    # RETURNS OPERATIONS
    async def get_returns(self, limit: int = 50, cursor: str = None) -> Dict[str, Any]:
        """Get returns using GraphQL"""
        query = """
        query getReturns($first: Int!, $after: String) {
            returns(first: $first, after: $after) {
                edges {
                    node {
                        id
                        name
                        status
                        totalQuantity
                        requestedAt
                        processedAt
                        order {
                            id
                            name
                            customer {
                                id
                                email
                                firstName
                                lastName
                            }
                        }
                        returnLineItems(first: 50) {
                            edges {
                                node {
                                    id
                                    quantity
                                    returnReason
                                    returnReasonNote
                                    fulfillmentLineItem {
                                        lineItem {
                                            id
                                            name
                                            sku
                                            price
                                            product {
                                                id
                                                title
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        refunds {
                            id
                            createdAt
                            totalRefunded {
                                amount
                                currencyCode
                            }
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        
        variables = {"first": limit}
        if cursor:
            variables["after"] = cursor
            
        return await self.execute_query(query, variables)

    async def get_return_by_id(self, return_id: str) -> Dict[str, Any]:
        """Get a specific return by ID"""
        query = """
        query getReturn($id: ID!) {
            return(id: $id) {
                id
                name
                status
                totalQuantity
                requestedAt
                processedAt
                declineReason
                order {
                    id
                    name
                    email
                    customer {
                        id
                        email
                        firstName
                        lastName
                        phone
                    }
                    billingAddress {
                        address1
                        city
                        country
                        zip
                    }
                }
                returnLineItems(first: 100) {
                    edges {
                        node {
                            id
                            quantity
                            returnReason
                            returnReasonNote
                            fulfillmentLineItem {
                                id
                                lineItem {
                                    id
                                    name
                                    sku
                                    price
                                    product {
                                        id
                                        title
                                        handle
                                    }
                                }
                            }
                        }
                    }
                }
                refunds {
                    id
                    createdAt
                    note
                    totalRefunded {
                        amount
                        currencyCode
                    }
                    refundLineItems {
                        lineItem {
                            id
                        }
                        quantity
                        subtotal {
                            amount
                            currencyCode
                        }
                    }
                }
            }
        }
        """
        
        variables = {"id": return_id}
        return await self.execute_query(query, variables)

    async def create_return(self, order_id: str, return_line_items: List[Dict]) -> Dict[str, Any]:
        """Create a new return"""
        query = """
        mutation createReturn($input: ReturnInput!) {
            returnCreate(return: $input) {
                return {
                    id
                    name
                    status
                    requestedAt
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        variables = {
            "input": {
                "orderId": order_id,
                "returnLineItems": return_line_items
            }
        }
        
        return await self.execute_query(query, variables)

    async def approve_return(self, return_id: str) -> Dict[str, Any]:
        """Approve a return"""
        query = """
        mutation approveReturn($id: ID!) {
            returnApprove(id: $id) {
                return {
                    id
                    status
                    processedAt
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        variables = {"id": return_id}
        return await self.execute_query(query, variables)

    async def decline_return(self, return_id: str, reason: str) -> Dict[str, Any]:
        """Decline a return"""
        query = """
        mutation declineReturn($id: ID!, $reason: String!) {
            returnDecline(id: $id, reason: $reason) {
                return {
                    id
                    status
                    declineReason
                    processedAt
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        variables = {"id": return_id, "reason": reason}
        return await self.execute_query(query, variables)

    # ORDERS OPERATIONS
    async def get_orders_with_returns(self, limit: int = 50, cursor: Optional[str] = None, 
                                    query_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all orders with returns - implements guide requirement
        Query: GetOrdersWithReturns from Shopify RMS Guide
        """
        query = """
        query GetOrdersWithReturns($first: Int!, $after: String, $query: String) {
            orders(first: $first, after: $after, query: $query) {
                edges {
                    node {
                        id
                        name
                        email
                        displayFinancialStatus
                        displayFulfillmentStatus
                        returnStatus
                        createdAt
                        updatedAt
                        totalPriceSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }
                        customer {
                            id
                            email
                            firstName
                            lastName
                        }
                        lineItems(first: 50) {
                            edges {
                                node {
                                    id
                                    title
                                    quantity
                                    sku
                                    product {
                                        id
                                        title
                                    }
                                }
                            }
                        }
                        returns(first: 10) {
                            edges {
                                node {
                                    id
                                    status
                                    name
                                    totalQuantity
                                    returnLineItems(first: 25) {
                                        edges {
                                            node {
                                                ... on ReturnLineItem {
                                                    id
                                                    quantity
                                                    refundableQuantity
                                                    refundedQuantity
                                                    returnReason
                                                    returnReasonNote
                                                    customerNote
                                                    fulfillmentLineItem {
                                                        lineItem {
                                                            id
                                                            title
                                                            sku
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    exchangeLineItems(first: 10) {
                                        edges {
                                            node {
                                                lineItem {
                                                    id
                                                    title
                                                    sku
                                                    quantity
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        
        # Use return status filter if no custom query provided
        if not query_filter:
            query_filter = "returnStatus:IN_PROGRESS,RETURNED,REQUESTED"
        
        variables = {
            "first": limit,
            "after": cursor,
            "query": query_filter
        }
        
        return await self.execute_query(query, variables)

    async def get_returnable_fulfillments(self, order_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        Get returnable fulfillments for an order - implements guide requirement
        Query: GetReturnableFulfillments from Shopify RMS Guide
        """
        query = """
        query GetReturnableFulfillments($orderId: ID!, $first: Int!) {
            returnableFulfillments(orderId: $orderId, first: $first) {
                edges {
                    node {
                        id
                        fulfillment {
                            id
                            displayStatus
                            status
                            name
                            originAddress {
                                address1
                                city
                                province
                                country
                                zip
                            }
                        }
                        returnableFulfillmentLineItems(first: 50) {
                            edges {
                                node {
                                    fulfillmentLineItem {
                                        id
                                        lineItem {
                                            id
                                            title
                                            sku
                                            product {
                                                id
                                                title
                                            }
                                        }
                                    }
                                    quantity
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "orderId": order_id,
            "first": limit
        }
        
        return await self.execute_query(query, variables)

    async def get_return_details(self, return_id: str) -> Dict[str, Any]:
        """
        Get specific return details - implements guide requirement
        Query: GetReturn from Shopify RMS Guide
        """
        query = """
        query GetReturn($id: ID!) {
            return(id: $id) {
                id
                status
                name
                totalQuantity
                order {
                    id
                    name
                }
                returnLineItems(first: 50) {
                    edges {
                        node {
                            ... on ReturnLineItem {
                                id
                                quantity
                                processableQuantity
                                processedQuantity
                                refundableQuantity
                                refundedQuantity
                                returnReason
                                returnReasonNote
                                customerNote
                                fulfillmentLineItem {
                                    id
                                    lineItem {
                                        id
                                        title
                                        sku
                                        variant {
                                            id
                                            title
                                            price
                                        }
                                        product {
                                            id
                                            title
                                        }
                                    }
                                }
                                restockingFee {
                                    amountSet {
                                        shopMoney {
                                            amount
                                            currencyCode
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                exchangeLineItems(first: 10) {
                    edges {
                        node {
                            id
                            lineItem {
                                id
                                title
                                sku
                                quantity
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {"id": return_id}
        return await self.execute_query(query, variables)

    async def create_return_request(self, order_id: str, return_line_items: List[Dict]) -> Dict[str, Any]:
        """
        Create a return request - implements guide requirement
        Mutation: CreateReturnRequest from Shopify RMS Guide
        """
        query = """
        mutation CreateReturnRequest($orderId: ID!, $returnLineItems: [ReturnRequestLineItemInput!]!) {
            returnRequest(orderId: $orderId, returnLineItems: $returnLineItems) {
                return {
                    id
                    status
                    name
                    returnLineItems(first: 10) {
                        edges {
                            node {
                                ... on ReturnLineItem {
                                    id
                                    quantity
                                    returnReason
                                    returnReasonNote
                                    customerNote
                                }
                            }
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        variables = {
            "orderId": order_id,
            "returnLineItems": return_line_items
        }
        
        return await self.execute_query(query, variables)

    async def approve_return_request(self, return_id: str) -> Dict[str, Any]:
        """
        Approve a return request - implements guide requirement
        Mutation: ApproveReturn from Shopify RMS Guide
        """
        query = """
        mutation ApproveReturn($id: ID!) {
            returnApproveRequest(id: $id) {
                return {
                    id
                    status
                    name
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        variables = {"id": return_id}
        return await self.execute_query(query, variables)

    async def process_return_with_refund(self, return_id: str, refund_input: Dict, 
                                       return_line_items: List[Dict]) -> Dict[str, Any]:
        """
        Process return with refund - implements guide requirement
        Mutation: ProcessReturn from Shopify RMS Guide
        """
        query = """
        mutation ProcessReturn($id: ID!, $refund: RefundInput, $returnLineItems: [ProcessReturnLineItemInput!]!) {
            returnProcess(id: $id, refund: $refund, returnLineItems: $returnLineItems) {
                return {
                    id
                    status
                }
                refund {
                    id
                    createdAt
                    totalRefundedSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        variables = {
            "id": return_id,
            "refund": refund_input,
            "returnLineItems": return_line_items
        }
        
        return await self.execute_query(query, variables)

    async def get_order_by_id(self, order_id: str) -> Dict[str, Any]:
        """Get a specific order by ID"""
        query = """
        query getOrder($id: ID!) {
            order(id: $id) {
                id
                name
                email
                createdAt
                processedAt
                financialStatus
                fulfillmentStatus
                totalPrice
                currencyCode
                customer {
                    id
                    email
                    firstName
                    lastName
                    phone
                }
                lineItems(first: 100) {
                    edges {
                        node {
                            id
                            name
                            sku
                            quantity
                            price
                            fulfillableQuantity
                            product {
                                id
                                title
                            }
                            variant {
                                id
                                title
                                sku
                            }
                        }
                    }
                }
                fulfillments {
                    id
                    status
                    createdAt
                    trackingNumber
                    trackingCompany
                    fulfillmentLineItems(first: 100) {
                        edges {
                            node {
                                id
                                quantity
                                lineItem {
                                    id
                                }
                            }
                        }
                    }
                }
                refunds {
                    id
                    createdAt
                    totalRefunded {
                        amount
                        currencyCode
                    }
                }
            }
        }
        """
        
        variables = {"id": order_id}
        return await self.execute_query(query, variables)

    # REFUNDS OPERATIONS
    async def create_refund(self, order_id: str, refund_line_items: List[Dict], 
                          amount: float, reason: str = None) -> Dict[str, Any]:
        """Create a refund"""
        query = """
        mutation createRefund($input: RefundInput!) {
            refundCreate(input: $input) {
                refund {
                    id
                    createdAt
                    totalRefunded {
                        amount
                        currencyCode
                    }
                }
                order {
                    id
                    totalRefunded
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        refund_input = {
            "orderId": order_id,
            "refundLineItems": refund_line_items
        }
        
        if reason:
            refund_input["note"] = reason
            
        variables = {"input": refund_input}
        return await self.execute_query(query, variables)

    # PRODUCTS OPERATIONS
    async def get_products(self, limit: int = 50, cursor: str = None) -> Dict[str, Any]:
        """Get products"""
        query = """
        query getProducts($first: Int!, $after: String) {
            products(first: $first, after: $after) {
                edges {
                    node {
                        id
                        title
                        handle
                        status
                        createdAt
                        updatedAt
                        productType
                        vendor
                        tags
                        variants(first: 100) {
                            edges {
                                node {
                                    id
                                    title
                                    sku
                                    price
                                    inventoryQuantity
                                    availableForSale
                                }
                            }
                        }
                        images(first: 10) {
                            edges {
                                node {
                                    id
                                    src
                                    altText
                                }
                            }
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        
        variables = {"first": limit}
        if cursor:
            variables["after"] = cursor
            
        return await self.execute_query(query, variables)

    # CUSTOMERS OPERATIONS  
    async def get_customer_by_email(self, email: str) -> Dict[str, Any]:
        """Get customer by email"""
        query = """
        query getCustomer($query: String!) {
            customers(first: 1, query: $query) {
                edges {
                    node {
                        id
                        email
                        firstName
                        lastName
                        phone
                        createdAt
                        updatedAt
                        ordersCount
                        totalSpent
                        addresses {
                            id
                            address1
                            city
                            country
                            zip
                        }
                    }
                }
            }
        }
        """
        
        variables = {"query": f"email:{email}"}
        return await self.execute_query(query, variables)

    # UTILITY METHODS
    def parse_shopify_id(self, gid: str) -> str:
        """Extract numeric ID from Shopify GraphQL ID"""
        if gid and "/" in gid:
            return gid.split("/")[-1]
        return gid

    def create_shopify_id(self, resource_type: str, numeric_id: str) -> str:
        """Create Shopify GraphQL ID from numeric ID"""
        return f"gid://shopify/{resource_type}/{numeric_id}"


class ShopifyGraphQLFactory:
    """Factory for creating GraphQL service instances"""
    
    @staticmethod
    async def create_service(tenant_id: str) -> Optional[ShopifyGraphQLService]:
        """Create GraphQL service for a tenant"""
        from ..modules.auth.service import auth_service
        
        credentials = await auth_service.get_decrypted_credentials(tenant_id)
        if not credentials:
            return None
            
        return ShopifyGraphQLService(
            shop=credentials["shop"],
            access_token=credentials["access_token"],
            api_version="2025-07"
        )