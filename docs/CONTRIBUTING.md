# Contributing Guide

*Last updated: 2025-01-11*

## Development Workflow

### Branch Strategy

**Main Branches:**
- `main`: Production-ready code
- `develop`: Integration branch for features
- `release/*`: Release preparation branches
- `hotfix/*`: Emergency production fixes

**Feature Branches:**
- `feature/TICKET-123-description`: New features
- `bugfix/TICKET-456-description`: Bug fixes  
- `docs/update-api-documentation`: Documentation updates

**Branch Naming Convention:**
```bash
# Feature branches
feature/RET-123-add-bulk-return-approval
feature/RET-124-implement-return-analytics

# Bug fix branches  
bugfix/RET-125-fix-shopify-webhook-timeout
bugfix/RET-126-resolve-tenant-isolation-issue

# Hot fix branches
hotfix/RET-127-critical-oauth-security-fix

# Documentation branches
docs/RET-128-update-api-reference
docs/add-troubleshooting-guide
```

### Development Setup

**Prerequisites:**
- Python 3.11+
- Node.js 18+
- MongoDB 6.0+
- Git 2.30+

**Initial Setup:**
```bash
# Clone repository
git clone https://github.com/your-org/returns-management-saas.git
cd returns-management-saas

# Create feature branch
git checkout -b feature/RET-123-your-feature-description

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Update .env with your configuration

# Frontend setup  
cd ../frontend
yarn install
cp .env.example .env
# Update .env with your configuration

# Database setup
mongo returns_management < scripts/init_database.js
```

**Running Development Servers:**
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python server.py

# Terminal 2: Frontend
cd frontend  
yarn start

# Terminal 3: Database (if local)
mongod --dbpath ./data/db
```

### Code Style & Standards

**Python (Backend):**
```python
# Use Black formatter
pip install black
black --line-length 88 src/

# Use isort for imports
pip install isort
isort src/ --profile black

# Use flake8 for linting
pip install flake8
flake8 src/ --max-line-length 88 --extend-ignore E203

# Type hints required for new code
from typing import List, Dict, Optional
from pydantic import BaseModel

def process_returns(returns: List[Dict]) -> Optional[Dict]:
    """Process multiple return requests.
    
    Args:
        returns: List of return request dictionaries
        
    Returns:
        Summary of processing results or None if no returns
    """
    if not returns:
        return None
        
    # Implementation here
    return {"processed": len(returns)}
```

**JavaScript/React (Frontend):**
```javascript
// Use Prettier formatter
yarn add --dev prettier
yarn prettier --write src/

// ESLint configuration
yarn add --dev eslint
yarn eslint src/ --fix

// Component structure
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const ReturnsList = ({ tenantId, onReturnSelect }) => {
  const [returns, setReturns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadReturns();
  }, [tenantId]);

  const loadReturns = async () => {
    // Implementation
  };

  return (
    <div className="returns-list">
      {/* JSX content */}
    </div>
  );
};

ReturnsList.propTypes = {
  tenantId: PropTypes.string.isRequired,
  onReturnSelect: PropTypes.func.isRequired
};

export default ReturnsList;
```

**Database (MongoDB):**
```javascript
// Collection naming: snake_case
db.return_requests.insertOne(document);
db.webhook_events.find(query);

// Field naming: snake_case  
{
  "tenant_id": "tenant-rms34",
  "created_at": ISODate("2025-01-11T10:00:00Z"),
  "customer_email": "customer@example.com",
  "line_items": [
    {
      "line_item_id": "123456",
      "unit_price": {"amount": 100.00, "currency": "USD"}
    }
  ]
}

// Always include indexes for performance
db.returns.createIndex({tenant_id: 1, created_at: -1});
db.returns.createIndex({tenant_id: 1, status: 1});
```

### Commit Message Format

**Conventional Commits Standard:**
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```bash
# Feature commits
git commit -m "feat(returns): add bulk approval functionality

- Add bulk selection checkboxes to returns list
- Implement bulk approve/reject API endpoint
- Add confirmation dialog for bulk actions
- Update tests for bulk operations

Closes RET-123"

# Bug fix commits
git commit -m "fix(auth): resolve OAuth redirect URI mismatch

The callback URL was not matching Shopify app configuration
causing authentication failures.

- Update callback URL to match app settings
- Add environment variable validation
- Update documentation

