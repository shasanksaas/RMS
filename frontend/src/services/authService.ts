/**
 * Authentication Service - Production Ready
 * Handles all authentication flows with comprehensive error handling
 * Integrates with backend user management APIs
 */

import axios, { AxiosResponse, AxiosError } from 'axios';
import { toast } from '../components/ui/use-toast';

// Types
export interface LoginRequest {
  tenant_id: string;
  email: string;
  password: string;
  remember_me: boolean;
}

export interface GoogleOAuthRequest {
  tenant_id: string;
  auth_code: string;
  role?: 'merchant' | 'customer' | 'admin';
}

export interface RegisterRequest {
  tenant_id: string;
  email: string;
  password: string;
  confirm_password: string;
  role: 'merchant' | 'customer' | 'admin';
  first_name?: string;
  last_name?: string;
  auth_provider?: 'email' | 'google' | 'shopify';
}

export interface UserResponse {
  user_id: string;
  tenant_id: string;
  email: string;
  role: 'merchant' | 'customer' | 'admin';
  auth_provider: 'email' | 'google' | 'shopify';
  permissions: string[];
  is_active: boolean;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  profile_image_url?: string;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
}

export interface UserUpdateRequest {
  email?: string;
  first_name?: string;
  last_name?: string;
  permissions?: string[];
  is_active?: boolean;
  profile_image_url?: string;
  metadata?: Record<string, any>;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface UserListResponse {
  users: UserResponse[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// API Configuration
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Axios instance with interceptors
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add authentication headers
apiClient.interceptors.request.use(
  (config) => {
    // Add tenant ID header
    const tenantId = localStorage.getItem('currentTenant');
    if (tenantId) {
      config.headers['X-Tenant-Id'] = tenantId;
    }

    // Add authentication token
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor - Handle global errors and token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // Handle different error types
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as any;

      switch (status) {
        case 401:
          // Unauthorized - token expired or invalid
          if (!originalRequest._retry) {
            originalRequest._retry = true;
            
            // Try to refresh token
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              try {
                const refreshResponse = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
                  refresh_token: refreshToken
                });
                
                const newToken = refreshResponse.data.access_token;
                localStorage.setItem('auth_token', newToken);
                
                // Retry original request with new token
                originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
                return apiClient(originalRequest);
              } catch (refreshError) {
                // Refresh failed, redirect to login
                authService.logout();
                window.location.href = '/auth/login';
                return Promise.reject(refreshError);
              }
            } else {
              // No refresh token, redirect to login
              authService.logout();
              window.location.href = '/auth/login';
            }
          }
          break;

        case 403:
          // Forbidden - insufficient permissions
          toast({
            title: 'Access Denied',
            description: data.detail || 'You do not have permission to perform this action.',
            variant: 'destructive'
          });
          break;

        case 404:
          // Not found
          console.error('Resource not found:', error.config?.url);
          break;

        case 409:
          // Conflict - usually duplicate data
          toast({
            title: 'Conflict',
            description: data.detail || 'The resource already exists.',
            variant: 'destructive'
          });
          break;

        case 429:
          // Rate limiting
          toast({
            title: 'Rate Limited',
            description: 'Too many requests. Please try again later.',
            variant: 'destructive'
          });
          break;

        case 500:
        case 502:
        case 503:
          // Server errors
          toast({
            title: 'Server Error',
            description: 'Something went wrong on our end. Please try again.',
            variant: 'destructive'
          });
          break;

        default:
          // Other errors
          console.error('API Error:', error);
      }

      // Return structured error
      return Promise.reject({
        status,
        message: data.detail || error.message || 'An error occurred',
        data
      });
    } else if (error.request) {
      // Network error
      toast({
        title: 'Connection Error',
        description: 'Unable to connect to the server. Please check your internet connection.',
        variant: 'destructive'
      });
      
      return Promise.reject({
        status: 0,
        message: 'Network error - please check your connection',
        data: null
      });
    } else {
      // Request setup error
      console.error('Request setup error:', error.message);
      return Promise.reject({
        status: 0,
        message: error.message || 'Request failed',
        data: null
      });
    }

