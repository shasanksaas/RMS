import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import { authService } from './services/authService';

// Auth Components
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import GoogleCallback from './components/auth/GoogleCallback';
import ForgotPassword from './components/auth/ForgotPassword';
import { ToastProvider } from './components/ui/use-toast';

// Layout Components
import MerchantLayout from './components/layout/MerchantLayout';
import CustomerLayout from './components/layout/CustomerLayout';
import AdminLayout from './components/layout/AdminLayout';

// Merchant App Pages
import Dashboard from './pages/merchant/Dashboard';
import AllReturns from './pages/merchant/returns/AllReturns';
import ReturnDetail from './pages/merchant/returns/ReturnDetail';
import CreateReturnMerchant from './pages/merchant/returns/CreateReturn';
import Orders from './pages/merchant/Orders';
import OrderDetail from './pages/merchant/OrderDetail';
import Rules from './pages/merchant/Rules';
import Workflows from './pages/merchant/Workflows';
import Analytics from './pages/merchant/Analytics';
import Billing from './pages/merchant/Billing';
import GeneralSettings from './pages/merchant/settings/General';
import BrandingSettings from './pages/merchant/settings/Branding';
import EmailSettings from './pages/merchant/settings/Email';
import IntegrationsSettings from './pages/merchant/settings/Integrations';
import TeamSettings from './pages/merchant/settings/Team';
import OnboardingWizard from './pages/merchant/Onboarding';

// Customer Portal Pages
import CustomerStart from './pages/customer/Start';
import CustomerCreateReturn from './pages/customer/CreateReturn';
import CustomerReturnConfirmation from './pages/customer/ReturnConfirmation';
import CustomerSelectItems from './pages/customer/SelectItems';
import CustomerResolution from './pages/customer/Resolution';
import CustomerConfirm from './pages/customer/Confirm';
import CustomerStatus from './pages/customer/Status';
import ReturnPortal from './pages/customer/ReturnPortal';

// Admin Pages
import AdminTenants from './pages/admin/Tenants';
import AdminOperations from './pages/admin/Operations';
import AdminAudit from './pages/admin/Audit';
import AdminFeatureFlags from './pages/admin/FeatureFlags';
import AdminCatalog from './pages/admin/Catalog';

import './App.css';

// Simple Auth Context
const AuthContext = React.createContext();

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Simple Auth Provider
const SimpleAuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const userInfo = localStorage.getItem('user_info');
    
    if (token && userInfo) {
      try {
        setUser(JSON.parse(userInfo));
        setIsAuthenticated(true);
      } catch (e) {
        localStorage.clear();
      }
    }
    
    setIsLoading(false);
  }, []);

  const login = async (loginData) => {
    const response = await authService.login(loginData);
    localStorage.setItem('auth_token', response.access_token);
    localStorage.setItem('user_info', JSON.stringify(response.user));
    setUser(response.user);
    setIsAuthenticated(true);
    return response;
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Simple Protected Route
const SimpleProtectedRoute = ({ children, requiredRole }) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const navigate = useNavigate();

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    const redirectPath = user?.role === 'admin' ? '/admin/dashboard' : 
                        user?.role === 'merchant' ? '/app/dashboard' : '/returns/start';
    return <Navigate to={redirectPath} replace />;
  }

  return children;
};

// Main App Component
const App = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <ErrorBoundary>
      <ToastProvider>
        <SimpleAuthProvider>
          <BrowserRouter>
            <Routes>
              {/* Auth Routes */}
              <Route path="/auth/login" element={<Login />} />
              <Route path="/auth/register" element={<Register />} />
              <Route path="/auth/forgot-password" element={<ForgotPassword />} />
              <Route path="/auth/google/callback" element={<GoogleCallback />} />

              {/* Customer Portal Routes */}
              <Route path="/returns" element={<CustomerLayout />}>
                <Route path="start" element={<CustomerStart />} />
                <Route path="create" element={<CustomerCreateReturn />} />
                <Route path="confirmation/:returnId" element={<CustomerReturnConfirmation />} />
                <Route path="select" element={<CustomerSelectItems />} />
                <Route path="resolution" element={<CustomerResolution />} />
                <Route path="confirm" element={<CustomerConfirm />} />
                <Route path="status/:returnId" element={<CustomerStatus />} />
                <Route index element={<Navigate to="/returns/start" replace />} />
              </Route>

              {/* Public Portal Routes */}
              <Route path="/portal/returns/start" element={<ReturnPortal />} />
              <Route path="/portal/returns/confirmation/:returnId" element={<CustomerReturnConfirmation />} />

              {/* Merchant App Routes */}
              <Route path="/app" element={
                <SimpleProtectedRoute requiredRole="merchant">
                  <MerchantLayout isOnline={isOnline} />
                </SimpleProtectedRoute>
              }>
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="returns" element={<AllReturns />} />
                <Route path="returns/create" element={<CreateReturnMerchant />} />
                <Route path="returns/:id" element={<ReturnDetail />} />
                <Route path="orders" element={<Orders />} />
                <Route path="orders/:orderId" element={<OrderDetail />} />
                <Route path="rules" element={<Rules />} />
                <Route path="workflows" element={<Workflows />} />
                <Route path="analytics" element={<Analytics />} />
                <Route path="billing" element={<Billing />} />
                <Route path="settings/general" element={<GeneralSettings />} />
                <Route path="settings/branding" element={<BrandingSettings />} />
                <Route path="settings/email" element={<EmailSettings />} />
                <Route path="settings/integrations" element={<IntegrationsSettings />} />
                <Route path="settings/team" element={<TeamSettings />} />
                <Route path="onboarding" element={<OnboardingWizard />} />
                <Route index element={<Navigate to="/app/dashboard" replace />} />
              </Route>

              {/* Admin Routes */}
              <Route path="/admin" element={
                <SimpleProtectedRoute requiredRole="admin">
                  <AdminLayout />
                </SimpleProtectedRoute>
              }>
                <Route path="dashboard" element={<div>Admin Dashboard</div>} />
                <Route path="tenants" element={<AdminTenants />} />
                <Route path="ops" element={<AdminOperations />} />
                <Route path="audit" element={<AdminAudit />} />
                <Route path="flags" element={<AdminFeatureFlags />} />
                <Route path="catalog" element={<AdminCatalog />} />
                <Route index element={<Navigate to="/admin/dashboard" replace />} />
              </Route>

              {/* Default Routes */}
              <Route path="/" element={<Navigate to="/auth/login" replace />} />
              <Route path="/dashboard" element={<Navigate to="/app/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/auth/login" replace />} />
            </Routes>
          </BrowserRouter>
        </SimpleAuthProvider>
      </ToastProvider>
    </ErrorBoundary>
  );
};

export default App;