/**
 * Authentication Service - Frontend API Integration
 * Handles all authentication-related API calls to the backend
 */

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

class AuthService {
  constructor() {
    this.baseURL = `${API_BASE_URL}/api/users`;
  }

  /**
   * Get authentication headers with tenant ID
   */
  getHeaders(tenantId = null) {
    const headers = {
      'Content-Type': 'application/json',
    };

    // Add tenant header if provided
    if (tenantId) {
      headers['X-Tenant-Id'] = tenantId;
    } else {
      // Try to get from localStorage
      const storedTenant = localStorage.getItem('currentTenant');
      if (storedTenant) {
        headers['X-Tenant-Id'] = storedTenant;
      }
    }

    // Add authorization header if token exists
    const token = localStorage.getItem('auth_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  /**
   * Handle API response and errors
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

  /**
   * Register new user
   */
  async register(userData) {
    try {
      const response = await fetch(`${this.baseURL}/register`, {
        method: 'POST',
        headers: this.getHeaders(userData.tenant_id),
        body: JSON.stringify(userData)
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  }

  /**
   * Login with email and password
   */
  async login(loginData) {
    console.log('🌐 AuthService.login called with:', loginData);
    try {
      const url = `${this.baseURL}/login`;
      const headers = this.getHeaders(loginData.tenant_id);
      
      console.log('📡 Making request to:', url);
      console.log('📡 Headers:', headers);
      console.log('📡 Body:', JSON.stringify(loginData));

      const response = await fetch(url, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(loginData)
      });

      console.log('📡 Response status:', response.status);
      const result = await this.handleResponse(response);
      console.log('📡 Parsed result:', result);
      return result;
    } catch (error) {
      console.error('❌ AuthService.login error:', error);
      throw error;
    }
  }

  /**
   * Login with Google OAuth
   */
  async loginWithGoogle(oauthData) {
    try {
      const response = await fetch(`${this.baseURL}/login/google`, {
        method: 'POST',
        headers: this.getHeaders(oauthData.tenant_id),
        body: JSON.stringify(oauthData)
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Google OAuth login error:', error);
      throw error;
    }
  }

  /**
   * Logout user
   */
  async logout() {
    try {
      const response = await fetch(`${this.baseURL}/logout`, {
        method: 'POST',
        headers: this.getHeaders()
      });

      if (response.ok) {
        // Clear local storage
        this.clearAuthData();
      }

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Logout error:', error);
      // Clear local storage even if API call fails
      this.clearAuthData();
      throw error;
    }
  }

  /**
   * Get current user profile
   */
  async getCurrentUser() {
    try {
      const response = await fetch(`${this.baseURL}/me`, {
        method: 'GET',
        headers: this.getHeaders()
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  }

  /**
   * Update current user profile
   */
  async updateProfile(userData) {
    try {
      const response = await fetch(`${this.baseURL}/me`, {
        method: 'PUT',
        headers: this.getHeaders(),
        body: JSON.stringify(userData)
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Update profile error:', error);
      throw error;
    }
  }

  /**
   * Change password
   */
  async changePassword(passwordData) {
    try {
      const response = await fetch(`${this.baseURL}/me/change-password`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(passwordData)
      });

      return await this.handleResponse(response);
    } catch (error) {
      console.error('Change password error:', error);
      throw error;
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    const token = localStorage.getItem('auth_token');
    if (!token) return false;

    try {
      // Basic JWT expiry check (decode without verification)
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      
      return payload.exp > currentTime;
    } catch (error) {
      console.error('Token validation error:', error);
      return false;
    }
  }

  /**
   * Get current user info from localStorage
   */
  getCurrentUserFromStorage() {
    try {
      const userInfo = localStorage.getItem('user_info');
      return userInfo ? JSON.parse(userInfo) : null;
    } catch (error) {
      console.error('Error getting user from storage:', error);
      return null;
    }
  }

  /**
   * Get current tenant from localStorage
   */
  getCurrentTenantFromStorage() {
    return localStorage.getItem('currentTenant');
  }

  /**
   * Clear authentication data from localStorage
   */
  clearAuthData() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_info');
    localStorage.removeItem('currentTenant');
  }

  /**
   * Get authentication token from localStorage or cookies (for impersonation)
   */
  getToken() {
    // First check localStorage for regular auth token
    const localToken = localStorage.getItem('auth_token');
    if (localToken) {
      return localToken;
    }
    
    // Check for impersonation session token in cookies
    const cookies = document.cookie.split(';').reduce((acc, cookie) => {
      const [key, value] = cookie.trim().split('=');
      acc[key] = value;
      return acc;
    }, {});
    
    return cookies.session_token || null;
  }

  /**
   * Check if current session is an impersonation session
   */
  isImpersonationSession() {
    const cookies = document.cookie.split(';').reduce((acc, cookie) => {
      const [key, value] = cookie.trim().split('=');
      acc[key] = value;
      return acc;
    }, {});
    
    return !!cookies.session_token;
  }

  /**
   * Get impersonation info from session token
   */
  getImpersonationInfo() {
    const cookies = document.cookie.split(';').reduce((acc, cookie) => {
      const [key, value] = cookie.trim().split('=');
      acc[key] = value;
      return acc;
    }, {});
    
    if (cookies.session_token) {
      try {
        // Decode JWT token (note: this is not secure validation, just for display)
        const payload = JSON.parse(atob(cookies.session_token.split('.')[1]));
        return {
          isImpersonating: payload.act === 'impersonate',
          tenantId: payload.tenant_id,
          originalAdminEmail: payload.orig_email,
          originalUserId: payload.orig_user_id
        };
      } catch (error) {
        console.error('Error decoding impersonation token:', error);
        return { isImpersonating: false };
      }
    }
    
    return { isImpersonating: false };
  }

  /**
   * Validate authentication token
   */
  async validateToken() {
    if (!this.isAuthenticated()) {
      return false;
    }

    try {
      await this.getCurrentUser();
      return true;
    } catch (error) {
      // Token is invalid, clear auth data
      this.clearAuthData();
      return false;
    }
  }

  /**
   * Refresh authentication token
   */
  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await fetch(`${this.baseURL}/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refresh_token: refreshToken
        })
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      
      // Update stored tokens
      localStorage.setItem('auth_token', data.access_token);
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }

      return data;
    } catch (error) {
      console.error('Token refresh error:', error);
      this.clearAuthData();
      throw error;
    }
  }
}

// Export singleton instance
export const authService = new AuthService();
export default authService;