Fixes RET-125"

# Documentation commits  
git commit -m "docs: update API reference with new endpoints

- Add bulk operations endpoints
- Update request/response examples
- Fix typos in authentication section"
```

### Pull Request Process

**PR Template:**
```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality) 
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated  
- [ ] Manual testing completed
- [ ] Backend testing agent validation passed
- [ ] Frontend testing validation completed

## Changes Made
- List key changes made
- Include any database migrations
- Note any environment variable changes

## Screenshots (if applicable)
Add screenshots of UI changes

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally
- [ ] Any dependent changes have been merged and published
```

**PR Review Criteria:**
1. **Code Quality:**
   - Follows established patterns and conventions
   - Proper error handling and validation
   - No hardcoded values or secrets
   - Adequate test coverage

2. **Security:**
   - No security vulnerabilities introduced
   - Proper input validation and sanitization
   - Tenant isolation maintained
   - Secrets properly managed

3. **Performance:**
   - No significant performance regressions
   - Database queries optimized
   - Appropriate caching where needed
   - No memory leaks

4. **Documentation:**
   - API changes documented
   - README updated if needed
   - Code comments for complex logic
   - Migration guides for breaking changes

### Testing Standards

**Backend Testing:**
```python
# Unit tests - test_services/test_return_service.py
import pytest
from unittest.mock import Mock, patch
from src.services.return_service import ReturnService

class TestReturnService:
    def setup_method(self):
        self.return_service = ReturnService()
        self.mock_db = Mock()
    
    @pytest.mark.asyncio
    async def test_create_return_success(self):
        """Test successful return creation"""
        # Arrange
        return_data = {
            "order_id": "12345",
            "customer_email": "test@example.com",
            "items": [{"line_item_id": "67890", "quantity": 1}]
        }
        
        self.mock_db.returns.insert_one.return_value = Mock(
            inserted_id="return_123"
        )
        
        # Act
        with patch.object(self.return_service, 'db', self.mock_db):
            result = await self.return_service.create_return(
                return_data, 
                "tenant-test"
            )
        
        # Assert
        assert result["return_id"] == "return_123"
        self.mock_db.returns.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_return_validation_error(self):
        """Test return creation with invalid data"""
        invalid_data = {"order_id": ""}  # Missing required fields
        
        with pytest.raises(ValidationError):
            await self.return_service.create_return(
                invalid_data, 
                "tenant-test"
            )

# Integration tests - test_integration/test_returns_api.py
import pytest
from fastapi.testclient import TestClient
from server import app

class TestReturnsAPI:
    def setup_method(self):
        self.client = TestClient(app)
        self.headers = {
            "X-Tenant-Id": "tenant-test",
            "Content-Type": "application/json"
        }
    
    def test_create_return_endpoint(self):
        """Test return creation API endpoint"""
        return_data = {
            "order_id": "5813364687033",
            "customer_email": "test@example.com",
            "return_method": "customer_ships",
            "items": [{
                "line_item_id": "13851721105593",
                "quantity": 1,
                "reason": "defective"
            }]
        }
        
        response = self.client.post(
            "/api/elite/portal/returns/create",
            json=return_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "return_id" in data["return_request"]
```

**Frontend Testing:**
```javascript
// Component tests - src/components/__tests__/ReturnsList.test.jsx
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import ReturnsList from '../ReturnsList';

// Mock API responses
global.fetch = jest.fn();

const mockReturns = [
  {
    id: 'return-123',
    order_number: '1001',
    customer_email: 'test@example.com',
    status: 'requested',
    created_at: '2025-01-11T10:00:00Z'
  }
];

describe('ReturnsList Component', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders returns list successfully', async () => {
    // Mock successful API response
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        returns: mockReturns,
        pagination: { total: 1 }
      })
    });

    render(
      <BrowserRouter>
        <ReturnsList tenantId="tenant-test" />
      </BrowserRouter>
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Order #1001')).toBeInTheDocument();
    });

    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByText('REQUESTED')).toBeInTheDocument();
  });

  test('handles API error gracefully', async () => {
    // Mock API error
    fetch.mockRejectedValueOnce(new Error('Network error'));

    render(
      <BrowserRouter>
        <ReturnsList tenantId="tenant-test" />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to load returns/)).toBeInTheDocument();
    });
  });

  test('filters returns by status', async () => {
    const user = userEvent.setup();

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ returns: mockReturns, pagination: { total: 1 } })
    });

    render(
      <BrowserRouter>
        <ReturnsList tenantId="tenant-test" />
      </BrowserRouter>
    );

    // Click status filter
    const filterButton = screen.getByText('Filter by Status');
    await user.click(filterButton);

    const approvedFilter = screen.getByText('Approved');
    await user.click(approvedFilter);

    // Verify API called with filter
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('status=approved'),
      expect.any(Object)
    );
  });
});

