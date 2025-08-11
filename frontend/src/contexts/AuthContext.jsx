import React, { createContext, useState, useContext, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [tenant, setTenant] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize authentication state
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Check if user is authenticated
        if (authService.isAuthenticated()) {
          const userInfo = authService.getCurrentUserFromStorage();
          const tenantInfo = authService.getCurrentTenantFromStorage();
          
          if (userInfo && tenantInfo) {
            // Validate token with backend
            const isValidToken = await authService.validateToken();
            
            if (isValidToken) {
              setUser(userInfo);
              setTenant(tenantInfo);
              setIsAuthenticated(true);
            } else {
              // Token is invalid, clear auth data
              authService.clearAuthData();
              setUser(null);
              setTenant(null);
              setIsAuthenticated(false);
            }
          } else {
            // No user info, not authenticated
            setUser(null);
            setTenant(null);
            setIsAuthenticated(false);
          }
        } else {
          // Not authenticated
          setUser(null);
          setTenant(null);
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        // Clear invalid auth data
        authService.clearAuthData();
        setUser(null);
        setTenant(null);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []); // Empty dependency array to run only once

  const login = async (loginData) => {
    try {
      const response = await authService.login(loginData);
      
      // Store authentication data
      localStorage.setItem('auth_token', response.access_token);
      localStorage.setItem('currentTenant', loginData.tenant_id);
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token);
      }
      localStorage.setItem('user_info', JSON.stringify(response.user));

      // Update context state
      setUser(response.user);
      setTenant(loginData.tenant_id);
      setIsAuthenticated(true);

      return response;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const loginWithGoogle = async (oauthData) => {
    try {
      const response = await authService.loginWithGoogle(oauthData);
      
      // Store authentication data
      localStorage.setItem('auth_token', response.access_token);
      localStorage.setItem('currentTenant', oauthData.tenant_id);
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token);
      }
      localStorage.setItem('user_info', JSON.stringify(response.user));

      // Update context state
      setUser(response.user);
      setTenant(oauthData.tenant_id);
      setIsAuthenticated(true);

      return response;
    } catch (error) {
      console.error('Google OAuth login error:', error);
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      const userResponse = await authService.register(userData);
      
      // Auto-login after registration
      const loginResponse = await login({
        tenant_id: userData.tenant_id,
        email: userData.email,
        password: userData.password,
        remember_me: false
      });

      return { user: userResponse, login: loginResponse };
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
      // Continue with logout even if API call fails
    } finally {
      // Always clear local state and storage
      authService.clearAuthData();
      setUser(null);
      setTenant(null);
      setIsAuthenticated(false);
    }
  };

  const updateProfile = async (userData) => {
    try {
      const updatedUser = await authService.updateProfile(userData);
      
      // Update stored user info and context state
      localStorage.setItem('user_info', JSON.stringify(updatedUser));
      setUser(updatedUser);
      
      return updatedUser;
    } catch (error) {
      console.error('Profile update error:', error);
      throw error;
    }
  };

  const changePassword = async (passwordData) => {
    try {
      const response = await authService.changePassword(passwordData);
      
      // Password change requires re-authentication
      // Clear current session but keep user info for login form
      const currentEmail = user?.email;
      const currentTenant = tenant;
      
      await logout();
      
      return { 
        success: true, 
        message: response.message,
        email: currentEmail,
        tenant_id: currentTenant
      };
    } catch (error) {
      console.error('Password change error:', error);
      throw error;
    }
  };

  const refreshToken = async () => {
    try {
      const response = await authService.refreshToken();
      
      // Update stored tokens
      localStorage.setItem('auth_token', response.access_token);
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token);
      }
      
      return response;
    } catch (error) {
      console.error('Token refresh error:', error);
      // If refresh fails, logout user
      await logout();
      throw error;
    }
  };

  const getCurrentUser = async () => {
    try {
      const userInfo = await authService.getCurrentUser();
      
      // Update stored user info and context state
      localStorage.setItem('user_info', JSON.stringify(userInfo));
      setUser(userInfo);
      
      return userInfo;
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  };

  // Helper functions
  const hasPermission = (permission) => {
    return user?.permissions?.includes(permission) || false;
  };

  const hasRole = (role) => {
    return user?.role === role;
  };

  const isMerchant = () => hasRole('merchant');
  const isCustomer = () => hasRole('customer');
  const isAdmin = () => hasRole('admin');

  const getRedirectPath = (userRole = null) => {
    const role = userRole || user?.role;
    
    switch (role) {
      case 'merchant':
        return '/app/dashboard';
      case 'admin':
        return '/admin/dashboard';
      case 'customer':
        return '/returns/start';
      default:
        return '/app/dashboard';
    }
  };

  const contextValue = {
    // State
    user,
    tenant,
    isAuthenticated,
    isLoading,
    
    // Authentication methods
    login,
    loginWithGoogle,
    register,
    logout,
    
    // User management
    updateProfile,
    changePassword,
    getCurrentUser,
    refreshToken,
    
    // Helper functions
    hasPermission,
    hasRole,
    isMerchant,
    isCustomer,
    isAdmin,
    getRedirectPath,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;