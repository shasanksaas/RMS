# Returns Management SaaS - Development Makefile
# Last updated: 2025-01-11

.PHONY: help install dev test lint format docs clean deploy

# Default target
help:
	@echo "🚀 Returns Management SaaS - Development Commands"
	@echo "================================================="
	@echo ""
	@echo "📦 Setup & Installation:"
	@echo "  make install         Install all dependencies (backend + frontend)"
	@echo "  make install-backend Install backend Python dependencies"
	@echo "  make install-frontend Install frontend Node.js dependencies"
	@echo ""
	@echo "🏃 Development:"
	@echo "  make dev             Start development servers (backend + frontend)"
	@echo "  make dev-backend     Start backend development server only"
	@echo "  make dev-frontend    Start frontend development server only"
	@echo "  make services        Show supervisor service status"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test            Run all tests (backend + frontend)"
	@echo "  make test-backend    Run backend tests only"
	@echo "  make test-frontend   Run frontend tests only"
	@echo "  make lint            Run linting on all code"
	@echo "  make format          Format all code (black, prettier)"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  make docs:check      Validate documentation consistency"
	@echo "  make docs:serve      Serve documentation locally"
	@echo "  make docs:build      Build documentation"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean           Clean temporary files and caches"
	@echo "  make reset           Reset development environment"
	@echo "  make logs            Show application logs"
	@echo ""
	@echo "🚢 Deployment:"
	@echo "  make deploy-staging  Deploy to staging environment"
	@echo "  make deploy-prod     Deploy to production environment"

# Installation targets
install: install-backend install-frontend
	@echo "✅ All dependencies installed"

install-backend:
	@echo "📦 Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "✅ Backend dependencies installed"

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd frontend && yarn install
	@echo "✅ Frontend dependencies installed"

# Development targets
dev:
	@echo "🏃 Starting development environment..."
	@echo "Backend will be available at: http://localhost:8001"
	@echo "Frontend will be available at: http://localhost:3000" 
	@echo "Press Ctrl+C to stop all servers"
	@trap 'kill %1 %2; wait' INT; \
	make dev-backend & \
	make dev-frontend & \
	wait

dev-backend:
	@echo "🐍 Starting backend server..."
	cd backend && python server.py

dev-frontend:
	@echo "⚛️  Starting frontend server..."
	cd frontend && yarn start

services:
	@echo "📊 Service Status:"
	@sudo supervisorctl status

# Testing targets
test: test-backend test-frontend
	@echo "✅ All tests completed"

test-backend:
	@echo "🧪 Running backend tests..."
	cd backend && python -m pytest tests/ -v --cov=src/ --cov-report=term-missing

test-frontend:
	@echo "🧪 Running frontend tests..."
	cd frontend && yarn test --coverage --watchAll=false

# Code quality targets
lint: lint-backend lint-frontend
	@echo "✅ Linting completed"

lint-backend:
	@echo "🔍 Linting backend code..."
	cd backend && flake8 src/ --max-line-length=88 --extend-ignore=E203
	cd backend && mypy src/ --ignore-missing-imports

lint-frontend:
	@echo "🔍 Linting frontend code..."
	cd frontend && yarn lint

format: format-backend format-frontend
	@echo "✨ Code formatting completed"

format-backend:
	@echo "🎨 Formatting backend code..."
	cd backend && black --line-length=88 src/
	cd backend && isort src/ --profile=black

format-frontend:
	@echo "🎨 Formatting frontend code..."
	cd frontend && yarn prettier --write src/

# Documentation targets
docs\:check:
	@echo "📚 Validating documentation..."
	python scripts/docs_validate.py

docs\:serve:
	@echo "📖 Serving documentation locally..."
	@echo "Documentation will be available at: http://localhost:8080"
	cd docs && python -m http.server 8080

docs\:build:
	@echo "📚 Building documentation..."
	@# Add documentation build process here if needed
	@echo "✅ Documentation built"

# Maintenance targets  
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	cd frontend && rm -rf node_modules/.cache 2>/dev/null || true
	cd backend && rm -rf .coverage htmlcov/ 2>/dev/null || true
	@echo "✅ Cleanup completed"

