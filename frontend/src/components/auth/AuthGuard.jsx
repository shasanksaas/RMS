import React, { useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

/**
 * AuthGuard component to handle authentication redirects and checks
 * Can be used to wrap components or pages that need authentication logic
 */
const AuthGuard = ({ 
  children, 
  requireAuth = true,
  redirectOnAuth = false,
  checkTokenValidity = true 
}) => {
  const { isAuthenticated, isLoading, user, getCurrentUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleAuthCheck = async () => {
      // Don't do anything while auth is loading
      if (isLoading) return;

      try {
        // If we require auth but user is not authenticated
        if (requireAuth && !isAuthenticated) {
          const returnUrl = location.pathname !== '/auth/login' ? location.pathname : '/';
          navigate(`/auth/login?return_url=${encodeURIComponent(returnUrl)}`, { replace: true });
          return;
        }

        // If we don't want authenticated users (like login page) but user is authenticated
        if (redirectOnAuth && isAuthenticated) {
          const dashboardPath = getDashboardPath(user?.role);
          navigate(dashboardPath, { replace: true });
          return;
        }

        // Validate token periodically if authenticated
        if (checkTokenValidity && isAuthenticated) {
          try {
            await getCurrentUser();
          } catch (error) {
            console.error('Token validation failed:', error);
            // Token is invalid, user will be logged out by AuthContext
          }
        }
      } catch (error) {
        console.error('AuthGuard error:', error);
      }
    };

    handleAuthCheck();
  }, [
    isAuthenticated, 
    isLoading, 
    user, 
    requireAuth, 
    redirectOnAuth, 
    checkTokenValidity,
    navigate, 
    location, 
    getCurrentUser
  ]);

  // Show loading while authentication state is being determined
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading...</h2>
          <p className="text-gray-600">Checking authentication status...</p>
        </div>
      </div>
    );
  }

  return children;
};

// Helper function to get dashboard path based on role
const getDashboardPath = (role) => {
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

export default AuthGuard;