#!/usr/bin/env python3
"""
Documentation Validation Script

Validates that documentation is consistent with the codebase:
- Ensures all API endpoints mentioned in docs actually exist
- Validates that referenced file paths exist
- Checks for broken internal links
- Verifies Mermaid diagram syntax

Usage:
    python scripts/docs_validate.py
    make docs:check
    npm run docs:check
"""

import os
import sys
import re
import json
import asyncio
import glob
from pathlib import Path
from typing import List, Dict, Set, Tuple
import importlib.util

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message: str, status: str = "INFO"):
    """Print colored status message"""
    color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
    print(f"{color}[{status}]{Colors.END} {message}")

class DocumentationValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.docs_dir = self.project_root / "docs"
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        
        self.errors = []
        self.warnings = []
        
    def validate_all(self) -> bool:
        """Run all validation checks"""
        print(f"{Colors.BOLD}🔍 Starting Documentation Validation{Colors.END}\n")
        
        # Check if docs directory exists
        if not self.docs_dir.exists():
            print_status("Documentation directory not found", "FAIL")
            return False
        
        # Run validation checks
        self.validate_file_references()
        self.validate_api_endpoints()
        self.validate_internal_links()
        self.validate_mermaid_diagrams()
        self.validate_component_references()
        
        # Print summary
        self.print_summary()
        
        return len(self.errors) == 0
    
    def validate_file_references(self):
        """Validate that all file paths mentioned in docs exist"""
        print_status("Validating file path references...")
        
        # Pattern to match file paths in documentation
        file_path_patterns = [
            r'`([^`]+\.(py|js|jsx|ts|tsx|json|md|yml|yaml))`',
            r'`([^`]+/[^`]+)`',
            r'File: `([^`]+)`',
            r'Component: `([^`]+)`',
            r'src/([a-zA-Z0-9_/.-]+\.(py|js|jsx|ts|tsx))',
        ]
        
        for doc_file in self.docs_dir.glob("*.md"):
            content = doc_file.read_text()
            
            for pattern in file_path_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    file_path = match if isinstance(match, str) else match[0]
                    
                    # Skip obvious placeholders or examples
                    if any(placeholder in file_path.lower() for placeholder in [
                        'your-', 'example', 'placeholder', 'template', 'sample'
                    ]):
                        continue
                    
                    # Try different possible locations
                    possible_paths = [
                        self.project_root / file_path,
                        self.backend_dir / file_path,
                        self.frontend_dir / file_path,
                        self.backend_dir / "src" / file_path,
                        self.frontend_dir / "src" / file_path,
                    ]
                    
                    if not any(p.exists() for p in possible_paths):
                        self.errors.append(f"File not found: {file_path} (referenced in {doc_file.name})")
        
        print_status(f"File reference validation completed", "PASS" if not self.errors else "FAIL")
    
    def validate_api_endpoints(self):
        """Validate that API endpoints in docs exist in the backend"""
        print_status("Validating API endpoint references...")
        
        # Extract API endpoints from documentation
        documented_endpoints = self.extract_documented_endpoints()
        
        # Extract actual endpoints from FastAPI controllers
        actual_endpoints = self.extract_actual_endpoints()
        
        # Check for mismatches
        for endpoint in documented_endpoints:
            method, path = endpoint
            if endpoint not in actual_endpoints:
                # Try to find similar endpoints
                similar = self.find_similar_endpoint(endpoint, actual_endpoints)
                if similar:
                    self.warnings.append(f"Endpoint {method} {path} not found, did you mean {similar[0]} {similar[1]}?")
                else:
                    self.errors.append(f"Documented endpoint not found in code: {method} {path}")
        
        print_status(f"Found {len(documented_endpoints)} documented endpoints, {len(actual_endpoints)} actual endpoints")
    
    def extract_documented_endpoints(self) -> Set[Tuple[str, str]]:
        """Extract API endpoints mentioned in documentation"""
        endpoints = set()
        
        # Pattern to match HTTP methods and paths
        endpoint_patterns = [
            r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}:]+)',
            r'`(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}:]+)`',
            r'curl.*?-X\s+(GET|POST|PUT|DELETE|PATCH).*?"([^"]*)"',
            r'fetch\([\'"]([/\w\-\{\}:]+)[\'"].*method:\s*[\'"](\w+)[\'"]',
        ]
        
        for doc_file in self.docs_dir.glob("*.md"):
            content = doc_file.read_text()
            
            for pattern in endpoint_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        method, path = match
                        if isinstance(method, str) and isinstance(path, str):
                            # Normalize path
                            path = path.strip().rstrip('/')
                            if path.startswith('/api'):
                                endpoints.add((method.upper(), path))
        
        return endpoints
    
    def extract_actual_endpoints(self) -> Set[Tuple[str, str]]:
        """Extract actual API endpoints from FastAPI controllers"""
        endpoints = set()
        
        # Find all controller files
        controller_files = list((self.backend_dir / "src" / "controllers").glob("*.py"))
        
        for controller_file in controller_files:
            try:
                content = controller_file.read_text()
                
                # Pattern to match FastAPI route decorators
                route_pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
                matches = re.findall(route_pattern, content, re.IGNORECASE)
                
                for method, path in matches:
                    # Convert relative paths to absolute API paths
                    if not path.startswith('/'):
                        path = '/' + path
                    
                    # Prefix with /api if not already present
                    if not path.startswith('/api'):
                        path = '/api' + path
                    
                    endpoints.add((method.upper(), path))
                    
            except Exception as e:
                self.warnings.append(f"Could not parse {controller_file.name}: {e}")
        
        return endpoints
    
    def find_similar_endpoint(self, endpoint: Tuple[str, str], actual_endpoints: Set[Tuple[str, str]]) -> Tuple[str, str]:
        """Find similar endpoint in actual endpoints"""
        method, path = endpoint
        
        for actual_method, actual_path in actual_endpoints:
            # Check for exact method match and similar path
            if method == actual_method:
                # Remove path parameters for comparison
                norm_path = re.sub(r'\{[^}]+\}', '{id}', path)
                norm_actual = re.sub(r'\{[^}]+\}', '{id}', actual_path)
                
                if norm_path == norm_actual:
                    return (actual_method, actual_path)
        
        return None
    
    def validate_internal_links(self):
        """Validate internal links between documentation files"""
        print_status("Validating internal documentation links...")
        
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        for doc_file in self.docs_dir.glob("*.md"):
            content = doc_file.read_text()
            matches = re.findall(link_pattern, content)
            
            for link_text, link_url in matches:
                # Skip external links
                if link_url.startswith('http') or link_url.startswith('mailto'):
                    continue
                
                # Handle relative links
                if link_url.startswith('./'):
                    target_file = doc_file.parent / link_url[2:]
                elif link_url.startswith('../'):
                    target_file = doc_file.parent / link_url
                else:
                    target_file = doc_file.parent / link_url
                
                # Remove anchor if present
                if '#' in str(target_file):
                    target_file = Path(str(target_file).split('#')[0])
                
                if not target_file.exists():
                    self.errors.append(f"Broken link in {doc_file.name}: {link_url}")
        
        print_status("Internal link validation completed")
    
    def validate_mermaid_diagrams(self):
        """Validate Mermaid diagram syntax"""
        print_status("Validating Mermaid diagram syntax...")
        
        mermaid_pattern = r'```mermaid\n(.*?)\n```'
        
        for doc_file in self.docs_dir.glob("*.md"):
            content = doc_file.read_text()
            matches = re.findall(mermaid_pattern, content, re.DOTALL)
            
            for diagram in matches:
                # Basic syntax validation
                if not self.validate_mermaid_syntax(diagram):
                    self.errors.append(f"Invalid Mermaid syntax in {doc_file.name}")
        
        print_status("Mermaid diagram validation completed")
    
    def validate_mermaid_syntax(self, diagram: str) -> bool:
        """Basic Mermaid syntax validation"""
        diagram = diagram.strip()
        
        # Check for common diagram types
        valid_starts = [
            'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
            'stateDiagram', 'erDiagram', 'journey', 'gantt'
        ]
        
        if not any(diagram.startswith(start) for start in valid_starts):
            return False
        
        # Check for balanced brackets
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for char in diagram:
            if char in brackets:
                stack.append(brackets[char])
            elif char in brackets.values():
                if not stack or stack.pop() != char:
                    return False
        
        return len(stack) == 0
    
    def validate_component_references(self):
        """Validate React component references in frontend documentation"""
        print_status("Validating React component references...")
        
        # Extract component names from documentation
        component_pattern = r'`([A-Z][a-zA-Z0-9_]*(?:\.jsx?)?)`'
        
        # Find actual components
        actual_components = set()
        if self.frontend_dir.exists():
            for comp_file in (self.frontend_dir / "src").rglob("*.jsx"):
                # Extract component name from filename
                component_name = comp_file.stem
                actual_components.add(component_name)
                actual_components.add(f"{component_name}.jsx")
        
        for doc_file in self.docs_dir.glob("*.md"):
            content = doc_file.read_text()
            matches = re.findall(component_pattern, content)
            
            for component in matches:
                # Skip obvious non-components
                if component.lower() in ['react', 'component', 'props', 'state']:
                    continue
                
                # Check if component exists
                clean_name = component.replace('.jsx', '').replace('.js', '')
                if (clean_name not in actual_components and 
                    component not in actual_components and
                    f"{clean_name}.jsx" not in actual_components):
                    self.warnings.append(f"Component reference not found: {component} (in {doc_file.name})")
        
        print_status("Component reference validation completed")
    
    def print_summary(self):
        """Print validation summary"""
        print(f"\n{Colors.BOLD}📊 Validation Summary{Colors.END}")
        print(f"{'='*50}")
        
        if not self.errors and not self.warnings:
            print_status("All validation checks passed! ✨", "PASS")
        else:
            if self.errors:
                print(f"\n{Colors.RED}❌ Errors ({len(self.errors)}):{Colors.END}")
                for i, error in enumerate(self.errors, 1):
                    print(f"  {i}. {error}")
            
            if self.warnings:
                print(f"\n{Colors.YELLOW}⚠️  Warnings ({len(self.warnings)}):{Colors.END}")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"  {i}. {warning}")
        
        print(f"\n{Colors.BOLD}Results:{Colors.END}")
        print(f"  • Errors: {Colors.RED}{len(self.errors)}{Colors.END}")
        print(f"  • Warnings: {Colors.YELLOW}{len(self.warnings)}{Colors.END}")
        print(f"  • Status: {'✅ PASS' if len(self.errors) == 0 else '❌ FAIL'}")

def main():
    """Main validation function"""
    validator = DocumentationValidator()
    
    try:
        success = validator.validate_all()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Validation interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_status(f"Validation failed with error: {e}", "FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main()