reset: clean
	@echo "🔄 Resetting development environment..."
	cd frontend && rm -rf node_modules && yarn install
	cd backend && pip install -r requirements.txt --force-reinstall
	@echo "✅ Environment reset completed"

logs:
	@echo "📋 Application Logs:"
	@echo "==================="
	@echo "Backend Error Logs:"
	@tail -n 50 /var/log/supervisor/backend.err.log 2>/dev/null || echo "No backend error logs found"
	@echo ""
	@echo "Backend Output Logs:"
	@tail -n 50 /var/log/supervisor/backend.out.log 2>/dev/null || echo "No backend output logs found"
	@echo ""
	@echo "Frontend Error Logs:"
	@tail -n 50 /var/log/supervisor/frontend.err.log 2>/dev/null || echo "No frontend error logs found"

# Database targets
db\:migrate:
	@echo "🗄️  Running database migrations..."
	cd backend && python scripts/migrate.py --up
	@echo "✅ Migrations completed"

db\:seed:
	@echo "🌱 Seeding database with test data..."
	cd backend && python scripts/seed_data.py
	@echo "✅ Database seeded"

db\:reset:
	@echo "🔄 Resetting database..."
	cd backend && python scripts/reset_db.py
	@echo "✅ Database reset completed"

# Health check targets
health:
	@echo "🏥 Health Check:"
	@echo "================"
	@echo "Backend Health:"
	@curl -s http://localhost:8001/api/health | jq '.' 2>/dev/null || curl -s http://localhost:8001/api/health || echo "❌ Backend not responding"
	@echo ""
	@echo "Database Connection:"
	@cd backend && python -c "from src.database import database; import asyncio; print('✅ Database connected' if asyncio.run(database.ping()) else '❌ Database connection failed')" 2>/dev/null || echo "❌ Database connection failed"

# Development utilities
shell\:backend:
	@echo "🐍 Starting backend Python shell..."
	cd backend && python -c "from src.database import *; import asyncio; print('Backend shell ready. Database available as db.')"

shell\:db:
	@echo "🗄️  Starting MongoDB shell..."
	mongo returns_management

# Deployment targets (customize for your deployment setup)
deploy-staging:
	@echo "🚀 Deploying to staging..."
	@echo "⚠️  This is a placeholder - implement your staging deployment process"
	@# git push staging main
	@# kubectl apply -f k8s/staging/
	@echo "✅ Staging deployment completed"

deploy-prod:
	@echo "🚀 Deploying to production..."
	@echo "⚠️  This is a placeholder - implement your production deployment process"
	@echo "🛡️  Production deployment requires additional safety checks"
	@# Implement production deployment with proper checks
	@echo "✅ Production deployment completed"

# Environment setup
env\:setup:
	@echo "⚙️  Setting up environment files..."
	@if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env; echo "Created backend/.env"; fi
	@if [ ! -f frontend/.env ]; then cp frontend/.env.example frontend/.env; echo "Created frontend/.env"; fi
	@echo "✅ Environment setup completed"
	@echo "📝 Please edit .env files with your configuration"

# Quick commands
quick\:test:
	@echo "🚀 Quick Test Suite:"
	@cd backend && python -m pytest tests/test_health.py -v
	@cd frontend && yarn test --watchAll=false src/App.test.js
	@echo "✅ Quick tests completed"

quick\:lint:
	@echo "🔍 Quick Lint Check:"
	@cd backend && flake8 src/ --select=E9,F63,F7,F82 --show-source --statistics
	@cd frontend && yarn lint --max-warnings=0
	@echo "✅ Quick lint completed"

# Monitoring
monitor:
	@echo "📊 System Monitor:"
	@echo "=================="
	@echo "CPU Usage:"
	@top -bn1 | grep "Cpu(s)" | awk '{print $2 " " $4}' || echo "CPU info not available"
	@echo "Memory Usage:"
	@free -h | grep "^Mem" || echo "Memory info not available"
	@echo "Disk Usage:"
	@df -h / | tail -1 | awk '{print $5 " used"}' || echo "Disk info not available"
	@echo "Process Status:"
	@ps aux | grep -E "(python|node)" | head -5 || echo "No processes found"