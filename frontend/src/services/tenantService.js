/**
 * Tenant Management Service - Real API Integration
 * Handles real tenant CRUD operations and admin impersonation
 * NO MOCK DATA - All operations hit live backend APIs
 */

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

class TenantService {
  constructor() {
    this.baseURL = `${API_BASE_URL}/api`;
  }

  /**
   * Get authentication headers for API calls
   */
  getHeaders(includeAuth = true) {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (includeAuth) {
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  /**
   * Handle API responses with comprehensive error handling
   */
  async handleResponse(response) {
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      const errorMessage = error.detail || error.message || `HTTP ${response.status}`;
      
      const customError = new Error(errorMessage);
      customError.status = response.status;
      customError.response = error;
      
      throw customError;
    }

    return response.json();
  }

  // ===== REAL ADMIN TENANT MANAGEMENT APIs =====

  /**
   * List all tenants from database (Admin only, NO MOCKS)
   */
  async listTenants(page = 1, pageSize = 50, status = null) {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString()
      });
      
      if (status) {
        params.append('status', status);
      }

      const response = await fetch(`${this.baseURL}/admin/tenants?${params}`, {
        method: 'GET',
        headers: this.getHeaders()
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('List tenants error:', error);
      throw error;
    }
  }

  /**
   * Create new tenant (Admin only)
   */
  async createTenant(tenantData) {
    try {
      const response = await fetch(`${this.baseURL}/admin/tenants`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(tenantData)
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Create tenant error:', error);
      throw error;
    }
  }

  /**
   * Delete/archive tenant (Admin only)
   */
  async deleteTenant(tenantId) {
    try {
      const response = await fetch(`${this.baseURL}/admin/tenants/${tenantId}`, {
        method: 'DELETE',
        headers: this.getHeaders()
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Delete tenant error:', error);
      throw error;
    }
  }

  /**
   * Admin impersonation - Direct login to tenant dashboard
   */
  async impersonateTenant(tenantId) {
    try {
      const response = await fetch(`${this.baseURL}/admin/tenants/${tenantId}/impersonate`, {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include'  // Include cookies for session
      });

      // This endpoint returns a redirect, so we handle it differently
      if (response.redirected) {
        // Browser will follow redirect automatically
        window.location.href = response.url;
        return { success: true, redirected: true };
      }

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Impersonate tenant error:', error);
      throw error;
    }
  }

  /**
   * End admin impersonation session
   */
  async endImpersonation() {
    try {
      const response = await fetch(`${this.baseURL}/admin/tenants/end-impersonation`, {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include'
      });

      if (response.redirected) {
        window.location.href = response.url;
        return { success: true, redirected: true };
      }

      return await this.handleResponse(response);
    } catch (error) {
      console.error('End impersonation error:', error);
      throw error;
    }
  }

  /**
   * Get tenant details (Admin only)
   */
  async getTenantById(tenantId) {
    try {
      const response = await fetch(`${this.baseURL}/tenants/${tenantId}`, {
        method: 'GET',
        headers: this.getHeaders()
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Get tenant error:', error);
      throw error;
    }
  }

  /**
   * Update tenant (Admin only)
   */
  async updateTenant(tenantId, updateData) {
    try {
      const response = await fetch(`${this.baseURL}/tenants/${tenantId}`, {
        method: 'PUT',
        headers: this.getHeaders(),
        body: JSON.stringify(updateData)
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Update tenant error:', error);
      throw error;
    }
  }

  /**
   * Archive tenant (Admin only)
   */
  async archiveTenant(tenantId) {
    try {
      const response = await fetch(`${this.baseURL}/tenants/${tenantId}/archive`, {
        method: 'POST',
        headers: this.getHeaders()
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Archive tenant error:', error);
      throw error;
    }
  }

  /**
   * Reactivate tenant (Admin only)
   */
  async reactivateTenant(tenantId) {
    try {
      const response = await fetch(`${this.baseURL}/tenants/${tenantId}/reactivate`, {
        method: 'POST',
        headers: this.getHeaders()
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Reactivate tenant error:', error);
      throw error;
    }
  }

  /**
   * Get tenant connection status (Admin only)
   */
  async getTenantConnectionStatus(tenantId) {
    try {
      const response = await fetch(`${this.baseURL}/tenants/${tenantId}/connection`, {
        method: 'GET',
        headers: this.getHeaders()
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Get tenant connection error:', error);
      throw error;
    }
  }

  /**
   * Get tenant statistics (Admin only)
   */
  async getTenantStats(tenantId) {
    try {
      const response = await fetch(`${this.baseURL}/tenants/${tenantId}/stats`, {
        method: 'GET',
        headers: this.getHeaders()
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Get tenant stats error:', error);
      throw error;
    }
  }

  // ===== PUBLIC MERCHANT SIGNUP APIs =====

  /**
   * Check if tenant_id is valid for signup (Public)
   */
  async checkTenantStatus(tenantId) {
    try {
      const response = await fetch(`${this.baseURL}/auth/tenant-status/${tenantId}`, {
        method: 'GET',
        headers: this.getHeaders(false) // No auth required
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Check tenant status error:', error);
      throw error;
    }
  }

  /**
   * Get tenant signup information (Public)
   */
  async getTenantSignupInfo(tenantId) {
    try {
      const response = await fetch(`${this.baseURL}/auth/signup-info/${tenantId}`, {
        method: 'GET',
        headers: this.getHeaders(false) // No auth required
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Get tenant signup info error:', error);
      throw error;
    }
  }

  /**
   * Merchant signup with tenant_id (Public)
   */
  async merchantSignup(signupData) {
    try {
      const response = await fetch(`${this.baseURL}/auth/merchant-signup`, {
        method: 'POST',
        headers: this.getHeaders(false), // No auth required
        body: JSON.stringify(signupData)
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Merchant signup error:', error);
      throw error;
    }
  }

  // ===== UTILITY METHODS =====

  /**
   * Validate tenant_id format
   */
  validateTenantId(tenantId) {
    const tenantIdPattern = /^tenant-[a-z0-9-]+$/;
    return tenantIdPattern.test(tenantId);
  }

  /**
   * Generate tenant_id suggestion
   */
  generateTenantId(storeName) {
    if (!storeName) return '';
    
    // Convert to lowercase, replace spaces/special chars with hyphens
    const slug = storeName
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .substring(0, 20);
    
    // Add random suffix for uniqueness
    const randomSuffix = Math.random().toString(36).substring(2, 8);
    
    return `tenant-${slug}-${randomSuffix}`;
  }

  /**
   * Format tenant status for display
   */
  formatTenantStatus(status) {
    const statusMap = {
      'new': { label: 'New', color: 'blue', description: 'Tenant created, awaiting first merchant' },
      'claimed': { label: 'Claimed', color: 'green', description: 'First merchant signed up' },
      'active': { label: 'Active', color: 'green', description: 'Tenant active with users' },
      'suspended': { label: 'Suspended', color: 'yellow', description: 'Temporarily suspended' },
      'archived': { label: 'Archived', color: 'gray', description: 'No longer active' }
    };
    
    return statusMap[status] || { label: status, color: 'gray', description: '' };
  }

  /**
   * Check if user can manage tenants
   */
  canManageTenants() {
    const userInfo = localStorage.getItem('user_info');
    if (!userInfo) return false;
    
    try {
      const user = JSON.parse(userInfo);
      return user.role === 'admin';
    } catch (error) {
      return false;
    }
  }

  /**
   * Get current user's tenant context
   */
  getCurrentTenant() {
    const userInfo = localStorage.getItem('user_info');
    const tenantId = localStorage.getItem('currentTenant');
    
    if (!userInfo || !tenantId) return null;
    
    try {
      const user = JSON.parse(userInfo);
      return {
        tenant_id: tenantId,
        user_role: user.role,
        user_email: user.email
      };
    } catch (error) {
      return null;
    }
  }
}

// Export singleton instance
export const tenantService = new TenantService();
export default tenantService;