    return Promise.reject(error);
  }
);

// Authentication Service Class
class AuthService {
  // === Authentication Methods ===

  /**
   * Login with email and password
   */
  async login(loginData: LoginRequest): Promise<TokenResponse> {
    try {
      console.log('🔐 Attempting login for:', loginData.email);
      
      const response = await apiClient.post<TokenResponse>('/api/users/login', {
        tenant_id: loginData.tenant_id,
        email: loginData.email,
        password: loginData.password,
        remember_me: loginData.remember_me
      });

      console.log('✅ Login successful');
      return response.data;
    } catch (error: any) {
      console.error('❌ Login error:', error);
      throw error;
    }
  }

  /**
   * Login with Google OAuth
   */
  async googleOAuthLogin(oauthData: GoogleOAuthRequest): Promise<TokenResponse> {
    try {
      console.log('🔐 Attempting Google OAuth login for tenant:', oauthData.tenant_id);
      
      const response = await apiClient.post<TokenResponse>('/api/users/login/google', {
        tenant_id: oauthData.tenant_id,
        auth_code: oauthData.auth_code,
        role: oauthData.role || 'customer'
      });

      console.log('✅ Google OAuth login successful');
      return response.data;
    } catch (error: any) {
      console.error('❌ Google OAuth login error:', error);
      throw error;
    }
  }