// E2E tests - cypress/integration/returns_flow.spec.js
describe('Returns Creation Flow', () => {
  beforeEach(() => {
    // Setup test data
    cy.intercept('POST', '/api/elite/portal/returns/lookup-order', {
      fixture: 'order-1001.json'
    }).as('lookupOrder');
    
    cy.intercept('POST', '/api/elite/portal/returns/create', {
      fixture: 'return-success.json'
    }).as('createReturn');
  });

  it('completes full return creation flow', () => {
    // Visit customer portal
    cy.visit('/returns/start');

    // Enter order details
    cy.get('[data-testid="order-number-input"]').type('1001');
    cy.get('[data-testid="customer-email-input"]').type('test@example.com');
    cy.get('[data-testid="lookup-order-button"]').click();

    // Wait for order lookup
    cy.wait('@lookupOrder');

    // Select items for return
    cy.get('[data-testid="item-checkbox"]').first().click();
    cy.get('[data-testid="continue-button"]').click();

    // Choose resolution
    cy.get('[data-testid="refund-option"]').click();
    cy.get('[data-testid="continue-button"]').click();

    // Confirm return
    cy.get('[data-testid="submit-return-button"]').click();

    // Wait for return creation
    cy.wait('@createReturn');

    // Verify success page
    cy.get('[data-testid="success-message"]')
      .should('contain', 'Return request submitted successfully');
    cy.get('[data-testid="return-id"]').should('be.visible');
  });
});
```

### Database Migrations

**Migration Script Template:**
```python
# scripts/migrations/001_add_return_status_index.py
"""
Migration: Add index for return status queries
Date: 2025-01-11
Description: Improve performance of status-based return queries
"""

from pymongo import MongoClient
import os

def up():
    """Apply migration"""
    client = MongoClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # Create compound index for better query performance
    db.returns.create_index([
        ("tenant_id", 1),
        ("status", 1), 
        ("created_at", -1)
    ], name="idx_returns_tenant_status_created")
    
    print("✅ Added returns status index")

def down():
    """Rollback migration"""
    client = MongoClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # Drop the index
    db.returns.drop_index("idx_returns_tenant_status_created")
    
    print("✅ Removed returns status index")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        down()
    else:
        up()
```

**Running Migrations:**
```bash
# Apply migration
python scripts/migrations/001_add_return_status_index.py

# Rollback migration  
python scripts/migrations/001_add_return_status_index.py down

# Migration management script
python scripts/migrate.py --up
python scripts/migrate.py --down --target=001
```

### Environment Management

**Environment Files:**
```bash
# .env.example - Template for environment configuration
# Backend Configuration
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_api_secret_NEVER_COMMIT_THIS
APP_URL=https://your-app-domain.com
SHOPIFY_API_VERSION=2024-10

# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=returns_management

# Security
ENCRYPTION_KEY=your_32_byte_encryption_key_GENERATE_NEW

# External Services
RESEND_API_KEY=re_your_email_api_key

# Development
DEBUG=false
LOG_LEVEL=INFO

# .env.local - Local development overrides
DEBUG=true
LOG_LEVEL=DEBUG
MONGO_URL=mongodb://localhost:27017
DB_NAME=returns_management_dev

# .env.staging - Staging environment
DEBUG=false
LOG_LEVEL=INFO
APP_URL=https://staging.your-app.com
DB_NAME=returns_management_staging

# .env.production - Production environment
DEBUG=false
LOG_LEVEL=WARNING
APP_URL=https://app.your-domain.com
DB_NAME=returns_management_production
```

**Environment Validation:**
```python
# config/environment.py
import os
from typing import Optional

