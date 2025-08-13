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

  // Initialize authentication state - RUNS ONLY ONCE
  useEffect(() => {
    let isMounted = true; // Track if component is mounted to prevent state updates after unmount
    
    const initAuth = async () => {
      try {
        // Check for OAuth token in URL parameters (from Shopify OAuth callback)
        const urlParams = new URLSearchParams(window.location.search);
        const oauthToken = urlParams.get('token');
        const connected = urlParams.get('connected');
        const tenantId = urlParams.get('tenant_id');
        
        if (oauthToken && isMounted) {
          console.log('🔄 OAuth token detected in URL - logging in user');
          
          // Store the token and try to fetch user info
          authService.setToken(oauthToken);
          
          try {
            // Fetch user profile with the OAuth token
            const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/users/profile`, {
              headers: {
                'Authorization': `Bearer ${oauthToken}`,
                'Content-Type': 'application/json'
              }
            });
            
            if (response.ok) {
              const userData = await response.json();
              
              // Create user and tenant objects
              const user = {
                user_id: userData.user_id,
                email: userData.email,
                role: userData.role,
                tenant_id: userData.tenant_id,
                auth_provider: "shopify_oauth",
                permissions: userData.permissions || ["read", "write"]
              };
              
              const tenant = {
                tenant_id: userData.tenant_id,
                name: userData.tenant_name || `Tenant ${userData.tenant_id}`
              };
              
              // Store user and tenant info
              authService.setUserData(user, tenant);
              
              setUser(user);
              setTenant(tenant);
              setIsAuthenticated(true);
              
              console.log('✅ OAuth login successful:', user);
              
              // Clean up URL parameters
              const newUrl = new URL(window.location);
              newUrl.searchParams.delete('token');
              window.history.replaceState({}, '', newUrl);
              
              if (isMounted) {
                setIsLoading(false);
              }
              return;
            } else {
              console.error('❌ Failed to fetch user profile with OAuth token');
              authService.clearAuthData();
            }
          } catch (profileError) {
            console.error('❌ Error fetching user profile:', profileError);
            authService.clearAuthData();
          }
        }
        
        // Check if user is authenticated (regular or impersonation)
        const token = authService.getToken();
        
        if (token && isMounted) {
          // Check if this is an impersonation session
          if (authService.isImpersonationSession()) {
            const impersonationInfo = authService.getImpersonationInfo();
            
            if (impersonationInfo.isImpersonating) {
              // Set up impersonation session
              const impersonatedUser = {
                user_id: impersonationInfo.originalUserId,
                email: impersonationInfo.originalAdminEmail,
                role: "merchant",  // Admin is impersonating as merchant
                tenant_id: impersonationInfo.tenantId,
                auth_provider: "impersonation",
                permissions: ["read", "write", "delete", "admin"], // Admin has full permissions
                isImpersonating: true,
                originalAdminEmail: impersonationInfo.originalAdminEmail
              };
              
              const tenant = {
                tenant_id: impersonationInfo.tenantId,
                name: `Impersonated Tenant (${impersonationInfo.tenantId})`
              };
              
              setUser(impersonatedUser);
              setTenant(tenant);
              setIsAuthenticated(true);
              
              console.log('🔐 Impersonation session detected:', impersonatedUser);
              return;
            }
          }
          
          // Regular authentication session
          const userInfo = authService.getCurrentUserFromStorage();
          const tenantInfo = authService.getCurrentTenantFromStorage();
          
          if (userInfo && tenantInfo) {
            setUser(userInfo);
            setTenant(tenantInfo);
            setIsAuthenticated(true);
          } else {
            // Token exists but no user info - clear everything
            authService.clearAuthData();
            setUser(null);
            setTenant(null);
            setIsAuthenticated(false);
          }
        } else if (isMounted) {
          setUser(null);
          setTenant(null);
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        if (isMounted) {
          authService.clearAuthData();
          setUser(null);
          setTenant(null);
          setIsAuthenticated(false);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    initAuth();
    
    return () => {
      isMounted = false; // Cleanup flag
    };
  }, []); // Empty dependency array - runs only once

  const login = async (loginData) => {
    console.log('🔐 AuthContext.login called with:', loginData);
    try {
      const response = await authService.login(loginData);
      console.log('📡 AuthService.login response:', response);
      
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

      console.log('✅ AuthContext state updated, user:', response.user);
      return response;
    } catch (error) {
      console.error('❌ AuthContext.login error:', error);
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
        return '/admin/tenants';
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