# Returns Management SaaS - Test Suite

## Overview

Comprehensive test suite for the Returns Management SaaS MVP, covering unit tests, integration tests, and end-to-end testing.

## Test Structure

```
/tests/
├── conftest.py           # Test configuration and fixtures
├── unit/                 # Unit tests for individual services
│   ├── test_tenant_service.py
│   ├── test_rules_service.py  
│   ├── test_returns_service.py
│   └── test_analytics_service.py
└── integration/          # Integration tests for full workflows
    └── test_return_workflow.py
```

## Running Tests

### Prerequisites

1. **MongoDB**: Ensure MongoDB is running locally for tests
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 mongo:latest
   
   # Or install MongoDB locally
   ```

2. **Python Dependencies**: Install test dependencies
   ```bash
   cd /app/backend
   pip install pytest pytest-asyncio motor
   ```

### Run All Tests

```bash
cd /app
python -m pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only  
python -m pytest tests/integration/ -v

# Specific test file
python -m pytest tests/unit/test_tenant_service.py -v

# Specific test method
python -m pytest tests/unit/test_tenant_service.py::TestTenantService::test_create_tenant_success -v
```

### Test Coverage

```bash
# Install coverage
pip install pytest-cov

# Run tests with coverage
python -m pytest tests/ --cov=backend/src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Configuration

### Environment Variables

Tests use a separate test database to avoid affecting development data:
- **TEST_MONGO_URL**: `mongodb://localhost:27017`
- **TEST_DB_NAME**: `test_returns_management`

### Fixtures

Common test fixtures are defined in `conftest.py`:
- `test_db`: Clean test database connection
- `sample_tenant_data`: Sample tenant for testing
- `sample_product_data`: Sample product for testing
- `sample_order_data`: Sample order for testing
- `sample_return_data`: Sample return request for testing
- `sample_rule_data`: Sample return rule for testing

## Test Categories

### 1. Unit Tests (`/tests/unit/`)

Test individual service classes in isolation:

**TenantService Tests:**
- ✅ Create tenant with default settings
- ✅ Get tenant by ID
- ✅ Update tenant information
- ✅ Update tenant settings
- ✅ Verify tenant existence
- ✅ Deactivate tenant

**RulesService Tests:**
- ✅ Create return rules
- ✅ Get tenant rules (sorted by priority)
- ✅ Apply rules for auto-approval
- ✅ Apply rules for expired returns
- ✅ Deactivate rules

**ReturnsService Tests:**
- ✅ Create return requests
- ✅ Get returns by tenant
- ✅ Update return status
- ✅ Filter returns by status
- ✅ Get customer returns
- ✅ Search returns

**AnalyticsService Tests:**
- ✅ Calculate tenant analytics
- ✅ Generate return trends
- ✅ Handle empty data sets
- ✅ Custom time periods

### 2. Integration Tests (`/tests/integration/`)

Test complete business workflows:

**Return Workflow Tests:**
- ✅ End-to-end return creation and processing
- ✅ Rules engine integration
- ✅ Status transitions
- ✅ Analytics updates

### 3. API Tests

Backend API endpoint testing is handled by the comprehensive test suite in `/app/backend_test.py`.

## Writing New Tests

### Unit Test Template

```python
import pytest
import pytest_asyncio

class TestYourService:
    @pytest_asyncio.fixture
    async def your_service(self, test_db):
        return YourService(test_db)
    
    async def test_your_method(self, your_service):
        # Arrange
        # Act  
        # Assert
        pass
```

### Best Practices

1. **Isolation**: Each test should be independent
2. **Clean Up**: Use fixtures to ensure clean test state
3. **Descriptive Names**: Test names should describe what is being tested
4. **AAA Pattern**: Arrange, Act, Assert structure
5. **Edge Cases**: Test both success and failure scenarios
6. **Async Testing**: Use `pytest_asyncio` for async service methods

## Continuous Integration

Tests are designed to run in CI/CD pipelines with:
- Automatic test database cleanup
- Proper async handling
- Comprehensive error reporting
- Coverage metrics

## Test Data

All test data is generated using fixtures to ensure:
- Consistent test conditions
- Easy maintenance
- No dependency on external data
- Proper cleanup after tests