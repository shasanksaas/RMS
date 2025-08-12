import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const ProtectedRoute = ({ 
  children, 
  requireAuth = true, 
  requiredRole = null,
  requiredPermissions = [],
  redirectTo = null 
}) => {
  const { isAuthenticated, isLoading, user, hasRole, hasPermission, getRedirectPath } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // If authentication is required but user is not authenticated
  if (requireAuth && !isAuthenticated) {
    // Check if we're already navigating to a login page (logout scenario)
    const isNavigatingToLogin = location.pathname === '/auth/login' || location.pathname === '/admin/login';
    
    if (isNavigatingToLogin) {
      // Don't interfere with logout navigation - let the user reach their intended login page
      return children;
    }
    
    // Determine appropriate login page based on route for normal unauthenticated access
    const isAdminRoute = location.pathname.startsWith('/admin');
    const loginUrl = isAdminRoute 
      ? `/admin/login?return_url=${encodeURIComponent(location.pathname)}`
      : `/auth/login?return_url=${encodeURIComponent(location.pathname)}`;
    return <Navigate to={loginUrl} replace />;
  }

  // If user is authenticated but authentication is not required (e.g., login page)
  if (!requireAuth && isAuthenticated) {
    const fallbackRedirect = redirectTo || (user ? getRedirectPath(user.role) : '/app/dashboard');
    return <Navigate to={fallbackRedirect} replace />;
  }

  // Check role requirements
  if (requireAuth && requiredRole && !hasRole(requiredRole)) {
    // Redirect to appropriate dashboard based on user's actual role
    const userDashboard = getRedirectPath(user.role);
    return <Navigate to={userDashboard} replace />;
  }

  // Check permission requirements
  if (requireAuth && requiredPermissions.length > 0) {
    const hasRequiredPermissions = requiredPermissions.every(permission => 
      hasPermission(permission)
    );
    
    if (!hasRequiredPermissions) {
      // Redirect to appropriate dashboard with access denied message
      const userDashboard = getRedirectPath(user.role);
      return <Navigate to={`${userDashboard}?error=access_denied`} replace />;
    }
  }

  // All checks passed, render children
  return children;
};

export default ProtectedRoute;