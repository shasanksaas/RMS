import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';

// Auth Components
import AuthProvider from './contexts/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AuthGuard from './components/auth/AuthGuard';

// Shopify OAuth Components (for Merchants)
import ShopifyLogin from './components/auth/ShopifyLogin';

// Admin Components (separate email/password login)
import AdminLogin from './components/auth/AdminLogin';

// Dashboard Components  
import ConnectedDashboard from './components/dashboard/ConnectedDashboard';

// Legacy Auth (Now used for simple email/password login)  
import Login from './components/auth/Login.tsx';
// import Register from './components/auth/Register.tsx';
// import GoogleCallback from './components/auth/GoogleCallback';
// import ForgotPassword from './components/auth/ForgotPassword';

import { ToastProvider } from './components/ui/use-toast';

import SimpleLogin from './components/SimpleLogin';

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
import TenantManager from './pages/admin/TenantManager';

// Public Pages
import MerchantSignup from './pages/public/MerchantSignup';

import './App.css';

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
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              {/* Simple Email/Password Login for Returns Portal */}
              <Route path="/auth/login" element={<Login />} />
              <Route path="/login" element={<Login />} />
              
              {/* Shopify OAuth (moved to different route) */}
              <Route path="/auth/shopify" element={<ShopifyLogin />} />
              
              {/* Admin Login Route - Email/Password */}
              <Route path="/admin/login" element={<AdminLogin />} />
              
              {/* Legacy Auth Routes (Disabled) */}
              {/* 
              <Route path="/auth/register" element={<Register />} />
              <Route path="/auth/forgot-password" element={<ForgotPassword />} />
              <Route path="/auth/google/callback" element={<GoogleCallback />} />
              */}

              {/* Public Merchant Signup Routes (Legacy - may be removed) */}
              <Route path="/signup" element={<MerchantSignup />} />
              <Route path="/signup/:tenantId" element={<MerchantSignup />} />
              
              {/* Simple Login Test Route */}
              <Route path="/simple-login" element={<SimpleLogin />} />

              {/* Customer Portal Routes (Some Public, Some Protected) */}
              <Route path="/returns" element={<CustomerLayout />}>
                <Route path="start" element={<CustomerStart />} />
                <Route path="create" element={<CustomerCreateReturn />} />
                <Route path="confirmation/:returnId" element={<CustomerReturnConfirmation />} />
                <Route path="select" element={<CustomerSelectItems />} />
                <Route path="resolution" element={<CustomerResolution />} />
                <Route path="confirm" element={<CustomerConfirm />} />
                <Route path="status/:returnId" element={<CustomerStatus />} />
                <Route path="status/:returnId" element={<CustomerStatus />} />
                <Route index element={<Navigate to="/returns/start" replace />} />
              </Route>

              {/* Public Portal Routes */}
              <Route path="/portal/returns/start" element={<ReturnPortal />} />
              <Route path="/portal/returns/confirmation/:returnId" element={<CustomerReturnConfirmation />} />

              {/* Legacy customer route */}
              <Route path="/customer" element={<Navigate to="/returns/start" replace />} />

              {/* Merchant App Routes (Protected - Merchant Role Required) */}
              <Route path="/app" element={
                <ProtectedRoute requiredRole="merchant">
                  <MerchantLayout isOnline={isOnline} />
                </ProtectedRoute>
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

              {/* Super Admin Routes (Protected - Admin Role Required) */}
              <Route path="/admin" element={
                <ProtectedRoute requiredRole="admin">
                  <AdminLayout />
                </ProtectedRoute>
              }>
                <Route path="tenants" element={<TenantManager />} />
                <Route path="ops" element={<AdminOperations />} />
                <Route path="audit" element={<AdminAudit />} />
                <Route path="flags" element={<AdminFeatureFlags />} />
                <Route path="catalog" element={<AdminCatalog />} />
                <Route index element={<Navigate to="/admin/tenants" replace />} />
              </Route>

              {/* Default Routes */}
              <Route path="/" element={<Navigate to="/auth/login" replace />} />
              <Route path="/dashboard" element={<Navigate to="/app/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/auth/login" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </ErrorBoundary>
  );
};

export default App;