  /**
   * Register new user
   */
  async register(registerData: RegisterRequest): Promise<UserResponse> {
    try {
      console.log('📝 Attempting registration for:', registerData.email);
      
      const response = await apiClient.post<UserResponse>('/api/users/register', {
        tenant_id: registerData.tenant_id,
        email: registerData.email,
        password: registerData.password,
        confirm_password: registerData.confirm_password,
        role: registerData.role,
        first_name: registerData.first_name,
        last_name: registerData.last_name,
        auth_provider: registerData.auth_provider || 'email'
      });

      console.log('✅ Registration successful');
      return response.data;
    } catch (error: any) {
      console.error('❌ Registration error:', error);
      throw error;
    }
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      // Call logout endpoint to invalidate server-side session
      await apiClient.post('/api/users/logout');
    } catch (error) {
      console.warn('Logout API call failed, continuing with local cleanup');
    } finally {
      // Clean up local storage
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_info');
      localStorage.removeItem('currentTenant');
      
      console.log('🚪 User logged out');
    }
  }

  // === User Profile Methods ===

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<UserResponse> {
    try {
      const response = await apiClient.get<UserResponse>('/api/users/me');
      return response.data;
    } catch (error: any) {
      console.error('❌ Get current user error:', error);
      throw error;
    }
  }

  /**
   * Update current user profile
   */
  async updateProfile(updateData: UserUpdateRequest): Promise<UserResponse> {
    try {
      console.log('📝 Updating user profile');
      
      const response = await apiClient.put<UserResponse>('/api/users/me', updateData);
      
      // Update stored user info
      localStorage.setItem('user_info', JSON.stringify(response.data));
      
      console.log('✅ Profile updated successfully');
      return response.data;
    } catch (error: any) {
      console.error('❌ Profile update error:', error);
      throw error;
    }
  }

  /**
   * Change user password
   */
  async changePassword(passwordData: PasswordChangeRequest): Promise<void> {
    try {
      console.log('🔑 Changing user password');
      
      await apiClient.post('/api/users/me/change-password', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
        confirm_password: passwordData.confirm_password
      });

      console.log('✅ Password changed successfully');
      
      // Show success message
      toast({
        title: 'Password Changed',
        description: 'Your password has been updated successfully. Please log in again.',
        variant: 'default'
      });

      // Force logout and redirect to login
      await this.logout();
      window.location.href = '/auth/login';
    } catch (error: any) {
      console.error('❌ Password change error:', error);
      throw error;
    }
  }

  // === Admin User Management Methods ===

  /**
   * Get paginated list of users (Admin only)
   */
  async getUsers(params: {
    role?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
  } = {}): Promise<UserListResponse> {
    try {
      const searchParams = new URLSearchParams();
      
      if (params.role) searchParams.append('role', params.role);
      if (params.is_active !== undefined) searchParams.append('is_active', params.is_active.toString());
      if (params.page) searchParams.append('page', params.page.toString());
      if (params.page_size) searchParams.append('page_size', params.page_size.toString());

      const response = await apiClient.get<UserListResponse>(`/api/users?${searchParams.toString()}`);
      return response.data;
    } catch (error: any) {
      console.error('❌ Get users error:', error);
      throw error;
    }
  }

  /**
   * Get user by ID (Admin only)
   */
  async getUserById(userId: string): Promise<UserResponse> {
    try {
      const response = await apiClient.get<UserResponse>(`/api/users/${userId}`);
      return response.data;
    } catch (error: any) {
      console.error('❌ Get user by ID error:', error);
      throw error;
    }
  }

  /**
   * Update user by ID (Admin only)
   */
  async updateUser(userId: string, updateData: UserUpdateRequest): Promise<UserResponse> {
    try {
      console.log(`📝 Updating user ${userId}`);
      
      const response = await apiClient.put<UserResponse>(`/api/users/${userId}`, updateData);
      
      console.log('✅ User updated successfully');
      return response.data;
    } catch (error: any) {
      console.error('❌ Update user error:', error);
      throw error;
    }
  }

  /**
   * Delete user by ID (Admin only) - Soft delete
   */
  async deleteUser(userId: string): Promise<void> {
    try {
      console.log(`🗑️ Deleting user ${userId}`);
      
      await apiClient.delete(`/api/users/${userId}`);
      
      console.log('✅ User deleted successfully');
      
      toast({
        title: 'User Deleted',
        description: 'User has been successfully deactivated.',
        variant: 'default'
      });
    } catch (error: any) {
      console.error('❌ Delete user error:', error);
      throw error;
    }
  }

  // === Utility Methods ===

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('auth_token');
    return !!token;
  }

  /**
   * Get stored user info
   */
  getCurrentUserInfo(): UserResponse | null {
    try {
      const userInfo = localStorage.getItem('user_info');
      return userInfo ? JSON.parse(userInfo) : null;
    } catch {
      return null;
    }
  }

  /**
   * Get stored tenant ID
   */
  getCurrentTenant(): string | null {
    return localStorage.getItem('currentTenant');
  }

  /**
   * Check if user has permission
   */
  hasPermission(permission: string): boolean {
    const userInfo = this.getCurrentUserInfo();
    return userInfo?.permissions?.includes(permission) || false;
  }

  /**
   * Check if user has role
   */
  hasRole(role: string): boolean {
    const userInfo = this.getCurrentUserInfo();
    return userInfo?.role === role;
  }

  /**
   * Get user's full name
   */
  getUserDisplayName(): string {
    const userInfo = this.getCurrentUserInfo();
    if (userInfo?.full_name) return userInfo.full_name;
    if (userInfo?.first_name) return userInfo.first_name;
    return userInfo?.email || 'User';
  }

  /**
   * Cleanup expired sessions (Admin only)
   */
  async cleanupSessions(): Promise<void> {
    try {
      await apiClient.post('/api/users/cleanup-sessions');
      
      toast({
        title: 'Sessions Cleaned',
        description: 'Expired sessions have been cleaned up successfully.',
        variant: 'default'
      });
    } catch (error: any) {
      console.error('❌ Session cleanup error:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const authService = new AuthService();

// Export types for use in components
export type {
  LoginRequest,
  GoogleOAuthRequest,
  RegisterRequest,
  UserResponse,
  TokenResponse,
  UserUpdateRequest,
  PasswordChangeRequest,
  UserListResponse
};