class EnvironmentConfig:
    """Environment configuration with validation"""
    
    def __init__(self):
        self.validate_required_vars()
    
    @property
    def shopify_api_key(self) -> str:
        return self._get_required_var('SHOPIFY_API_KEY')
    
    @property
    def shopify_api_secret(self) -> str:
        return self._get_required_var('SHOPIFY_API_SECRET')
    
    @property 
    def encryption_key(self) -> str:
        key = self._get_required_var('ENCRYPTION_KEY')
        if len(key.encode()) != 44:  # Base64 encoded 32 bytes
            raise ValueError("ENCRYPTION_KEY must be 32 bytes (44 chars base64)")
        return key
    
    def _get_required_var(self, var_name: str) -> str:
        value = os.environ.get(var_name)
        if not value:
            raise ValueError(f"Required environment variable {var_name} not set")
        return value
    
    def _get_optional_var(self, var_name: str, default: str = None) -> Optional[str]:
        return os.environ.get(var_name, default)
    
    def validate_required_vars(self):
        """Validate all required environment variables at startup"""
        required_vars = [
            'SHOPIFY_API_KEY',
            'SHOPIFY_API_SECRET', 
            'MONGO_URL',
            'DB_NAME',
            'ENCRYPTION_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

# Usage in main application
config = EnvironmentConfig()
```

### Documentation Standards

**Code Documentation:**
```python
def calculate_refund_amount(
    original_price: Decimal,
    return_policy: Dict,
    condition: str,
    days_since_purchase: int
) -> Decimal:
    """Calculate refund amount based on policy rules.
    
    Applies restocking fees, depreciation, and policy-specific
    adjustments to determine final refund amount.
    
    Args:
        original_price: Original item purchase price
        return_policy: Tenant return policy configuration
        condition: Item condition ('new', 'like_new', 'good', 'poor')
        days_since_purchase: Days elapsed since original purchase
        
    Returns:
        Final refund amount after all deductions
        
    Raises:
        ValueError: If original_price is negative or condition is invalid
        PolicyError: If return policy rules are malformed
        
    Example:
        >>> policy = {"restocking_fee": 0.15, "depreciation_per_day": 0.001}
        >>> calculate_refund_amount(
        ...     Decimal('100.00'), 
        ...     policy, 
        ...     'good', 
        ...     15
        ... )
        Decimal('83.50')
    """
    if original_price < 0:
        raise ValueError("Original price cannot be negative")
    
    valid_conditions = ['new', 'like_new', 'good', 'fair', 'poor']
    if condition not in valid_conditions:
        raise ValueError(f"Invalid condition. Must be one of: {valid_conditions}")
    
    # Apply policy rules
    refund_amount = original_price
    
    # Restocking fee
    if return_policy.get('restocking_fee'):
        fee = original_price * Decimal(str(return_policy['restocking_fee']))
        refund_amount -= fee
    
    # Condition-based deduction
    condition_multipliers = {
        'new': Decimal('1.0'),
        'like_new': Decimal('0.95'), 
        'good': Decimal('0.85'),
        'fair': Decimal('0.70'),
        'poor': Decimal('0.50')
    }
    
    refund_amount *= condition_multipliers[condition]
    
    return max(refund_amount, Decimal('0.00'))
```

**API Documentation:**
```python
@router.post(
    "/create",
    response_model=CreateReturnResponse,
    summary="Create return request",
    description="""
    Create a new return request for an existing order.
    
    This endpoint handles the complete return creation workflow:
    1. Validates order exists and belongs to customer
    2. Checks return eligibility based on policies
    3. Calculates estimated refund amount
    4. Creates return record in database
    5. Triggers notification workflows
    
    **Business Rules:**
    - Returns must be initiated within policy return window
    - Items must be in returnable condition
    - Customer email must match order email
    - Maximum 10 items per return request
    
    **Rate Limits:**
    - 10 requests per minute per tenant
    - 100 requests per day per customer email
    """,
    tags=["Returns", "Customer Portal"],
    responses={
        200: {"description": "Return created successfully"},
        400: {"description": "Invalid request data"},
        404: {"description": "Order not found"},
        409: {"description": "Return already exists for this order"},
        429: {"description": "Rate limit exceeded"}
    }
)
async def create_return(
    request: CreateReturnRequest,
    tenant_id: str = Depends(get_tenant_id)
) -> CreateReturnResponse:
    """Create return request endpoint implementation"""
    pass
```

---

**Next**: See [CHANGELOG.md](./CHANGELOG.md) for version history.